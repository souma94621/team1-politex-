## Архитектура регулятора:
### Топики

* v1.firmware.certification.request

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
* v1.system.certification.request

```
{
  "request_id": "req-sys-001",
  "timestamp": "2026-03-12T10:00:00Z",

  "system_id": "NUS-Team2",
  "system_type": "ground_control_station",

  "repository_url": "https://github.com/example/nus-system",
  "commit_hash": "d71763e430b45ee01012b005751861627d7b4147"
}
```
* v1.system.certification.result

```
{
  "request_id": "req-sys-001",
  "timestamp": "2026-03-12T10:05:00Z",

  "status": "CERTIFIED",

  "certificate": {
    "certificate_id": "CERT-SYS-2026-001",

    "system_id": "NUS-Team2",
    "system_type": "ground_control_station",

    "security_goals_checked": [
      "FW-SEC-01",
      "FW-SEC-02",
      "FW-SEC-03",
      "SYS-SEC-01"
    ],

    "hash": "c3d2e1f0a9b8",
    "digital_signature": "REGULATOR_SIGNATURE"
  },

  "errors": []
}
```
* v1.operator.certificate_status.request
```
{
  "timestamp": "2026-03-18T17:50:00Z",
  "message_id": "op-cert-req-101",
  "operator_id": "OP-77",
  "drone_id": "DRN-C2-4048",
  "digital_signature": "sha256:a1b2c3d4e5..."
}
```
* v1.operator.certificate_status.result
```
{
  "timestamp": "2026-03-18T17:50:00Z",
  "message_id": "op-cert-req-101",
  "operator_id": "OP-77",
  "drone_id": "DRN-C2-4048",
  "certificate_status": "certified",
  "certificate_id": "CERT-2026-999-XYZ",
  "security_goals_checked": ["FW-SEC-01", "FW-SEC-02", "FW-SEC-05"],
  "digital_signature": "sha256:f1g2h3j4k5..."
}
```
* v1.certificate.status.request
```
{
  "request_id": "req-status-001",
  "timestamp": "2026-03-18T17:50:00Z",
  "certificate_id": "CERT-FW-2026-001"
}
```
* v1.certificate.status.result
```
{
  "request_id": "req-status-001",
  "timestamp": "2026-03-18T17:50:01Z",
  "certificate_id": "CERT-FW-2026-001",
  "status": "VALID"
}
```
* v1.drone.owner.transfer.request
```
{
  "request_id": "req-transfer-001",
  "timestamp": "2026-03-15T10:00:00Z",
  "drone_id": "DRN-C2-4048",
  "current_owner_id": "OP-77",
  "new_owner_id": "OP-88"
}
```
* v1.drone.owner.transfer.result
```
{
  "request_id": "req-transfer-001",
  "timestamp": "2026-03-15T10:00:02Z",
  "status": "APPROVED",
  "drone_certificate_id": "CERT-DRONE-2026-04521",
  "new_owner_id": "OP-88",
  "errors": []
}
```
