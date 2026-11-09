#!/usr/bin/env node
// climb.mjs <hill> [--deadline <ISO time>] [--max-attempts N] [--once] [--no-council] [--accept-git-config] [--recover-only]
// The unattended loop. Every attempt is a fresh, sandboxed agent session that sees only the prompt and the work folder.
// One change per attempt -> score -> keep (a commit on hill/<name>) or undo (saved as refs/hill/<name>/rejected/<n>).
// Stage 1: visible score >= target, hidden score within the gap, no must-pass failures.
// Stage 2: every council judge scores every category >= council_bar, says ship and (with references) leads every
// reference (council.mjs). Stops at done, deadline, stuck, budget or a blocker.
// All memory is on disk (state.json, ledger.jsonl, runs/), so a killed run resumes with nothing lost.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  now, readJSON, writeJSON, loadHill, P, loadState, saveState, appendLedger, readLedger, verifyLedger, checkLock, checkSettings,
  git, gitx, currentBranch, gitDirs, runAgent, clip, nonce, matchesAny, killActive, listCases, processCommand,
  processStart, sleepSync, run, reapJobs, sandboxTool, sandboxRules, snapshotGuard, restoreGuard, guardDigest, currentGuardDigest,
  worktreeTree, treeChanges, restoreWorktree, pointIndex, filterAttrProblems, stagedOnlyProblems, commitTree, createRef, listFiles,
  treeFiles, treeOf, takeRunLock,
} from './lib.mjs';
import { scoreSplit, ScoreError, DeadlineError, scoringSettingsProblems, takeCheckUsage } from './score.mjs';
import { runCouncil, councilBetter, confirmRises, mergeVerdict, logRound, describeRound, addUsage, addCheckUsage, usageText, councilProblems } from './council.mjs';
import { measureBaseline } from './hill.mjs';
import { renderBoard } from './board.mjs';

const argv = process.argv.slice(2);
const flag = (name, d = null) => { const i = argv.indexOf(`--${name}`); return i >= 0 ? (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true) : d; };
const dir = argv[0];
if (!dir || dir.startsWith('--')) { console.log('usage: climb.mjs <hill> [--deadline ISO] [--max-attempts N] [--once] [--no-council] [--accept-git-config] [--recover-only]'); process.exit(1); }

const hill = loadHill(dir);
const W = hill.workdir;
const say = (m) => process.stderr.write(`[hill ${hill.name} ${new Date().toISOString().slice(11, 19)}] ${m}\n`);
let state = loadState(hill);
const DIGEST = state.lock_digest; // held in memory: a rewritten lock.json or state.json cannot fool this run
const deadline = flag('deadline') ? new Date(flag('deadline')) : hill.stop.deadline ? new Date(hill.stop.deadline) : null;
const DL = deadline ? deadline.getTime() : null; // every scoring pass and judge is bounded by this, not just the climber
const maxAttempts = Number(flag('max-attempts')) || hill.stop.max_attempts || null;
const noCouncil = !!flag('no-council');
const once = !!flag('once');
const runLock = P(hill, 'run.lock');
const INDEX = P(hill, 'cache', `index-${process.pid}`);
const REF = (kind, label) => `refs/hill/${hill.name}/${kind}/${label}`;
run.jobsDir = P(hill, 'jobs');
let startAttempts = 0;
let liveGuard = null; // the git guard snapshot of the attempt in flight, put back on interrupt
// What council.mjs needs: the hill, the live state (a getter: state is replaced after the baseline), the deadline, usage.
const ctx = { hill, get state() { return state; }, DL, addUsage: (kind, name, r) => addUsage(state, kind, name, r) };
const drainChecks = () => addCheckUsage(state, takeCheckUsage());
// The recorded spend (yes/no checks drained first) has reached stop.budget_usd: checked before every paid council round.
const overBudget = () => { drainChecks(); return hill.stop.budget_usd != null && (state.usage?.total ?? 0) >= hill.stop.budget_usd; };
const budgetStop = (more = '') => finish('budget', `budget reached: ${usageText(state.usage)} spent of $${hill.stop.budget_usd} (best ${state.best.optimise}).${more} Runs of unknown cost are not counted.`);

function out(v) { process.stdout.write(`${JSON.stringify(v, null, 2)}\n`); }
function board() { try { fs.writeFileSync(P(hill, 'board.html'), renderBoard(hill, state)); } catch (e) { say(`board render failed: ${e.message}`); } }
function release() {
  for (const f of [INDEX, `${INDEX}-recheck`]) fs.rmSync(f, { force: true });
  try { const l = readJSON(runLock, null); if (l?.pid === process.pid && l?.host === os.hostname()) fs.rmSync(runLock); } catch { /* ignore */ }
}

function finish(status, reason, code = 0, { keepInProgress = false } = {}) {
  state.status = status; state.stop_reason = reason;
  if (!keepInProgress) delete state.in_progress;
  drainChecks();
  saveState(hill, state);
  appendLedger(hill, { kind: 'stop', status, reason, best: state.best ?? null, attempts: state.attempts ?? 0 });
  board(); writeReport(); release();
  out({ status, reason, name: hill.name, baseline: state.baseline?.optimise, best: state.best?.optimise, holdout: state.best?.holdout, secondary: state.best?.secondary, target: hill.metric.target, attempts: state.attempts, kept: state.kept, council: state.council?.last ?? null, usage: state.usage ?? null, board: P(hill, 'board.html'), report: P(hill, 'report.md'), branch: hill.branch, best_sha: state.best?.sha });
  process.exit(code);
}
const block = (reason, opts) => finish('blocked', reason, 2, opts);

