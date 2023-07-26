# simple_vk_telegram_search_bot

Простой python-скрипт, который ходит в VK-API,
ищет заданные слова в группе VK,
и отправляет найденное в ТГ-бота. 


#### Пример использования:
Проверка группы мэрии на отключение ЖКУ в вашем доме.


###
## Запуск
Установка зависимостей(команды для разных ОС):
* Создание venv:
	*  `python -m venv venv`
	*  `python3 -m venv venv`
* Активация venv: 
	* `source venv/scripts/activate`
	* `source venv/bin/activate`
	* `.venv\Scripts\Activate.ps1`
* Установка `requirements.txt`:
	* `pip install -r requirements.txt`
* Заполнение данных в `.env` файле.
## Хостинг
- Для хостинга удобно использовать  ОС-Linux.
- Для постоянной работы бота удобно создать демон для `systemd`. Он будет работать в фоне.

### Создание `systemd - service`файла.
- Фигурные скобки далее указывают на необходимость заменить их на что-либо.
```
sudo nano /etc/systemd/system/{file_name}.service
```
#### Пример заполнения `service`файла.
```
[Unit]
# Это текстовое описание юнита, пояснение для разработчика.
Description={name_of_daemon}

# Условие: при старте операционной системы запускать процесс только после того, 
# как операционная система загрузится и настроит подключение к сети.
# Ссылка на документацию с возможными вариантами значений 
# https://systemd.io/NETWORK_ONLINE/
After=network.target 

[Service]
# От чьего имени будет происходить запуск:
# укажите имя, под которым вы подключались к серверу.
User={username}

# Путь к директории проекта:
# /home/<имя-пользователя-в-системе>/
# <директория-с-проектом>/<директория-с-файлом-manage.py>/.
# Например:
WorkingDirectory=/home/{username}/{simple_vk_telegram_search_bot}/

# Команду, которую вы запускали руками, теперь будет запускать systemd:
# /home/<имя-пользователя-в-системе>/
# <директория-с-проектом>/<путь-до-bot_name-в-виртуальном-окружении> python main.py
ExecStart=/home/{username}/{simple_vk_telegram_search_bot} python main.py

[Install]
# В этом параметре указывается вариант запуска процесса.
# Значение <multi-user.target> указывают, чтобы systemd запустил процесс,
# доступный всем пользователям и без графического интерфейса.
WantedBy=multi-user.target
```
#### Управлеине `systemd` демоном:
```
sudo systemctl                           # Простотр всех демонов.
sudo systemctl start {deamon-name}       # Запуск.
sudo systemctl stop {deamon-name}        # Остановка.
sudo systemctl restart {deamon-name}     # Перезапуск.
sudo systemctl enable {deamon-name}      # Добавление в автозапуск.
sudo systemctl status {deamon-name}      # Проверка статуса.
sydo systemctl daemon-reload             # Перезапуск при изменениях в service файлах.
```
