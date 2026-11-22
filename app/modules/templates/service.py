from app.clock import instant
from .versions import read_versions


def resolve(raw, prints):
    result = read_versions(raw)
    matches = {}
    for row in prints:
        item = row['data']
        at = instant(item['at'])
        eligible = [version for version in result['versions'] if version['format'] == item['format']
                    and instant(version['start']) <= at < instant(version['end'])]
        matches[item['label']] = max(eligible, key=lambda version: version['revision'], default=None)
    return dict(result, bindings=[{'label': label, 'line': version['line'] if version else None,
                                   'revision': version['revision'] if version else None}
                                  for label, version in matches.items()]), matches
