"""
Шаблон «Монитор» (ГОСТ Р 72118-2025, Приложение А.1)

Структура:
  SecurityEventSensor    — датчик (перехват событий из Dispatcher)
  SecurityKnowledgeBase  — база знаний (правила из JSON)
  SecurityEventDetector  — детектор (анализ по правилам)
  SecurityReactionModule — модуль реакции (лог + алерт + опциональный отзыв)
  SecurityMonitor        — фасад, склеивает всё вместе
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# База знаний (обновляется без перезапуска)
# ---------------------------------------------------------------------------

class SecurityKnowledgeBase:
    """Хранит правила детектора. Перечитывает файл при вызове reload()."""

    def __init__(self, rules_path: str = "security_knowledge_base.json"):
        self._path = Path(rules_path)
        self.rules: List[Dict] = []
        self.reload()

    def reload(self):
        try:
            with open(self._path, encoding="utf-8") as f:
                self.rules = json.load(f).get("rules", [])
            logger.info(f"[KnowledgeBase] Загружено правил: {len(self.rules)}")
        except Exception as e:
            logger.error(f"[KnowledgeBase] Ошибка загрузки правил: {e}")


# ---------------------------------------------------------------------------
# Датчик (sensor)
# ---------------------------------------------------------------------------

class SecurityEventSensor:
    """
    Перехватывает события из Dispatcher не влияя на основной поток.
    Вызывается через monkey-patch dispatch() — оборачивает оригинальный метод.
    """

    def __init__(self, on_event: Callable[[Dict], None]):
        self._on_event = on_event

    def wrap_dispatcher(self, dispatcher) -> None:
        """Оборачивает dispatcher.dispatch() — датчик работает как side-channel."""
        original_dispatch = dispatcher.dispatch

        async def patched_dispatch(topic: str, message: Any):
            # Сначала — основной обработчик (без задержки)
            await original_dispatch(topic, message)
            # Потом — асинхронно датчик (не блокирует ответ)
            asyncio.create_task(self._capture(topic, message))

        dispatcher.dispatch = patched_dispatch
        logger.info("[Sensor] Датчик подключён к Dispatcher")

    async def _capture(self, topic: str, message: Any):
        """Нормализует событие и передаёт детектору."""
        try:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "topic": topic,
                "payload": message,
                "event_type": self._classify(topic, message),
            }
            self._on_event(event)
        except Exception as e:
            logger.error(f"[Sensor] Ошибка захвата события: {e}")

    @staticmethod
    def _classify(topic: str, message: Any) -> str:
        """Определяет тип события по топику и содержимому сообщения."""
        status = message.get("status", "") if isinstance(message, dict) else ""
        cert_status = message.get("certificate_status", "") if isinstance(message, dict) else ""

        if "firmware" in topic and status == "REJECTED":
            return "cert_rejected"
        if "firmware" in topic:
            return "firmware_request"
        if "cert" in topic and cert_status == "invalid":
            return "revoked_cert_verify"
        if "operator" in topic and cert_status == "error":
            return "unknown_operator"
        return "generic"


# ---------------------------------------------------------------------------
# Детектор (detector)
# ---------------------------------------------------------------------------

class SecurityEventDetector:
    """
    Проверяет события по правилам из KnowledgeBase.
    Считает частоту событий в скользящем окне (deque с TTL).
    """

    def __init__(self, kb: SecurityKnowledgeBase):
        self._kb = kb
        # event_type -> deque of timestamps
        self._counters: Dict[str, Deque[float]] = defaultdict(deque)

    def analyze(self, event: Dict) -> Optional[Dict]:
        """
        Возвращает вердикт если сработало правило, иначе None.
        """
        event_type = event.get("event_type", "generic")
        now = datetime.utcnow().timestamp()

        for rule in self._kb.rules:
            if rule["event_type"] != event_type:
                continue

            window = rule["window_seconds"]
            buf = self._counters[event_type]

            # Добавляем текущий момент и чистим старые
            buf.append(now)
            while buf and now - buf[0] > window:
                buf.popleft()

            if len(buf) >= rule["threshold"]:
                return {
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "event_type": event_type,
                    "count": len(buf),
                    "window_seconds": window,
                    "triggered_at": event["timestamp"],
                    "topic": event.get("topic"),
                }
        return None


# ---------------------------------------------------------------------------
# Модуль реакции
# ---------------------------------------------------------------------------

class SecurityReactionModule:
    """
    Реагирует на вердикт детектора:
    - пишет структурированный лог
    - публикует алерт в топик security.alerts
    - при CRITICAL — отзывает сертификат (опционально)
    """

    ALERT_TOPIC = "regulator.security.alerts"

    def __init__(
        self,
        broker_publish: Callable,
        revoke_handler=None,  # CertificateRevokeHandler, опционально
    ):
        self._publish = broker_publish
        self._revoke = revoke_handler

    async def react(self, verdict: Dict, original_event: Dict):
        severity = verdict["severity"]
        logger.warning(
            f"[Monitor] АЛЕРТ [{severity}] {verdict['rule_name']} | "
            f"count={verdict['count']} за {verdict['window_seconds']}с | "
            f"topic={verdict['topic']}"
        )

        alert = {
            "alert": verdict,
            "source_event": {
                "topic": original_event.get("topic"),
                "timestamp": original_event.get("timestamp"),
            },
        }
        await self._publish(self.ALERT_TOPIC, alert)

        if severity == "CRITICAL" and self._revoke:
            cert_id = (original_event.get("payload") or {}).get("certificate_id")
            if cert_id:
                logger.warning(f"[Monitor] Автоотзыв сертификата {cert_id}")
                await self._revoke.handle({
                    "certificate_id": cert_id,
                    "reason": f"Auto-revoked by SecurityMonitor: {verdict['rule_id']}",
                })


# ---------------------------------------------------------------------------
# Фасад — SecurityMonitor
# ---------------------------------------------------------------------------

class SecurityMonitor:
    """
    Собирает шаблон «Монитор» из четырёх элементов по ГОСТ Р 72118-2025 А.1.
    Использование:
        monitor = SecurityMonitor(broker.publish, rules_path="security_knowledge_base.json")
        monitor.attach(dispatcher)          # подключить датчик
        await monitor.reload_rules()        # обновить правила без перезапуска
    """

    def __init__(
        self,
        broker_publish: Callable,
        rules_path: str = "security_knowledge_base.json",
        revoke_handler=None,
    ):
        self._kb = SecurityKnowledgeBase(rules_path)
        self._detector = SecurityEventDetector(self._kb)
        self._reaction = SecurityReactionModule(broker_publish, revoke_handler)
        self._sensor = SecurityEventSensor(on_event=self._on_event)
        self._queue: asyncio.Queue = asyncio.Queue()

    def attach(self, dispatcher) -> None:
        """Подключает датчик к dispatcher и запускает фоновый цикл обработки."""
        self._sensor.wrap_dispatcher(dispatcher)
        asyncio.create_task(self._processing_loop())
        logger.info("[Monitor] Монитор безопасности запущен")

    def _on_event(self, event: Dict):
        """Вызывается датчиком — кладёт событие в очередь (non-blocking)."""
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("[Monitor] Очередь событий переполнена, событие сброшено")

    async def _processing_loop(self):
        """Фоновый цикл: детектор → реакция."""
        while True:
            try:
                event = await self._queue.get()
                verdict = self._detector.analyze(event)
                if verdict:
                    await self._reaction.react(verdict, event)
            except Exception as e:
                logger.error(f"[Monitor] Ошибка в цикле обработки: {e}")

    async def reload_rules(self):
        """Перечитывает правила из файла без перезапуска (требование ГОСТ)."""
        self._kb.reload()
        logger.info("[Monitor] Правила обновлены")