function writeReport() {
  const b = state.best ?? {}, base = state.baseline ?? {};
  const kept = (state.history ?? []).filter((h) => h.decision === 'kept');
  const md = `# ${hill.name}: ${state.status}\n\n${hill.goal}\n\n- Result: ${state.stop_reason ?? state.status}\n- ${hill.metric.name}: ${base.optimise} -> ${b.optimise} (target ${hill.metric.target})\n- Hidden check: ${base.holdout} -> ${b.holdout ?? 'not measured'} (allowed gap ${hill.metric.holdout_gap_max})\n${hill.metric.secondary ? `- ${hill.metric.secondary.name}: ${base.secondary} -> ${b.secondary}\n` : ''}- Attempts: ${state.attempts ?? 0} (${state.kept ?? 0} kept)\n- Judges: ${state.council?.last ? describeRound(state.council.last) : 'not run'}${state.council?.last?.drift ? ' (a judge drifted: its score for an unchanged version moved more than 1 point)' : ''}\n- Usage: ${usageText(state.usage)}${hill.stop.budget_usd != null ? ` of a $${hill.stop.budget_usd} budget` : ''}\n- Branch: ${hill.branch} at ${b.sha?.slice(0, 10)} (rejected attempts saved under refs/hill/${hill.name}/rejected/)\n\n## Changes that stuck\n${kept.map((h) => `- #${h.n} (+${h.delta}): ${h.hypothesis ?? ''}`).join('\n') || '- none'}\n${state.council?.last ? `\n## Judges' top faults\n${state.council.last.scores.map((s) => `- ${s.judge}: ${s.top_fault ?? s.error ?? ''}`).join('\n')}\n` : ''}`;
  fs.writeFileSync(P(hill, 'report.md'), md);
}

// ---------- one runner per hill ----------
function acquire() {
  const l = takeRunLock(hill, { label: 'climb.mjs' });
  if (!l.ok) { out({ status: 'busy', reason: l.reason }); process.exit(3); }
}

function preflight({ recoverOnly }) {
  const stop = (reason) => { out({ status: 'blocked', reason }); release(); process.exit(2); };
  const bad = [...checkSettings(hill), ...scoringSettingsProblems(hill), ...councilProblems(hill)];
  if (bad.length) stop(`hill.json settings: ${bad.join('; ')}`);
  if (deadline && Number.isNaN(DL)) stop(`the deadline ${flag('deadline') ?? hill.stop.deadline} is not a date (use an ISO time like 2026-11-02T06:00:00+08:00)`);
  if (!String(hill.branch).startsWith('hill/')) stop('the hill branch must start with hill/ (the runner only moves its own branches)');
  const chain = verifyLedger(hill);
  if (!chain.ok) stop(`ledger chain broken at line ${chain.broken_at}`);
  const br = currentBranch(W);
  if (br !== hill.branch) stop(`work folder ${W} is on ${br ?? 'a detached HEAD'}, not ${hill.branch}. Nothing was reset. Check out ${hill.branch} there (after saving anything you need), then run again.`);
  const filters = filterAttrProblems(W);
  if (filters.length) stop(`this repo transforms files through git (${filters.slice(0, 4).join('; ')}). The runner saves and restores raw bytes, so it does not support filters, LFS, ident, encodings, CRLF conversion or sparse checkout. Climb in a repo or copy without them.`);
  const staged = stagedOnlyProblems(W, { alsoIn: [state.head] });
  if (staged.length) stop(`staged changes in ${W} exist only in git's index (${staged.slice(0, 6).join(', ')}). The runner resets the index, which would lose them: commit, unstage or stash them, then run again.`);
  if (recoverOnly) return;
  if (hill.sandbox !== 'off' && !sandboxTool()) stop('no sandbox tool on this machine (sandbox-exec on macOS, bubblewrap on Linux). Install one, or set "sandbox": "off" in hill.json and re-freeze to run unprotected.');
  const lock = checkLock(hill, DIGEST);
  if (!DIGEST || !lock.ok) stop(`answer key not frozen or changed: ${lock.reason}`);
  if (hill.checkpoint !== false && state.approved_for !== `${DIGEST}:${state.baseline?.sha}`) stop('waiting for the owner: run `hill.mjs brief`, show checkpoint.html, then `hill.mjs approve --by <name>`');
}

// ---------- files git cannot see ----------
// Ignored files (outside scope_ignore) on disk before an attempt, with size and modified time. After the attempt, new ones are moved to
// quarantine/<n>/ and reject the attempt; changed or deleted ones cannot be put back, so the run stops for the owner.
function ignoredInventory(tree) {
  const tracked = treeFiles(W, tree);
  const inv = {};
  for (const f of listFiles(W, hill.scope_ignore)) if (!tracked.has(f)) { try { const st = fs.lstatSync(path.join(W, f)); inv[f] = `${st.size}:${st.mtimeMs}`; } catch { /* raced */ } }
  return inv;
}
function ignoredCheck(n, tree, pre) {
  const post = ignoredInventory(tree);
  const fresh = Object.keys(post).filter((f) => !(f in pre));
  const touched = Object.keys(pre).filter((f) => post[f] !== pre[f]);
  const q = P(hill, 'quarantine', String(n));
  for (const f of fresh) { const to = path.join(q, f); fs.mkdirSync(path.dirname(to), { recursive: true }); fs.renameSync(path.join(W, f), to); }
  return { quarantined: fresh, touched };
}
const ignoredHelp = 'If these are build or cache output the climber is allowed to regenerate, add their folder to scope_ignore in hill.json and re-freeze.';

