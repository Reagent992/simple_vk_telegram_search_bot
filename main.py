import logging
import os
import time
from logging.handlers import RotatingFileHandler

import telegram
import vk_api
from dotenv import load_dotenv

# ---------------Константы--------------------------
load_dotenv()

KEYWORD = os.getenv('keyword')
BOT_TOKEN = os.getenv('bot_token')
CHAT_ID = os.getenv('chat_id')
LOGIN = os.getenv('login')
PASSWORD = os.getenv('password')
VK_GROUP_NAME = os.getenv('vk_group_name')
BOT_NAME = os.getenv('bot_name')
CHECK_PERIOD = int(os.getenv('check_period'))
# ----------------Логгер---------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] [%(lineno)d строка]  %(message)s '
)
log_files_handler = RotatingFileHandler(
    'custom_logger.log', maxBytes=2000000, backupCount=5, encoding='utf-8')
log_files_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(log_files_handler)
logger.addHandler(stream_handler)
# ------------------------------------------------


def check_tokens() -> bool:
    """Проверяем доступность необходимых переменных окружения."""
    logger.debug('Запущена проверка необходимых переменных окружения')
    return all([KEYWORD, BOT_TOKEN, CHAT_ID, LOGIN, PASSWORD,
                VK_GROUP_NAME, BOT_NAME, CHECK_PERIOD])


def send_message(bot: telegram.Bot, message: str) -> bool:
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.debug('Запущена отправка сообщения в Telegram')
        bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f'Сообщение {message} отправлено на №{CHAT_ID}')
        return True
    except telegram.error.TelegramError as e:
        logger.error(f'Неудачная отправка сообщения: {message} ошибка {e}')
        return False


def auth_handler():
    """
    При двухфакторной аутентификации вызывается эта функция.
    Код двуфакторки нужно будет ввести в консоли
    """
    logger.info('Запуск функции двуфакторки')
    # Код двухфакторной аутентификации
    key = input("Введите код двухфакторной аутентификации: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device


def get_vk_posts(login, password):
    """
    Получения постов группы.
    Через использование встроенного в API поиска.
    """

    try:
        logger.debug('Запущено получение постов из VK')
        vk_session = vk_api.VkApi(login, password, auth_handler=auth_handler)
        vk_session.auth(token_only=True)
        vk = vk_session.get_api()
        response = vk.wall.search(domain=VK_GROUP_NAME, query=KEYWORD)
    except vk_api.AuthError as error_msg:
        logger.error(error_msg)
        raise KeyError(error_msg)

    if response:
        logger.debug('Посты получены')
        return response
    else:
        logger.debug('Посты не получены')
        return None


def parse_posts(response):
    """Вытаскивает ID-постов из ответа API"""
    # Собираем id постов
    posts_id = []
    logger.debug('Запуск парсинга id постов из ответа API.')

    # Запись идшников в переменные.
    if t := response["items"]:
        [posts_id.append(i["id"]) for i in t]

    logger.debug(f'Получены посты:{posts_id}')
    if posts_id:
        logger.debug('В ответе есть id')
        return posts_id
    else:
        logger.debug('В ответе нет id.')
        return None


def first_run(posts_id):
    """При первом запуске сохраняет id постов в файл."""
    logger.debug('Первичная запись id постов в файл, при первом запуске бота.')
    with open("posts_ids.txt", "w") as file:
        for post_id in posts_id:
            file.write(str(post_id) + "\n")


def check_new_posts(posts_id):
    """
    Ищет новые посты.
    Дозаписывает в файл.
    Отдает id новых постов.
    """
    logger.debug('Запуск проверки новых постов.')

    # Считываем старый список ID из файла
    with open("posts_ids.txt", "r") as f:
        old_posts_id = [int(line.strip()) for line in f]
        logger.debug(f'Старые id:{old_posts_id}')

    # Сравниваем списки ID
    new_ids = set(posts_id) - set(old_posts_id)
    if new_ids:
        logger.debug('Найдены новые посты, дозаписываем в список')
        with open("posts_ids.txt", "a") as f:
            for post_id in new_ids:
                f.write(str(post_id) + "\n")
        return new_ids
    else:
        logger.debug('Новые посты не найдены.')
        return False


def get_new_post_text(response, new_posts_id):
    """Получает текст нового поста по id."""
    p_id = list(new_posts_id)[0]
    logger.debug(p_id)
    logger.debug(type(p_id))
    for i in response['items']:
        if i['id'] == p_id:
            return i['text']


def main():
    """Основной цикл бота."""
    if not check_tokens():
        msg = 'Отсутствуют переменные окружения'
        logger.critical(msg)
        raise NameError(msg)

    bot = telegram.Bot(token=BOT_TOKEN)
    last_telegram_message = None
    is_first_run = True

    while True:
        try:
            logger.debug("Начало цикла работы бота.")
            # Получаем ответ API
            if vk_response := get_vk_posts(LOGIN, PASSWORD):
                # Достаем id постов из ответа.
                if parsed_posts := parse_posts(vk_response):
                    # Если первый запуск просто сохраняем посты в файл
                    if is_first_run:
                        first_run(parsed_posts)
                        is_first_run = False
                    else:
                        # Иначе отправляем текст нового поста.
                        if new_posts_id := check_new_posts(parsed_posts):
                            message_post_text = (
                                get_new_post_text(vk_response, new_posts_id))
                            logger.info('Отправка нового поста в ТГ')
                            send_message(bot, str(message_post_text))

        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе [{BOT_NAME}]: {error}'
            if message != last_telegram_message:
                send_message(bot, message)
                # Сохраняем последнее отправленное сообщение
                last_telegram_message = message

        finally:
            logger.debug('Идем спать')
            time.sleep(CHECK_PERIOD)
            logger.debug(
                f"Конец цикла работы бота. Прошло {CHECK_PERIOD} секунд.")


if __name__ == '__main__':
    main()
