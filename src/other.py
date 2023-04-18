import re
import time

def is_youtube_url(url: str) -> bool:
    """функция для проверки url которую вводит пользователь"""
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*'
    match = re.match(pattern, url)
    return match is not None

def convert_time(time_: int) -> str:
    """Функция которая преобразует секунды в время"""
    time_answer = time.strftime("%M:%S",
                        time.gmtime(time_))
    return time_answer