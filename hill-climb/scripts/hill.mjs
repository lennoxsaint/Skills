#!/usr/bin/env node
// hill.mjs - build, check, freeze and inspect a hill (one climb's answer key and state).
//   init <hill> --name <slug> (--repo <git repo> [--base <ref>] | --scratch) [--worktree <path>]
//   split <hill> [--holdout 0.3] [--seed <s>] [--reset]  move cases/pool/*.json into cases/optimise + cases/holdout
//   validate <hill> [--run]                      spec + answer-key checks; --run also scores the exemplars
//   discriminate <hill>                          does the answer key pass every good exemplar and fail every bad one?
//   judge-test <hill> --question "..."           try one yes/no judge question on every exemplar before adding it
//   freeze <hill> [--reason <why>]               lock the answer key (hashes), make the hidden cases read-only
//   score <hill> [--split optimise|holdout|both] score the work folder as it is now
//   try <hill> --case <id> [--split pool|optimise|holdout] [--allow-hidden] | --input '<json>'  one case through the real producer
//   brief <hill>                                 measure the baseline (clean, committed work folder) and write the checkpoint
//   approve <hill> --by <name>                   record the owner's "go"
//   council-test <hill> [--sha <ref>]            ask the full council once about a commit and print the verdicts (records nothing)
//   raise <hill> --bar <n> [--focus "..."]       after done: save the result as hill/<name>-level-<bar>, lift the bar, re-freeze
//   status <hill> | verify <hill> | board <hill>
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  HOME, now, sha256, readJSON, writeJSON, loadHill, P, listCases, listExemplars, loadState, saveState, appendLedger,
  verifyLedger, frozenFiles, digestOf, checkLock, git, gitx, gitOk, clip, checkSettings, sandboxTool, worktreeTree, treeOf,
  currentBranch, takeRunLock, filterAttrProblems, stagedOnlyProblems,
} from './lib.mjs';
import { scoreSplit, discriminate, runCheck, scoringSettingsProblems, tryCase, takeCheckUsage } from './score.mjs';
import { councilProblems, renderTree, cachedRender, listReferences, runCouncil, describeRound, addUsage, addCheckUsage, usageText } from './council.mjs';
import { renderBoard, renderCheckpoint } from './board.mjs';

const argv = process.argv.slice(2);
const flag = (name, d = null) => { const i = argv.indexOf(`--${name}`); return i >= 0 ? (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true) : d; };
const out = (v) => process.stdout.write(`${JSON.stringify(v, null, 2)}\n`);
const die = (msg, extra = {}) => { out({ status: 'error', error: msg, ...extra }); process.exit(1); };
// Settings that would change what a score means (lib's checkSettings plus score.mjs's scoringSettingsProblems).
const settingsProblems = (hill) => [...new Set([...checkSettings(hill), ...scoringSettingsProblems(hill), ...councilProblems(hill)])];
function refuseUnsound(hill) { const bad = settingsProblems(hill); if (bad.length) die('unsound scoring settings: fix hill.json or the cases first', { problems: bad }); }
// freeze, brief and approve change what the runner owns, so they hold its run lock for their whole run (released on
// every exit). Busy: prints {status: "busy"} and exits 3.
function holdLock(dir, cmd) {
  const d = path.resolve(dir);
  if (!fs.existsSync(path.join(d, 'hill.json'))) die(`no hill.json in ${d}`);
  const l = takeRunLock({ _dir: d }, { label: `hill.mjs ${cmd}` });
  if (!l.ok) { out({ status: 'busy', reason: l.reason }); process.exit(3); }
  process.on('exit', l.release);
  return l.release;
}
// Real paths (symlinks resolved) even for folders that do not exist yet, so containment checks cannot be fooled.
function realish(p) {
  let head = path.resolve(p); const rest = [];
  while (!fs.existsSync(head) && path.dirname(head) !== head) { rest.unshift(path.basename(head)); head = path.dirname(head); }
  return path.join(fs.realpathSync(head), ...rest);
}
const isInside = (child, parent) => { const r = path.relative(realish(parent), realish(child)); return r === '' || (!r.startsWith('..') && !path.isAbsolute(r)); };
function nearestExisting(p) { let d = path.resolve(p); while (!fs.existsSync(d)) d = path.dirname(d); return d; }

