from datetime import datetime, timezone

from .errors import DomainError


def instant(text):
    if not isinstance(text, str) or 'T' not in text:
        raise DomainError('BAD_TIME')
    try:
        value = datetime.fromisoformat(text.replace('Z', '+00:00'))
        if value.tzinfo is None:
            raise ValueError
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise DomainError('BAD_TIME') from None


def stamp(value):
    return value.isoformat().replace('+00:00', 'Z')
