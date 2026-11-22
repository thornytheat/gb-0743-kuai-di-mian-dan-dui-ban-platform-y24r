import {$, command, element, explanation, field, fillSelection, summary, table} from './dom.js';
let visibleBox = '';

function axes(grid, axis, distance, scale, step) {
  const ruler = element('div', '', `${axis}-axis`);
  for (let tick = 0; tick < distance; tick += step) {
    const mark = element('span', tick, 'tick');
    mark.style[axis === 'x' ? 'left' : 'top'] = `${tick * scale}px`;
    ruler.append(mark);
  }
  grid.append(ruler);
}

function place(paper, key, rect, theme, scale, issues = []) {
  const isZone = theme === 'zone';
  const title = theme === 'quiet' ? field(key) : field(theme);
  const marker = element(isZone ? 'span' : 'button', isZone || theme === 'quiet' ? '' : title,
    `rect ${theme}${issues.length ? ' problem' : ''}`);
  marker.style.left = `${Number(rect.x) * scale}px`;
  marker.style.top = `${Number(rect.y) * scale}px`;
  marker.style.width = `${Number(rect.w) * scale}px`;
  marker.style.height = `${Number(rect.h) * scale}px`;
  if (!isZone) {
    marker.type = 'button';
    marker.title = `${title} · ${rect.x}, ${rect.y} · ${rect.w} × ${rect.h} mm`;
    marker.setAttribute('aria-label', marker.title);
    marker.setAttribute('aria-pressed', String(visibleBox === key));
    marker.addEventListener('click', () => {
      visibleBox = key;
      for (const box of paper.querySelectorAll('button')) box.setAttribute('aria-pressed', String(box === marker));
      $('coord-meta').textContent = [marker.title, ...new Set(issues.map(row => explanation(row.code)))].join(' · ');
    });
  }
  paper.append(marker);
}

function board(row, test) {
  const [width, height] = row.paper.map(Number);
  const scale = Math.min(4, 600 / Math.max(width, height));
  const tick = width < 40 ? 5 : width > 220 ? 20 : 10;
  const grid = element('div', '', 'proof');
  grid.style.setProperty('--sheet-width', `${width * scale}px`);
  grid.style.setProperty('--sheet-height', `${height * scale}px`);
  grid.style.setProperty('--major', `${tick * scale}px`);
  grid.append(element('div', 'mm', 'corner'));
  axes(grid, 'x', width, scale, tick);
  axes(grid, 'y', height, scale, tick);
  const paper = element('div', '', 'paper');
  for (const [key, rect] of Object.entries(row.zones)) place(paper, key, rect, 'zone', scale);
  for (const [key, rect] of Object.entries(test?.quiet || {}))
    place(paper, key, rect, 'quiet', scale, test.issues.filter(issue => issue.side === key));
  for (const [key, rect] of Object.entries(row.boxes))
    place(paper, key, rect, key, scale, (test?.issues || []).filter(issue => issue.fields.includes(key)));
  grid.append(paper);
  $('board').replaceChildren(grid);
}

export function coordinates(rows, checks, anchor, select) {
  const good = rows.filter(row => row.boxes);
  const initial = anchor || (rows.some(row => row.label === 'L-006') ? 'L-006' : good[0]?.label);
  const chosen = fillSelection('coord-label', rows.map(row => [row.label, row.label]), initial);
  const row = rows.find(item => item.label === chosen);
  const test = checks.find(item => item.label === chosen);
  summary([['坐标回执',rows.length,'张'],['完成换算',good.length,'张'],['换算隔离',rows.length-good.length,'张','warn'],
    ['当前 DPI',row?.dpi ?? '—'],['旋转',typeof row?.rotation === 'number' ? row.rotation : '—','°']]);
  visibleBox = '';
  $('coord-meta').textContent = row?.dpi ? `${row.device} · ${row.origin} · ${row.unit} → mm` : '';
  if (row?.boxes) board(row, test);
  else $('board').replaceChildren(element('p', row?.code ? explanation(row.code) : '请选择面单', 'empty'));
  const list = [...Object.entries(row?.boxes || {}), ...Object.entries(test?.quiet || {})];
  table('coord-fields', ['字段','X','Y','宽','高'], list.map(([key, rect]) => [field(key),
    ...['x','y','w','h'].map(prop => element('span', rect[prop], 'mono'))]));
  table('coordinate-index', ['源行','面单','设备','DPI','旋转','原点','单位','判定'], rows.map(item =>
    [item.line, command(item.label, () => select(item.label)), item.device, String(item.dpi_raw), String(item.rotation),
      String(item.origin), String(item.unit), item.code ? explanation(item.code) : '坐标已归一']));
}