function init(dir) {
  const name = flag('name') || die('--name <slug> is required');
  if (!/^[a-z0-9][a-z0-9-]*$/.test(name)) die('name must be lowercase letters, digits and dashes');
  const hillDir = path.resolve(dir);
  if (fs.existsSync(path.join(hillDir, 'hill.json'))) die(`${hillDir} already has a hill.json`);
  const workdir = path.resolve(flag('worktree') || path.join(HOME, '.hill-climb', 'worktrees', name));
  const branch = `hill/${name}`;
  // Every refusal happens before anything is created.
  if (isInside(hillDir, workdir) || isInside(workdir, hillDir)) die('the hill folder and the work folder must not contain each other (the answer key has to stay out of the climber\'s folder)');
  if (flag('scratch')) {
    if (fs.existsSync(workdir) && fs.readdirSync(workdir).length) die(`--scratch needs a new or empty folder: ${workdir} has files. Use --repo for an existing git repo.`);
    const anc = nearestExisting(fs.existsSync(workdir) ? workdir : path.dirname(workdir));
    if (gitOk(anc, 'rev-parse', '--git-dir')) die(`--scratch folder ${workdir} would sit inside the git repo at ${git(anc, 'rev-parse', '--show-toplevel')}: pick a folder outside any repo, or use --repo.`);
  }
  let baseRef;
  if (flag('repo')) {
    const repo = path.resolve(flag('repo'));
    const base = flag('base') || 'HEAD';
    baseRef = git(repo, 'rev-parse', base);
    if (fs.existsSync(workdir)) die(`worktree path already exists: ${workdir}`);
    git(repo, 'worktree', 'add', '-b', branch, workdir, baseRef);
  } else if (flag('scratch')) {
    fs.mkdirSync(workdir, { recursive: true });
    git(workdir, 'init', '-q', '-b', branch);
    fs.writeFileSync(path.join(workdir, 'README.md'), `# ${name}\nScratch work folder for hill ${name}. Put the climbable files here.\n`);
    git(workdir, 'add', '-A'); git(workdir, '-c', 'user.name=hill-climb', '-c', 'user.email=hill-climb@localhost', 'commit', '-qm', 'hill: scratch start');
    baseRef = git(workdir, 'rev-parse', 'HEAD');
  } else die('pass --repo <git repo> (a hill/<name> worktree is created) or --scratch (a fresh git folder)');
  for (const sub of ['cases/pool', 'cases/optimise', 'cases/holdout', 'exemplars', 'scorer', 'runs']) fs.mkdirSync(path.join(hillDir, sub), { recursive: true });
  const spec = {
    version: 1, name, goal: 'TODO: the goal in one plain sentence',
    workdir, branch, base_ref: baseRef,
    climbable: ['TODO: paths or globs the climber may edit'],
    produce: { command: 'node "$HILL_SCORER_DIR/produce.mjs"', timeout_sec: 300, concurrency: 4, model: null, pass_env: [] },
    judge: { cli: 'claude', model: 'claude-haiku-5-5' },
    metric: { name: 'TODO: what the % measures', unit: '%', target: 90, holdout_gap_max: 5 },
    climber: { cli: 'claude', model: 'claude-opus-5-5', effort: 'high', timeout_sec: 1800 },
    council: [{ cli: 'codex', model: 'gpt-6.1-sol', effort: 'high' }, { cli: 'claude', model: 'claude-opus-5-5' }],
    council_bar: 9,
    stop: { deadline: null, plateau: 10, switch_every: 4, min_switches: 2, max_attempts: null, min_attempt_sec: 300 },
    repeats: 1, pass_rule: 'all', accept_margin: 0, confirm_gains: false, holdout_every: 3, checkpoint: true, sandbox: 'auto',
    authority: 'Edit only the climbable files on this hill branch. Never publish, send, deploy, push, merge or write production data.',
  };
  writeJSON(path.join(hillDir, 'hill.json'), spec);
  fs.writeFileSync(path.join(hillDir, 'notes.md'), `# ${name} notes\nLearnings the climber should know. The runner shows this file to every attempt.\n`);
  out({ status: 'ok', hill: hillDir, workdir, branch, base_ref: baseRef, next: 'fill hill.json, add exemplars/ and cases/pool/, write scorer/produce.mjs, then split, validate --run, freeze, brief' });
}

function split(dir) {
  const hill = loadHill(dir);
  const frac = Number(flag('holdout', 0.3));
  const seed = String(flag('seed', hill.name));
  if (!(frac >= 0 && frac < 1)) die('--holdout must be a fraction from 0 to under 1');
  for (const sub of ['pool', 'optimise', 'holdout']) fs.mkdirSync(P(hill, 'cases', sub), { recursive: true });
  const placed = [...listCases(hill, 'optimise'), ...listCases(hill, 'holdout')];
  if (placed.length) {
    if (!flag('reset')) die(`cases are already split (${placed.length} in optimise/holdout). Add new cases to cases/pool and run split --reset to re-split everything.`);
    for (const c of placed) { fs.chmodSync(c._file, 0o644); fs.renameSync(c._file, P(hill, 'cases', 'pool', path.basename(c._file))); }
  }
  const pool = listCases(hill, 'pool');
  if (!pool.length) die('cases/pool is empty');
  const groups = {};
  for (const c of pool) {
    const key = c.must_pass ? 'must' : `${c.origin ?? 'real'}|${c.negative ? 'neg' : 'pos'}`;
    (groups[key] ??= []).push(c);
  }
  const moved = { optimise: 0, holdout: 0 };
  for (const [key, cs] of Object.entries(groups)) {
    cs.sort((a, b) => sha256(seed + a.id).localeCompare(sha256(seed + b.id)));
    const nHold = key === 'must' ? 0 : Math.round(cs.length * frac);
    cs.forEach((c, i) => {
      const to = i < nHold ? 'holdout' : 'optimise';
      fs.renameSync(c._file, P(hill, 'cases', to, path.basename(c._file)));
      moved[to]++;
    });
  }
  out({ status: 'ok', ...moved, note: 'must-pass cases always stay in optimise; other groups are split by origin and negative/positive' });
}

