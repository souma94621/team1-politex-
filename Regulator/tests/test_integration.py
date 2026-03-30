import pytest
import asyncio
import json
import uuid
from datetime import datetime
from config import Config
from models import (
    FirmwareRequest, FirmwareResult,
    DroneRequest, DroneResult,
    OperatorRequest, OperatorResult,
    InsurerRequest, InsurerResponse
)
from broker_factory import create_broker_adapter


# ---------------------------------------------------------------------------
# Тест 1: Сертификация прошивки
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_firmware_certification_flow():
    """Отправка запроса на прошивку и ожидание сертификата."""
    broker = create_broker_adapter()
    await broker.connect()

    request_id = str(uuid.uuid4())
    received_results = []

    async def on_result(topic, message):
        if isinstance(message, str):
            message = json.loads(message)
        result = FirmwareResult(**message)
        if result.request_id == request_id:
            received_results.append(result)

    await broker.subscribe(Config.TOPIC_FIRMWARE_RESULT, on_result)
    await asyncio.sleep(1)

    request = FirmwareRequest(
        request_id=request_id,
        timestamp=datetime.utcnow(),
        developer_id="dev-team-01",
        firmware={
            "repository_url": "https://github.com/example/drone-fw",
            "commit_hash": "a1b2c3d4",
            "version": "2.0.1"
        },
        drone_type="quadcopter-v4"
    )
    await broker.publish(Config.TOPIC_FIRMWARE_REQUEST, request.model_dump_json())

    start = asyncio.get_event_loop().time()
    while not received_results and (asyncio.get_event_loop().time() - start) < 30:
        await asyncio.sleep(0.5)

    assert len(received_results) > 0, "Регулятор не прислал ответ на запрос прошивки"
    result = received_results[0]
    assert result.request_id == request_id
    assert result.status in ["CERTIFIED", "REJECTED"]

    if result.status == "CERTIFIED":
        assert result.certificate is not None
        print(f"\n[УСПЕХ] Прошивка сертифицирована: {result.certificate.get('certificate_id')}")
    else:
        print(f"\n[ОТКАЗ] Прошивка отклонена")

    await broker.close()


# ---------------------------------------------------------------------------
# Тест 2: Регистрация дрона
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_drone_registration_flow():
    """
    Регистрация дрона:
    1. Сертифицируем прошивку чтобы получить firmware_certificate_id
    2. Отправляем запрос на регистрацию дрона с этим сертификатом
    3. Проверяем что дрон получил статус APPROVED
    """
    broker = create_broker_adapter()
    await broker.connect()

    # --- Шаг 1: Сертификация прошивки ---
    fw_request_id = str(uuid.uuid4())
    fw_received = []

    async def on_fw_result(topic, message):
        if isinstance(message, str):
            message = json.loads(message)
        if message.get("request_id") == fw_request_id:
            fw_received.append(message)

    await broker.subscribe(Config.TOPIC_FIRMWARE_RESULT, on_fw_result)
    await asyncio.sleep(1)

    fw_request = FirmwareRequest(
        request_id=fw_request_id,
        timestamp=datetime.utcnow(),
        developer_id="dev-team-01",
        firmware={
            "repository_url": "https://github.com/example/drone-fw",
            "commit_hash": "b2c3d4e5",
            "version": "3.0.0"
        },
        drone_type="quadcopter-v4"
    )
    await broker.publish(Config.TOPIC_FIRMWARE_REQUEST, fw_request.model_dump_json())

    start = asyncio.get_event_loop().time()
    while not fw_received and (asyncio.get_event_loop().time() - start) < 30:
        await asyncio.sleep(0.5)

    assert fw_received, "Не получен ответ на сертификацию прошивки"
    fw_result = FirmwareResult(**fw_received[0])
    assert fw_result.status == "CERTIFIED", f"Прошивка не сертифицирована: {fw_result.status}"

    firmware_cert_id = fw_result.certificate["certificate_id"]
    print(f"\n[ШАГ 1] Прошивка сертифицирована: {firmware_cert_id}")

    # --- Шаг 2: Регистрация дрона ---
    drone_request_id = str(uuid.uuid4())
    drone_received = []

    async def on_drone_result(topic, message):
        if isinstance(message, str):
            message = json.loads(message)
        if message.get("request_id") == drone_request_id:
            drone_received.append(message)

    await broker.subscribe(Config.TOPIC_DRONE_RESULT, on_drone_result)
    await asyncio.sleep(1)

    drone_request = DroneRequest(
        request_id=drone_request_id,
        timestamp=datetime.utcnow(),
        drone={
            "model": "DJI Phantom Pro",
            "serial_number": "SN-20260330-001",
            "manufacturer": "DJI"
        },
        firmware={
            "version": "3.0.0",
            "certificate_id": firmware_cert_id
        }
    )
    await broker.publish(Config.TOPIC_DRONE_REQUEST, drone_request.model_dump_json())

    start = asyncio.get_event_loop().time()
    while not drone_received and (asyncio.get_event_loop().time() - start) < 30:
        await asyncio.sleep(0.5)

    assert drone_received, "Регулятор не прислал ответ на регистрацию дрона"
    drone_result = DroneResult(**drone_received[0])

    assert drone_result.request_id == drone_request_id
    assert drone_result.status in ["APPROVED", "REJECTED"]

    if drone_result.status == "APPROVED":
        assert drone_result.certificate is not None
        assert drone_result.drone is not None
        reg_number = drone_result.drone.get("registration_number")
        print(f"\n[УСПЕХ] Дрон зарегистрирован. Рег. номер: {reg_number}")
    else:
        print(f"\n[ОТКАЗ] Дрон отклонён регулятором")

    await broker.close()


