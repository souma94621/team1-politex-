import asyncio
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """Информация о версии Регулятора."""
    version: str
    release_date: str
    download_url: str
    signature_url: str
    checksum: str
    changelog: List[str]
    min_compatible_version: str
    is_critical: bool = False


class UpdateError(Exception):
    """Исключение при обновлении."""
    pass


class UpdaterService:
    """
    Сервис безопасного обновления Регулятора (шаблон А.10).
    Проверяет подписи, скачивает обновления, выполняет обновление с откатом.
    """

    def __init__(
        self,
        update_server_url: str,
        public_key_path: str,
        current_version: str,
        app_path: Path,
        backup_path: Optional[Path] = None,
        check_interval_hours: int = 24
    ):
        self.update_server_url = update_server_url.rstrip('/')
        self.public_key_path = Path(public_key_path)
        self.current_version = current_version
        self.app_path = Path(app_path)
        self.backup_path = backup_path or Path(app_path.parent / f"{app_path.name}_backup")
        self.check_interval_hours = check_interval_hours
        self._session: Optional[aiohttp.ClientSession] = None
        self._verification_key = None
        self._load_verification_key()

    def _load_verification_key(self):
        """Загружает публичный ключ для проверки подписей обновлений."""
        try:
            with open(self.public_key_path, "rb") as key_file:
                self._verification_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )
            logger.info(f"Loaded verification key from {self.public_key_path}")
        except Exception as e:
            logger.error(f"Failed to load verification key: {e}")
            raise UpdateError(f"Cannot load verification key: {e}")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def check_for_updates(self) -> Optional[VersionInfo]:
        """
        Проверяет наличие обновлений на сервере.
        Возвращает VersionInfo или None, если обновлений нет.
        """
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.update_server_url}/api/version/latest",
                params={"current": self.current_version},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 204:
                    logger.info("No updates available")
                    return None
                if resp.status != 200:
                    logger.error(f"Update check failed: {resp.status}")
                    return None

                data = await resp.json()
                version_info = VersionInfo(
                    version=data["version"],
                    release_date=data["release_date"],
                    download_url=data["download_url"],
                    signature_url=data["signature_url"],
                    checksum=data["checksum"],
                    changelog=data.get("changelog", []),
                    min_compatible_version=data.get("min_compatible_version", "0.0.0"),
                    is_critical=data.get("is_critical", False)
                )

                logger.info(f"Found update: {self.current_version} -> {version_info.version}")
                return version_info

        except asyncio.TimeoutError:
            logger.error("Update check timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return None

    async def download_update(self, version_info: VersionInfo, target_path: Path) -> bool:
        """
        Скачивает обновление по URL.
        Возвращает True при успехе.
        """
        try:
            session = await self._get_session()
            async with session.get(
                version_info.download_url,
                timeout=aiohttp.ClientTimeout(total=300)  # 5 минут на скачивание
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Download failed: {resp.status}")
                    return False

                with open(target_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)

            # Проверяем контрольную сумму
            if not await self._verify_checksum(target_path, version_info.checksum):
                logger.error("Checksum verification failed")
                target_path.unlink(missing_ok=True)
                return False

            logger.info(f"Downloaded update to {target_path}")
            return True

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    async def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Проверяет SHA-256 контрольную сумму файла."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual = sha256.hexdigest()
        return actual == expected_checksum

    async def verify_signature(self, file_path: Path, signature_url: str) -> bool:
        """
        Проверяет цифровую подпись обновления.
        Использует асимметричную криптографию (RSA/ECDSA).
        """
        try:
            session = await self._get_session()
            async with session.get(signature_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to download signature: {resp.status}")
                    return False
                signature = await resp.read()

            # Читаем файл обновления
            with open(file_path, "rb") as f:
                update_data = f.read()

            # Проверяем подпись
            self._verification_key.verify(
                signature,
                update_data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            logger.info("Signature verification successful")
            return True

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    async def create_backup(self) -> bool:
        """Создаёт резервную копию текущей версии Регулятора."""
        try:
            if self.backup_path.exists():
                shutil.rmtree(self.backup_path)
            shutil.copytree(self.app_path, self.backup_path)
            logger.info(f"Backup created at {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    async def restore_backup(self) -> bool:
        """Восстанавливает Регулятор из резервной копии при неудачном обновлении."""
        try:
            if not self.backup_path.exists():
                logger.error("No backup found to restore")
                return False

            # Останавливаем текущий процесс
            # В реальной системе здесь должен быть graceful shutdown

            # Восстанавливаем
            shutil.rmtree(self.app_path)
            shutil.copytree(self.backup_path, self.app_path)
            logger.info(f"Restored from backup {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    async def apply_update(self, update_path: Path) -> bool:
        """
        Применяет обновление.
        Поддерживает два формата:
        - Архив (.tar.gz, .zip) с новыми файлами
        - Скрипт обновления (update.sh)
        """
        try:
            if update_path.suffix == '.tar.gz':
                import tarfile
                with tarfile.open(update_path, "r:gz") as tar:
                    tar.extractall(self.app_path)
            elif update_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(update_path, 'r') as zip_ref:
                    zip_ref.extractall(self.app_path)
            elif update_path.suffix == '.sh':
                # Выполняем скрипт обновления
                os.chmod(update_path, 0o755)
                process = await asyncio.create_subprocess_exec(
                    str(update_path),
                    str(self.app_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
                if process.returncode != 0:
                    logger.error(f"Update script failed: {stderr.decode()}")
                    return False
            else:
                # Просто копируем файл (если это отдельный файл, например, новый executable)
                shutil.copy2(update_path, self.app_path / update_path.name)

            logger.info("Update applied successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            return False

    async def update_version_file(self, new_version: str):
        """Обновляет файл с текущей версией Регулятора."""
        version_file = self.app_path / "version.json"
        try:
            with open(version_file, "w") as f:
                json.dump({
                    "version": new_version,
                    "updated_at": datetime.utcnow().isoformat()
                }, f, indent=2)
            self.current_version = new_version
            logger.info(f"Updated version file to {new_version}")
        except Exception as e:
            logger.error(f"Failed to update version file: {e}")

    async def perform_update(self, version_info: VersionInfo) -> Dict[str, Any]:
        """
        Полный цикл безопасного обновления:
        1. Создание резервной копии
        2. Скачивание обновления
        3. Проверка подписи и контрольной суммы
        4. Применение обновления
        5. Проверка работоспособности
        6. При ошибке - откат
        """
        result = {
            "success": False,
            "old_version": self.current_version,
            "new_version": version_info.version,
            "steps": []
        }

        # Шаг 1: Создание резервной копии
        logger.info("Step 1: Creating backup...")
        if not await self.create_backup():
            result["steps"].append({"step": "backup", "status": "failed"})
            return result
        result["steps"].append({"step": "backup", "status": "success"})

        # Создаём временный файл для обновления
        with tempfile.NamedTemporaryFile(suffix="_update.tar.gz", delete=False) as tmp:
            update_path = Path(tmp.name)

        try:
            # Шаг 2: Скачивание
            logger.info("Step 2: Downloading update...")
            if not await self.download_update(version_info, update_path):
                result["steps"].append({"step": "download", "status": "failed"})
                await self.restore_backup()
                return result
            result["steps"].append({"step": "download", "status": "success"})

            # Шаг 3: Проверка подписи
            logger.info("Step 3: Verifying signature...")
            if not await self.verify_signature(update_path, version_info.signature_url):
                result["steps"].append({"step": "signature", "status": "failed"})
                await self.restore_backup()
                return result
            result["steps"].append({"step": "signature", "status": "success"})

            # Шаг 4: Применение обновления
            logger.info("Step 4: Applying update...")
            if not await self.apply_update(update_path):
                result["steps"].append({"step": "apply", "status": "failed"})
                await self.restore_backup()
                return result
            result["steps"].append({"step": "apply", "status": "success"})

            # Шаг 5: Проверка работоспособности
            logger.info("Step 5: Health check...")
            if not await self._health_check():
                logger.error("Health check failed, rolling back...")
                result["steps"].append({"step": "health_check", "status": "failed"})
                await self.restore_backup()
                return result
            result["steps"].append({"step": "health_check", "status": "success"})

            # Шаг 6: Обновление версии
            await self.update_version_file(version_info.version)
            result["success"] = True

            logger.info(f"Successfully updated from {self.current_version} to {version_info.version}")
            return result

        finally:
            # Очистка временного файла
            if update_path.exists():
                update_path.unlink(missing_ok=True)

    async def _health_check(self) -> bool:
        """
        Проверяет, что Регулятор работает после обновления.
        Отправляет запрос к health endpoint.
        """
        try:
            # Ждём, пока сервис перезапустится
            await asyncio.sleep(5)

            # Проверяем HTTP endpoint, если он есть
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8088/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("status") == "healthy"
            return False
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def start_auto_update_checker(self):
        """Запускает периодическую проверку обновлений в фоне."""
        while True:
            try:
                await asyncio.sleep(self.check_interval_hours * 3600)
                logger.info("Auto-update check...")
                update = await self.check_for_updates()
                if update and update.is_critical:
                    logger.info(f"Critical update available: {update.version}")
                    # В реальной системе здесь можно отправить уведомление
                    # и/или выполнить автоматическое обновление
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-update check failed: {e}")
