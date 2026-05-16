import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .config import Config

logger = logging.getLogger(__name__)


class SecurityGoalsRegistry:
    """
    Хранилище целей безопасности для разных типов систем.
    Загружает данные из JSON-файла, при отсутствии создаёт с целями по умолчанию.
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = Config.GOALS_STORAGE_PATH
        self.storage_path = Path(storage_path)
        self._goals: Dict[str, List[str]] = {}       # system_type -> [goal_id, ...]
        self._test_commands: Dict[str, str] = {}     # goal_id -> shell command / test script
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._goals = data.get("goals", {})
                    self._test_commands = data.get("test_commands", {})
                logger.info(f"Loaded security goals from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load goals: {e}")
                self._init_defaults()
        else:
            self._init_defaults()
            self._save()

    def _init_defaults(self):
        """Инициализация целями по умолчанию (совместимо с существующей логикой)."""
        self._goals = {
            "firmware": ["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"],
            "drone": ["DRONE-INTEGRITY", "DRONE-AUTH"],
            "operator": ["OPERATOR-AUTH", "MISSION-APPROVAL"],
            "system": ["SYSTEM-INTEGRITY"],
        }
        self._test_commands = {
            "FW-SEC-01": "pytest tests/test_fw_sec_01.py",
            "FW-SEC-02": "pytest tests/test_fw_sec_02.py",
            "FW-SEC-05": "pytest tests/test_fw_sec_05.py",
            "DRONE-INTEGRITY": "check_drone_integrity.sh",
            "DRONE-AUTH": "verify_drone_auth.py",
            "OPERATOR-AUTH": "check_operator_auth.sh",
            "MISSION-APPROVAL": "validate_mission.py",
            "SYSTEM-INTEGRITY": "system_integrity_check.sh",
        }
        logger.info("Initialized default security goals and test commands")

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({
                    "goals": self._goals,
                    "test_commands": self._test_commands
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved security goals to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save goals: {e}")

    def get_goals(self, system_type: str) -> List[str]:
        """Возвращает список целей безопасности для заданного типа системы."""
        return self._goals.get(system_type, [])

    def get_test_command(self, goal_id: str) -> Optional[str]:
        """Возвращает команду для запуска теста, соответствующего цели безопасности."""
        return self._test_commands.get(goal_id)

    def register_goals(self, system_type: str, goal_ids: List[str]) -> bool:
        """Регистрирует новый набор целей для типа системы."""
        if not system_type or not goal_ids:
            logger.warning("Invalid system_type or empty goals")
            return False
        self._goals[system_type] = goal_ids
        self._save()
        logger.info(f"Registered new security goals for {system_type}: {goal_ids}")
        return True

    def register_test_command(self, goal_id: str, command: str) -> bool:
        """Регистрирует команду для теста цели безопасности."""
        if not goal_id or not command:
            return False
        self._test_commands[goal_id] = command
        self._save()
        logger.info(f"Registered test command for {goal_id}: {command}")
        return True
