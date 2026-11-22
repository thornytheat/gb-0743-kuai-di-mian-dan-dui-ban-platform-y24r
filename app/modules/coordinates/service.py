from app.errors import DomainError
from .box import printable, rectangle, scalar
from .calibration import transform


def calibrate(prints, versions):
    results, physical = [], {}
    for entry in prints:
        row = entry['data']
        key = row['label']
        version = versions[key]
        output = {'label': key, 'line': entry['line'], 'device': row['device'], 'dpi_raw': row['dpi'],
                  'rotation': row['rotation'], 'origin': row['origin'], 'unit': row['unit']}
        try:
            if version is None:
                raise DomainError('NO_TEMPLATE')
            width, height = map(scalar, version['paper'])
            dpi, boxes = transform(row, width, height)
            physical[key] = boxes
            output.update(dpi=dpi, paper=[printable(width), printable(height)],
                          zones={field: rectangle(box).output() for field, box in version['zones'].items()},
                          boxes={field: box.output() for field, box in boxes.items()})
        except DomainError as error:
            output.update(code=error.code, details=error.details)
        results.append(output)
    return results, physical
