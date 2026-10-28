#!/usr/bin/env node
// selftest.mjs: proves the judge and the flight check fail closed, using fake judges. No network, no real models.
//   node selftest.mjs        prints each check and exits 0 when all pass, 1 otherwise. Node 18+, no dependencies.
// Run it after changing judge.mjs or flight_check.mjs.
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { applyBar, artifactDigest, combineOrders, extractJson, independence, modelFamily, parseBar, parseClaudeReply, validateCompare, validateScore } from './judge.mjs';
import { audit, skeleton } from './flight_check.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok: Boolean(ok) }); process.stdout.write(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : `  ${detail}`}\n`); };

const DIMS = ['fit', 'depth', 'craft', 'money_moment', 'truth', 'delight'];
const verdict = (n) => ({
  scores: Object.fromEntries(DIMS.map((d) => [d, n])), evidence: Object.fromEntries(DIMS.map((d) => [d, `seen ${d}`])),
  top_fault: 'the hook', fix: 'cut the first second', would_keep: ['the CTA sheet'], summary: 'fine.',
});

// --- validation: out-of-range and incomplete replies are not verdicts -----------------------------------------
check('scores of 99 are rejected', validateScore(verdict(99)).length > 0);
check('scores of 0 are rejected', validateScore(verdict(0)).length > 0);
check('string scores are rejected', validateScore({ ...verdict(9), scores: { ...verdict(9).scores, fit: '9' } }).length > 0);
check('missing evidence is rejected', validateScore({ ...verdict(9), evidence: {} }).length > 0);
check('missing top_fault is rejected', validateScore({ ...verdict(9), top_fault: '' }).length > 0);
check('a complete 1-10 verdict is accepted', validateScore(verdict(9)).length === 0, JSON.stringify(validateScore(verdict(9))));
check('applyBar fails a 99 instead of passing it', applyBar(verdict(99).scores, parseBar('all>=8')).verdict === 'fail');
check('applyBar: truth 8 fails the default truth>=9 bar', applyBar({ ...verdict(9).scores, truth: 8 }, parseBar('')).verdict === 'fail');
check('applyBar: all 9 passes the default bar', applyBar(verdict(9).scores, parseBar('')).verdict === 'pass');
const cmp = { winner: 'A', margin: 'clear', why: 'x', dimensions: Object.fromEntries(DIMS.map((d) => [d, { winner: 'A', why: '' }])) };
check('compare: a valid reply is accepted', validateCompare(cmp).length === 0);
check('compare: winner "C" is rejected', validateCompare({ ...cmp, winner: 'C' }).length > 0);

// --- parsing: the verdict is the outer object, whatever wraps it ----------------------------------------------------
const cmpReply = `Here is my verdict.\n\`\`\`json\n${JSON.stringify(cmp, null, 2)}\n\`\`\`\nThat {is} all.`;
check('compare: nested dimension objects do not replace the verdict', validateCompare(extractJson(cmpReply, 'winner') ?? {}).length === 0, JSON.stringify(extractJson(cmpReply, 'winner')));
check('compare: the last top-level verdict wins', extractJson(`${JSON.stringify({ ...cmp, winner: 'B' })}\n${JSON.stringify(cmp)}`, 'winner')?.winner === 'A');
check('score: a nested key inside an outer object still found', extractJson('{"note": {"scores": {"fit": 9}}}', 'scores')?.scores?.fit === 9);
check('claude reply as one object', parseClaudeReply(JSON.stringify({ type: 'result', result: 'ok', model: 'm1' }))?.text === 'ok');
check('claude reply as an event array', (() => { const p = parseClaudeReply(JSON.stringify([{ type: 'system', subtype: 'init', model: 'claude-x' }, { type: 'assistant' }, { type: 'result', result: 'ok' }])); return p?.text === 'ok' && p.model === 'claude-x'; })());
check('claude reply as stream-json lines', parseClaudeReply(`${JSON.stringify({ type: 'system', subtype: 'init', model: 'claude-x' })}\n${JSON.stringify({ type: 'result', result: 'ok' })}\n`)?.text === 'ok');
check('claude reply with no result event is not a reply', parseClaudeReply(JSON.stringify([{ type: 'assistant' }])) === null);

