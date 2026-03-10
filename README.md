# team1 (ПК)
Наша команда отвечает за:
* регулятор
* эксплуатанты
* DevSecOps

## Регулятор
Используюся топики:
* drone.registration.request - запрос на регистрацию дрона

#### Поля:

request_id - идентификатор запроса

timestamp - время отправки

drone.drone_id - id дрона

drone.model - модель

drone.manufacturer - издатель

firmware.version - версия прошивки


#### Пример запроса:
```json
{

  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  
  "timestamp": "2026-03-10T12:30:00Z",
  
  "drone": {
  
    "drone_id": "UAV-4521",
    
    "model": "DeliveryDrone-X2",
    
    "manufacturer": "DroneTech"
    
  },
  
  "firmware": {
  
    "version": "3.2.1"
    
  }
  
}
```
* drone.registration.result - ответ о (не)успешной регистрации
#### Поля
request_id - ID исходного запроса

timestamp - время ответа

status - результат операции (SUCCESS/FAILED)

drone_id - ID дрона в системе Эксплуатанта

#### Пример успешной регистрации
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-03-10T12:30:03Z",

  "status": "SUCCESS",

  "drone_id": "UAV-4521"
}
```
## Эксплуатант
Используются топики:
* 