// ---------- recovery ----------
// A run killed mid-attempt can leave a climber running, git files edited, an agent commit, a finished keep that was
// never recorded, or half-done edits. Each is handled here; nothing the climber wrote is lost.
function recover() {
  const stopped = reapJobs(run.jobsDir);
  if (stopped.length) { appendLedger(hill, { kind: 'orphan_stopped', jobs: stopped.map((j) => ({ pgid: j.pgid, label: j.label })) }); say(`stopped ${stopped.length} process group(s) the last runner left behind`); }
  const ip = state.in_progress;
  if (!state.head) {
    if (ip) block('state has an attempt in progress but no head commit: inspect state.json', { keepInProgress: true });
    return;
  }
  if (ip?.guard && currentGuardDigest(W) !== ip.guard) {
    if (!flag('accept-git-config')) block(`git config, attributes or hooks changed during attempt #${ip.n} and the runner stopped before putting them back. Inspect ${gitDirs(W).commonDir} (config, info/, hooks/) and ~/.gitconfig, then run again with --accept-git-config.`, { keepInProgress: true });
    appendLedger(hill, { kind: 'git_config_accepted', attempt: ip.n });
  }
  const headTree = treeOf(W, state.head);
  const head = git(W, 'rev-parse', 'HEAD');
  // decision.json is written before any git side effect of an outcome; one made for this very attempt means the
  // outcome was decided and only its git steps or bookkeeping may be unfinished.
  const found = ip ? readJSON(P(hill, 'runs', String(ip.n), 'decision.json'), null) : null;
  const dec = found?.id && found.id === ip?.id ? found : null;
  const pre = ip ? readJSON(P(hill, 'runs', String(ip.n), 'pre-ignored.json'), null) : null;
  const skip = pre ? new Set(Object.keys(pre)) : null;
  let keptSha = null, savedHead = null, savedTree = null;
  if (head !== state.head) {
    if (!ip) block(`${hill.branch} moved to ${head.slice(0, 10)} outside the runner (state expects ${state.head.slice(0, 10)}). Nothing was reset: move it back with \`git update-ref refs/heads/${hill.branch} ${state.head}\` if that commit is unwanted, or re-freeze and brief to start from it.`);
    if (dec?.decision === 'kept' && dec.parent === state.head && git(W, 'rev-parse', `${head}^`) === state.head && treeOf(W, head) === dec.tree) keptSha = head;
    else {
      savedHead = createRef(W, REF('rejected', `interrupted-${ip.n}-commit`), head);
      gitx({ cwd: W }, 'update-ref', `refs/heads/${hill.branch}`, state.head, head);
    }
  } else if (dec?.decision === 'kept' && dec.parent === state.head && worktreeTree(W, state.head, INDEX, { skip }) === dec.tree) {
    // Stopped after the keep was decided but before the branch moved, with the scored files still in place: finish it.
    keptSha = commitTree(W, dec.tree, state.head, keepMessage(dec));
    gitx({ cwd: W }, 'update-ref', '-m', `hill keep #${dec.n}`, `refs/heads/${hill.branch}`, keptSha, state.head);
  }
  const decided = dec && (dec.decision !== 'kept' || keptSha); // a keep whose files are gone is just interrupted
  const base = keptSha ?? state.head;
  const baseTree = keptSha ? dec.tree : headTree;
  const tree = worktreeTree(W, base, INDEX, { skip });
  if (tree !== baseTree) {
    if (!ip) block(`the work folder has uncommitted changes the runner did not make. Commit or stash them (or move them off ${hill.branch}), then run again.`);
    if (decided && tree === dec.tree && dec.saved_ref) dec.entry.saved_as = createRef(W, dec.saved_ref, commitTree(W, tree, base, rejectedMessage(dec)));
    else savedTree = createRef(W, REF('rejected', `interrupted-${ip.n}`), commitTree(W, tree, base, `hill(${hill.name}): interrupted attempt #${ip.n}`));
  } else if (decided && dec.saved_ref) dec.entry.saved_as = savedRefOf(dec);
  if (ip) restoreWorktree(W, baseTree, INDEX, { skip }); // also points the owner's index at the recovered keep
  const ig = ip && pre ? ignoredCheck(ip.n, baseTree, pre) : null;
  if (ig?.quarantined.length) say(`moved ${ig.quarantined.length} ignored file(s) from the interrupted attempt to quarantine/${ip.n}`);
  if (decided) {
    complete(dec, keptSha);
    appendLedger(hill, { kind: 'recovered_completion', id: dec.id, n: dec.n, decision: dec.decision, sha: keptSha, also_saved: [savedTree, savedHead].filter(Boolean) });
    say(`finished recording attempt #${dec.n} (${dec.decision}) cut short by the last stop`);
  } else if (ip) {
    state.history.push({ id: ip.id, n: ip.n, decision: 'interrupted', score: null, note: [savedTree, savedHead].filter(Boolean).join(' ') || 'no changes' });
    appendLedger(hill, { kind: 'attempt', id: ip.id, n: ip.n, decision: 'interrupted', saved_as: savedTree, saved_commit: savedHead });
    if (savedTree || savedHead) say(`saved interrupted attempt #${ip.n} as ${[savedTree, savedHead].filter(Boolean).join(' and ')}`);
  }
  delete state.in_progress;
  saveState(hill, state);
  if (ig?.touched.length) block(`attempt #${ip.n} (cut short by the last stop) changed or deleted ignored files that existed before it: ${ig.touched.slice(0, 8).join(', ')}. Check them, then run again. ${ignoredHelp}`);
}

// The ref a finished rejection was saved under, found again after a stop (a name collision may have added a suffix).
function savedRefOf(dec) {
  const out = gitx({ cwd: W }, 'for-each-ref', '--format=%(refname) %(objectname)', `refs/hill/${hill.name}/rejected/`);
  for (const line of out.split('\n').filter(Boolean)) {
    const [ref, sha] = line.split(' ');
    if ((ref === dec.saved_ref || ref.startsWith(`${dec.saved_ref}-`)) && treeOf(W, sha) === dec.tree && git(W, 'rev-parse', `${sha}^`) === dec.parent) return ref;
  }
  return null;
}
const rejectedMessage = (dec) => `hill(${hill.name}): rejected #${dec.n} ${dec.decision} ${clip(dec.entry.hypothesis ?? '', 100)}`;
const keepMessage = (dec) => `hill(${hill.name}): keep #${dec.n} ${clip(dec.entry.hypothesis ?? '', 120)}${hill.commit_trailer ? `\n\n${hill.commit_trailer}` : ''}`;

// Records an attempt's outcome exactly once. The state and the ledger line both carry the attempt id, so a stop
// between any two writes is finished by recover() without a duplicate line or a lost decision.
const UNCOUNTED = ['error', 'score_error', 'deadline', 'budget']; // not the idea's fault: no streak, no switch
function complete(dec, sha = null) {
  const e = { ...dec.entry, ...(sha ? { sha } : {}) };
  // After a stop, state.json can be older than decision.json: its usage snapshot keeps the judges' spend counted.
  const u = state.usage;
  if (dec.usage && (!u || dec.usage.total > u.total || dec.usage.unknown_runs > u.unknown_runs)) state.usage = structuredClone(dec.usage);
  if (!state.history.some((h) => h.id === dec.id)) {
    state.history.push({ id: dec.id, n: dec.n, decision: dec.decision, score: e.score, delta: e.delta, secondary: e.secondary, holdout: e.holdout ?? null, hypothesis: e.hypothesis, note: e.note });
    if (dec.decision === 'kept') applyKeep(dec.n, sha, dec);
    else if (!UNCOUNTED.includes(dec.decision)) state.streak = (state.streak ?? 0) + 1;
    state.consecutive_errors = ['error', 'score_error'].includes(dec.decision) ? (state.consecutive_errors ?? 0) + 1 : 0;
    if (dec.council && dec.decision !== 'kept') state.council = { ...(state.council ?? {}), last_rejected: dec.council };
    if (dec.council) logRound(state, dec.council, { n: dec.n, decision: dec.decision });
    state.switches = Math.floor(state.streak / hill.stop.switch_every);
  }
  if (!readLedger(hill).some((l) => l.kind === 'attempt' && l.id === dec.id)) appendLedger(hill, { kind: 'attempt', ...e });
  fault('after_ledger');
  delete state.in_progress;
  drainChecks();
  saveState(hill, state);
}

