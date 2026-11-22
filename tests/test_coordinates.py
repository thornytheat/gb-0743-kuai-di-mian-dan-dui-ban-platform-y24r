from fractions import Fraction

import pytest

from app.errors import DomainError
from app.modules.coordinates.box import rectangle
from app.modules.coordinates.calibration import transform


def by_label(batch, label):
    return next(row for row in batch['coordinates'] if row['label'] == label)


# TRAP-06 TRAP-15

def test_fullwidth_dpi_90_degree_lower_left_px_matches_upper_left_mm(batch):
    base, rotated = [by_label(batch, label) for label in ('L-001','L-002')]
    assert (rotated['dpi_raw'], rotated['dpi'], rotated['origin'], rotated['unit']) == ('２５４ ｄｐｉ', 254, 'BL', 'px')
    assert rotated['boxes'] == base['boxes']
    assert rotated['boxes']['barcode'] == {'x':'20','y':'20','w':'60','h':'14'}


def test_180_and_270_rotate_whole_rectangle_instead_of_just_point(batch):
    base = by_label(batch, 'L-001')['boxes']
    assert by_label(batch, 'L-003')['boxes'] == by_label(batch, 'L-004')['boxes'] == base


def test_ambiguous_device_dpi_is_never_guessed(batch):
    row = by_label(batch, 'L-012')
    assert (row['code'], row['dpi_raw']) == ('BAD_DPI', '203/300') and 'boxes' not in row


def test_fractional_conversion_remains_exact_until_output():
    row = {'dpi':203,'unit':'px','rotation':0,'origin':'TL','fields':{'barcode':{'box':[1,3,5,7]}}}
    _, boxes = transform(row, Fraction(100), Fraction(150))
    assert boxes['barcode'].x == Fraction(127, 1015)
    assert boxes['barcode'].output()['x'] == '0.125123'


def test_invalid_origin_and_nonpositive_extent_report_field_failure():
    row = {'dpi':300,'unit':'mm','rotation':0,'origin':'CENTER','fields':{'barcode':{'box':[1,3,0,7]}}}
    with pytest.raises(DomainError, match='BAD_ORIGIN'):
        transform(row, Fraction(100), Fraction(150))
    with pytest.raises(DomainError, match='BAD_BOX') as failure:
        transform(dict(row, origin='TL'), Fraction(100), Fraction(150))
    assert failure.value.details == {'field':'barcode'}


def test_disallows_boolean_dpi_and_nonright_angle():
    row = {'dpi':True,'unit':'px','rotation':45,'origin':'TL','fields':{'barcode':{'box':[1,3,5,7]}}}
    with pytest.raises(DomainError, match='BAD_DPI'):
        transform(row, Fraction(100), Fraction(150))
    with pytest.raises(DomainError, match='BAD_ROTATION'):
        transform(dict(row, dpi=300), Fraction(100), Fraction(150))
    assert rectangle(['0.000001',0,1,1]).x == Fraction(1, 1000000)
