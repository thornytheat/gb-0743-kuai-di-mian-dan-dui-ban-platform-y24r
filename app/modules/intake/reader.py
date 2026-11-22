import json

from app.canonical import canonical
from app.config import MAX_BYTES, MAX_ROWS
from app.errors import DomainError


class DuplicateKey(ValueError):
    pass


class NumericToken(str):
    """保留原始小数文本，供坐标字段精确解析。"""


def decode(raw):
    if len(raw) > MAX_BYTES:
        raise DomainError('INPUT_TOO_LARGE', 413)
    try:
        return raw.decode('utf-8-sig'), 'UTF-8 BOM' if raw.startswith(b'\xef\xbb\xbf') else 'UTF-8'
    except UnicodeDecodeError:
        try:
            return raw.decode('gb18030'), 'GB18030'
        except UnicodeDecodeError:
            raise DomainError('BAD_ENCODING') from None


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKey(key)
        if isinstance(value, str):
            value.encode('utf-8')
        key.encode('utf-8')
        out[key] = value
    return out


def reject_nonfinite(_):
    raise ValueError


def lines(raw, allow_empty=False):
    text, encoding = decode(raw)
    result = []
    physical = text.removesuffix('\n').split('\n') if text else []
    for index, text_line in enumerate(physical, 1):
        if index > MAX_ROWS:
            raise DomainError('INPUT_TOO_LARGE', 413)
        text_line = text_line.removesuffix('\r')
        row = {'line': index, 'raw': text_line, 'data': None, 'code': None}
        try:
            if not text_line.strip():
                row['code'] = 'BLANK_LINE'
            else:
                value = json.loads(text_line, object_pairs_hook=unique_pairs, parse_float=NumericToken,
                                   parse_constant=reject_nonfinite)
                if not isinstance(value, dict):
                    raise ValueError
                canonical(value).encode('utf-8')
                row['data'] = value
        except DuplicateKey:
            row['code'] = 'DUPLICATE_KEY'
        except (ValueError, RecursionError):
            row['code'] = 'BAD_JSON_LINE'
        result.append(row)
    if not result and not allow_empty:
        raise DomainError('EMPTY_INPUT')
    return result, encoding


def append_row(raw, data):
    _, encoding = decode(raw)
    codec = 'gb18030' if encoding == 'GB18030' else 'utf-8'
    separator = b'' if not raw or raw.endswith(b'\n') else b'\n'
    return raw + separator + canonical(data).encode(codec) + b'\n'
