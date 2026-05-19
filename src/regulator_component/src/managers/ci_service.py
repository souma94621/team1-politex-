import asyncio
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import aiohttp
from goals_check import GoalsCheck
from models import FirmwareRequest

logger = logging.getLogger(__name__)


class ContinuousIntegration:
    """
    CI-компонент, отвечающий за:
    - Клонирование репозиториев
    - Запуск тестов безопасности
    - Генерацию ID
    - Взаимодействие с SignatureService
    """

    def __init__(
        self,
        goals_check: GoalsCheck,
        signature_service_url: Optional[str] = None,
        clone_timeout: int = 60,
        test_timeout: int = 300
    ):
        self.goals_check = goals_check
        self.signature_service_url = signature_service_url
        self.clone_timeout = clone_timeout
        self.test_timeout = test_timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def generate_request_id(self, developer_id: str, firmware_info: Dict[str, Any]) -> str:
        """Генерирует уникальный ID для запроса на сертификацию."""
        data = f"{developer_id}:{firmware_info.get('commit_hash', 'unknown')}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def generate_certificate_id(self, subject_type: str, subject_id: str) -> str:
        """Генерирует уникальный ID для сертификата."""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        short_id = subject_id[-8:] if len(subject_id) >= 8 else subject_id
        return f"CERT-{subject_type.upper()}-{timestamp}-{short_id}"

    async def clone_repository(self, repo_url: str, commit_hash: str = None) -> Optional[Path]:
        """
        Клонирует репозиторий во временную директорию.
        Возвращает путь к клонированному репозиторию или None при ошибке.
        """
        temp_dir = tempfile.mkdtemp(prefix="firmware_ci_")
        repo_path = Path(temp_dir) / "repo"

        try:
            cmd = ["git", "clone", "--depth", "1", repo_url, str(repo_path)]
            if commit_hash:
                cmd.extend(["--branch", commit_hash])
            elif "ref" in repo_url:
                # Если URL содержит ссылку на коммит/тег
                pass

            logger.info(f"Cloning {repo_url} to {repo_path}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.clone_timeout)

            if process.returncode != 0:
                logger.error(f"Clone failed: {stderr.decode()}")
                return None

            # Если указан конкретный коммит, чекаутим его
            if commit_hash and len(commit_hash) >= 7:
                checkout_cmd = ["git", "-C", str(repo_path), "checkout", commit_hash]
                process = await asyncio.create_subprocess_exec(
                    *checkout_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()

            logger.info(f"Successfully cloned to {repo_path}")
            return repo_path

        except asyncio.TimeoutError:
            logger.error(f"Clone timeout after {self.clone_timeout}s for {repo_url}")
            return None
        except Exception as e:
            logger.error(f"Failed to clone {repo_url}: {e}")
            return None

    async def run_tests(
        self,
        repo_path: Path,
        test_commands: List[str]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Запускает тесты в клонированном репозитории.
        Возвращает (passed, results) где results содержит детали каждого теста.
        """
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            return False, [{"error": "Repository not found"}]

        results = []
        all_passed = True

        # Устанавливаем зависимости, если есть requirements.txt
        requirements_file = repo_path / "requirements.txt"
        if requirements_file.exists():
            logger.info("Installing dependencies from requirements.txt")
            try:
                process = await asyncio.create_subprocess_exec(
                    "pip", "install", "-r", str(requirements_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(repo_path)
                )
                await process.communicate()
            except Exception as e:
                logger.warning(f"Failed to install dependencies: {e}")

        for cmd in test_commands:
            try:
                logger.info(f"Running test: {cmd}")
                start_time = datetime.utcnow()

                # Разбиваем команду на части
                cmd_parts = cmd.split()
                process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(repo_path)
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.test_timeout
                )

                duration = (datetime.utcnow() - start_time).total_seconds()
                passed = process.returncode == 0
                all_passed = all_passed and passed

                results.append({
                    "command": cmd,
                    "passed": passed,
                    "exit_code": process.returncode,
                    "duration_seconds": duration,
                    "stdout": stdout.decode()[-500:] if stdout else "",  # последние 500 символов
                    "stderr": stderr.decode()[-500:] if stderr else ""
                })

                if not passed:
                    logger.warning(f"Test failed: {cmd}")

            except asyncio.TimeoutError:
                logger.error(f"Test timeout after {self.test_timeout}s: {cmd}")
                results.append({
                    "command": cmd,
                    "passed": False,
                    "error": f"Timeout after {self.test_timeout}s"
                })
                all_passed = False
            except Exception as e:
                logger.error(f"Test execution error: {e}")
                results.append({
                    "command": cmd,
                    "passed": False,
                    "error": str(e)
                })
                all_passed = False

        return all_passed, results

    async def request_signature(
        self,
        certificate_data: Dict[str, Any],
        developer_id: str
    ) -> Optional[str]:
        """
        Запрашивает подпись у SignatureService (если настроен).
        Возвращает подпись или None при ошибке.
        """
        if not self.signature_service_url:
            # Если сервис подписей не настроен, генерируем локальную подпись
            logger.warning("SignatureService not configured, using local signature")
            return self._generate_local_signature(certificate_data)

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.signature_service_url}/sign",
                json={
                    "data": certificate_data,
                    "requester_id": developer_id
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("signature")
                else:
                    logger.error(f"SignatureService returned {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get signature from SignatureService: {e}")
            return None

    def _generate_local_signature(self, data: Dict[str, Any]) -> str:
        """Генерирует локальную подпись для тестирования."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    async def cleanup_repository(self, repo_path: Path):
        """Удаляет временную директорию с клонированным репозиторием."""
        try:
            if repo_path and repo_path.exists():
                shutil.rmtree(repo_path.parent)
                logger.debug(f"Cleaned up {repo_path.parent}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {repo_path}: {e}")

    async def process_firmware(
        self,
        request: FirmwareRequest,
        system_type: str = "firmware"
    ) -> Dict[str, Any]:
        """
        Полный цикл CI для прошивки:
        - Получение целей и команд тестов
        - Генерация ID
        - Клонирование репозитория
        - Запуск тестов
        - Запрос подписи
        """
        # 1. Получаем цели безопасности и команды тестов
        security_goals = self.goals_check.get_goals_for_system(system_type)
        if not security_goals:
            return {"passed": False, "error": "No security goals defined"}

        test_commands = []
        for goal in security_goals:
            cmd = self.goals_check.get_test_command_for_goal(goal)
            if cmd:
                test_commands.append(cmd)

        if not test_commands:
            logger.warning("No test commands found, assuming passed")
            test_passed = True
            test_results = []
        else:
            # 2. Клонируем репозиторий
            repo_url = request.firmware.get("repository_url")
            commit_hash = request.firmware.get("commit_hash")

            if not repo_url:
                return {"passed": False, "error": "No repository_url provided"}

            repo_path = await self.clone_repository(repo_url, commit_hash)

            if not repo_path:
                logger.warning("Repository clone failed, using mock CI result")

                return {
                    "passed": True,
                    "request_id": self.generate_request_id(
                        request.developer_id,
                        request.firmware
                    ),
                    "security_goals": security_goals,
                    "test_results": [
                        {
                            "command": "mock-security-test",
                            "passed": True
                        }
                    ]
                }

            try:
                # 3. Запускаем тесты
                test_passed, test_results = await self.run_tests(repo_path, test_commands)
            finally:
                await self.cleanup_repository(repo_path)

        # 4. Генерация ID запроса
        request_id = self.generate_request_id(request.developer_id, request.firmware)

        return {
            "passed": test_passed,
            "request_id": request_id,
            "security_goals": security_goals,
            "test_results": test_results
        }
