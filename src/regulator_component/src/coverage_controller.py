# src/regulator_component/src/managers/coverage_controller.py
import logging
import subprocess
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


class CoverageController:
    """Контроллер для проверки покрытия кода в репозитории."""

    def __init__(self, mock: bool = True):
        self.mock = mock

    async def get_coverage(self, repo_path: str, commit_hash: str) -> Optional[float]:
        """
        Проверяет покрытие кода в репозитории.
        Возвращает процент покрытия или None при ошибке.
        """
        if self.mock:
            logger.info(f"Mock coverage check for {repo_path}: 85%")
            return 85.0

        # Реальная проверка покрытия
        try:
            # Предполагаем, что в репозитории есть скрипт check_coverage.sh
            cmd = ["bash", "check_coverage.sh", commit_hash]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            if process.returncode == 0:
                # Парсим вывод, ожидаем число
                coverage_str = stdout.decode().strip()
                coverage = float(coverage_str)
                logger.info(f"Coverage for {repo_path}: {coverage}%")
                return coverage
            else:
                logger.error(f"Coverage check failed: {stderr.decode()}")
                return None

        except Exception as e:
            logger.error(f"Failed to get coverage: {e}")
            return None
