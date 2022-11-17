import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from exceptions import CheckResponseError, HTTPRequestError, ParseStatusError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDIKT = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """отправляет сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение от бота {message}, успешно отправлено')
    except telegram.TelegramError as error:
        raise telegram.TelegramError(f'Ошибка отправки сообщения: {error}')


def get_api_answer(current_timestamp):
    """Отправляем запрос."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info(f'Отправка запроса {ENDPOINT} с параметрами {params}')
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError(response)
    return response.json()


def check_response(response):
    """Проверка полученного ответа."""
    if not response:
        raise KeyError('содержит пустой словарь')

    if not isinstance(response, dict):
        raise TypeError('имеет некорректный тип')

    if 'homeworks' not in response:
        raise KeyError('отсутствие ожидаемых ключей в ответе')

    if not isinstance(response.get('homeworks'), list):
        raise CheckResponseError('формат ответа не соответствует')

    return response['homeworks']


def parse_status(homework):
    """Статус домашней работы."""
    homework_name = homework.get('homework_name')
    if not homework.get('homework_name'):
        raise KeyError('Отсутствует имя домашней работы.')

    homework_status = homework.get('status')
    if 'status' not in homework:
        raise ParseStatusError('Отсутстует ключ homework_status')

    verdict = HOMEWORK_VERDIKT.get(homework_status)
    if homework_status not in HOMEWORK_VERDIKT:
        raise KeyError('Недокументированный статус домашней работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """проверяет доступность переменных окружения необходимых для работы."""
    env_list = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    return all(env_list)


def main():
    """Основная логика работы бота."""
    last_send = {
        'error': None,
    }
    if not check_tokens():
        sys.exit(
            'Отсутствует обязательная переменная окружения.\n'
            'Программа принудительно остановлена.'
        )

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logging.debug('Ответ API пуст: нет домашних работ.')
            else:
                message = parse_status(homeworks[-1])
                send_message(bot, message)
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_send['error'] != message:
                send_message(bot, message)
                last_send['error'] = message
            logging.error(last_send['error'])
        else:
            last_send['error'] = None
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stdout

    )
    main()