function validateSpec(hill) {
  const problems = settingsProblems(hill), warnings = [];
  const todo = (v) => v == null || (typeof v === 'string' && (/^TODO/.test(v) || !v.trim()));
  if (todo(hill.goal)) problems.push('goal is empty');
  if (hill.sandbox !== 'off' && !sandboxTool()) problems.push('no sandbox tool on this machine (sandbox-exec or bubblewrap): install one, or set "sandbox": "off" to run unprotected');
  if (hill.sandbox === 'off') warnings.push('sandbox is off: producers, checks and climbers can read the hidden cases and write anywhere');
  if (!hill.workdir || !fs.existsSync(hill.workdir)) problems.push(`work folder missing: ${hill.workdir}`);
  else {
    if (!gitOk(hill.workdir, 'rev-parse', '--git-dir')) problems.push('work folder is not a git repo');
    else {
      const br = gitOk(hill.workdir, 'symbolic-ref', '-q', 'HEAD') ? git(hill.workdir, 'symbolic-ref', '--short', 'HEAD') : '(detached)';
      if (br !== hill.branch) problems.push(`work folder is on ${br}, hill expects ${hill.branch}`);
      if (!String(hill.branch).startsWith('hill/')) problems.push('branch must start with hill/ (the runner only moves its own hill branches)');
      const dirty = gitx({ cwd: hill.workdir }, 'status', '--porcelain', '--untracked-files=normal');
      if (dirty.trim()) warnings.push(`work folder has uncommitted changes: commit them before brief (the baseline needs a clean folder): ${clip(dirty.trim().split('\n').slice(0, 5).join('; '), 300)}`);
    }
    if (isInside(hill._dir, hill.workdir) || isInside(hill.workdir, hill._dir)) problems.push('hill folder and work folder must not contain each other');
  }
  if (!Array.isArray(hill.climbable) || !hill.climbable.length || hill.climbable.some(todo)) problems.push('climbable is empty');
  if (hill.climbable?.some((g) => g === '**' || g === '*' || g === '**/*')) warnings.push('climbable allows every file: scope it to the files that should change');
  if (typeof hill.metric?.target !== 'number') problems.push('metric.target must be a number');
  if (todo(hill.metric?.name)) problems.push('metric.name is empty');
  if (!hill.climber?.cli) problems.push('climber.cli missing');
  const council = hill.council ?? [];
  if (!council.length) warnings.push('no council: stage 2 (outside judges >= bar) will be skipped');
  else if (new Set(council.map((c) => c.cli === 'cmd' ? 'cmd' : c.cli)).size < 2) warnings.push('council judges all come from one family: use two (e.g. codex + claude)');
  if (hill.produce?.model && hill.judge?.model === hill.produce.model) warnings.push(`judge checks use ${hill.judge.model}, the same model as the producer (produce.model): a grader should not be the model under test`);
  return { problems, warnings };
}

function validateCases(hill) {
  const problems = [], warnings = [];
  const opt = listCases(hill, 'optimise'), hold = listCases(hill, 'holdout'), ex = listExemplars(hill), poolLeft = listCases(hill, 'pool');
  if (poolLeft.length) warnings.push(`${poolLeft.length} cases still in cases/pool (run split)`);
  const minOpt = hill.min_cases?.optimise ?? 20, minHold = hill.min_cases?.holdout ?? 8;
  if (opt.length < minOpt) problems.push(`only ${opt.length} optimise cases (need ${minOpt}+)`);
  if (hold.length < minHold) problems.push(`only ${hold.length} hidden cases (need ${minHold}+)`);
  const tot = opt.length + hold.length;
  if (tot && (hold.length / tot < 0.15 || hold.length / tot > 0.45)) warnings.push(`hidden share is ${Math.round((100 * hold.length) / tot)}% (aim for 25-35%)`);
  const ids = new Map();
  for (const c of [...opt, ...hold]) {
    if (typeof c.id !== 'string' || !c.id) problems.push(`case without a string id: ${c._file}`);
    if (ids.has(c.id)) problems.push(`duplicate case id ${c.id}`);
    ids.set(c.id, c._file);
    if (c.input === undefined) problems.push(`case ${c.id} has no input`);
    if (!c.checks?.length) problems.push(`case ${c.id} has no checks`);
  }
  const holdMust = hold.filter((c) => c.must_pass);
  if (holdMust.length) problems.push(`must_pass cases belong in optimise, not the hidden set: ${holdMust.map((c) => c.id).join(', ')} (run split --reset)`);
  if (!opt.some((c) => c.must_pass)) warnings.push('no must_pass cases: add the few things that must never break');
  if (![...opt, ...hold].some((c) => c.negative)) warnings.push('no negative cases (things the output must NOT do): one-sided keys get gamed');
  const real = [...opt, ...hold].filter((c) => (c.origin ?? 'real') === 'real').length;
  if (real < 3) problems.push(`only ${real} cases come from real data (origin: real): the key must be anchored in real examples`);
  if (!hold.some((c) => (c.origin ?? 'real') === 'real')) warnings.push('no real cases in the hidden set: the hidden check should include real data');
  if (ex.length < 3) problems.push(`only ${ex.length} exemplars (need 3+ real labelled outputs)`);
  if (!ex.some((e) => e.label === 'pass') || !ex.some((e) => e.label === 'fail')) problems.push('exemplars need at least one good (label: pass) and one bad (label: fail)');
  for (const e of ex) {
    if (e.output === undefined || !['pass', 'fail'].includes(e.label)) problems.push(`exemplar ${e.id ?? e._file} needs output and label pass|fail`);
    if (!e.checks?.length) problems.push(`exemplar ${e.id ?? e._file} has no checks: copy the checks its case would carry, so the key can be tested on it`);
  }
  // Answer key must not leak into the climbable files' prompt: holdout inputs must not appear in optimise.
  const optInputs = new Set(opt.map((c) => JSON.stringify(c.input)));
  const dup = hold.filter((c) => optInputs.has(JSON.stringify(c.input)));
  if (dup.length) problems.push(`hidden cases duplicate optimise inputs: ${dup.map((c) => c.id).slice(0, 5).join(', ')}`);
  return { problems, warnings, counts: { optimise: opt.length, holdout: hold.length, exemplars: ex.length, real } };
}

