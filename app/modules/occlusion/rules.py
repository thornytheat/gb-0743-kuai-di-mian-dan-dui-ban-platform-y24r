from itertools import combinations

from app.modules.coordinates.box import Box, printable, rectangle, scalar


def inspect(boxes, version):
    width, height = map(scalar, version['paper'])
    page = Box(0, 0, width, height)
    quiet = scalar(version['quiet_mm'])
    barcode = boxes['barcode']
    strips = {'left': Box(barcode.x - quiet, barcode.y, quiet, barcode.h),
              'right': Box(barcode.right, barcode.y, quiet, barcode.h)}
    issues = []

    def add(code, fields, amount, side=None):
        issues.append({'code': code, 'fields': fields, 'area_mm2': printable(amount),
                       'area_exact_mm2': str(amount), 'side': side})

    for field, box in sorted(boxes.items()):
        if not page.contains(box):
            add('BOX_OUTSIDE_SHEET', [field], box.area - page.overlap(box))
        zone = rectangle(version['zones'][field])
        if not zone.contains(box):
            add('FIELD_OUTSIDE_ZONE', [field], box.area - zone.overlap(box))
    for left, right in combinations(sorted(boxes), 2):
        if area := boxes[left].overlap(boxes[right]):
            add('FIELD_OVERLAP', [left, right], area)
    for side, strip in strips.items():
        if not page.contains(strip):
            add('QUIET_EDGE', ['barcode'], strip.area - page.overlap(strip), side)
        for field, box in sorted(boxes.items()):
            if field != 'barcode' and (area := strip.overlap(box)):
                add('QUIET_OCCUPIED', ['barcode', field], area, side)
    return issues, {side: box.output() for side, box in strips.items()}