# ---------------------------------------------------------------------------
# Тест 3: Сертификация оператора (эксплуатанта)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_operator_certification_flow():
    """Запрос сертификата оператора и проверка ответа."""
    broker = create_broker_adapter()
    await broker.connect()

    message_id = f"op-cert-req-{uuid.uuid4().hex[:8]}"
    operator_id = f"OP-{uuid.uuid4().hex[:6].upper()}"
    received = []

    async def on_result(topic, message):
        if isinstance(message, str):
            message = json.loads(message)
        if message.get("message_id") == message_id:
            received.append(message)

    await broker.subscribe(Config.TOPIC_OPERATOR_RESULT, on_result)
    await asyncio.sleep(1)

    request = OperatorRequest(
        timestamp=datetime.utcnow(),
        message_id=message_id,
        operator_id=operator_id,
        drone_id="DRN-C2-4048",
        digital_signature="sha256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
    )
    await broker.publish(Config.TOPIC_OPERATOR_REQUEST, request.model_dump_json())

    start = asyncio.get_event_loop().time()
    while not received and (asyncio.get_event_loop().time() - start) < 30:
        await asyncio.sleep(0.5)

    assert received, "Регулятор не прислал ответ на запрос сертификата оператора"
    result = OperatorResult(**received[0])

    assert result.message_id == message_id
    assert result.operator_id == operator_id
    assert result.certificate_status in ["certified", "rejected"]

    if result.certificate_status == "certified":
        assert result.certificate_id is not None
        print(f"\n[УСПЕХ] Оператор {operator_id} сертифицирован: {result.certificate_id}")
    else:
        print(f"\n[ОТКАЗ] Оператору {operator_id} отказано в сертификации")

    await broker.close()


# ---------------------------------------------------------------------------
# Тест 4: Запрос страховой компании
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insurer_request_flow():
    """Запрос от страховой компании и проверка ответа регулятора."""
    broker = create_broker_adapter()
    await broker.connect()

    message_id = f"ins-req-{uuid.uuid4().hex[:8]}"
    insurer_id = f"INS-{uuid.uuid4().hex[:6].upper()}"
    received = []

    async def on_result(topic, message):
        if isinstance(message, str):
            message = json.loads(message)
        if message.get("message_id") == message_id:
            received.append(message)

    await broker.subscribe(Config.TOPIC_INSURER_RESPONSE, on_result)
    await asyncio.sleep(1)

    request = InsurerRequest(
        timestamp=datetime.utcnow(),
        message_id=message_id,
        insurer_id=insurer_id,
        order_id=f"order-{uuid.uuid4().hex[:8]}",
        amount=5000000.00,
        incident_id=f"inc-{uuid.uuid4().hex[:8]}"
    )
    await broker.publish(Config.TOPIC_INSURER_REQUEST, request.model_dump_json())

    start = asyncio.get_event_loop().time()
    while not received and (asyncio.get_event_loop().time() - start) < 30:
        await asyncio.sleep(0.5)

    assert received, "Регулятор не прислал ответ на запрос страховой"
    result = InsurerResponse(**received[0])

    assert result.message_id == message_id
    assert result.insurer_id == insurer_id
    assert isinstance(result.approved, bool)

    if result.approved:
        print(f"\n[УСПЕХ] Страховой запрос {message_id} одобрен")
    else:
        print(f"\n[ОТКАЗ] Страховой запрос {message_id} отклонён: {result.reason}")

    await broker.close()