# src/regulator_component/src/managers/security_test_runner.py
import logging
from typing import Dict, Any

from .managers.ci_service import ContinuousIntegration
from .goals_check import GoalsCheck
from .models import FirmwareRequest

logger = logging.getLogger(__name__)


class SecurityTestRunner:
    """Обёртка над CI для запуска тестов безопасности."""

    def __init__(self, ci_service: ContinuousIntegration):
        self.ci_service = ci_service

    async def run_tests(self, firmware_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запускает тесты безопасности на основе firmware_info.
        Возвращает результат с деталями.
        """
        # Создаём FirmwareRequest из словаря
        try:
            request = FirmwareRequest(**firmware_info)
        except Exception as e:
            logger.error(f"Failed to parse firmware info: {e}")
            return {"passed": False, "error": str(e)}

        result = await self.ci_service.process_firmware(request)
        return {
            "passed": result.get("passed", False),
            "details": {
                "request_id": result.get("request_id"),
                "test_results": result.get("test_results", []),
                "security_goals": result.get("security_goals", [])
            }
        }
