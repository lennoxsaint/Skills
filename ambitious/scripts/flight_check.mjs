#!/usr/bin/env node
// flight_check.mjs: the flight log for an /ambitious run, and the check that it landed honestly.
//
//   node flight_check.mjs init   <run-dir> --task "<one line>" [--tier lean|standard|max] [--author-model <your model id>]
//   node flight_check.mjs status <run-dir> in_flight|awaiting|abandoned [--reason "<why>"]
//   node flight_check.mjs check  <run-dir>
//
// init writes <run-dir>/flight.json and prints the run folder (so other tools can find the run).
// check passes only when the brief, targets with measurements, an outside judge, a red team, the deliverables
// and the money move are all recorded, or when each miss is written down as a gap. A final judge verdict of "fail"
// must be owned in gaps ("bar: ..."), and a Max run needs two different judges passing the same final version
// (same artifact digest). On pass it marks the run "landed". It never grades the work itself: that is the judge's job.
// JSON on stdout. Exit 0 on pass/ok, 2 when the check finds problems, 1 on usage errors. Node 18+, no dependencies.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { artifactDigest } from './judge.mjs';

const TIERS = ['lean', 'standard', 'max'];
const STATUSES = ['in_flight', 'awaiting', 'landed', 'abandoned'];
const MONEY = ['prepared', 'none_honest', 'not_applicable'];
const MODEL_JUDGES = ['codex', 'claude', 'other_model'];

// writeSync, not process.stdout.write: a pipe write is async and process.exit would cut a long reply short.
const out = (obj, code = 0) => { fs.writeSync(1, JSON.stringify(obj, null, 2) + '\n'); process.exit(code); };
const argValue = (args, flag, fallback = null) => { const i = args.indexOf(flag); return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback; };
const blank = (v) => v === null || v === undefined || (typeof v === 'string' && v.trim() === '') || (Array.isArray(v) && v.length === 0);
const now = () => new Date().toISOString();
const expand = (p) => (p.startsWith('~/') ? path.join(os.homedir(), p.slice(2)) : p);

export function skeleton(task, tier, authorModel = null) {
  return {
    version: 1,
    task,
    tier,
    author_model: authorModel ?? '', // the model doing the work; judge.mjs uses it to report how independent each judge is
    status: 'in_flight',
    started_at: now(),
    altitude: { goal_behind_goal: '', verbs: '', money_moment: '' },
    sweep: [],          // { finding, source }
    questions: [],      // { q, answer, assumed }
    brief: { top_pro_move: '', rawest_material: '', instruments: [], outside_proof: '' },
    targets: [],        // { name, target, measured, met, evidence }
    crew: [],           // { field, method, changed, red_team }
    deliverables: [],   // paths or URLs
    judges: [],         // judge.mjs appends { round, kind, model, file, status, verdict, scores, top_fault, independence, artifact_digest }; tool checks: { kind: "tool", command, result }
    money_move: { status: '', action: '', yes_does: '' },
    unasked_for: [],
    gaps: [],           // honest misses, e.g. "judge: codex unavailable – ..." or "target hook: not measured – ..."
    follow_ups: [],     // { what, when } for anything only measurable after the run
  };
}

function load(dir) {
  const file = path.join(dir, 'flight.json');
  if (!fs.existsSync(file)) out({ status: 'error', error: `no flight.json in ${dir}; run init first` }, 1);
  try { return { file, flight: JSON.parse(fs.readFileSync(file, 'utf8')) }; } catch (e) { out({ status: 'error', error: `flight.json is not valid JSON: ${e.message}` }, 1); }
}

const save = (file, flight) => fs.writeFileSync(file, JSON.stringify(flight, null, 2) + '\n');