async function validate(dir, { runDisc } = {}) {
  const hill = loadHill(dir);
  const a = validateSpec(hill), b = validateCases(hill);
  const problems = [...a.problems, ...b.problems], warnings = [...a.warnings, ...b.warnings];
  let disc = null;
  if (runDisc && !problems.some((p) => /exemplar/.test(p))) {
    disc = await discriminate(hill);
    writeJSON(P(hill, 'calibration.json'), disc);
    const min = hill.calibration_min ?? 0.8;
    if (disc.tpr == null || disc.tnr == null) problems.push('the key could not be tested: needs at least one good and one bad exemplar with checks');
    if (disc.judge_errors) problems.push(`${disc.judge_errors} judge error(s) while checking exemplars: fix the judge spec or login, then re-run`);
    if (disc.tpr != null && disc.tpr < min) problems.push(`answer key fails ${Math.round((1 - disc.tpr) * 100)}% of GOOD exemplars (TPR ${disc.tpr.toFixed(2)} < ${min}): ${disc.misclassified.filter((m) => m.label === 'pass').map((m) => m.id).join(', ')}`);
    if (disc.tnr != null && disc.tnr < min) problems.push(`answer key passes ${Math.round((1 - disc.tnr) * 100)}% of BAD exemplars (TNR ${disc.tnr.toFixed(2)} < ${min}): ${disc.misclassified.filter((m) => m.label === 'fail').map((m) => m.id).join(', ')}`);
  }
  return { ok: problems.length === 0, problems, warnings, counts: b.counts, discrimination: disc };
}

async function freeze(dir) {
  const release = holdLock(dir, 'freeze');
  try { out(await freezeLocked(dir)); } finally { release(); }
}
// onFail runs before a refusal exits (raise uses it to put the old hill.json back).
async function freezeLocked(dir, { reason = typeof flag('reason') === 'string' ? flag('reason') : null, onFail = null } = {}) {
  const fail = (msg, extra) => { onFail?.(); die(msg, extra); };
  const hill = loadHill(dir);
  const state = loadState(hill);
  if (state.in_progress) fail(`attempt #${state.in_progress.n} was interrupted: run climb.mjs ${hill._dir} --recover-only first`);
  const v = await validate(dir, { runDisc: true });
  if (!v.ok) fail('validation failed: fix these before freezing', { problems: v.problems, warnings: v.warnings });
  for (const c of listCases(hill, 'holdout')) fs.chmodSync(c._file, 0o444);
  const files = frozenFiles(hill);
  const digest = digestOf(files);
  writeJSON(P(hill, 'lock.json'), { digest, files, at: now() });
  const refreeze = !!state.lock_digest;
  // A new key starts a new generation: the old climb's numbers are archived, never compared with the new key's.
  if (refreeze && (state.baseline || state.attempts > (state.attempts_base ?? 0))) {
    (state.generations ??= []).push({ digest: state.lock_digest, attempts_base: state.attempts_base ?? 0, attempts: state.attempts ?? 0, kept: state.kept ?? 0, best: state.best ?? null, baseline: state.baseline ?? null, council: state.council?.last ?? null, council_bar: state.council_bar ?? null, usage: state.usage ?? null, stop_reason: state.stop_reason ?? null, at: now() });
  }
  Object.assign(state, { status: 'frozen', lock_digest: digest, approved_by: null, approved_at: null, approved_for: null, baseline: null, best: null, head: null, kept: 0, streak: 0, switches: 0, council: null, usage: null, council_bar: hill.council?.length ? hill.council_bar : null, overfit: false, history: [], consecutive_errors: 0, stop_reason: null, attempts_base: state.attempts ?? 0 });
  saveState(hill, state);
  appendLedger(hill, { kind: refreeze ? 'refreeze' : 'freeze', digest, reason, counts: v.counts, tpr: v.discrimination?.tpr, tnr: v.discrimination?.tnr });
  return { status: 'ok', digest, counts: v.counts, discrimination: { tpr: v.discrimination?.tpr, tnr: v.discrimination?.tnr }, warnings: v.warnings, note: refreeze ? 'answer key changed: baseline and approval reset' : 'frozen' };
}

