# team1 (ПК)
Наша команда отвечает за:
* регулятор
* эксплуатанты
* DevSecOps

## Архитектруа регулятора:
<img width="1134" height="1031" alt="регулятор" src="https://github.com/user-attachments/assets/b168aa57-0364-4acc-bf5c-58ef297d9eab" />



### Топики
* firmware.certification.request

Поля:
```json
{
  "request_id": "req-fw-001",
  "timestamp": "2026-03-10T10:00:00Z",

  "developer_id": "DroneTech",

  "firmware": {
    "repository_url": "https://github.com/AMCP-Drones/drones",
    "commit_hash": "d71763e430b45ee01012b005751861627d7b4147",
    "version": "3.2.1"
  },

  "drone_type": "DeliveryDrone-X2"
}
```
* firmware.certificate.issued

Поля:
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

    "requirements_checked": [
      "FW-SEC-01",
      "FW-SEC-02",
      "FW-SEC-05"
    ],

    "hash": "a7f6b5c4d3e2",
    "digital_signature": "REGULATOR_SIGNATURE"
  }
}
```
* regulator.registration.request

Поля:
```json
{
  "request_id": "req-drone-001",
  "timestamp": "2026-03-11T09:00:00Z",

  "drone": {
    "model": "DeliveryDrone-X2",
    "serial_number": "SN-998877",
    "manufacturer": "DroneTech"
  },

  "firmware": {
    "version": "3.2.1",
    "certificate_id": "CERT-FW-2026-001"
  }
}
```
* regulator.registration.approved

Поля:
```json
{
  "request_id": "req-drone-001",
  "timestamp": "2026-03-11T09:00:05Z",

  "status": "APPROVED",

  "drone": {
    "serial_number": "SN-998877",
    "model": "DeliveryDrone-X2",
    "registration_number": "RU-BAS-0004521"
  },

  "certificate": {
    "certificate_id": "CERT-DRONE-2026-04521",
    "issued_by": "REGULATOR",
    "digital_signature": "REGULATOR_SIGNATURE"
  }
}
```
* operator.registration.request

Поля:
```json
{
  "request_id": "req-operator-001",
  "timestamp": "2026-03-11T09:30:00Z",

  "drone": {
    "serial_number": "SN-998877",
    "registration_number": "RU-BAS-0004521",
    "model": "DeliveryDrone-X2"
  },

  "firmware": {
    "version": "3.2.1"
  }
}
```
* operator.registration.result

Поля:
```json
{
  "request_id": "req-operator-001",
  "timestamp": "2026-03-11T09:30:03Z",

  "status": "REGISTERED",

  "operator_id": "operator-01",

  "drone": {
    "drone_id": "UAV-4521",
    "serial_number": "SN-998877",
    "registration_number": "RU-BAS-0004521"
  }
}
```
* regulator.info.request

Поля:
```json
{
  "request_id": "req-reg-check-001",
  "timestamp": "2026-03-11T09:30:01Z",

  "registration_number": "RU-BAS-0004521"
}
```
* regulator.info.response

Поля:
```json
{
  "request_id": "req-reg-check-001",
  "timestamp": "2026-03-11T09:30:02Z",

  "status": "FOUND",

  "drone": {
    "registration_number": "RU-BAS-0004521",
    "serial_number": "SN-998877",
    "model": "DeliveryDrone-X2",
    "manufacturer": "DroneTech"
  },

  "firmware": {
    "version": "3.2.1",
    "certificate_id": "CERT-FW-2026-001"
  }
}
```
