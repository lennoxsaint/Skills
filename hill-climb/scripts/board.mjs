// Renders the scoreboard and the owner checkpoint as self-contained HTML (no scripts, no external assets),
// readable on a phone and publishable as a private page. Rendered screens are embedded as data URIs, within a size cap.
import fs from 'node:fs';
import path from 'node:path';
import { readManifest, rubricOf, listReferences } from './council.mjs';
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const clip = (s, n) => { s = typeof s === 'string' ? s : JSON.stringify(s ?? ''); return s.length > n ? `${s.slice(0, n)}…` : s; };
const pct = (v) => (v == null ? '–' : `${Number(v).toFixed(1).replace(/\.0$/, '')}`);

const STYLE = `
:root{--bg:#f7f6f2;--panel:#ffffff;--ink:#1d1c19;--muted:#6b6860;--line:#e3e0d8;--accent:#2f6fde;--good:#1f8a4c;--bad:#c2412d;--warn:#b7791f;--hold:#8a4fd8}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141412;--panel:#1d1d1a;--ink:#ecebe6;--muted:#a19e95;--line:#33322e;--accent:#6ea0ff;--good:#4cc27e;--bad:#f07a63;--warn:#e0aa4a;--hold:#b48cf2}}
:root[data-theme="dark"]{--bg:#141412;--panel:#1d1d1a;--ink:#ecebe6;--muted:#a19e95;--line:#33322e;--accent:#6ea0ff;--good:#4cc27e;--bad:#f07a63;--warn:#e0aa4a;--hold:#b48cf2}
*{box-sizing:border-box}html,body{margin:0}body{background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 10px}p{margin:6px 0}
.muted{color:var(--muted)}.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:13px;font-weight:600;border:1px solid var(--line)}
.ok{color:var(--good)}.no{color:var(--bad)}.warn{color:var(--warn)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:16px 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.tile b{display:block;font-size:24px;line-height:1.2}.tile span{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:10px 0;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;font-size:13.5px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
svg{width:100%;height:auto;display:block}
code,pre{font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}pre{white-space:pre-wrap;margin:6px 0;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;max-height:220px;overflow:auto}
.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.shot{margin:0}.shot img{width:100%;height:auto;border:1px solid var(--line);border-radius:8px;display:block;background:var(--bg)}.shot figcaption{font-size:12.5px;color:var(--muted);margin:4px 0 0}
.cats{font-size:12px;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:var(--muted);margin-top:6px}.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
`;

