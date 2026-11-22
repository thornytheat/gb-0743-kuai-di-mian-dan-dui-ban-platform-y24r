from app.modules.coordinates.box import rectangle
from app.modules.occlusion.rules import inspect


def checked(batch, label):
    return next(row for row in batch['occlusion'] if row['label'] == label)


def test_zero_area_touch_still_can_occlude_quiet_strip(batch):
    row = checked(batch, 'L-005')
    assert 'FIELD_OVERLAP' not in {item['code'] for item in row['issues']}
    hit = next(item for item in row['issues'] if item['code'] == 'QUIET_OCCUPIED')
    assert (hit['fields'], hit['side'], hit['area_mm2']) == (['barcode','route'], 'right', '28')


def test_detects_both_positive_overlap_and_quiet_overlap(batch):
    row = checked(batch, 'L-006')
    areas = {item['code']: item['area_mm2'] for item in row['issues']}
    assert areas['FIELD_OVERLAP'] == '7' and areas['QUIET_OCCUPIED'] == '28'


def test_quiet_margin_can_fail_even_with_print_fully_inside(batch):
    row = checked(batch, 'L-007')
    assert row['issues'] == [{'code':'QUIET_EDGE','fields':['barcode'],'area_mm2':'14','area_exact_mm2':'14','side':'left'}]


def test_clip_area_counts_only_portion_off_paper(batch):
    row = checked(batch, 'L-008')
    issues = {entry['code']:entry['area_mm2'] for entry in row['issues']}
    assert issues['BOX_OUTSIDE_SHEET'] == '72' and issues['FIELD_OUTSIDE_ZONE'] == '144'


def test_new_version_quiet_width_takes_effect_at_boundary(batch):
    assert checked(batch, 'L-018')['quiet']['left']['w'] == '4'
    row = checked(batch, 'L-019')
    assert row['quiet']['left']['w'] == '5' and row['issues'][0]['area_mm2'] == '90'


def test_sub_display_precision_overlap_remains_a_failure(batch):
    template = batch['templates']['versions'][0]
    boxes = {'barcode':rectangle([20,20,60,14]), 'route':rectangle(['79.999999','33.999999',1,1]),
             'recipient':rectangle([12,70,68,9])}
    rows, _ = inspect(boxes, template)
    tiny = next(row for row in rows if row['code'] == 'FIELD_OVERLAP')
    assert tiny['area_mm2'] == '0' and tiny['area_exact_mm2'] == '1/1000000000000'