// ---------- decisions ----------
const secBetter = (a, b) => {
  const s = hill.metric.secondary;
  if (!s || a == null || b == null) return false;
  const m = s.margin ?? 0;
  return s.direction === 'up' ? a > b + m : a < b - m;
};
const secMet = (v) => {
  const s = hill.metric.secondary;
  if (!s || s.target == null) return true;
  if (v == null) return false;
  return s.direction === 'up' ? v >= s.target : v <= s.target;
};
function isBetter(o, best) {
  if (o.must_pass_failures.length > best.must_pass_failures.length) return false;
  if (o.score > best.optimise + hill.accept_margin) return true;
  if (o.score >= best.optimise && o.must_pass_failures.length < best.must_pass_failures.length) return true;
  // Once the main score holds, the secondary number (e.g. prompt size) may climb on its own.
  return o.score >= best.optimise && secBetter(o.secondary, best.secondary);
}

async function ensureHoldout() {
  if (state.best.holdout_sha === state.best.sha) return;
  const h = await scoreSplit(hill, 'holdout', { save: P(hill, 'runs', `holdout-${state.best.attempt}.json`), deadline: DL });
  if (h.judge_errors) throw new ScoreError(`${h.judge_errors} judge error(s) while scoring the hidden cases`);
  Object.assign(state.best, { holdout: h.score, holdout_sha: state.best.sha, holdout_must_pass_failures: h.must_pass_failures });
  const last = state.history.findLast((x) => x.n === state.best.attempt);
  if (last) last.holdout = h.score;
  appendLedger(hill, { kind: 'holdout', attempt: state.best.attempt, sha: state.best.sha, score: h.score, must_pass_failures: h.must_pass_failures });
  drainChecks();
  saveState(hill, state);
}
// 'met' | 'no' | 'saturated' (visible tests maxed, hidden check fails: nothing left to climb) | 'unmeasured'
async function stage1(allowScoring) {
  const b = state.best;
  if (b.optimise < hill.metric.target || b.must_pass_failures.length || !secMet(b.secondary)) return 'no';
  if (b.holdout_sha !== b.sha) { if (!allowScoring) return 'unmeasured'; await ensureHoldout(); }
  const ok = b.optimise - b.holdout <= hill.metric.holdout_gap_max && !(b.holdout_must_pass_failures?.length);
  state.overfit = !ok;
  if (ok) return 'met';
  return b.optimise >= 100 ? 'saturated' : 'no';
}

// ---------- the attempt prompt ----------
function attemptPrompt(n, stage, lastOpt) {
  const hist = (state.history ?? []).filter((h) => h.n > 0).slice(-15).reverse()
    .map((h) => `#${h.n} ${h.decision}${typeof h.delta === 'number' ? ` (${h.delta >= 0 ? '+' : ''}${h.delta})` : ''}: ${clip(h.hypothesis ?? h.note ?? '', 200)}`).join('\n');
  const failing = (lastOpt?.results ?? []).filter((r) => !r.pass);
  const failText = failing.slice(0, hill.show_failing ?? 14).map((r) => `- ${r.id}${r.must_pass ? ' [MUST PASS]' : ''}${r.negative ? ' [must NOT do]' : ''}\n  input: ${clip(caseInput(r.id), 700)}\n  output: ${clip(r.runs[0]?.output, 600)}\n  failed: ${clip((r.runs[0]?.failed ?? []).join('; '), 400)}`).join('\n');
  const switching = state.streak >= hill.stop.switch_every;
  const notes = fs.existsSync(P(hill, 'notes.md')) ? clip(fs.readFileSync(P(hill, 'notes.md'), 'utf8'), 4000) : '';
  const c = state.council?.last;
  const council = stage === 2 && c ? c.scores.map((s) => councilLine(s)).join('\n') : '';
  const refMode = !!c?.ref_mode;
  return `You are attempt #${n} of an unattended hill climb. This is a fresh session: everything you need is in this message and in the files of this folder.

GOAL: ${hill.goal}
SCORE: ${hill.metric.name} is ${state.best.optimise} on the visible tests (${lastOpt ? `${lastOpt.passed}/${lastOpt.total}` : ''}); target ${hill.metric.target}.${hill.metric.secondary ? ` ${hill.metric.secondary.name} is ${state.best.secondary} (${hill.metric.secondary.direction === 'up' ? 'higher' : 'lower'} is better${hill.metric.secondary.target != null ? `, target ${hill.metric.secondary.target}` : ''}).` : ''}
${state.best.must_pass_failures.length ? `MUST-PASS tests failing: ${state.best.must_pass_failures.join(', ')}. Fix these first.\n` : ''}${state.overfit ? 'WARNING: a hidden set of tests (which you cannot see) shows recent gains do not generalise. Prefer general, principled changes over ones that fit specific tests. A change that keeps the visible score and raises the hidden score is kept.\n' : ''}
YOU MAY EDIT ONLY: ${hill.climbable.join(', ')}
RULES: ${hill.authority} Do not edit tests, scorers, configs, git settings or any other file; changes elsewhere are thrown away and count against you. Do not run git commit, checkout, reset, stash or branch commands. Do not copy test inputs or ids into the files, and do not special-case individual tests: changes that do are rejected. Do not look for the hidden tests.
${stage === 2 ? `\nSTAGE 2: the tests are at target. Outside judges now review the work. Done needs every judge to score every category ${hill.council_bar}/10 or more${refMode ? ', score your work above every reference product they compare it with' : ''} and say they would ship it. Their latest verdicts:\n${council}\nFix the top fault without lowering the test score.\n` : ''}${switching ? `\nSWITCH APPROACH: the last ${state.streak} attempts brought no gain. Do not repeat or tweak those ideas; try a fundamentally different kind of change.\n` : ''}
RECENT ATTEMPTS (newest first; "reverted" means it was tried and undone):
${hist || '(none yet)'}
${notes ? `\nNOTES:\n${notes}\n` : ''}
FAILING VISIBLE TESTS (${failing.length}, showing up to ${hill.show_failing ?? 14}):
${failText || '(none: see stage notes above)'}

YOUR JOB: make ONE focused change to the editable files that should fix a group of failures (or the judges' top fault) without breaking what passes. Keep it general and small. Read the files first. Then stop.
End your final message with exactly one line: HYPOTHESIS: <what you changed and why, under 25 words>`;
}
// One judge's latest verdict for the climber. Labels like "A" in its notes are mapped back to what they were.
const ROLE = (id) => (id === 'candidate' ? 'your work' : id === 'base' ? 'the starting version' : `reference "${id.slice(4)}"`);
function councilLine(s) {
  if (s.score == null) return `${s.judge}: no verdict (${s.error ?? 'not asked'})`;
  const cats = s.categories ? ` (${Object.entries(s.categories).map(([k, v]) => `${k} ${v}`).join(', ')})` : '';
  const lead = s.lead != null ? `; ${s.lead > 0 ? `ahead of the best reference by ${s.lead}` : s.lead === 0 ? 'level with the best reference' : `behind the best reference by ${-s.lead}`}` : '';
  const labels = s.labels ? `\n  Labels in its notes: ${Object.entries(s.labels).map(([l, id]) => `${l} = ${ROLE(id)}`).join(', ')}` : '';
  return `${s.judge}${s.carried ? ' (an earlier verdict: not asked about the latest kept change)' : ''}: lowest category ${s.score}/10${cats}${lead}${s.ship === false ? ', would not ship' : ''}. Top fault: ${s.top_fault}\n  Fixes: ${(s.critique ?? []).join(' | ')}${labels}`;
}
const caseIndex = new Map();
function caseInput(id) {
  if (!caseIndex.size) for (const c of listCases(hill, 'optimise')) caseIndex.set(c.id, c.input);
  return caseIndex.get(id);
}

