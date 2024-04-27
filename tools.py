def convert_date(date: str) -> str:
    day, month = date.split('.')

    monthes = ['Січня', 'Лютого', 'Березня', 'Квітня', 'Травня', 'Червня', 'Липня', 'Серпня', 'Вересня', 'Жовтня',
               'Листопада', 'Грудня']
    return f'{day} {monthes[int(month) - 1]}'


def trim_date(date: str) -> str:
    s1, s2, s3 = date.split(' ')
    return s1 + ' ' + s2


def total_minutes(t: str) -> int:
    hours, minutes = t.split(':')
    return 60 * int(hours) + int(minutes)


def tsc_coords(tsc: str):
    coords = {'8049': '(483px, 206px, 0px)',
              '3246': '(472px, 208px, 0px)',
              '8041': '(471px, 206px, 0px)',
              '8042*': '(472px, 203px, 0px)',
              '3242': '(460px, 250px, 0px)',
              '3248': '(522px, 232px, 0px)',
              '1841': '(390px, 217px, 0px)'}
    return coords[tsc]