// --- independence is computed, never assumed --------------------------------------------------------------------
check('model families', modelFamily('gpt-6.1-sol') === 'openai' && modelFamily('claude-opus-5-5') === 'anthropic' && modelFamily('UNKNOWN') === null);
check('codex judging claude work = different_family', independence('gpt-6.1-sol', 'codex', 'claude-opus-5-5').independence === 'different_family');
check('claude judging claude work = same family, fresh context', independence('claude-sonnet-5-5', 'claude', 'claude-opus-5-5').independence === 'same_family_fresh_context');
check('unknown author = unknown independence', independence('gpt-6.1-sol', 'codex', null).independence === 'unknown');

// --- digests: same bytes, same digest; any edit, new digest -------------------------------------------------------
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ambitious-selftest-'));
const art = path.join(tmp, 'page.md');
fs.writeFileSync(art, '# v1\n');
const d1 = artifactDigest([art]);
check('digest is stable', d1 === artifactDigest([art]));
fs.writeFileSync(art, '# v2\n');
check('digest changes when the artifact changes', d1 !== artifactDigest([art]));

// --- end to end with fake judges: fallback, fail closed, no overwrite -------------------------------------------
const bin = path.join(tmp, 'bin');
fs.mkdirSync(bin);
const valid = JSON.stringify(verdict(9));
const invalid = JSON.stringify(verdict(99));
fs.writeFileSync(path.join(bin, 'codex'), `#!/bin/sh
out=""; cwd=""; prev=""
for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; [ "$prev" = "-C" ] && cwd="$a"; prev="$a"; done
cat > /dev/null
echo "model: gpt-fake-1" >&2
case "$FAKE_CODEX" in
  valid) [ -n "$out" ] && printf '%s' '${valid}' > "$out" ;;
  invalid) [ -n "$out" ] && printf '%s' '${invalid}' > "$out" ;;
  flaky) if [ -f "${path.join(tmp, 'flaky-seen')}" ]; then [ -n "$out" ] && printf '%s' '${valid}' > "$out"; else touch "${path.join(tmp, 'flaky-seen')}"; echo "not json"; fi ;;
  cmp_first) printf '%s' '${JSON.stringify(cmp)}' > "$out" ;;
  cmp_content) if grep -rqs WINNER "$cwd/A"; then printf '%s' '${JSON.stringify(cmp)}' > "$out"; else printf '%s' '${JSON.stringify({ ...cmp, winner: 'B' })}' > "$out"; fi ;;
  *) echo "not json" ;;
esac
exit 0
`);
fs.writeFileSync(path.join(bin, 'claude'), `#!/bin/sh
if [ "$1" = "--help" ]; then echo "  --safe-mode   Start with all customizations disabled"; exit 0; fi
echo "$@" > "${path.join(tmp, 'claude-args.txt')}"
cat > /dev/null
case "$FAKE_CLAUDE" in
  valid) printf '%s' '${JSON.stringify({ result: valid, model: 'claude-fake-1' }).replace(/'/g, "'\\''")}' ;;
  *) printf '%s' '${JSON.stringify({ result: invalid, model: 'claude-fake-1' }).replace(/'/g, "'\\''")}' ;;
esac
`);
fs.chmodSync(path.join(bin, 'codex'), 0o755);
fs.chmodSync(path.join(bin, 'claude'), 0o755);

const runDir = path.join(tmp, 'run');
fs.mkdirSync(runDir);
fs.writeFileSync(path.join(runDir, 'flight.json'), JSON.stringify({ ...skeleton('selftest', 'standard', 'claude-opus-5-5') }, null, 2));
const judge = (env, extra = []) => {
  const r = spawnSync(process.execPath, [path.join(here, 'judge.mjs'), 'score', '--run', runDir, '--brief', 'Selftest brief', '--artifact', art, '--no-transcribe', '--timeout-sec', '60', ...extra],
    { encoding: 'utf8', env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, ...env } });
  try { return { code: r.status, ...JSON.parse(r.stdout) }; } catch { return { code: r.status, raw: r.stdout + r.stderr }; }
};