// Rejects diffs that paste visible or hidden test inputs into the climbable files (memorising the answer key).
function leakCheck(tree) {
  const added = gitx({ cwd: W }, 'diff', '--no-ext-diff', '--no-textconv', '-U0', state.head, tree).split('\n').filter((l) => l.startsWith('+') && !l.startsWith('+++')).join('\n').toLowerCase().replace(/\s+/g, ' ');
  if (!added) return null;
  const strings = (v, acc = []) => { if (typeof v === 'string') acc.push(v); else if (v && typeof v === 'object') for (const x of Object.values(v)) strings(x, acc); return acc; };
  for (const split of ['holdout', 'optimise']) {
    for (const c of listCases(hill, split)) {
      for (const s of strings(c.input)) {
        const t = s.toLowerCase().replace(/\s+/g, ' ').trim();
        if (t.length < (hill.leak_min_chars ?? 40)) continue;
        if (added.includes(t.slice(0, 80))) return { split, id: c.id };
      }
    }
  }
  return null;
}

function applyKeep(n, sha, dec) {
  state.best = { sha, attempt: n, optimise: dec.optimise, holdout: dec.holdout ?? null, holdout_sha: dec.holdout != null ? sha : null, holdout_must_pass_failures: dec.holdout_must_pass_failures ?? [], secondary: dec.secondary, must_pass_failures: dec.must_pass_failures };
  state.head = sha; state.kept = (state.kept ?? 0) + 1; state.streak = 0; state.switches = 0;
  if (dec.council) state.council = { ...(state.council ?? {}), rounds: (state.council?.rounds ?? 0) + 1, last: mergeVerdict(hill, dec.council, state.council?.last), last_sha: sha };
}

const fault = (point) => { if (process.env.HILL_FAULT === point) { say(`HILL_FAULT=${point}: exiting hard`); process.exit(137); } };