const page = (title, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><style>${STYLE}</style></head><body><main>${body}</main></body></html>`;

function chart(hill, state) {
  const hist = state.history ?? [];
  if (!hist.length) return '<p class="muted">No attempts yet.</p>';
  const W = 900, H = 300, L = 40, R = 14, T = 14, B = 30;
  const xs = hist.map((h) => h.n), maxN = Math.max(1, ...xs);
  const vals = hist.flatMap((h) => [h.score, h.holdout]).filter((v) => typeof v === 'number');
  const target = hill.metric?.target;
  const lo = Math.max(0, Math.floor((Math.min(...vals, target ?? 100) - 5) / 5) * 5), hi = 100;
  const x = (n) => L + ((W - L - R) * n) / maxN, y = (v) => T + ((H - T - B) * (hi - v)) / Math.max(1, hi - lo);
  let best = null; const steps = [];
  for (const h of hist) if (['baseline', 'kept'].includes(h.decision) && typeof h.score === 'number') { best = h.score; steps.push([h.n, best]); }
  steps.push([maxN, best]);
  const path = steps.map(([n, v], i) => `${i ? `L${x(n)},${y(steps[i - 1][1])} L` : 'M'}${x(n)},${y(v)}`).join(' ');
  const grid = []; for (let v = lo; v <= hi; v += (hi - lo) / 4) grid.push(`<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${Math.round(v)}</text>`);
  const pts = hist.map((h) => {
    if (typeof h.score !== 'number') return `<text x="${x(h.n)}" y="${H - B - 4}" text-anchor="middle" font-size="11" fill="var(--muted)">·</text>`;
    const kept = ['baseline', 'kept'].includes(h.decision);
    return `<circle cx="${x(h.n)}" cy="${y(h.score)}" r="${kept ? 4.5 : 3.5}" fill="${kept ? 'var(--accent)' : 'var(--panel)'}" stroke="${kept ? 'var(--accent)' : 'var(--muted)'}" stroke-width="1.5"><title>#${h.n} ${h.decision} ${pct(h.score)}</title></circle>`;
  }).join('');
  const hold = hist.filter((h) => typeof h.holdout === 'number').map((h) => `<rect x="${x(h.n) - 4}" y="${y(h.holdout) - 4}" width="8" height="8" transform="rotate(45 ${x(h.n)} ${y(h.holdout)})" fill="var(--hold)"><title>#${h.n} hidden ${pct(h.holdout)}</title></rect>`).join('');
  const tgt = typeof target === 'number' ? `<line x1="${L}" x2="${W - R}" y1="${y(target)}" y2="${y(target)}" stroke="var(--good)" stroke-dasharray="6 5" stroke-width="1.5"/><text x="${W - R}" y="${y(target) - 6}" text-anchor="end" font-size="11" fill="var(--good)">target ${target}</text>` : '';
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Score by attempt">${grid.join('')}${tgt}<path d="${path}" fill="none" stroke="var(--accent)" stroke-width="2"/>${pts}${hold}<text x="${(W + L) / 2}" y="${H - 6}" text-anchor="middle" font-size="11" fill="var(--muted)">attempt</text></svg>
<div class="legend"><span><i style="background:var(--accent)"></i>kept (best so far)</span><span><i style="border:1.5px solid var(--muted)"></i>tried and undone</span><span><i style="background:var(--hold);border-radius:1px;transform:rotate(45deg)"></i>hidden check</span><span><i style="background:var(--good);border-radius:0;height:2px"></i>target</span></div>`;
}

// The files of one render or reference folder as figures: images inline (data URIs), text as a short excerpt. Embedding
// stops at EMBED_CAP bytes per page; later images are named, not shown.
const MIME = { png: 'image/png', jpeg: 'image/jpeg', webp: 'image/webp' };
const EXT_KIND = { '.png': 'png', '.jpg': 'jpeg', '.jpeg': 'jpeg', '.webp': 'webp' };
const EMBED_CAP = 12 * 1024 * 1024, EMBED_ONE = 3 * 1024 * 1024;
function shots(dir, title, budget, max = 2) {
  if (!dir || !fs.existsSync(path.join(dir, 'manifest.json'))) return '';
  const m = readManifest(dir, title);
  if (!m.ok) return `<figure class="shot"><figcaption>${esc(title)}: ${esc(clip(m.problems.join('; '), 200))}</figcaption></figure>`;
  return m.files.slice(0, max).map((f) => {
    const cap = `<figcaption><b>${esc(title)}</b> · ${esc(f.label)}</figcaption>`;
    if (f.kind === 'text') return `<figure class="shot"><pre>${esc(clip(fs.readFileSync(path.join(dir, f.file), 'utf8'), 1500))}</pre>${cap}</figure>`;
    if (f.bytes > EMBED_ONE || budget.used + f.bytes > EMBED_CAP) return `<figure class="shot"><p class="muted">${esc(path.join(dir, f.file))} (too large to embed)</p>${cap}</figure>`;
    budget.used += f.bytes;
    const b64 = fs.readFileSync(path.join(dir, f.file)).toString('base64');
    return `<figure class="shot"><img alt="${esc(`${title}: ${f.label}`)}" src="data:${MIME[EXT_KIND[path.extname(f.file).toLowerCase()]]};base64,${b64}">${cap}</figure>`;
  }).join('');
}
const renderPath = (hill, name) => (name ? path.join(hill._dir, 'cache', 'renders', name) : null);
// Before, after and every reference side by side (render hills only).
function gallery(hill, state, budget) {
  if (!hill.council_render) return '';
  const after = state.council?.last?.render ?? null;
  const parts = [shots(renderPath(hill, state.baseline?.render), 'Before (start)', budget)];
  if (after && after !== state.baseline?.render) parts.push(shots(renderPath(hill, after), 'After (best judged)', budget));
  for (const r of listReferences(hill)) parts.push(shots(r.dir, `Reference: ${r.id}`, budget, 1));
  const html = parts.filter(Boolean).join('');
  return html ? `<h2>Before, after and the references</h2><div class="card"><div class="shots">${html}</div></div>` : '';
}
const signed = (v) => (v == null ? '' : `${v > 0 ? '+' : ''}${v}`);
const catLine = (c) => (c ? Object.entries(c).map(([k, v]) => `${esc(k)} ${v}`).join(' · ') : '');
function judgeCard(hill, s) {
  if (s.skipped) return `<p><b>${esc(s.judge)}</b>: <span class="muted">not asked this round (an earlier judge did not pass)</span></p>`;
  if (s.score == null) return `<p><b>${esc(s.judge)}</b>: <span class="no">${esc(s.error ?? 'no verdict')}</span></p>`;
  const lead = s.lead != null ? ` · <span class="${s.lead > 0 ? 'ok' : 'no'}">${signed(s.lead)} vs the best reference</span>` : '';
  const flags = [s.carried && 'earlier verdict (not asked about the latest change)', s.first && `asked twice (first ${s.first.score}${s.first.lead != null ? `, ${signed(s.first.lead)}` : ''})`, s.control != null && `scored the starting version ${s.control}`, s.drift?.length && `<span class="warn">drift: ${s.drift.map((d) => `${esc(d.item)} ${d.from} → ${d.to}`).join(', ')}</span>`].filter(Boolean);
  return `<p><b>${esc(s.judge)}</b>: <b class="${s.score >= hill.council_bar ? 'ok' : 'no'}">${s.score}/10</b> lowest category${lead} · ${s.ship ? '<span class="ok">would ship</span>' : '<span class="no">would not ship</span>'}<br><span class="cats">${catLine(s.categories)}</span>${flags.length ? `<br><span class="cats">${flags.join(' · ')}</span>` : ''}<br><span class="muted">${esc(clip(s.top_fault ?? '', 400))}</span></p>`;
}
// One row per council round: each judge's lowest category, lead and ship vote, with the categories underneath.
function roundsTable(hill, log) {
  if (!log?.length) return '';
  const judges = [...new Set(log.flatMap((r) => r.judges.map((j) => j.judge)))];
  const cell = (j) => {
    if (!j) return '<td class="muted">–</td>';
    if (j.skipped) return '<td class="muted">not asked</td>';
    if (j.score == null) return `<td class="no">${esc(clip(j.error ?? 'error', 60))}</td>`;
    return `<td><b class="${j.score >= hill.council_bar ? 'ok' : ''}">${j.score}</b>${j.lead != null ? ` <span class="${j.lead > 0 ? 'ok' : 'no'}">(${signed(j.lead)})</span>` : ''}${j.ship ? '' : ' <span class="no">no ship</span>'}${j.reasked ? ' <span class="muted">×2</span>' : ''}${j.drift?.length ? ' <span class="warn">drift</span>' : ''}<br><span class="cats">${catLine(j.categories)}${j.control != null ? ` · start ${j.control}` : ''}</span></td>`;
  };
  const rows = [...log].reverse().map((r) => `<tr><td>${r.n ?? '–'}</td><td>${esc(r.decision)}${r.pass ? ' <span class="ok">pass</span>' : ''}<br><span class="cats">${esc(r.mode ?? '')}</span>${r.control_missing ? ' <span class="warn">no control</span>' : ''}</td>${judges.map((name) => cell(r.judges.find((j) => j.judge === name))).join('')}</tr>`).join('');
  return `<div class="card scroll"><table><thead><tr><th>#</th><th>Round</th>${judges.map((j) => `<th>${esc(j)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table><p class="cats">Lowest category per judge; (+n) = lead over the best reference; ×2 = asked twice before it counted; start = its score for the starting version (a hidden control).</p></div>`;
}
const money = (u) => (u ? `$${u.total.toFixed(2)}` : '$0.00');

