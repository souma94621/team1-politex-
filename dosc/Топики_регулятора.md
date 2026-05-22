## Архитектура регулятора:
### Топики
#### v1.developer.registration.request - регистрация разработчика
```json
{
  "request_id": "req-dev-001",
  "timestamp": "2026-03-13T09:00:00Z",
  "organization_name": "DroneTech LLC",
  "contact_email": "cert@dronetech.ru"
}
```
#### v1.developer.registration.result
```json
{
  "request_id": "req-dev-001",
  "timestamp": "2026-03-13T09:00:01Z",
  "status": "REGISTERED",
  "developer_id": "DEV-2026-001",
  "organization_name": "DroneTech LLC",
  "errors": []
}
```
#### v1.firmware.certification.request - сертификация прошивки
```json
{
  "request_id": "req-fw-001",
  "timestamp": "2026-03-10T10:00:00Z",
  "developer_id": "DEV-2026-001",
  "firmware": {
    "repository_url": "https://github.com/AMCP-Drones/drones",
    "commit_hash": "d71763e430b45ee01012b005751861627d7b4147",
    "version": "3.2.1"
  },
  "drone_type": "DeliveryDrone-X2"
}
```
#### v1.firmware.certification.result
```json
{
  "request_id": "req-fw-001",
  "timestamp": "2026-03-10T12:00:00Z",
  "status": "CERTIFIED",
  "certificate": {
    "certificate_id": "CERT-FW-2026-001",
    "firmware": {
      "version": "3.2.1",
      "commit_hash": "d71763e430b45ee01012b005751861627d7b4147"
    },
    "drone_type": "DeliveryDrone-X2",
    "developer_id": "DEV-2026-001",
    "security_goals_checked": ["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"],
    "issued_at": "2026-03-10T12:00:00Z",
    "valid_until": "2027-03-10T12:00:00Z",
    "hash": "a7f6b5c4d3e2",
    "digital_signature": "REGULATOR_SIGNATURE"
  },
  "errors": []
}
```
#### v1.drone.registration.request - регистрация дрона
```json
{
  "request_id": "req-drone-001",
  "timestamp": "2026-03-11T09:00:00Z",
  "developer_id": "DEV-2026-001",
  "drone": {
    "model": "DeliveryDrone-X2",
    "serial_number": "SN-998877"
  },
  "firmware": {
    "version": "3.2.1",
    "certificate_id": "CERT-FW-2026-001"
  }
}
```
#### v1.drone.registration.result
```json
{
  "request_id": "req-drone-001",
  "timestamp": "2026-03-11T09:00:05Z",
  "status": "CERTIFIED",
  "drone": {
    "serial_number": "SN-998877",
    "model": "DeliveryDrone-X2",
    "registration_number": "RU-BAS-0004521",
    "owner_id": "DEV-2026-001"
  },
  "certificate": {
    "certificate_id": "CERT-DRONE-2026-04521",
    "developer_id": "DEV-2026-001",
    "firmware_certificate_id": "CERT-FW-2026-001",
    "security_goals_checked": ["DRONE-SEC-01", "DRONE-SEC-02"],
    "issued_at": "2026-03-11T09:00:05Z",
    "valid_until": "2027-03-11T09:00:05Z",
    "digital_signature": "REGULATOR_SIGNATURE"
  },
  "errors": []
}
```

