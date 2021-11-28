# SelfStorage

Бот позволяет подобрать и арендовать необходимую площадь на складе для хранения вещей.

### Env Настройки
Create `.env` from `.env.Example`
1. MODE - `dev` или `prod`, мод работы бота локально или на heroku
2. TELEGRAM_TOKEN - str, токен бота от [@BotFather](https://t.me/botfather)
3. PROVIDER_TOKEN - str, токен платежной системы от [@BotFather](https://t.me/botfather) для выбранной системы оплаты для бота
4. DATABASE_URL - str, строка подключения к postgres формата `postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]`

### Как установить
Python3 должен быть уже установлен.
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```console
$ pip install -r requirements.txt
```

### Как запускать
```console
$ python3 main.py
```

### Использование
`/start` - команда для старта работы с ботом

`/cancel` - команда для завершения работы бота на любом шаге