async function attempt(stage, lastOpt) {
  const n = (state.attempts ?? 0) + 1;
  const runDir = P(hill, 'runs', String(n));
  const agentDir = path.join(runDir, 'agent');
  fs.mkdirSync(agentDir, { recursive: true });
  const headTree = treeOf(W, state.head);
  const pre = ignoredInventory(headTree);
  const skip = new Set(Object.keys(pre));
  writeJSON(path.join(runDir, 'pre-ignored.json'), pre);
  liveGuard = snapshotGuard(W);
  const id = `${n}-${nonce()}`;
  state.attempts = n;
  state.in_progress = { id, n, stage, phase: 'climber', started: now(), guard: guardDigest(liveGuard) };
  saveState(hill, state);

  const left = deadline ? (deadline.getTime() - Date.now()) / 1000 : Infinity;
  const timeoutSec = Math.max(1, Math.floor(Math.min(hill.climber.timeout_sec ?? 1800, left)));
  say(`attempt #${n} (stage ${stage}, best ${state.best.optimise}, streak ${state.streak})`);
  const r = await runAgent(hill.climber, 'climber', { cwd: W, prompt: attemptPrompt(n, stage, lastOpt), timeoutSec, dir: agentDir, env: { HILL_ATTEMPT: String(n), HILL_WORKDIR: W }, sandbox: sandboxRules(hill, 'climber', { agentDir }) });
  addUsage(state, 'climber', 'climber', r);
  if (r.sandboxMissing) throw new Error(r.stderr);
  const hyp = (String(r.text).match(/HYPOTHESIS:\s*(.+)/gi) ?? []).at(-1)?.replace(/HYPOTHESIS:\s*/i, '').trim() ?? clip(String(r.text).trim().split('\n').at(-1) ?? '', 200);
  state.in_progress.phase = 'checking'; saveState(hill, state);

  // 1. Git's own config, attributes and hooks go back exactly as they were before anything else runs git.
  const gitTouched = restoreGuard(liveGuard);
  liveGuard = null;
  // 2. Still on the hill branch? If not, touch nothing and hand it to the owner.
  const br = currentBranch(W);
  if (br !== hill.branch) {
    let evidence = null;
    try { evidence = createRef(W, REF('evidence', `${n}-off-branch`), git(W, 'rev-parse', 'HEAD')); } catch { /* no HEAD */ }
    appendLedger(hill, { kind: 'off_branch', id, n, branch: br, evidence, git_restored: gitTouched }); // recorded as an attempt once recovered
    block(`attempt #${n} left the work folder on ${br ?? 'a detached HEAD'} (evidence: ${evidence}). Nothing was reset. Check out ${hill.branch} in ${W}, then run again: the attempt's edits are saved then.`, { keepInProgress: true });
  }
  // 3. Commits the agent made on the hill branch are kept as evidence and folded back into plain edits.
  const head = git(W, 'rev-parse', 'HEAD');
  let agentCommit = null;
  if (head !== state.head) {
    agentCommit = createRef(W, REF('rejected', `${n}-agent-commit`), head);
    gitx({ cwd: W }, 'update-ref', `refs/heads/${hill.branch}`, state.head, head);
  }
  // 4. The tree the folder holds now, its changes, and files git cannot see.
  const tree = worktreeTree(W, state.head, INDEX, { skip });
  const changes = treeChanges(W, headTree, tree);
  const changed = changes.map((c) => c.file);
  const ig = ignoredCheck(n, tree, pre);

  let decision, detail = null, o = null;
  const extra = {};
  const lock = checkLock(hill, DIGEST);
  const outside = changed.filter((f) => !matchesAny(f, hill.climbable));
  const oddModes = changes.filter((c) => /^(120000|160000)$/.test(c.newMode)).map((c) => c.file);
  const gitControl = changed.filter((f) => ['.gitattributes', '.gitmodules'].includes(path.basename(f)));
  if (!lock.ok) { decision = 'tampered'; detail = lock.reason; }
  else if (r.escaped?.length) { decision = 'escaped_process'; detail = `left processes running after it finished (stopped): ${r.escaped.slice(0, 4).map((e) => `pid ${e.pid} ${e.why}`).join('; ')}`; }
  else if (ig.touched.length) { decision = 'ignored_files_changed'; detail = ig.touched.slice(0, 8).join(', '); }
  else if (gitTouched.length) { decision = 'tampered_git'; detail = `edited git files (put back): ${gitTouched.slice(0, 6).join(', ')}`; }
  else if (ig.quarantined.length) { decision = 'out_of_scope'; detail = `wrote ignored files (moved to quarantine/${n}): ${ig.quarantined.slice(0, 6).join(', ')}`; }
  else if (oddModes.length) { decision = 'out_of_scope'; detail = `symlink or submodule: ${oddModes.join(', ')}`; }
  else if (gitControl.length) { decision = 'out_of_scope'; detail = `git attributes or submodule file: ${gitControl.join(', ')}`; }
  else if (!changed.length) { decision = r.code !== 0 || r.timedOut ? 'error' : 'noop'; detail = r.code !== 0 || r.timedOut ? clip(r.stderr || r.text || (r.timedOut ? 'timed out' : ''), 300) : null; }
  else if (outside.length) { decision = 'out_of_scope'; detail = outside.join(', '); }
  else {
    const leak = leakCheck(tree);
    if (leak) { decision = leak.split === 'holdout' ? 'leaked_hidden_test' : 'memorised_test'; detail = `pasted ${leak.split} case ${leak.id}`; }
    else {
      state.in_progress.phase = 'scoring'; saveState(hill, state);
      try { ({ decision, detail, o } = await judgeAttempt(stage, tree, runDir, extra)); }
      catch (e) {
        if (e instanceof DeadlineError) { decision = 'deadline'; detail = 'the deadline passed before scoring finished: not judged (the edits are saved)'; o = null; }
        else if (e instanceof ScoreError) { decision = 'score_error'; detail = clip(e.message, 300); }
        else throw e;
      }
      // Scoring must not change the folder (the sandbox blocks it; this catches sandbox: "off").
      if (worktreeTree(W, state.head, `${INDEX}-recheck`, { skip }) !== tree) { decision = 'out_of_scope'; detail = 'the work folder changed while it was being scored'; }
      fs.rmSync(`${INDEX}-recheck`, { force: true });
      if (decision === 'kept' && !checkLock(hill, DIGEST).ok) { decision = 'tampered'; detail = 'answer key changed while scoring'; }
    }
  }

  const prev = state.best.optimise;
  drainChecks();
  const entry = { id, n, decision, stage, ...(extra.council?.control_missing ? { control_missing: true } : {}), ...(extra.council?.drift ? { judge_drift: true } : {}), score: o?.score ?? null, delta: o ? Math.round((o.score - prev) * 100) / 100 : null, secondary: o?.secondary ?? null, holdout: extra.holdout ?? null, hypothesis: clip(hyp, 300), note: detail, changed, agent_exit: r.code, agent_ms: r.ms, agent_commit: agentCommit };
  // Transaction for every outcome: decision.json (exact tree and parent) -> git steps -> ledger line -> state.
  // recover() finishes a stop between any two of them from decision.json (see complete()).
  const dec = { id, n, decision, entry, tree, parent: state.head, optimise: o?.score ?? null, holdout: extra.holdout ?? null, holdout_must_pass_failures: extra.holdout_must_pass_failures ?? [], secondary: o?.secondary ?? null, must_pass_failures: o?.must_pass_failures ?? [], council: extra.council ?? null, usage: state.usage ? structuredClone(state.usage) : null, saved_ref: decision !== 'kept' && tree !== headTree ? REF('rejected', String(n)) : null };
  writeJSON(path.join(runDir, 'decision.json'), dec);
  fault('after_decision');
  let sha = null;
  if (decision === 'kept') {
    sha = commitTree(W, tree, state.head, keepMessage(dec));
    gitx({ cwd: W }, 'update-ref', '-m', `hill keep #${n}`, `refs/heads/${hill.branch}`, sha, state.head);
    fault('after_commit');
    pointIndex(W, sha);
    if (treeOf(W, 'HEAD') !== tree) throw new Error(`kept commit ${sha} does not hold the scored tree`);
  } else {
    if (dec.saved_ref) entry.saved_as = createRef(W, dec.saved_ref, commitTree(W, tree, state.head, rejectedMessage(dec)));
    restoreWorktree(W, headTree, INDEX, { skip });
    fault('after_restore');
  }
  complete(dec, sha);
  board();
  say(`#${n} ${decision}${o ? ` ${o.score}` : ''}${detail ? ` - ${clip(detail, 120)}` : ''}`);
  if (decision === 'tampered') finish('tampered', `answer key changed during attempt #${n}: ${detail}`, 2);
  if (decision === 'ignored_files_changed') block(`attempt #${n} changed or deleted ignored files that existed before it (${detail}). They cannot be put back automatically: check them, then run again. ${ignoredHelp}`);
  if (decision === 'kept' && stage === 1 && state.kept % hill.holdout_every === 0) {
    try { await ensureHoldout(); } catch (e) { if (!(e instanceof DeadlineError)) throw e; } // the loop then stops for the deadline
  }
  return decision === 'kept' ? o : null;
}

