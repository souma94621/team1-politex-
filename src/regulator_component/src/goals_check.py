import logging
from typing import List, Optional

from .security_goals_registry import SecurityGoalsRegistry

logger = logging.getLogger(__name__)


class GoalsCheck:
    """
    Клиент для получения целей безопасности и соответствующих тестов.
    Используется обработчиками для запроса правил сертификации.
    """

    def __init__(self, registry: SecurityGoalsRegistry):
        self.registry = registry

    def get_goals_for_system(self, system_type: str) -> List[str]:
        """Возвращает цели безопасности для указанного типа системы."""
        goals = self.registry.get_goals(system_type)
        logger.info(f"Retrieved {len(goals)} goals for system type '{system_type}'")
        return goals

    def get_test_command_for_goal(self, goal_id: str) -> Optional[str]:
        """Возвращает команду для тестирования конкретной цели."""
        return self.registry.get_test_command(goal_id)

    def get_all_tests_for_system(self, system_type: str) -> List[str]:
        """Возвращает список команд для всех целей, относящихся к системе."""
        goals = self.get_goals_for_system(system_type)
        commands = []
        for goal in goals:
            cmd = self.get_test_command_for_goal(goal)
            if cmd:
                commands.append(cmd)
        return commands
