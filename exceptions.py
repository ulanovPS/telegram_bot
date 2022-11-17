class HTTPRequestError(Exception):
    """Обработчик ошибки."""

    def __init__(self, response):
        """Ошибка отправки запроса."""
        message = (
            f'{response.url} Эндпоинт недоступен. '
            f'Код ответа API: {response.status_code}'
        )
        super().__init__(message)


class ParseStatusError(Exception):
    """Обработчик ошибки."""

    def __init__(self, text):
        """Ошибка обратки ответа."""
        message = (
            f'Парсинг ответа API: {text}'
        )
        super().__init__(message)


class CheckResponseError(Exception):
    """Обработчик ошибки."""

    def __init__(self, text):
        """Ошибка ответа."""
        message = (
            f'Проверка ответа API: {text}'
        )
        super().__init__(message)