// Scores a candidate and decides keep or revert. Stage 1 climbs the visible score; stage 2 holds the tests and climbs
// the judges. Every pass is bounded by the deadline (DeadlineError, never a partial score).
async function judgeAttempt(stage, tree, runDir, extra) {
  let o = await scoreSplit(hill, 'optimise', { save: path.join(runDir, 'optimise.json'), deadline: DL });
  if (o.judge_errors) return { decision: 'score_error', detail: `${o.judge_errors} judge error(s)`, o };
  if (stage === 1) {
    let better = isBetter(o, state.best);
    if (better && hill.confirm_gains) {
      const o2 = await scoreSplit(hill, 'optimise', { save: path.join(runDir, 'optimise-confirm.json'), deadline: DL });
      if (o2.judge_errors) return { decision: 'score_error', detail: `${o2.judge_errors} judge error(s)`, o };
      o = { ...o, score: Math.round(((o.score + o2.score) / 2) * 100) / 100, must_pass_failures: [...new Set([...o.must_pass_failures, ...o2.must_pass_failures])] };
      better = isBetter(o, state.best);
    }
    if (!better && holdsForHidden(o)) {
      // The hidden gap is what blocks the finish and this change holds the visible score: measure the hidden cases and
      // keep it if they rise. Only the keep or revert is shown to the climber, never which hidden case moved.
      const h = await scoreSplit(hill, 'holdout', { save: path.join(runDir, 'holdout.json'), deadline: DL });
      if (h.judge_errors) return { decision: 'score_error', detail: `${h.judge_errors} judge error(s) on hidden cases`, o };
      extra.holdout = h.score; extra.holdout_must_pass_failures = h.must_pass_failures;
      const b = state.best;
      if (h.score > b.holdout + hill.accept_margin && h.must_pass_failures.length <= (b.holdout_must_pass_failures?.length ?? 0)) return { decision: 'kept', detail: `hidden score ${b.holdout} -> ${h.score} with the visible score held`, o };
      return { decision: 'reverted', detail: 'visible score held but the hidden score did not rise', o };
    }
    return { decision: better ? 'kept' : 'reverted', detail: null, o };
  }
  const holds = o.score >= hill.metric.target && o.score >= state.best.optimise - (hill.council_tolerance ?? 0) && !o.must_pass_failures.length && secMet(o.secondary);
  if (!holds) return { decision: 'reverted', detail: 'tests regressed', o };
  const h = await scoreSplit(hill, 'holdout', { save: path.join(runDir, 'holdout.json'), deadline: DL });
  if (h.judge_errors) return { decision: 'score_error', detail: `${h.judge_errors} judge error(s) on hidden cases`, o };
  extra.holdout = h.score; extra.holdout_must_pass_failures = h.must_pass_failures;
  if (o.score - h.score > hill.metric.holdout_gap_max || h.must_pass_failures.length) return { decision: 'reverted', detail: `hidden check failed (gap ${Math.round((o.score - h.score) * 100) / 100}${h.must_pass_failures.length ? `, hidden must-pass failing: ${h.must_pass_failures.join(', ')}` : ''})`, o };
  // The work folder holds this tree now, so a render sees the candidate. Later judges are asked only once the earlier
  // ones pass (the panel was calibrated in full at the first council); a rise is confirmed by asking that judge again.
  const tag = path.basename(runDir), prev = state.council?.last;
  let c = await runCouncil(ctx, { tag, treeish: tree, lastOpt: o, full: !state.council?.calibrated });
  extra.council = c;
  if (c.render_error) return { decision: 'reverted', detail: `the render failed on this change: ${clip(c.render_error, 240)}`, o };
  const invalid = (v) => `judge gave no valid verdict: ${v.scores.filter((s) => s.score == null && !s.skipped).map((s) => `${s.judge}${s.error ? ` (${clip(s.error, 120)})` : ''}`).join(', ')}`;
  if (!c.valid) return { decision: 'score_error', detail: invalid(c), o };
  let better = councilBetter(c, prev);
  if (better && overBudget()) return { decision: 'budget', detail: `budget reached before the judges' rise could be confirmed: not kept (the edits are saved). Judges ${describeRound(c)}`, o };
  if (better) {
    c = await confirmRises(ctx, c, prev, { tag, treeish: tree, lastOpt: o });
    extra.council = c;
    if (!c.valid) return { decision: 'score_error', detail: `asked again: ${invalid(c)}`, o };
    better = councilBetter(c, prev);
  }
  return { decision: better ? 'kept' : 'reverted', detail: `judges ${describeRound(c)}${prev ? ` (before: ${describeRound(prev)})` : ''}${c.drift ? '; judge drift flagged' : ''}${c.control_missing ? '; the starting render was missing, so no hidden control' : ''}`, o };
}
// A stage 1 candidate that ties the visible score while the hidden gap is the only thing between it and the finish.
function holdsForHidden(o) {
  const b = state.best;
  return !!state.overfit && b.holdout != null && b.holdout_sha === b.sha && o.score >= b.optimise
    && o.must_pass_failures.length <= b.must_pass_failures.length && secMet(o.secondary) && !secBetter(b.secondary, o.secondary);
}

