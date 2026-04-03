# handlers/firmware_handler.py
async def handle_firmware_request(message, cert_manager, test_runner, coverage_controller):
    # 1. Валидация
    # 2. Запуск тестов безопасности
    test_result = await test_runner.run(message.firmware)
    if not test_result.passed:
        return publish_result(status="REJECTED", reason="Security tests failed")
    
    # 3. Проверка покрытия (если прошивка доверенная)
    if message.firmware.is_trusted:
        coverage = await coverage_controller.get_coverage(message.firmware.repository_url, message.firmware.commit_hash)
        if coverage < 70:   # для целостности
            return publish_result(status="REJECTED", reason=f"Code coverage {coverage}% < 70%")
    
    # 4. Создание сертификата
    cert = cert_manager.create_certificate(
        subject_type="firmware",
        subject_id=message.firmware.commit_hash,
        security_goals=message.requirements_checked  # или предопределённые
    )
    
    # 5. Публикация результата
    result = {
        "request_id": message.request_id,
        "status": "CERTIFIED",
        "certificate": cert.dict()
    }
    await broker.publish("v1.firmware.certificate.result", result)
    logger.info(f"Firmware certified: {cert.certificate_id}")