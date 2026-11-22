from .rules import inspect


def check(physical, versions):
    output = []
    for label, boxes in physical.items():
        version = versions[label]
        issues, quiet = inspect(boxes, version)
        output.append({'label': label, 'version_line': version['line'], 'issues': issues,
                       'quiet_mm': version['quiet_mm'], 'quiet': quiet, 'ok': not issues})
    return output