const a = judge({ FAKE_CODEX: 'valid', FAKE_CLAUDE: 'invalid' });
check('codex valid -> codex verdict, exit 0', a.code === 0 && a.kind === 'codex' && a.status === 'ok' && a.verdict === 'pass', JSON.stringify({ code: a.code, kind: a.kind, status: a.status, attempts: a.attempts, raw: a.raw }));
check('codex judging claude-authored work is labelled different_family', a.independence === 'different_family', a.independence);

const b = judge({ FAKE_CODEX: 'invalid', FAKE_CLAUDE: 'valid' });
check('codex out-of-range -> falls back to claude', b.code === 0 && b.kind === 'claude' && b.status === 'ok', JSON.stringify({ code: b.code, kind: b.kind, status: b.status, attempts: b.attempts }));
check('the failed codex attempt is reported', (b.attempts ?? []).some((x) => x.kind === 'codex' && x.status === 'invalid'));
check('a failed attempt keeps the end of the reply for diagnosis', (b.attempts ?? []).some((x) => x.kind === 'codex' && String(x.reply_tail ?? '').includes('"scores"')));
check('claude fallback is labelled same family, fresh context', b.independence === 'same_family_fresh_context', b.independence);
const claudeArgs = (() => { try { return fs.readFileSync(path.join(tmp, 'claude-args.txt'), 'utf8'); } catch { return ''; } })();
check('claude fallback runs with --safe-mode when the CLI has it (no owner CLAUDE.md, skills or hooks)', /--safe-mode/.test(claudeArgs) && /safe-mode/.test(b.label ?? ''), JSON.stringify({ claudeArgs, label: b.label }));

const c = judge({ FAKE_CODEX: 'garbage', FAKE_CLAUDE: 'invalid' });
check('both judges fail -> no verdict, exit 3', c.code === 3 && c.verdict === null && c.status === 'invalid', JSON.stringify({ code: c.code, status: c.status, verdict: c.verdict }));

const fl = judge({ FAKE_CODEX: 'flaky', FAKE_CLAUDE: 'invalid' }, ['--judge', 'codex']);
check('an unreadable reply from a clean exit is retried once, and the retry can pass', fl.code === 0 && fl.status === 'ok' && (fl.attempts ?? []).filter((x) => x.kind === 'codex').length === 2 && fl.attempts[0].status === 'no_verdict', JSON.stringify({ code: fl.code, status: fl.status, attempts: (fl.attempts ?? []).map((x) => `${x.kind}:${x.try}:${x.status}`) }));
check('out-of-range scores are not retried', (b.attempts ?? []).filter((x) => x.kind === 'codex').length === 1, JSON.stringify((b.attempts ?? []).map((x) => `${x.kind}:${x.status}`)));

const d = judge({ FAKE_CODEX: 'valid' }, ['--round', '1']);
const e = judge({ FAKE_CODEX: 'valid' }, ['--round', '1']);
check('same round twice -> two files, nothing overwritten', d.file && e.file && d.file !== e.file && fs.existsSync(path.join(runDir, d.file)) && fs.existsSync(path.join(runDir, e.file)), `${d.file} ${e.file}`);
const f = judge({ FAKE_CODEX: 'valid' });
check('round defaults to the next round', f.round > 1, String(f.round));
const g = judge({ FAKE_CODEX: 'valid' }, ['--concept']);
check('--concept is logged as round 0, stage concept', g.code === 0 && g.round === 0 && g.stage === 'concept' && /judge-0-/.test(g.file ?? ''), JSON.stringify({ r: g.round, s: g.stage, f: g.file }));