const STATUS_WORDS = { draft: 'Being built', frozen: 'Answer key locked', approved: 'Approved, ready to climb', climbing: 'Climbing', done: 'Done: target hit and judges agree', stuck: 'Stuck', deadline: 'Stopped at deadline', tampered: 'Stopped: answer key changed', stopped: 'Paused', error: 'Stopped on an error', max_attempts: 'Stopped at attempt cap', saturated: 'Stopped: visible tests maxed but the hidden check lags', blocked: 'Blocked: needs the owner', budget: 'Stopped at budget' };

export function renderBoard(hill, state) {
  const b = state.best ?? {}, base = state.baseline ?? {};
  const st = state.status ?? 'draft';
  const cls = st === 'done' ? 'ok' : ['stuck', 'tampered', 'error', 'blocked', 'saturated'].includes(st) ? 'no' : 'warn';
  const gap = typeof b.optimise === 'number' && typeof b.holdout === 'number' ? (b.optimise - b.holdout) : null;
  const sec = hill.metric?.secondary;
  const rows = [...(state.history ?? [])].reverse().slice(0, 80).map((h) => `<tr><td>${h.n}</td><td>${esc(h.decision)}</td><td>${pct(h.score)}${typeof h.delta === 'number' && h.n ? ` <span class="muted">(${h.delta >= 0 ? '+' : ''}${pct(h.delta)})</span>` : ''}</td><td>${pct(h.holdout)}</td>${sec ? `<td>${h.secondary ?? '–'}</td>` : ''}<td>${esc(clip(h.hypothesis ?? h.note ?? '', 160))}</td></tr>`).join('');
  const council = state.council?.last;
  const budget = { used: 0 };
  const councilHtml = council ? `<div class="card"><p><b>Latest verdict</b> (round ${state.council.rounds}) · lowest score <b class="${council.pass ? 'ok' : 'no'}">${council.min ?? '–'}/10</b> (bar ${hill.council_bar}${council.ref_mode ? ', and ahead of every reference' : ''})${council.drift ? ' · <span class="warn">a judge drifted</span>' : ''}</p>${(council.scores ?? []).map((s) => judgeCard(hill, s)).join('')}</div>${roundsTable(hill, state.council.log)}` : '<p class="muted">The judges run once the tests hit the target.</p>';
  const u = state.usage, cap = hill.stop?.budget_usd;
  return page(`${hill.name} climb`, `
<h1>${esc(hill.name)}</h1><p class="muted">${esc(hill.goal)}</p>
<p><span class="pill ${cls}">${esc(STATUS_WORDS[st] ?? st)}</span> ${state.stop_reason ? `<span class="muted">${esc(state.stop_reason)}</span>` : ''}</p>
<div class="tiles">
<div class="tile"><span>Best score</span><b>${pct(b.optimise)}${hill.metric?.unit === '%' ? '%' : ''}</b><span>target ${hill.metric?.target}</span></div>
<div class="tile"><span>Started at</span><b>${pct(base.optimise)}</b><span>baseline</span></div>
<div class="tile"><span>Hidden check</span><b>${pct(b.holdout)}</b><span>${gap == null ? 'not measured' : `gap ${pct(gap)} (max ${hill.metric?.holdout_gap_max})`}</span></div>
<div class="tile"><span>Attempts</span><b>${state.attempts ?? 0}</b><span>${state.kept ?? 0} kept · streak ${state.streak ?? 0}</span></div>
${sec ? `<div class="tile"><span>${esc(sec.name ?? 'secondary')}</span><b>${b.secondary ?? '–'}</b><span>from ${base.secondary ?? '–'}${sec.target != null ? ` · target ${sec.target}` : ''}</span></div>` : ''}
<div class="tile"><span>Spent</span><b>${money(u)}</b><span>${cap != null ? `budget $${cap}` : 'no budget set'}${u?.unknown_runs ? ` · ${u.unknown_runs} runs of unknown cost` : ''}</span></div>
</div>
<h2>Score over time</h2><div class="card">${chart(hill, state)}</div>
${gallery(hill, state, budget)}
<h2>Judges</h2>${councilHtml}
<h2>Every attempt</h2><div class="card scroll"><table><thead><tr><th>#</th><th>Result</th><th>Score</th><th>Hidden</th>${sec ? `<th>${esc(sec.name ?? 'secondary')}</th>` : ''}<th>What it tried</th></tr></thead><tbody>${rows}</tbody></table></div>
<p class="muted">Metric: ${esc(hill.metric?.name)}. Updated ${esc(new Date().toISOString().replace('T', ' ').slice(0, 16))} UTC. Answer key locked: ${esc((state.lock_digest ?? '').slice(0, 12))}.</p>`);
}

