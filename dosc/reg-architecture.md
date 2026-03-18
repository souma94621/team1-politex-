## Архитектура регулятора:
<img width="1135" height="1071" alt="регулятор" src="https://github.com/user-attachments/assets/9a7b1b49-f6a6-4b0f-b93c-53867f529111" />

### Топики
* v1.operator.op1.certificate_request
```
{
  "timestamp": "2026-03-18T17:50:00Z",
  "message_id": "op-cert-req-101",
  "operator_id": "OP-77",
  "drone_id": "DRN-C2-4048",
  "digital_signature": "sha256:a1b2c3d4e5..."
}
```
* v1.operator.op1.certificate_result
```
{
  "timestamp": "2026-03-18T17:50:00Z",
  "message_id": "op-cert-req-101",
  "operator_id": "OP-77",
  "certificate_status": "certified",
  "certificate_id": "CERT-2026-999-XYZ",
  "digital_signature": "sha256:f1g2h3j4k5..."
}
```
* v1.Insurer.reg1.insurer-service.responses - в процессе

Поля:
```
{
  "timestamp": "2026-03-18T17:35:00Z",
  "message_id": "ins-min-001",
  "insurer_id": "INS-GLOBAL-77",
  "digital_signature": "sha256:8f32a1b9c..."
}
```
* v1.Insurer.reg1.insurer-service.requests - в процессе

Поля:
```
{
  "timestamp": "2026-03-10T12:00:00Z",
  "message_id": "ins-min-001",
  "insurer_id": "INS-GLOBAL-77",
  "requirements_checked": [
      "FW-SEC-01",
      "FW-SEC-02",
      "FW-SEC-05"
  ],
  "status": "accepted",
  "digital_signature": "sha256:4d5e6f7a8b..."
}
```
* v1.firmware.certification.request

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
* v1.firmware.certificate.result

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
* v1.drone.registration.request

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
* v1.drone.registration.result

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
