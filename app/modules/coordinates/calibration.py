import re
import unicodedata
from fractions import Fraction

from app.errors import DomainError
from .box import Box, rectangle


def dpi_value(value):
    if type(value) not in (int, str):
        raise DomainError('BAD_DPI')
    text = unicodedata.normalize('NFKC', str(value)).strip().lower()
    if not (match := re.fullmatch(r'([0-9]{2,4})(?:\s*dpi)?', text)):
        raise DomainError('BAD_DPI')
    amount = int(match[1])
    if not 72 <= amount <= 1200:
        raise DomainError('BAD_DPI')
    return amount


def transform(row, width, height):
    dpi = dpi_value(row['dpi'])
    turn, origin, unit = row['rotation'], row['origin'], row['unit']
    if type(turn) is not int or turn not in (0, 90, 180, 270):
        raise DomainError('BAD_ROTATION')
    if origin not in ('TL', 'BL'):
        raise DomainError('BAD_ORIGIN')
    if unit not in ('px', 'mm'):
        raise DomainError('BAD_UNIT')
    scale = Fraction(127, 5 * dpi) if unit == 'px' else Fraction(1)
    raw_height = width if turn in (90, 270) else height
    result = {}
    for field, item in row['fields'].items():
        try:
            raw = rectangle(item['box'])
        except DomainError as error:
            raise DomainError(error.code, field=field) from None
        x, y, w, h = (getattr(raw, name) * scale for name in ('x', 'y', 'w', 'h'))
        if origin == 'BL':
            y = raw_height - y - h
        if turn == 0:
            box = Box(x, y, w, h)
        elif turn == 90:
            box = Box(y, height - x - w, h, w)
        elif turn == 180:
            box = Box(width - x - w, height - y - h, w, h)
        else:
            box = Box(width - y - h, x, h, w)
        result[field] = box
    return dpi, result
