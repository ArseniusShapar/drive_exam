import time
from random import uniform


def convert_date(date: str) -> str:
    day, month, year, _ = date.split()

    monthes = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня',
               'листопада', 'грудня']
    month_idx = monthes.index(month) + 1
    if month_idx == 0:
        raise ValueError('Unknown month')

    return f'{day}.{month_idx}'


def total_minutes(t: str) -> int:
    hours, minutes = t.split(':')
    return 60 * int(hours) + int(minutes)


def random_sleep(a: float = 0.3, b: float = 0.5):
    time.sleep(uniform(a, b))


def type_like_human(element, text):
    for c in text:
        element.send_keys(c)
        random_sleep(0.05, 0.1)