export function renderCheckpoint(hill, state, { exemplars, cases, holdoutCount, calibration }) {
  const base = state.baseline ?? {};
  const pick = [...cases.filter((c) => (c.origin ?? 'real') === 'real').slice(0, 5), ...cases.filter((c) => c.origin === 'synthetic').slice(0, 5)].slice(0, 10);
  const fill = pick.length < 10 ? cases.filter((c) => !pick.includes(c)).slice(0, 10 - pick.length) : [];
  const checks = (c) => (c.checks ?? []).map((k) => `<li>${esc(k.name ?? k.type)}${k.question ? `: ${esc(k.question)}` : k.values ? `: ${esc(k.values.join(', '))}` : k.value != null ? `: ${esc(clip(k.value, 80))}` : ''}</li>`).join('');
  const caseCard = (c) => `<div class="card"><p><b>${esc(c.id)}</b> <span class="muted">${esc(c.origin ?? 'real')}${c.must_pass ? ' · must pass' : ''}${c.negative ? ' · must NOT do' : ''}${c.source ? ` · from ${esc(clip(c.source, 80))}` : ''}</span></p><pre>${esc(clip(c.input, 600))}</pre><ul>${checks(c)}</ul></div>`;
  const exCard = (e) => `<div class="card"><p><b class="${e.label === 'pass' ? 'ok' : 'no'}">${e.label === 'pass' ? 'GOOD' : 'BAD'}</b> <b>${esc(e.id)}</b> <span class="muted">${esc(clip(e.source ?? '', 100))}</span></p><pre>${esc(clip(e.input, 400))}</pre><pre>${esc(clip(e.output, 500))}</pre>${e.why ? `<p class="muted">${esc(e.why)}</p>` : ''}</div>`;
  const s = hill.stop ?? {};
  return page(`${hill.name} answer key`, `
<h1>Before the climb: ${esc(hill.name)}</h1><p class="muted">One page to approve. Say "go" and it runs on its own until it finishes.</p>
<div class="tiles">
<div class="tile"><span>Goal</span><p>${esc(hill.goal)}</p></div>
<div class="tile"><span>Score today</span><b>${pct(base.optimise)}</b><span>${esc(hill.metric?.name)}</span></div>
<div class="tile"><span>Target</span><b>${hill.metric?.target}</b><span>hidden check within ${hill.metric?.holdout_gap_max}</span></div>
<div class="tile"><span>Tests</span><b>${cases.length} + ${holdoutCount}</b><span>visible + hidden</span></div>
</div>
<h2>How "done" is decided</h2><div class="card"><p>1. The visible tests reach ${hill.metric?.target}, the ${holdoutCount} hidden tests are no more than ${hill.metric?.holdout_gap_max} points lower, and every must-pass test passes.${hill.metric?.secondary?.target != null ? ` ${esc(hill.metric.secondary.name)} reaches ${hill.metric.secondary.target}.` : ''}</p>
${checkpointCouncil(hill, state)}
<p>It stops early if: ${s.deadline ? `the deadline ${esc(s.deadline)} passes, ` : ''}${s.budget_usd != null ? `it has spent $${s.budget_usd}, ` : ''}${s.plateau} tries in a row bring no gain after switching approach ${s.min_switches} times${s.max_attempts ? `, or after ${s.max_attempts} attempts` : ''}. It reports "stuck at X" honestly.</p>
<p>It may change only: <code>${esc((hill.climbable ?? []).join(', '))}</code> on branch <code>${esc(hill.branch)}</code>. ${esc(hill.authority)}</p></div>
${checkpointVisuals(hill, state)}
${calibration ? `<h2>Does the answer key tell good from bad?</h2><div class="card"><p>On ${calibration.exemplars} real labelled examples it passes <b>${calibration.tpr == null ? '–' : Math.round(calibration.tpr * 100)}%</b> of the good ones and fails <b>${calibration.tnr == null ? '–' : Math.round(calibration.tnr * 100)}%</b> of the bad ones.</p></div>` : ''}
<h2>The real examples it learned from</h2>${exemplars.slice(0, 10).map(exCard).join('')}
<h2>10 of the tests</h2>${[...pick, ...fill].map(caseCard).join('')}
<p class="muted">Answer key locked: ${esc((state.lock_digest ?? '').slice(0, 12))}. Climber: ${esc(hill.climber?.model ?? hill.climber?.cli)} in a fresh session per attempt.</p>`);
}