// --- compare: both blind orders by default; a winner only when they agree -----------------------------------------
const r = (shown, input, status = 'ok') => ({ status, winner_shown: shown, winner_input: input, dimensions_input: { fit: { winner: input } } });
check('combine: agreeing orders name the winner', combineOrders(r('A', 'a'), r('B', 'a')).winner_input === 'a');
check('combine: same shown slot twice is position bias, no winner', (() => { const c = combineOrders(r('B', 'b'), r('B', 'a')); return c.winner_input === 'no_consistent_winner' && c.position_bias; })());
check('combine: one failed order means no verdict', (() => { const c = combineOrders(r('A', 'a'), r(null, null, 'invalid')); return c.status === 'invalid' && c.winner_input === null; })());
const candA = path.join(tmp, 'cand-a.md'); const candB = path.join(tmp, 'cand-b.md');
fs.writeFileSync(candA, 'WINNER copy\n'); fs.writeFileSync(candB, 'plain copy\n');
const compareRun = (env, extra = []) => {
  const outFile = path.join(tmp, `cmp-${Math.random().toString(36).slice(2)}.json`);
  const res = spawnSync(process.execPath, [path.join(here, 'judge.mjs'), 'compare', '--brief', 'Selftest brief', '--a', candA, '--b', candB, '--out', outFile, '--judge', 'codex', '--no-transcribe', '--timeout-sec', '60', ...extra],
    { encoding: 'utf8', env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, ...env } });
  try { return { code: res.status, ...JSON.parse(res.stdout) }; } catch { return { code: res.status, raw: res.stdout + res.stderr }; }
};
const biased = compareRun({ FAKE_CODEX: 'cmp_first' });
check('compare end to end: a judge that always picks A gives no winner', biased.code === 0 && biased.orders_run === 2 && biased.winner_input === 'no_consistent_winner' && biased.position_bias === true, JSON.stringify({ code: biased.code, w: biased.winner_input, raw: biased.raw }));
const real = compareRun({ FAKE_CODEX: 'cmp_content' });
check('compare end to end: a judge that follows the content wins in both orders', real.code === 0 && real.winner_input === 'a' && real.consistent === true, JSON.stringify({ code: real.code, w: real.winner_input }));
const one = compareRun({ FAKE_CODEX: 'cmp_first' }, ['--swap']);
check('compare --swap still runs a single order', one.code === 0 && one.orders_run === undefined && one.swapped === true && one.winner_input === 'b', JSON.stringify({ w: one.winner_input, s: one.swapped }));

// --- flight check: final fail must be owned; max needs two passes on the same version -----------------------------
const base = {
  ...skeleton('audit', 'standard', 'claude-opus-5-5'),
  altitude: { goal_behind_goal: 'g', verbs: 'v', money_moment: 'm' },
  brief: { top_pro_move: 't', rawest_material: 'r', instruments: ['ffprobe'], outside_proof: 'o' },
  targets: [{ name: 'hook', target: '<2s', measured: '1.4s', met: true, evidence: 'ffprobe' }],
  crew: [{ field: 'copy', method: 'x', changed: 'y' }, { field: 'short seller', method: 'bear case', changed: 'z', red_team: true }],
  deliverables: [art], money_move: { status: 'none_honest', action: '', yes_does: '' }, unasked_for: ['u'], sweep: [{ finding: 'f', source: 's' }],
};
const j = (verdictWord, kind, digest, model) => ({ round: 1, kind, model, status: 'ok', verdict: verdictWord, independence: 'different_family', artifact_digest: digest });
check('final verdict fail without a "bar:" gap is a problem', audit({ ...base, judges: [j('fail', 'codex', 'd1', 'gpt')] }, tmp).problems.some((p) => p.includes('last judge verdict is fail')));
check('final verdict fail owned in gaps passes', audit({ ...base, judges: [j('fail', 'codex', 'd1', 'gpt')], gaps: ['bar: craft 7 < 8 after 3 rounds'] }, tmp).problems.length === 0);
check('a gap only owns the check it is labelled for: "bar: ...judge..." does not excuse max', audit({ ...base, tier: 'max', judges: [j('fail', 'codex', 'd1', 'gpt')], gaps: ['bar: the judge said craft 7 after 5 rounds'] }, tmp).problems.some((p) => p.includes('max tier')));
check('a target gap must start with the target name', (() => { const t = { ...base, targets: [{ name: 'hook', target: '<2s', measured: '' }] }; return audit({ ...t, judges: [j('pass', 'codex', 'd1', 'gpt')], gaps: ['the hook was not measured'] }, tmp).problems.some((p) => p.includes('target "hook"')) && audit({ ...t, judges: [j('pass', 'codex', 'd1', 'gpt')], gaps: ['hook: no render was possible'] }, tmp).problems.length === 0; })());
check('a concept check alone is not a verdict on the work', audit({ ...base, judges: [{ ...j('pass', 'codex', 'd1', 'gpt'), stage: 'concept', round: 0 }] }, tmp).problems.some((p) => p.includes('no outside model verdict')));
check('standard with a passing judge passes', audit({ ...base, judges: [j('pass', 'codex', 'd1', 'gpt')] }, tmp).problems.length === 0);
const max = { ...base, tier: 'max' };
check('max: two passes on the same version passes', audit({ ...max, judges: [j('pass', 'codex', 'd2', 'gpt'), j('pass', 'claude', 'd2', 'claude-x')] }, tmp).problems.length === 0);
check('max: two passes on different versions fails', audit({ ...max, judges: [j('pass', 'codex', 'd1', 'gpt'), j('pass', 'claude', 'd2', 'claude-x')] }, tmp).problems.some((p) => p.includes('max tier')));
check('max: one judge passing twice fails', audit({ ...max, judges: [j('pass', 'codex', 'd2', 'gpt'), j('pass', 'codex', 'd2', 'gpt')] }, tmp).problems.some((p) => p.includes('max tier')));

