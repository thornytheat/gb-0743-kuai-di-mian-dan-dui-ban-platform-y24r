import {$, api, clock, hint, localInput} from './dom.js';
import {coordinates} from './proof.js';
import * as views from './stages.js';

const navigation = new Map([...document.querySelectorAll('[data-stage]')].map(link => [link.dataset.stage, link]));
let stage, selected, anchor, info, data, extra, sequence = 0, busy = false;
const run = () => info.manifest.id;
const active = () => info.history.find(row => row.active)?.id;

function topbar() {
  const {manifest} = info;
  const current = run() === active();
  $('run-tag').textContent = run().slice(0, 12);
  $('version-chip').textContent = `${manifest.inputs.prints.sha256.slice(0, 12)} · v${manifest.rule_version}`;
  $('state').textContent = current ? '当前批次' : '历史批次';
  $('stamp').textContent = `${manifest.timezone} · ${clock(manifest.created)} · ${manifest.elapsed_ms} ms`;
  $('export').href = `/api/runs/${run()}/evidence.json`;
  $('export').removeAttribute('aria-disabled');
  $('rerun').disabled = !current || busy;
  $('upload-form').querySelector('button').disabled = !current || busy;
}

function chooseTarget(force = false) {
  const row = views.ticketForm(data, run() === active() && !busy);
  if (row && (force || !$('ticket-time').value)) {
    const defaultAt = $('ticket-action').value === 'reprint' ? Date.parse(row.void.at) + 60000 : Date.parse(row.at) + 60000;
    $('ticket-time').value = localInput(defaultAt);
  }
}

function draw() {
  if (!info || !data) return;
  if (stage === 'coordinates') coordinates(data, extra, anchor, id => { anchor = id; draw(); });
  else if (stage === 'occlusion') views.occlusion(data, id => { anchor = id; location.hash = 'coordinates'; });
  else if (stage === 'tickets') { views.tickets(data, info, id => load(id)); chooseTarget(); }
  else views[stage](data);
}

async function load(selection = selected) {
  selected = selection;
  const hash = location.hash.slice(1);
  stage = navigation.has(hash) ? hash : 'coordinates';
  const key = stage;
  const id = ++sequence;
  data = null;
  $('crumb').textContent = $('title').textContent = navigation.get(key).textContent;
  for (const [name, link] of navigation) {
    if (name === key) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
    $(`stage-${name}`).hidden = true;
  }
  $('kpis').replaceChildren();
  $('rerun').disabled = true;
  $('export').removeAttribute('href');
  $('export').setAttribute('aria-disabled','true');
  hint('正在读取批次…');
  try {
    const meta = await api(`/api/runs${selection ? `?run=${encodeURIComponent(selection)}` : ''}`);
    if (id !== sequence) return;
    const suffix = `?run=${encodeURIComponent(meta.manifest.id)}`;
    const [result, proof] = await Promise.all([api(`/api/${key}${suffix}`), key === 'coordinates' ? api(`/api/occlusion${suffix}`) : null]);
    if (id !== sequence) return;
    if (info?.manifest.id !== meta.manifest.id) $('ticket-time').value = '';
    info = meta;
    data = result.data;
    extra = proof?.data;
    topbar();
    draw();
    $(`stage-${key}`).hidden = false;
    hint();
  } catch (error) { if (id === sequence) hint(error.message || '读取失败', true, true); }
}

async function mutate(url, params, done) {
  if (busy) return;
  busy = true;
  const token = sequence;
  const forms = [$('ticket-form'), $('upload-form')];
  for (const form of forms) form.inert = true;
  $('rerun').disabled = $('restore').disabled = true;
  hint('正在检查…');
  try {
    const result = await api(url, params);
    if (token === sequence) {
      await load(null);
      if (data) done(result);
    }
  } catch (error) {
    if (token === sequence) hint(error.message || '提交失败，请重试', true, error.code === 'STALE_RUN');
  } finally {
    for (const form of forms) form.inert = false;
    busy = false;
    $('restore').disabled = false;
    if (data) { topbar(); if (stage === 'tickets') chooseTarget(); }
  }
}

window.addEventListener('hashchange', () => { if (location.hash !== '#main') load(); });
for (const id of ['intake-filter','template-filter','barcode-filter','occlusion-filter','parcel-filter','ticket-filter','void-filter']) $(id).addEventListener('change', draw);
$('coord-label').addEventListener('change', () => { anchor = $('coord-label').value; draw(); });
$('reload').addEventListener('click', () => load(null));
$('rerun').addEventListener('click', () => mutate('/api/runs/rerun',{expected:run()}, () => hint('复算完成 · 沿用原批次')));
$('restore').addEventListener('click', () => mutate('/api/runs/restore',{expected:active(),target:run()}, () => hint('已切回选中批次')));
$('ticket-action').addEventListener('change', () => chooseTarget(true));
$('ticket-target').addEventListener('change', () => chooseTarget(true));
$('upload-form').addEventListener('submit', event => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  form.set('expected',run());
  mutate('/api/intake',form, result => { $('upload-form').reset(); hint(result.created ? '收件已归档' : '沿用已有批次'); });
});
$('ticket-form').addEventListener('submit', event => {
  event.preventDefault();
  const time = $('ticket-time').value;
  const base = {expected:run(),at:`${time.length === 16 ? time + ':00' : time}+08:00`};
  const old = $('ticket-target').value;
  if ($('ticket-action').value === 'reprint') {
    mutate('/api/tickets/reprint',{...base,target:old,label:$('ticket-new').value}, () => {
      $('ticket-new').value = '';
      hint('重打已登记');
    });
  } else mutate('/api/tickets/void',{...base,label:old,reason:$('ticket-reason').value}, () => hint('面单已作废'));
});
load(null);