export function summarize(r) { return { split: r.split, score: r.score, passed: r.passed, total: r.total, must_pass_failures: r.must_pass_failures, secondary: r.secondary }; }

// The baseline is the committed work folder: uncommitted edits would be scored but never kept, so they are refused.
async function measureBaseline(hill, state) {
  const W = hill.workdir;
  if (currentBranch(W) !== hill.branch) throw new Error(`work folder is on ${currentBranch(W) ?? 'a detached HEAD'}, not ${hill.branch}`);
  const sha = git(W, 'rev-parse', 'HEAD');
  const idx = P(hill, 'cache', `index-baseline-${process.pid}`);
  let tree;
  try { tree = worktreeTree(W, sha, idx); } finally { fs.rmSync(idx, { force: true }); }
  if (tree !== treeOf(W, sha)) throw new Error(`the work folder has uncommitted changes: commit the starting files on ${hill.branch} first, then run brief again`);
  const dirRuns = P(hill, 'runs', 'baseline');
  const [o, h] = [await scoreSplit(hill, 'optimise', { save: path.join(dirRuns, 'optimise.json') }), await scoreSplit(hill, 'holdout', { save: path.join(dirRuns, 'holdout.json') })];
  addCheckUsage(state, takeCheckUsage());
  if (o.judge_errors || h.judge_errors) throw new Error(`${o.judge_errors + h.judge_errors} judge error(s) while measuring the baseline: fix the judge (try hill.mjs judge-test), then run brief again`);
  // The starting render: the judges' hidden control in every council round, and the "before" picture on the board.
  let render = null;
  if (hill.council_render) {
    const r = await renderTree(hill, tree);
    if (!r.ok) throw new Error(`the render command failed on the starting version: ${r.error}. Fix council_render (or the work folder), then run brief again`);
    render = path.basename(r.dir);
  }
  state.baseline = { sha, tree, ...(render ? { render } : {}), optimise: o.score, holdout: h.score, secondary: o.secondary, must_pass_failures: o.must_pass_failures, holdout_must_pass_failures: h.must_pass_failures, at: now() };
  state.best = { sha, attempt: 0, optimise: o.score, holdout: h.score, holdout_sha: sha, holdout_must_pass_failures: h.must_pass_failures, secondary: o.secondary, must_pass_failures: o.must_pass_failures };
  state.head = sha;
  state.history = [{ n: 0, decision: 'baseline', score: o.score, holdout: h.score, secondary: o.secondary }];
  saveState(hill, state);
  appendLedger(hill, { kind: 'baseline', sha, optimise: summarize(o), holdout: summarize(h) });
  return state;
}
export { measureBaseline };

async function brief(dir) {
  const release = holdLock(dir, 'brief');
  try { await briefLocked(dir); } finally { release(); }
}
async function briefLocked(dir) {
  const hill = loadHill(dir);
  let state = loadState(hill);
  const lock = checkLock(hill, state.lock_digest);
  if (!lock.ok) die(`not frozen or changed: ${lock.reason}`);
  if (state.in_progress) die(`attempt #${state.in_progress.n} was interrupted: run climb.mjs ${hill._dir} --recover-only first`);
  refuseUnsound(hill);
  // The same repo checks the runner makes before it starts, so the owner never approves a climb that cannot run.
  const W = hill.workdir, filters = filterAttrProblems(W), staged = stagedOnlyProblems(W);
  const repo = [
    filters.length && `this repo transforms files through git (${filters.slice(0, 4).join('; ')}). The runner saves and restores raw bytes, so it does not support filters, LFS, ident, encodings, CRLF conversion or sparse checkout. Climb in a repo or copy without them.`,
    staged.length && `staged changes in ${W} exist only in git's index (${staged.slice(0, 6).join(', ')}). The runner resets the index, which would lose them: commit, unstage or stash them, then run brief again.`,
  ].filter(Boolean);
  if (repo.length) die(repo.join(' '), { problems: [...filters, ...staged] });
  const head = git(W, 'rev-parse', 'HEAD');
  if (state.baseline && state.baseline.sha !== head) {
    if ((state.attempts ?? 0) > (state.attempts_base ?? 0)) die(`the work folder moved since the climb started (${state.baseline.sha.slice(0, 10)} -> ${head.slice(0, 10)}): re-freeze to start a new climb from here`);
    state.baseline = null; state.approved_for = null;
  }
  if (!state.baseline) state = await measureBaseline(hill, state);
  const html = renderCheckpoint(hill, state, { exemplars: listExemplars(hill), cases: listCases(hill, 'optimise'), holdoutCount: listCases(hill, 'holdout').length, calibration: readJSON(P(hill, 'calibration.json'), null) });
  fs.writeFileSync(P(hill, 'checkpoint.html'), html);
  const warnings = [];
  if (hill.council?.length && hill.council_render && !listReferences(hill).length) warnings.push('council_render is set but references/ is empty: the judges score the work alone, with nothing to compare it with. Add 1-3 reference products (the best you know) and re-freeze, or accept absolute scores.');
  if (hill.council?.length && !hill.council_rubric?.length) warnings.push('no council_rubric: each judge gives one overall score. A rubric of 3-6 categories drawn from the owner\'s own critiques makes the judges more consistent.');
  out({ status: 'ok', checkpoint: P(hill, 'checkpoint.html'), baseline: state.baseline, target: hill.metric.target, ...(warnings.length ? { warnings } : {}), next: 'show checkpoint.html to the owner; on their "go" run: hill.mjs approve <hill> --by <name>' });
}

