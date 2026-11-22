export const $ = id => document.getElementById(id);
const labels = JSON.parse($('labels').textContent);
const voids = JSON.parse($('void-labels').textContent);
const formatter = new Intl.DateTimeFormat('zh-CN', {timeZone:'Asia/Shanghai', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23'});
export const field = name => ({barcode:'条码', route:'路由码', recipient:'收件代号', left:'左静区', right:'右静区'})[name] || name;
export const explanation = code => labels[code] || voids[code] || code;
export const clock = value => formatter.format(new Date(value));
export const localInput = epochMs => new Date(epochMs + 8 * 3600000).toISOString().slice(0, 19);

export async function api(url, params) {
  const options = {cache: 'no-store'};
  if (params instanceof FormData) Object.assign(options, {method:'POST', body: params});
  else if (params) Object.assign(options, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(params)});
  const response = await fetch(url, options);
  const json = await response.json();
  if (!response.ok) throw Object.assign(new Error(json.message), json);
  return json;
}

export function element(tag, text = '', classes = '') {
  const item = document.createElement(tag);
  item.textContent = text;
  item.className = classes;
  return item;
}

export function command(text, invoke) {
  const button = element('button', text, 'text-btn');
  button.type = 'button';
  button.addEventListener('click', invoke);
  return button;
}

export function hint(text = '', problem = false, reload = false) {
  $('notice').hidden = !text;
  $('notice').classList.toggle('error', problem);
  $('message').textContent = text;
  $('reload').hidden = !reload;
}

export function summary(rows) {
  $('kpis').replaceChildren(...rows.map(([name, value, unit = '', tone = '']) => {
    const item = element('div', '', 'kpi');
    item.append(element('span', name), element('strong', value, `mono ${tone}`));
    if (unit) item.lastChild.append(element('span', ` ${unit}`));
    return item;
  }));
}

export function facts(id, rows) {
  $(id).replaceChildren(...rows.map(([name, value, tone='']) => {
    const item = element('div', '', 'fact');
    item.append(element('span', name, 'dim'), element('strong', value, `mono ${tone}`));
    return item;
  }));
}

export function table(id, headers, rows, empty = '暂无记录') {
  const target = $(id);
  if (!rows.length) { target.replaceChildren(element('p', empty, 'empty')); return; }
  const grid = element('table');
  const head = grid.createTHead().insertRow();
  headers.forEach((name, index) => {
    const th = element('th');
    th.scope = 'col';
    th.append(element('span', String.fromCharCode(65 + index), 'col-mark'), document.createTextNode(name));
    head.append(th);
  });
  const content = grid.createTBody();
  for (const row of rows) {
    const tr = content.insertRow();
    for (const value of row) {
      const td = tr.insertCell();
      td.tabIndex = 0;
      if (value instanceof Node) td.append(value);
      else {
        td.textContent = value ?? '—';
        td.title = td.textContent;
        if (typeof value === 'number') td.classList.add('mono');
      }
    }
  }
  target.replaceChildren(grid);
}

export function fillSelection(id, choices, selected) {
  const entries = choices.map(([value, text]) => {
    const option = element('option', text);
    option.value = value;
    return option;
  });
  const select = $(id);
  select.replaceChildren(...entries);
  if (entries.some(option => option.value === selected)) select.value = selected;
  return select.value;
}