const lean = { ...base, tier: 'lean', brief: { top_pro_move: '', rawest_material: 'the export', instruments: [], outside_proof: '' }, judges: [j('pass', 'codex', 'd1', 'gpt')] };
const leanAudit = audit(lean, tmp);
check('lean: a one-note brief (rawest material only) passes, the rest are warnings', leanAudit.problems.length === 0 && leanAudit.warnings.some((w) => w.includes('top_pro_move')), JSON.stringify(leanAudit.problems));
check('lean: an empty rawest_material is still a problem', audit({ ...lean, brief: { ...lean.brief, rawest_material: '' } }, tmp).problems.some((p) => p.includes('rawest_material')));

// --- the scripts run from a folder whose name has a space (import.meta.url has %20 there) -------------------------
const spaced = path.join(tmp, 'skills dir');
fs.mkdirSync(spaced);
for (const f of ['judge.mjs', 'flight_check.mjs']) fs.copyFileSync(path.join(here, f), path.join(spaced, f));
const spacedRun = path.join(tmp, 'spaced run');
const sp = spawnSync(process.execPath, [path.join(spaced, 'flight_check.mjs'), 'init', spacedRun, '--task', 'space test', '--tier', 'lean'], { encoding: 'utf8' });
check('flight_check runs from a path with a space', sp.status === 0 && fs.existsSync(path.join(spacedRun, 'flight.json')), `exit ${sp.status} ${sp.stdout}${sp.stderr}`.slice(0, 300));
const sj = spawnSync(process.execPath, [path.join(spaced, 'judge.mjs')], { encoding: 'utf8' });
check('judge.mjs runs from a path with a space', sj.status === 1 && /usage/.test(sj.stdout), `exit ${sj.status} ${sj.stdout}`.slice(0, 200));

const judged = path.join(tmp, 'judged.md');
fs.writeFileSync(judged, 'final copy\n');
const fresh = { ...j('pass', 'codex', artifactDigest([judged]), 'gpt'), artifacts: [judged] };
check('a verdict on the current version passes', audit({ ...base, judges: [fresh] }, tmp).problems.length === 0);
fs.writeFileSync(judged, 'edited after the judge\n');
check('editing the work after the verdict makes it stale', audit({ ...base, judges: [fresh] }, tmp).problems.some((p) => p.includes('changed after the last judge')));

fs.rmSync(tmp, { recursive: true, force: true });
const failed = results.filter((r) => !r.ok);
process.stdout.write(`\n${results.length - failed.length}/${results.length} passed\n`);
process.exit(failed.length ? 1 : 0);