После регистрации дрона его владельцем числится его же разработчик, а посел продажи дрона эксплуатанту и соответствующему запросу в соответствующем топике после "owner_id" изменяется
#### v1.system.certification.request - сертификация системы
```json
{
  "request_id": "req-sys-001",
  "timestamp": "2026-03-12T10:00:00Z",
  "system_id": "op1",
  "system_type": "operator",
  "repository_url": "https://github.com/example/nus-system",
  "commit_hash": "d71763e430b45ee01012b005751861627d7b4147"
}
```
#### v1.system.certification.result
```json
{
  "request_id": "req-sys-001",
  "timestamp": "2026-03-12T10:05:00Z",
  "status": "CERTIFIED",
  "certificate": {
    "certificate_id": "CERT-SYS-2026-001",
    "system_id": "op1",
    "system_type": "operator",
    "commit_hash": "d71763e430b45ee01012b005751861627d7b4147",
    "security_goals_checked": ["FW-SEC-01", "FW-SEC-02", "FW-SEC-03", "SYS-SEC-01"],
    "issued_at": "2026-03-12T10:05:00Z",
    "valid_until": "2027-03-12T10:05:00Z",
    "hash": "c3d2e1f0a9b8",
    "digital_signature": "REGULATOR_SIGNATURE"
  },
  "errors": []
}
```
#### v1.operator.certificate_status.request - проверка эксплуатантом статуса сертитфиката у дрона
```json
{
  "request_id": "req-op-status-001",
  "timestamp": "2026-03-18T17:50:00Z",
  "operator_id": "OP-77",
  "drone": {
    "model": "DeliveryDrone-X2",
    "serial_number": "SN-998877"
  }
}
```
#### v1.operator.certificate_status.result
```json
{
  "request_id": "req-op-status-001",
  "timestamp": "2026-03-18T17:50:00Z",
  "operator_id": "OP-77",
  "drone": {
    "model": "DeliveryDrone-X2",
    "serial_number": "SN-998877",
    "registration_number": "RU-BAS-0004521",
    "certificate_status": "CERTIFIED",
    "certificate_id": "CERT-2026-999-XYZ",
    "security_goals_checked": ["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"]
  }
}
```
#### v1.certificate.status.request - проверка статуса сертификата
```json
{
  "request_id": "req-status-001",
  "timestamp": "2026-03-18T17:50:00Z",
  "certificate_id": "CERT-FW-2026-001"
}
```
#### v1.certificate.status.result
```json
{
  "request_id": "req-status-001",
  "timestamp": "2026-03-18T17:50:01Z",
  "certificate_id": "CERT-FW-2026-001",
  "status": "VALID"
  "issued_at": "2026-03-10T12:00:00Z",
  "valid_until": "2027-03-10T12:00:00Z"
}
```
#### v1.drone.owner.transfer.request - смена владельца дрона
```json
{
  "request_id": "req-transfer-001",
  "timestamp": "2026-03-15T10:00:00Z",
  "drone": {
    "model": "DeliveryDrone-X2",
    "serial_number": "SN-998877"
  }
  "current_owner_id": "DEV-2026-001",
  "new_owner_id": "OP-88"
}
```
#### v1.drone.owner.transfer.result
```json
{
  "request_id": "req-transfer-001",
  "timestamp": "2026-03-15T10:00:02Z",
  "status": "APPROVED",
  "drone": {
    "serial_number": "SN-998877",
    "model": "DeliveryDrone-X2",
    "registration_number": "RU-BAS-0004521",
    "owner_id": "OP-88"
  },
  "errors": []
}
```
#### v1.registry.security_goals.request - вызов реестра цпб
```json
{
  "request_id": "req-registry-001",
  "timestamp": "2026-03-14T10:00:00Z"
}
```
#### v1.registry.security_goals.result
```json
{
  "request_id": "req-registry-001",
  "timestamp": "2026-03-14T10:00:00Z",
  "security_goals": [
    {
      "id": "FW-SEC-01",
      "description": "Покрытие unit-тестами trusted-компонентов не ниже 60%",
      "applies_to": "firmware",
      "certification_cost": 1000
    },
    {
      "id": "DRONE-SEC-01",
      "description": "Дрон использует сертифицированную прошивку",
      "applies_to": "drone",
      "certification_cost": 500
    },
    {
      "id": "SYS-SEC-01",
      "description": "Все security_goals системы присутствуют в реестре",
      "applies_to": "system",
      "certification_cost": 2000
    }
  ],
  "total_goals": 3
}
```