function approve(dir) {
  const release = holdLock(dir, 'approve');
  try { approveLocked(dir); } finally { release(); }
}
function approveLocked(dir) {
  const hill = loadHill(dir);
  const state = loadState(hill);
  const by = flag('by');
  if (!by || by === true) die('--by <name> is required (the person who said go)');
  const lock = checkLock(hill, state.lock_digest);
  if (!lock.ok) die(`cannot approve: ${lock.reason}`);
  if (!state.baseline) die('measure the baseline first (hill.mjs brief)');
  if (git(hill.workdir, 'rev-parse', 'HEAD') !== state.baseline.sha) die('the work folder moved since the brief: run brief again and show the new checkpoint');
  // The approval covers this exact answer key and starting commit; a re-freeze or a new baseline needs a new "go".
  Object.assign(state, { approved_by: by, approved_at: now(), approved_for: `${state.lock_digest}:${state.baseline.sha}`, status: state.status === 'frozen' ? 'approved' : state.status });
  saveState(hill, state);
  appendLedger(hill, { kind: 'approve', by, digest: state.lock_digest, baseline: state.baseline.sha, note: typeof flag('note') === 'string' ? flag('note') : null });
  out({ status: 'ok', approved_by: by, next: `node ${path.join(path.dirname(fileURLToPath(import.meta.url)), 'climb.mjs')} ${hill._dir}` });
}

function status(dir) {
  const hill = loadHill(dir);
  const s = loadState(hill);
  out({
    name: hill.name, status: s.status, stage: s.stage, approved_by: s.approved_by ?? null,
    target: hill.metric.target, baseline: s.baseline ? { optimise: s.baseline.optimise, holdout: s.baseline.holdout, secondary: s.baseline.secondary } : null,
    best: s.best ? { attempt: s.best.attempt, optimise: s.best.optimise, holdout: s.best.holdout, secondary: s.best.secondary, sha: s.best.sha } : null,
    attempts: s.attempts, kept: s.kept, streak: s.streak, switches: s.switches, council: s.council?.last ?? null, council_bar: hill.council?.length ? hill.council_bar : null, stop_reason: s.stop_reason ?? null,
    usage: s.usage ? { ...s.usage, text: usageText(s.usage) } : null, budget_usd: hill.stop.budget_usd ?? null,
    lock: checkLock(hill, s.lock_digest).ok, ledger: verifyLedger(hill), board: fs.existsSync(P(hill, 'board.html')) ? P(hill, 'board.html') : null,
    in_progress: s.in_progress ?? null, sandbox: hill.sandbox === 'off' ? 'off' : sandboxTool()?.kind ?? 'missing',
    generations: (s.generations ?? []).map((g) => ({ digest: g.digest?.slice(0, 12), attempts: g.attempts - g.attempts_base, kept: g.kept, best: g.best?.optimise ?? null, stop_reason: g.stop_reason })),
  });
}

// Tries one yes/no judge question on every exemplar, so a question can be tuned before it goes into the key.
// YES must mean good: a good exemplar should get YES and a bad one NO.
async function judgeTest(dir) {
  const hill = loadHill(dir);
  const question = flag('question');
  if (!question || question === true) die('--question "..." is required (phrase it so YES means the output is good)');
  const check = { type: 'judge', question, ...(flag('model') ? { judge: { ...(hill.judge ?? { cli: 'claude' }), model: flag('model') } } : {}) };
  const rows = [];
  for (const e of listExemplars(hill)) {
    const r = await runCheck(hill, check, e.output, e);
    rows.push({ id: e.id, label: e.label, judge: r.error ? 'error' : r.pass ? 'YES' : 'NO', agree: !r.error && (r.pass ? 'pass' : 'fail') === e.label, detail: r.detail });
  }
  const good = rows.filter((r) => r.label === 'pass'), bad = rows.filter((r) => r.label === 'fail');
  out({ question, tpr: good.length ? good.filter((r) => r.agree).length / good.length : null, tnr: bad.length ? bad.filter((r) => r.agree).length / bad.length : null, errors: rows.filter((r) => r.judge === 'error').length, rows });
}

