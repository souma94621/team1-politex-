# team1 (ПК)
Наша команда отвечает за регулятор

## Описание

Система реализует функционал регулятора.

## Установка

1. Клонируйте репозиторий:

```bash
git clone -b regulator https://github.com/souma94621/team1-regulator_operation_devsecops.git
cd team1-regulator_operation_devsecops/Regulator
```

Создайте и активируйте виртуальное окружение:
### Linux / Mac
```
python -m venv venv
source venv/bin/activate
```
### Windows
```
python -m venv venv
venv\Scripts\activate
```
2. Установите зависимости:
```
pip install -r requirements.txt
```

3. Запуск
```
python main.py
```

Система подключается к брокеру MQTT и обрабатывает запросы на сертификацию и регистрацию.


## Навигация

* [Техническое задание](dosc/ТЗ.md)
* [Топики регулятора](dosc/Топики_регулятора.md)
* [Архитектура регулятора](dosc/архитектура.png)
* [Архитектура политик регулятора](dosc/архитектура_политик.png)
* [План тестирования](dosc/тест_план.md)