// Step 2 of "how done is decided", in plain words.
function checkpointCouncil(hill, state) {
  const judges = hill.council ?? [];
  if (!judges.length) return '<p>2. No outside judges: the tests alone decide.</p>';
  const names = judges.map((c) => esc(c.name ?? c.model ?? c.cli)).join(', then ');
  const rubric = rubricOf(hill), refs = listReferences(hill);
  const what = hill.council_render
    ? `look at the rendered work${refs.length ? ` next to ${refs.length} reference${refs.length === 1 ? '' : 's'} (${refs.map((r) => esc(r.id)).join(', ')}) and the starting version, all shuffled under letters so they cannot tell which is which,` : ' and the starting version, shuffled under letters,'}`
    : 'read the change';
  return `<p>2. Then the judges (${names}) ${what} and score ${rubric.length > 1 ? `each of ${rubric.length} categories` : 'it'} from 1 to 10 in half points. They are never told the target or the bar. It keeps fixing until every judge gives ${hill.council_bar} or more in every category${refs.length ? ', scores it above every reference' : ''} and says it would ship. A judge whose score rises is asked a second time before the change counts.</p>
${rubric.length > 1 ? `<ul>${rubric.map((c) => `<li><b>${esc(c.name)}</b>: ${esc(c.ask)}</li>`).join('')}</ul>` : ''}${hill.review_focus ? `<p class="muted">What the judges are told you care about: ${esc(hill.review_focus)}</p>` : ''}`;
}
// The starting render and the references, for render hills.
function checkpointVisuals(hill, state) {
  if (!hill.council_render) return '';
  const budget = { used: 0 };
  const parts = [shots(renderPath(hill, state.baseline?.render), 'Today', budget)];
  for (const r of listReferences(hill)) parts.push(shots(r.dir, `Reference: ${r.id}`, budget, 1));
  const html = parts.filter(Boolean).join('');
  return `<h2>What the judges will look at</h2><div class="card">${html ? `<div class="shots">${html}</div>` : '<p class="muted">No render yet.</p>'}${listReferences(hill).length ? '' : '<p class="warn">No references: the judges score the work alone. Add 1-3 of the best products you know to compare against.</p>'}</div>`;
}