// Asks the full council once about one commit (default HEAD), with the render, the references and the starting render
// when they are set, and prints every verdict. It records nothing in state.json or the ledger, so the rubric, the
// references and the judge specs can be tuned before freezing. A render needs the clean work folder to hold that commit
// (or a cached render of it).
async function councilTest(dir) {
  const hill = loadHill(dir);
  const bad = [...checkSettings(hill), ...councilProblems(hill)];
  if (bad.length) die('fix hill.json first', { problems: bad });
  if (!hill.council?.length) die('this hill has no council (hill.json "council" is empty)');
  const W = hill.workdir, ref = typeof flag('sha') === 'string' ? flag('sha') : 'HEAD';
  if (!gitOk(W, 'rev-parse', '--verify', '-q', `${ref}^{commit}`)) die(`${ref} is not a commit in ${W}`);
  const sha = git(W, 'rev-parse', `${ref}^{commit}`), tree = treeOf(W, sha);
  if (hill.council_render && !cachedRender(hill, tree)) {
    const idx = P(hill, 'cache', `index-council-test-${process.pid}`);
    let now;
    try { now = worktreeTree(W, git(W, 'rev-parse', 'HEAD'), idx); } finally { fs.rmSync(idx, { force: true }); }
    if (now !== tree) die(`the render runs on the work folder, which does not hold ${sha.slice(0, 10)} as committed: check it out there with no uncommitted changes, then run again`);
  }
  const saved = loadState(hill);
  const scratch = JSON.parse(JSON.stringify(saved)); // drift anchors and usage land here, never in state.json
  scratch.usage = null;
  const lastOpt = readJSON(P(hill, 'runs', saved.best?.attempt ? String(saved.best.attempt) : 'baseline', 'optimise.json'), null);
  const ctx = { hill, state: scratch, DL: null, addUsage: (kind, name, r) => addUsage(scratch, kind, name, r) };
  const c = await runCouncil(ctx, { tag: `test-${Date.now()}`, treeish: sha, lastOpt, full: true });
  out({
    status: c.valid ? 'ok' : 'error', sha, valid: c.valid, pass: c.pass, bar: hill.council_bar, summary: describeRound(c),
    render: c.render ? P(hill, 'cache', 'renders', c.render) : null, render_error: c.render_error ?? null, items: c.items ?? null,
    control: !hill.council_render ? null
      : (c.items ?? []).some((i) => i.id === 'base') ? 'the starting render was shown as a hidden control'
      : scratch.baseline?.tree === tree ? 'this is the starting version itself: no separate control'
      : c.control_missing ? 'the starting render is missing from the cache (run brief again): no control in this round'
      : 'no starting render yet (run brief): no control in this round',
    verdicts: c.scores, usage: usageText(scratch.usage), usage_detail: scratch.usage,
    note: 'nothing was recorded: state.json and ledger.jsonl are unchanged (the judges\' logs are under runs/council-test-*)',
  });
  process.exit(c.valid ? 0 : 1);
}

// After done: keep the result as its own branch (hill/<name>-level-<bar>), lift council_bar (and optionally
// review_focus) and re-freeze. The cases stay as they are; the new generation starts from the done commit and needs
// brief and approve again. Taste is steered here, through the bar and the focus line the judges read, never through notes.md.
async function raise(dir) {
  const release = holdLock(dir, 'raise');
  try { await raiseLocked(dir); } finally { release(); }
}
async function raiseLocked(dir) {
  const hill = loadHill(dir);
  const state = loadState(hill);
  const bar = Number(flag('bar')), focus = flag('focus');
  if (!hill.council?.length) die('raise lifts the council bar, and this hill has no council');
  if (state.status !== 'done') die(`raise needs a finished climb (status done); this hill is ${state.status ?? 'not started'}`);
  if (!Number.isFinite(bar) || bar <= hill.council_bar || bar > 10 || !Number.isInteger(bar * 2)) die(`--bar must be above the current bar of ${hill.council_bar} and at most 10, in whole or half points (e.g. 9.5)`);
  if (focus === true) die('--focus needs a line of text: what the owner cares about most now');
  const W = hill.workdir;
  if (currentBranch(W) !== hill.branch || git(W, 'rev-parse', 'HEAD') !== state.best?.sha) die(`the work folder must be on ${hill.branch} at the done commit ${state.best?.sha?.slice(0, 10)}`);
  const level = `${hill.branch}-level-${hill.council_bar}`;
  const existing = gitOk(W, 'rev-parse', '--verify', '-q', `refs/heads/${level}`) ? git(W, 'rev-parse', `refs/heads/${level}`) : null;
  if (existing && existing !== state.best.sha) die(`branch ${level} already exists at ${existing.slice(0, 10)}, not the done commit: rename or remove it first`);
  const specFile = P(hill, 'hill.json'), before = fs.readFileSync(specFile);
  const raw = JSON.parse(before.toString('utf8'));
  raw.council_bar = bar;
  if (typeof focus === 'string') raw.review_focus = focus;
  fs.writeFileSync(specFile, `${JSON.stringify(raw, null, 2)}\n`);
  const f = await freezeLocked(dir, { reason: `raise: council_bar ${hill.council_bar} -> ${bar}${typeof focus === 'string' ? `, review_focus: ${clip(focus, 120)}` : ''}`, onFail: () => fs.writeFileSync(specFile, before) });
  if (!existing) gitx({ cwd: W }, 'branch', level, state.best.sha);
  appendLedger(hill, { kind: 'raise', from: hill.council_bar, to: bar, level_branch: level, sha: state.best.sha, focus: typeof focus === 'string' ? focus : null });
  out({ status: 'ok', council_bar: { from: hill.council_bar, to: bar }, level_branch: level, level_sha: state.best.sha, digest: f.digest, warnings: f.warnings, next: 'run brief (it measures the new baseline from the done commit), show checkpoint.html to the owner, then approve and climb again' });
}