// ---------- main ----------
async function main() {
  acquire();
  for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => {
    killActive();
    if (liveGuard) { try { restoreGuard(liveGuard); } catch { /* recover() checks it */ } }
    state.status = 'stopped'; state.stop_reason = `interrupted by ${sig}`; // in_progress stays: the next start recovers it
    saveState(hill, state); release(); process.exit(130);
  });
  const recoverOnly = !!flag('recover-only');
  preflight({ recoverOnly });
  recover();
  if (recoverOnly) finish('stopped', 'recovered; not climbing (--recover-only)');
  if (!state.baseline) { say('measuring the baseline'); state = await measureBaseline(hill, state); }
  state.status = 'climbing'; delete state.stop_reason;
  state.history ??= []; state.streak ??= 0; state.attempts ??= 0; state.attempts_base ??= 0;
  startAttempts = state.attempts;
  saveState(hill, state);
  appendLedger(hill, { kind: 'run_start', pid: process.pid, deadline: deadline?.toISOString() ?? null, max_attempts: maxAttempts });
  board();
  let lastOpt = readJSON(P(hill, 'runs', state.best.attempt ? String(state.best.attempt) : 'baseline', 'optimise.json'), null) ?? readJSON(P(hill, 'runs', 'baseline', 'optimise.json'), null);
  for (;;) {
    // Completion first: a run that already met every bar is done, whatever the limits say.
    const timeUp = !!deadline && Date.now() >= deadline.getTime();
    let stage = 1;
    let s1;
    try { s1 = await stage1(!timeUp); } catch (e) {
      if (e instanceof DeadlineError) finish('deadline', `deadline reached while measuring the hidden check (tests at ${state.best.optimise})`);
      if (e instanceof ScoreError) finish('error', `could not score the hidden cases: ${e.message}`, 1);
      throw e;
    }
    if (s1 === 'saturated') finish('saturated', `every visible test passes but the hidden score is ${state.best.holdout} (gap over ${hill.metric.holdout_gap_max}${state.best.holdout_must_pass_failures?.length ? `, hidden must-pass failing: ${state.best.holdout_must_pass_failures.join(', ')}` : ''}). The visible tests cannot steer further: add cases that cover the hidden failures, re-freeze and climb again.`);
    if (s1 === 'met') {
      if (!hill.council?.length) finish('done', `target met: ${state.best.optimise} (hidden ${state.best.holdout}); no council configured`);
      if (noCouncil) finish('stage1_only', `stage 1 met: ${state.best.optimise} (hidden ${state.best.holdout}). The council was skipped (--no-council), so this hill is NOT done: run again without --no-council for the judges' review.`);
      if (state.council?.last_sha !== state.best.sha || !state.council.last?.valid) {
        if (timeUp) finish('deadline', `deadline reached before the judges reviewed ${state.best.sha.slice(0, 10)} (tests at ${state.best.optimise}, hidden ${state.best.holdout})`);
        if (overBudget()) budgetStop(' The judges have not reviewed the best version yet.');
        say('stage 1 met: asking the council');
        // The first council of a generation asks the full panel (calibration); a pass is confirmed by asking again.
        const full = !state.council?.calibrated, tag = `best-${state.best.attempt}`;
        let c;
        try {
          c = await runCouncil(ctx, { tag, treeish: state.best.sha, lastOpt, full });
          // A pass counts only once confirmed; with the budget spent it is not recorded (run again with more budget).
          if (c.valid && c.pass && overBudget()) budgetStop(' The judges passed the best version once; it needs a second ask to count.');
          if (c.valid && c.pass) c = await confirmRises(ctx, c, null, { tag, treeish: state.best.sha, lastOpt });
        } catch (e) {
          if (e instanceof DeadlineError) finish('deadline', `deadline reached while the judges reviewed ${state.best.sha.slice(0, 10)} (tests at ${state.best.optimise}, hidden ${state.best.holdout})`);
          throw e;
        }
        state.council = { ...(state.council ?? {}), rounds: (state.council?.rounds ?? 0) + 1, last: c, last_sha: state.best.sha, ...(full && c.valid ? { calibrated: true } : {}) };
        logRound(state, c, { decision: 'review' });
        appendLedger(hill, { kind: 'council', sha: state.best.sha, mode: c.mode, min: c.min, pass: c.pass, drift: c.drift, ...(c.control_missing ? { control_missing: true } : {}), render_error: c.render_error ?? null, scores: c.scores.map((s) => ({ judge: s.judge, score: s.score, lead: s.lead ?? null, control: s.control ?? null, ship: s.ship, skipped: !!s.skipped, error: s.error ?? null })) });
        saveState(hill, state); board();
        if (c.render_error) finish('error', `the render command failed on the best version ${state.best.sha.slice(0, 10)}: ${c.render_error}`, 1);
        if (!c.valid) finish('error', `a judge could not give a valid verdict: ${c.scores.filter((s) => s.score == null && !s.skipped).map((s) => `${s.judge} (${s.error})`).join(', ')}`, 1);
      }
      const c = state.council.last;
      if (c.pass) finish('done', `target met (${state.best.optimise}, hidden ${state.best.holdout}) and every judge scored every category >= ${hill.council_bar}${c.ref_mode ? ', ahead of every reference,' : ''} and would ship: ${describeRound(c)}`);
      stage = 2;
    } else if (s1 === 'unmeasured') finish('deadline', `deadline reached with the tests at ${state.best.optimise} but the hidden check not yet measured`);
    if (timeUp) finish('deadline', `deadline ${deadline.toISOString()} reached at ${state.best.optimise} (target ${hill.metric.target})`);
    const leftSec = deadline ? (deadline.getTime() - Date.now()) / 1000 : Infinity;
    if (leftSec < hill.stop.min_attempt_sec) finish('deadline', `less than ${hill.stop.min_attempt_sec}s left before the deadline: not starting another attempt (best ${state.best.optimise})`);
    if (maxAttempts && state.attempts - state.attempts_base >= maxAttempts) finish('max_attempts', `attempt cap ${maxAttempts} reached at ${state.best.optimise}`);
    if (overBudget()) budgetStop();
    if (state.streak >= hill.stop.plateau && state.switches >= hill.stop.min_switches) finish('stuck', `stuck at ${state.best.optimise} (target ${hill.metric.target}): ${state.streak} tries with no gain after ${state.switches} approach switches`);
    if ((state.consecutive_errors ?? 0) >= 3) finish('error', 'three attempts in a row ended in an error (check runs/<n>/agent/climber-log.txt and the score files: auth, network, CLI or scorer problem)', 1);
    if (once && state.attempts > startAttempts) finish('stopped', 'paused after one attempt (--once)');
    const o = await attempt(stage, lastOpt);
    if (o) lastOpt = o;
  }
}
main().catch((e) => {
  killActive();
  if (liveGuard) { try { restoreGuard(liveGuard); } catch { /* recover() checks it */ } }
  state.status = 'error'; state.stop_reason = clip(e.stack ?? e.message, 800); saveState(hill, state); release();
  out({ status: 'error', reason: e.message }); process.exit(1);
});
