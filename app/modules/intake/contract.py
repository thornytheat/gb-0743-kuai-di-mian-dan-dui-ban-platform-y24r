import re

from app.clock import instant, stamp
from app.errors import DomainError

FIELDS = {'barcode', 'route', 'recipient'}
COLUMNS = {'label', 'parcel', 'at', 'format', 'device', 'dpi', 'rotation', 'origin', 'unit', 'fields'}


def valid_code(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,48}', value) is not None


def normalize(data):
    if not COLUMNS <= data.keys() or data.keys() - COLUMNS - {'replaces'}:
        raise DomainError('BAD_PRINT')
    if any(not valid_code(data[field]) for field in ('label', 'parcel', 'format', 'device')):
        raise DomainError('BAD_PRINT')
    fields = data['fields']
    if not isinstance(fields, dict) or set(fields) != FIELDS:
        raise DomainError('BAD_PRINT')
    for item in fields.values():
        if (not isinstance(item, dict) or set(item) != {'value', 'box'}
                or type(item['value']) is not str or not item['value'].strip()):
            raise DomainError('BAD_PRINT')
    replaces = data.get('replaces')
    if replaces is not None and not valid_code(replaces):
        raise DomainError('BAD_PRINT')
    return dict(data, at=stamp(instant(data['at'])), replaces=replaces)