// One case through the real producer or custom scorer, sandboxed, with each check's result. Hidden cases only with
// --allow-hidden (their output is then in front of you: never let it reach the climbable files).
async function tryOne(dir) {
  const hill = loadHill(dir);
  refuseUnsound(hill);
  const id = flag('case'), input = flag('input'), split = flag('split');
  let kase, where = null;
  if (typeof input === 'string') {
    let v; try { v = JSON.parse(input); } catch { v = input; }
    kase = { id: 'try', input: v, checks: [] };
  } else if (typeof id === 'string') {
    if (split != null && !['pool', 'optimise', 'holdout'].includes(split)) die('--split must be pool, optimise or holdout');
    if (split === 'holdout' && !flag('allow-hidden')) die('that is the hidden set: add --allow-hidden to run a hidden case (keep what you see out of the climbable files)');
    for (const s of split ? [split] : ['pool', 'optimise']) { kase = listCases(hill, s).find((c) => c.id === id); if (kase) { where = s; break; } }
    if (!kase) die(`no case ${id} in ${split ? `cases/${split}` : 'cases/pool or cases/optimise (a hidden case needs --split holdout --allow-hidden)'}`);
  } else die('pass --case <id> [--split pool|optimise|holdout] or --input \'<json>\'');
  const r = await tryCase(hill, kase);
  out({ status: 'ok', id: kase.id, split: where, output: r.output, ok: r.ok, error: r.error, pass: r.pass, checks: r.checks });
}

async function main() {
  const [cmd, dir] = argv;
  if (!cmd || !dir) { const lines = fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n'); process.stdout.write(lines.slice(1, lines.findIndex((l, i) => i > 0 && !l.startsWith('//'))).join('\n').replace(/^\/\/ ?/gm, '') + '\n'); process.exit(cmd ? 1 : 0); }
  switch (cmd) {
    case 'init': return init(dir);
    case 'split': return split(dir);
    case 'validate': { const v = await validate(dir, { runDisc: !!flag('run') }); out(v); process.exit(v.ok ? 0 : 1); }
    case 'judge-test': return judgeTest(dir);
    case 'discriminate': { const hill = loadHill(dir); const d = await discriminate(hill); writeJSON(P(hill, 'calibration.json'), d); return out(d); }
    case 'freeze': return freeze(dir);
    case 'score': {
      const hill = loadHill(dir);
      refuseUnsound(hill);
      const which = flag('split', 'optimise');
      const splits = which === 'both' ? ['optimise', 'holdout'] : [which];
      const res = [];
      for (const s of splits) res.push(await scoreSplit(hill, s, { save: P(hill, 'runs', 'manual', `${Date.now()}-${s}.json`) }));
      return out(flag('verbose') ? res : res.map((r) => ({ ...summarize(r), failing: r.results.filter((x) => !x.pass).map((x) => ({ id: x.id, failed: x.runs[0]?.failed })) })));
    }
    case 'try': return tryOne(dir);
    case 'brief': return brief(dir);
    case 'approve': return approve(dir);
    case 'status': return status(dir);
    case 'council-test': return councilTest(dir);
    case 'raise': return raise(dir);
    case 'verify': { const hill = loadHill(dir); const s = loadState(hill); const l = checkLock(hill, s.lock_digest), g = verifyLedger(hill); out({ ok: l.ok && g.ok, lock: l, ledger: g }); process.exit(l.ok && g.ok ? 0 : 1); }
    case 'board': { const hill = loadHill(dir); fs.writeFileSync(P(hill, 'board.html'), renderBoard(hill, loadState(hill))); return out({ status: 'ok', board: P(hill, 'board.html') }); }
    default: die(`unknown command ${cmd}`);
  }
}
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('hill.mjs')) main().catch((e) => die(e.message));
export { validate, clip };
