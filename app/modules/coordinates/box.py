import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction

from app.errors import DomainError


def scalar(value):
    if (not isinstance(value, (str, int, float)) or isinstance(value, bool)
            or not re.fullmatch(r'-?[0-9]{1,8}(?:\.[0-9]{1,6})?', str(value))):
        raise DomainError('BAD_BOX')
    return Fraction(Decimal(str(value)))


def printable(value):
    with localcontext() as context:
        context.prec = 40
        text = f'{Decimal(value.numerator) / Decimal(value.denominator):.6f}'.rstrip('0').rstrip('.')
    return text if text not in ('', '-0') else '0'


@dataclass(frozen=True)
class Box:
    x: Fraction
    y: Fraction
    w: Fraction
    h: Fraction

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    @property
    def area(self):
        return self.w * self.h

    def contains(self, other):
        return self.x <= other.x and self.y <= other.y and self.right >= other.right and self.bottom >= other.bottom

    def overlap(self, other):
        return max(0, min(self.right, other.right) - max(self.x, other.x)) * max(0, min(self.bottom, other.bottom) - max(self.y, other.y))

    def output(self):
        return {field: printable(getattr(self, field)) for field in ('x', 'y', 'w', 'h')}


def rectangle(values):
    if not isinstance(values, list) or len(values) != 4:
        raise DomainError('BAD_BOX')
    box = Box(*map(scalar, values))
    if min(box.w, box.h) <= 0:
        raise DomainError('BAD_BOX')
    return box