export function audit(flight, dir) {
  const problems = [];
  const warnings = [];
  const gaps = (flight.gaps ?? []).map((g) => String(g).toLowerCase().trim());
  // A gap owns a check only when it starts with that check's label ("bar:", "judge:", "<target name>:" or
  // "target <target name>:"). Matching anywhere in the text let "bar: the judge said craft 7" silence the judge checks too.
  const gapFor = (word) => { const w = String(word).toLowerCase().trim(); return gaps.some((g) => g.startsWith(`${w}:`) || g.startsWith(`target ${w}:`)); };

  if (flight.status === 'abandoned') {
    if (blank(flight.gaps)) problems.push('abandoned runs need the reason in gaps');
    return { problems, warnings };
  }
  if (blank(flight.task)) problems.push('task is empty');
  if (!TIERS.includes(flight.tier)) problems.push(`tier must be one of ${TIERS.join(', ')}`);

  const alt = flight.altitude ?? {};
  if (blank(alt.goal_behind_goal)) problems.push('altitude.goal_behind_goal is empty (step 2)');
  if (blank(alt.money_moment)) problems.push('altitude.money_moment is empty (step 2): name the decision this work exists to cause');
  if (blank(alt.verbs)) warnings.push('altitude.verbs is empty: the task restated as verbs is how the crew gets picked');

  const brief = flight.brief ?? {};
  // Lean writes a one-note brief: the rawest material is the one question it can't skip; the rest are warnings.
  for (const key of ['top_pro_move', 'rawest_material', 'instruments', 'outside_proof']) {
    if (!blank(brief[key])) continue;
    const msg = `brief.${key} is empty (step 5, Felix's four questions)`;
    if (flight.tier === 'lean' && key !== 'rawest_material') warnings.push(msg); else problems.push(msg);
  }
  if (blank(flight.sweep)) warnings.push('sweep is empty: no proactive findings recorded (step 3)');

  const targets = flight.targets ?? [];
  if (targets.length === 0) problems.push('no stretch targets (step 5)');
  if (flight.tier !== 'lean' && targets.length === 1) warnings.push('only one stretch target');
  for (const t of targets) {
    const name = t.name || t.target || '(unnamed)';
    if (blank(t.target)) problems.push(`target "${name}" has no target value`);
    const measured = !blank(t.measured);
    if (!measured && !gapFor(name)) problems.push(`target "${name}" has no measurement and no gap explaining why (add "${name}: <why>" to gaps)`);
    if (measured && typeof t.met !== 'boolean') problems.push(`target "${name}" is measured but met is not true/false`);
    if (measured && blank(t.evidence)) warnings.push(`target "${name}" has no evidence (command, file or source)`);
  }

  const crew = flight.crew ?? [];
  if (!crew.some((c) => c && c.red_team === true)) problems.push('no red team in crew (step 6): add one entry with "red_team": true and the method you ran');
  if (flight.tier !== 'lean' && crew.filter((c) => c && !c.red_team).length === 0) warnings.push('no crew fields besides the red team (step 6)');
  for (const c of crew) if (c && blank(c.method)) problems.push(`crew member "${c.field ?? '?'}" has no method: a field without a method is role-play`);

  const deliverables = flight.deliverables ?? [];
  if (deliverables.length === 0) problems.push('no deliverables listed');
  for (const d of deliverables) {
    const p = String(d);
    if (/^https?:\/\//.test(p)) continue;
    const abs = path.isAbsolute(expand(p)) ? expand(p) : path.resolve(dir, p);
    if (!fs.existsSync(abs)) problems.push(`deliverable not found on disk: ${p}`);
  }

  const judges = flight.judges ?? [];
  if (judges.some((j) => j && /self/i.test(String(j.kind)))) problems.push('a self-judgement is in judges: remove it; only tools and other models count');
  // Concept checks (judge.mjs --concept, round 0) judge a plan before the build; only verdicts on the work itself count here.
  const modelJudges = judges.filter((j) => j && MODEL_JUDGES.includes(j.kind) && j.stage !== 'concept');
  const okModel = modelJudges.filter((j) => j.status === 'ok');
  const tools = judges.filter((j) => j && j.kind === 'tool');
  if (flight.tier === 'lean') {
    if (okModel.length + tools.length === 0 && !gapFor('judge')) problems.push('no outside check: run a tool check or judge.mjs, or record "judge: ..." in gaps');
  } else if (okModel.length === 0 && !gapFor('judge')) {
    problems.push('no outside model verdict (step 9): run scripts/judge.mjs score, or record "judge: <why none could run>" in gaps');
  }
  if (flight.tier !== 'lean' && tools.length === 0) warnings.push('no tool checks recorded: measure with tools before asking a model');
  for (const j of judges) {
    if (j && j.file && !fs.existsSync(path.resolve(dir, j.file))) problems.push(`judge file missing: ${j.file}`);
  }
  const last = okModel[okModel.length - 1];
  if (last?.artifact_digest && Array.isArray(last.artifacts) && last.artifacts.length && !gapFor('judge')) {
    const now = artifactDigest(last.artifacts);
    if (now !== last.artifact_digest) problems.push(`the work changed after the last judge verdict (digest ${last.artifact_digest} -> ${now}): judge the final version, or record "judge: final edits not re-judged - <why>" in gaps`);
  }
  if (last && last.verdict === 'fail') {
    if (!gapFor('bar')) problems.push(`the last judge verdict is fail (top fault: ${last.top_fault ?? 'see file'}): fix it and judge again, or own it in gaps as "bar: <what missed and why you stopped>"`);
    else warnings.push('the last judge verdict is fail: say so in the first line of the report');
  }
  if (flight.tier === 'max' && !gapFor('judge')) {
    const finalDigest = last?.artifact_digest;
    const passing = okModel.filter((j) => j.verdict === 'pass' && (!finalDigest || j.artifact_digest === finalDigest));
    if (new Set(passing.map((j) => `${j.kind}:${j.model}`)).size < 2) problems.push('max tier needs two different judges to pass the same final version (same artifact_digest)');
  }
  if (okModel.length && !okModel.some((j) => j.independence === 'different_family')) {
    warnings.push(okModel.some((j) => j.independence === 'unknown' || !j.independence)
      ? 'judge independence unverified: set author_model (init --author-model) so judge.mjs can tell whether the judge is a different model family'
      : 'every judge is from the author\'s model family (fresh context, shared blind spots): say so in the report');
  }

  const money = flight.money_move ?? {};
  if (!MONEY.includes(money.status)) problems.push(`money_move.status must be one of ${MONEY.join(', ')}`);
  if (money.status === 'prepared' && (blank(money.action) || blank(money.yes_does))) problems.push('money_move is prepared but action or yes_does is empty: say exactly what "yes" will do');

  if (blank(flight.unasked_for)) warnings.push('unasked_for is empty: nothing beyond the literal ask was delivered (delight pass, step 10)');
  return { problems, warnings };
}

function main() {
  const [cmd, dirArg, ...rest] = process.argv.slice(2);
  if (!cmd || !dirArg) out({ status: 'usage', usage: 'flight_check.mjs init|status|check <run-dir> (see the header of this file)' }, 1);
  const dir = path.resolve(expand(dirArg));

  if (cmd === 'init') {
    const task = argValue(rest, '--task', '');
    const tier = (argValue(rest, '--tier', 'standard') || 'standard').toLowerCase();
    const authorModel = argValue(rest, '--author-model') ?? process.env.AMBITIOUS_AUTHOR_MODEL ?? null;
    if (!TIERS.includes(tier)) out({ status: 'error', error: `tier must be one of ${TIERS.join(', ')}` }, 1);
    fs.mkdirSync(dir, { recursive: true });
    const file = path.join(dir, 'flight.json');
    if (fs.existsSync(file)) out({ status: 'exists', run: dir, note: 'flight.json already exists; continuing that run' });
    save(file, skeleton(task, tier, authorModel));
    fs.writeSync(1, `AMBITIOUS_RUN=${dir}\n`);
    out({ status: 'ok', run: dir, file, next: 'fill altitude, sweep, brief, targets and crew as you go; run check before reporting' });
  }

  if (cmd === 'status') {
    const { file, flight } = load(dir);
    const next = rest[0];
    if (!STATUSES.includes(next) || next === 'landed') out({ status: 'error', error: 'status must be in_flight, awaiting or abandoned (landed is set by check)' }, 1);
    flight.status = next;
    const reason = argValue(rest, '--reason');
    if (next === 'abandoned' && reason) flight.gaps = [...(flight.gaps ?? []), `abandoned: ${reason}`];
    flight[`${next}_at`] = now();
    save(file, flight);
    out({ status: 'ok', run: dir, flight_status: next });
  }

  if (cmd === 'check') {
    const { file, flight } = load(dir);
    const { problems, warnings } = audit(flight, dir);
    if (problems.length) out({ status: 'fail', run: dir, problems, warnings, note: 'fix each problem, or record an honest gap for it, then check again' }, 2);
    if (flight.status !== 'abandoned') { flight.status = 'landed'; flight.landed_at = now(); save(file, flight); }
    out({ status: 'pass', run: dir, flight_status: flight.status, warnings });
  }

  out({ status: 'usage', usage: 'flight_check.mjs init|status|check <run-dir>' }, 1);
}

// pathToFileURL, not a hand-built file:// string: a folder name with a space is %20 in import.meta.url.
if (process.argv[1] && import.meta.url === pathToFileURL(fs.realpathSync(process.argv[1])).href) main();
