## Архитектура эксплуатанта
<img width="2040" height="1006" alt="Диаграмма без названия drawio" src="https://github.com/user-attachments/assets/bc22233c-1973-4e99-952c-9b1c5880affb" />

### Топики
* v1.orvd.component - в процессе

Предлагаемый формат сообщения регистрации миссии:

```
{
  "header": {
    "version": "1.0",
    "timestamp": "2026-03-18T10:55:00Z",
    "message_id": "req-998877"
  },
  "body": {
    "drone_id": "DRN-C2-4048",
    "mission_id": "MSN-2026-ALPHA",
    "operator_id": "OP-77",
    "flight_parameters": {
      "route": [
        {"lat": 55.7558, "lon": 37.6173, "alt": 100},
        {"lat": 55.7580, "lon": 37.6200, "alt": 120},
        {"lat": 55.7600, "lon": 37.6300, "alt": 100}
      ],
      "max_altitude": 150,
      "estimated_duration": 1800
    },
    "insurance_policy": "POL-55667788"
  }
}
```
Предлагаемый формат регистрации дрона:
```
{
  "header": {
    "version": "1.0",
    "timestamp": "2026-03-18T11:05:00Z",
    "message_id": "reg-drone-001"
  },
  "body": {
    "drone_details": {
      "serial_number": "SN-9988-GCS-2026",
      "model": "CyberBird-V2",
      "manufacturer": "DevSecOps_Labs",
      "category": "C1",
      "take_off_weight_grams": 1450
    },
    "hardware_signature": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```
* v1.drone_port.orchestretor - в процессе (https://github.com/Kaitrye/DronePortGCS/blob/drone_port/systems/drone_port/src/drone_manager/topics.py)
* v1.gcs.1.orchestrator находится в https://github.com/Kaitrye/DronePortGCS?tab=readme-ov-file#интеграция-с-эксплуатантом
* v1.Insurer.op1.insurer-service.requests и v1.Insurer.op1.insurer-service.responses находится в https://github.com/DashDashh/Insurer
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
  "message_id": "op-cert-req-101",
  "operator_id": "OP-77",
  "certificate_status": "certified",
  "certificate_id": "CERT-2026-999-XYZ",
  "digital_signature": "sha256:f1g2h3j4k5..."
}
```
* v1.aggregator_insurer.local.operator.responses и v1.aggregator_insurer.local.operator.requests находятся на https://github.com/DashDashh/Agregator
