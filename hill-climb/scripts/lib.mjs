// hill-climb shared library. Node 18+, no dependencies.
// A "hill" is a folder holding one climb: hill.json (frozen spec), cases/, exemplars/, scorer/,
// lock.json, state.json, ledger.jsonl and runs/. The work folder the climber edits lives elsewhere.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawn, spawnSync } from 'node:child_process';

export const HOME = os.homedir();
export const now = () => new Date().toISOString();
export const sha256 = (s) => crypto.createHash('sha256').update(s).digest('hex');
export const clip = (s, n) => { s = typeof s === 'string' ? s : JSON.stringify(s); return s == null ? '' : s.length > n ? `${s.slice(0, n)}… [${s.length - n} more chars]` : s; };
export const sleepSync = (sec) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, Math.max(0, sec * 1000));
export const nonce = () => crypto.randomBytes(6).toString('hex');
// The real format of an image file from its first bytes (an extension proves nothing): png, jpeg, webp or null.
export function imageKind(buf) {
  if (buf.length >= 8 && buf.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) return 'png';
  if (buf.length >= 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return 'jpeg';
  if (buf.length >= 12 && buf.toString('latin1', 0, 4) === 'RIFF' && buf.toString('latin1', 8, 12) === 'WEBP') return 'webp';
  return null;
}

export function readJSON(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) {
    if (fallback !== undefined) return fallback;
    throw new Error(`cannot read ${p}: ${e.message}`);
  }
}
// Atomic write: a kill mid-write never leaves half a state file.
export function writeJSON(p, v) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const tmp = `${p}.tmp${process.pid}`;
  fs.writeFileSync(tmp, `${JSON.stringify(v, null, 2)}\n`);
  fs.renameSync(tmp, p);
}

export const DEFAULTS = {
  repeats: 1,
  pass_rule: 'all',
  accept_margin: 0,
  confirm_gains: false,
  holdout_every: 3,
  concurrency: 4,
  stop: { deadline: null, plateau: 10, switch_every: 4, min_switches: 2, max_attempts: null, min_attempt_sec: 300 },
  council_bar: 9,
  checkpoint: true,
  sandbox: 'auto',
  scope_ignore: ['node_modules/**', '**/node_modules/**', '**/.cache/**', '**/__pycache__/**', '.next/**', '.turbo/**', 'coverage/**', '**/*.tsbuildinfo', '**/.DS_Store'],
};

export function loadHill(dir) {
  const d = path.resolve(dir);
  const hill = readJSON(path.join(d, 'hill.json'));
  hill._dir = d;
  for (const [k, v] of Object.entries(DEFAULTS)) {
    if (hill[k] === undefined) hill[k] = v;
    else if (v && typeof v === 'object' && !Array.isArray(v)) hill[k] = { ...v, ...hill[k] };
  }
  hill.metric = { direction: 'up', holdout_gap_max: 5, ...(hill.metric ?? {}) };
  return hill;
}
export const P = (hill, ...p) => path.join(hill._dir, ...p);

// Numeric and enum settings that would silently change what a score means. Empty list = sound.
export function checkSettings(hill) {
  const bad = [];
  const int = (v, lo, hi = Infinity) => Number.isInteger(v) && v >= lo && v <= hi;
  const num = (v, lo, hi = Infinity) => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
  if (!int(hill.repeats, 1, 50)) bad.push('repeats must be a whole number from 1 to 50');
  if (!['all', 'majority'].includes(hill.pass_rule)) bad.push('pass_rule must be "all" or "majority"');
  if (!num(hill.accept_margin, 0, 100)) bad.push('accept_margin must be 0-100');
  if (typeof hill.confirm_gains !== 'boolean') bad.push('confirm_gains must be true or false');
  if (!int(hill.holdout_every, 1)) bad.push('holdout_every must be a whole number of 1 or more');
  if (!int(hill.concurrency, 1, 64)) bad.push('concurrency must be 1-64');
  if (hill.produce?.concurrency != null && !int(hill.produce.concurrency, 1, 64)) bad.push('produce.concurrency must be 1-64');
  if (!num(hill.metric?.target, 0, 100)) bad.push('metric.target must be a number from 0 to 100');
  if (!num(hill.metric?.holdout_gap_max, 0, 100)) bad.push('metric.holdout_gap_max must be 0-100');
  if (!num(hill.council_bar, 1, 10) || !Number.isInteger(hill.council_bar * 2)) bad.push('council_bar must be 1-10 in whole or half points (e.g. 9 or 9.5)');
  if (hill.council_tolerance != null && !num(hill.council_tolerance, 0, 100)) bad.push('council_tolerance must be 0-100');
  const s = hill.stop ?? {};
  if (!int(s.plateau, 1)) bad.push('stop.plateau must be a whole number of 1 or more');
  if (!int(s.switch_every, 1)) bad.push('stop.switch_every must be a whole number of 1 or more');
  if (!int(s.min_switches, 0)) bad.push('stop.min_switches must be a whole number of 0 or more');
  if (s.max_attempts != null && !int(s.max_attempts, 1)) bad.push('stop.max_attempts must be null or 1+');
  if (!num(s.min_attempt_sec, 0)) bad.push('stop.min_attempt_sec must be 0 or more');
  if (s.deadline != null && Number.isNaN(new Date(s.deadline).getTime())) bad.push('stop.deadline is not a date');
  if (s.budget_usd != null && !num(s.budget_usd, 0.01)) bad.push('stop.budget_usd must be a positive number of dollars');
  for (const [k, spec] of [['produce', hill.produce], ['scorer', hill.scorer], ['climber', hill.climber], ['judge', hill.judge], ...(hill.council ?? []).map((c, i) => [`council[${i}]`, c])]) {
    if (spec?.timeout_sec != null && !num(spec.timeout_sec, 1)) bad.push(`${k}.timeout_sec must be a positive number`);
  }
  if (!['auto', 'off'].includes(hill.sandbox)) bad.push('sandbox must be "auto" or "off"');
  if (!Array.isArray(hill.scope_ignore)) bad.push('scope_ignore must be a list of globs');
  for (const k of ['sandbox_write', 'sandbox_allow_read']) {
    const v = hill[k];
    if (v != null && (!Array.isArray(v) || v.some((p) => typeof p !== 'string' || !p.trim()))) bad.push(`${k} must be a list of paths`);
    else if (v?.some((p) => ['/', HOME].includes(path.resolve(p.replace(/^~(?=\/|$)/, HOME))))) bad.push(`${k} cannot open the whole disk or home folder`);
  }
  return bad;
}

// Hill files are read without following symlinks: a link could point the key (or a judge) at any file on disk.
export function listJSON(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort().map((f) => {
    const p = path.join(dir, f);
    if (fs.lstatSync(p).isSymbolicLink()) throw new Error(`symlinks are not allowed in the hill folder: ${p}`);
    return { ...readJSON(p), _file: p };
  });
}
export const listCases = (hill, split) => listJSON(P(hill, 'cases', split));
export const listExemplars = (hill) => listJSON(P(hill, 'exemplars'));

// ---------- state + ledger ----------
export const loadState = (hill) => readJSON(P(hill, 'state.json'), { status: 'draft', attempts: 0, kept: 0, streak: 0, switches: 0, stage: 1, history: [] });
export const saveState = (hill, s) => writeJSON(P(hill, 'state.json'), s);

function entryHash(e) { const { hash, ...rest } = e; return sha256(JSON.stringify(rest)); }
export function readLedger(hill) {
  const f = P(hill, 'ledger.jsonl');
  if (!fs.existsSync(f)) return [];
  return fs.readFileSync(f, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l));
}
// Each line carries the hash of the line before it, so an edited or deleted line breaks the chain.
export function appendLedger(hill, entry) {
  const lines = readLedger(hill);
  const e = { ...entry, at: now(), prev: lines.at(-1)?.hash ?? 'genesis' };
  e.hash = entryHash(e);
  fs.appendFileSync(P(hill, 'ledger.jsonl'), `${JSON.stringify(e)}\n`);
  return e;
}
export function verifyLedger(hill) {
  let lines;
  try { lines = readLedger(hill); } catch { return { ok: false, lines: null, broken_at: 'unparseable line' }; }
  let prev = 'genesis';
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].prev !== prev || entryHash(lines[i]) !== lines[i].hash) return { ok: false, lines: lines.length, broken_at: i + 1 };
    prev = lines[i].hash;
  }
  return { ok: true, lines: lines.length };
}

// ---------- one writer per hill ----------
// run.lock is held by the runner for a whole climb and by freeze, brief and approve while they change the key or state.
// It is written to a temp file and hard-linked into place, so it never exists half-written. A stale lock (its process
// gone, or replaced by another with the same pid) is removed only under a reclaim mutex, and only if it is still the
// same stale lock. Returns { ok: true, release } or { ok: false, reason }.
function lockHolderAlive(l) {
  if (!l || l.host !== os.hostname() || l.pid === process.pid) return false;
  return l.started ? processStart(l.pid) === l.started : /(climb|hill)\.mjs/.test(processCommand(l.pid));
}
export function takeRunLock(hill, { label = 'runner' } = {}) {
  const runLock = P(hill, 'run.lock');
  const lockAge = () => { try { return Date.now() - fs.statSync(runLock).mtimeMs; } catch { return 0; } };
  fs.mkdirSync(path.dirname(runLock), { recursive: true });
  const tmp = `${runLock}.${process.pid}`;
  const mine = { pid: process.pid, host: os.hostname(), started: processStart(process.pid), at: now(), label };
  fs.writeFileSync(tmp, JSON.stringify(mine));
  const release = () => { try { const l = readJSON(runLock, null); if (l?.pid === process.pid && l?.host === os.hostname()) fs.rmSync(runLock); } catch { /* gone */ } };
  try {
    for (let k = 0; k < 20; k++) {
      try { fs.linkSync(tmp, runLock); return { ok: true, release }; } catch (e) { if (e.code !== 'EEXIST') throw e; }
      const l = readJSON(runLock, null);
      if (l?.pid === process.pid && l?.host === os.hostname()) return { ok: true, release: () => {} }; // already ours (re-entrant)
      if (lockHolderAlive(l)) return { ok: false, reason: `${l.label ?? 'a runner'} is already running as pid ${l.pid} since ${l.at}` };
      if (l && l.host !== os.hostname()) return { ok: false, reason: `locked by ${l.host} pid ${l.pid}; delete ${runLock} only if that run is gone` };
      const mutex = `${runLock}.reclaim`;
      try { fs.mkdirSync(mutex); } catch {
        try { if (Date.now() - fs.statSync(mutex).mtimeMs > 30000) fs.rmSync(mutex, { recursive: true, force: true }); } catch { /* gone */ }
        sleepSync(0.2); continue;
      }
      try {
        const again = readJSON(runLock, null);
        const sameStale = again ? JSON.stringify(again) === JSON.stringify(l) && !lockHolderAlive(again) : lockAge() > 60000;
        if (sameStale) fs.rmSync(runLock, { force: true });
        else sleepSync(0.2);
      } finally { fs.rmSync(mutex, { recursive: true, force: true }); }
    }
  } finally { fs.rmSync(tmp, { force: true }); }
  return { ok: false, reason: `could not take the run lock ${runLock}` };
}

// ---------- freeze lock ----------
// Everything that defines "the answer" is hashed: the spec, every case (visible and hidden), the exemplars and the scorer.
// A symlink anywhere in it is refused: it could swap the key for a file the lock never sees.
function walk(dir, base, out) {
  if (!fs.existsSync(dir)) return out;
  if (fs.lstatSync(dir).isSymbolicLink()) throw new Error(`symlinks are not allowed in the hill folder: ${dir}`);
  for (const ent of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const p = path.join(dir, ent.name);
    if (ent.isSymbolicLink()) throw new Error(`symlinks are not allowed in the hill folder: ${p}`);
    if (ent.isDirectory()) walk(p, base, out);
    else if (ent.isFile()) out[path.relative(base, p)] = sha256(fs.readFileSync(p));
  }
  return out;
}
export function frozenFiles(hill) {
  const files = {};
  const spec = P(hill, 'hill.json');
  if (fs.lstatSync(spec).isSymbolicLink()) throw new Error('hill.json must not be a symlink');
  files['hill.json'] = sha256(fs.readFileSync(spec));
  for (const sub of ['cases', 'exemplars', 'scorer', 'references']) walk(P(hill, sub), hill._dir, files);
  for (const extra of hill.frozen_extra ?? []) {
    const abs = path.resolve(hill._dir, extra);
    files[`extra:${extra}`] = fs.existsSync(abs) && !fs.lstatSync(abs).isSymbolicLink() ? sha256(fs.readFileSync(abs)) : 'missing-or-symlink';
  }
  return files;
}
export const digestOf = (files) => sha256(JSON.stringify(Object.entries(files).sort()));
export function checkLock(hill, expectedDigest) {
  const lock = readJSON(P(hill, 'lock.json'), null);
  if (!lock) return { ok: false, reason: 'no lock.json: run `hill.mjs freeze` first' };
  let files;
  try { files = frozenFiles(hill); } catch (e) { return { ok: false, reason: e.message }; }
  const digest = digestOf(files);
  const want = expectedDigest ?? lock.digest;
  if (digest === want && lock.digest === want && digestOf(lock.files ?? {}) === want) return { ok: true, digest };
  const changed = [...new Set([...Object.keys(files), ...Object.keys(lock.files ?? {})])].filter((k) => files[k] !== lock.files?.[k]);
  return { ok: false, digest, reason: `frozen files changed since freeze: ${changed.slice(0, 8).join(', ') || 'lock.json itself'}` };
}

// ---------- environment ----------
// Children get an allowlisted environment: enough for CLIs to find their login, never the owner's other secrets.
// Add names a scorer or agent needs with `pass_env` on its spec.
export const ENV_ALLOW = ['PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'TERM', 'TZ', 'COLORTERM',
  'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy', 'NODE_EXTRA_CA_CERTS', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
  'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', '__CF_USER_TEXT_ENCODING'];
export function childEnv(extra = {}, passEnv = []) {
  const env = {};
  for (const [k, v] of Object.entries(process.env)) if (ENV_ALLOW.includes(k) || k.startsWith('LC_') || passEnv.includes(k)) env[k] = v;
  return { ...env, ...extra };
}

// ---------- sandbox ----------
// rules: { kind, hide: [no read or write], read: [re-allowed for reading inside a hidden folder], write: [read+write],
// noWrite: [readable, never writable], noWriteRe: [absolute-path regexes, never writable], tmp: private temp folder }.
// Writes are denied everywhere except `write`, `tmp`, terminal devices and the run-state files the claude and codex
// CLIs keep (never their settings, hooks, skills, plugins, memory or MCP config). Owner secrets (ssh, cloud, gh,
// docker, kube, 1Password, git credentials) and codex's global instructions, skills and plugins are unreadable.
// macOS uses sandbox-exec; Linux uses bubblewrap. Returns the argv prefix, or null when this machine has neither.
let sbTool;
export function sandboxTool() {
  if (sbTool !== undefined) return sbTool;
  sbTool = null;
  if (process.platform === 'darwin' && fs.existsSync('/usr/bin/sandbox-exec')) sbTool = { kind: 'seatbelt', bin: '/usr/bin/sandbox-exec' };
  else if (process.platform === 'linux') {
    const w = spawnSync('/bin/sh', ['-c', 'command -v bwrap'], { encoding: 'utf8' }).stdout.trim();
    if (w) sbTool = { kind: 'bwrap', bin: w };
  }
  return sbTool;
}
const real = (p) => { try { return fs.realpathSync(p); } catch { return path.resolve(p); } };
const sbq = (p) => `"${real(p).replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const sbre = (re) => `(regex #"${re.replace(/"/g, '\\"')}")`;
// A glob (as in scope_ignore) as a POSIX regex body for sandbox profiles, which have no (?:) groups.
export function globToPosix(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === '*') {
      if (glob[i + 1] === '*') { re += glob[i + 2] === '/' ? '(.*/)?' : '.*'; i += glob[i + 2] === '/' ? 2 : 1; } else re += '[^/]*';
    } else if (c === '?') re += '[^/]';
    else re += reEsc(c);
  }
  return re;
}

// Where the claude and codex CLIs keep run state. `dirs` are writable folders; `prefixes` are writable files whose
// path starts with that string (sqlite files grow -wal/-shm siblings). `logs` covers launch
// wrappers that log there. Found by running both CLIs under a deny-all-writes profile (2026-11-01, claude 2.1.314, codex 0.162.1).
// With CLAUDE_CONFIG_DIR set (another account), claude writes there while wrappers still write under ~/.claude: both count.
export function agentState() {
  const cs = [...new Set([process.env.CLAUDE_CONFIG_DIR, path.join(HOME, '.claude')].filter(Boolean).map(real))];
  const x = real(process.env.CODEX_HOME || path.join(HOME, '.codex'));
  return {
    claudeDirs: cs, codexDir: x,
    dirs: cs.flatMap((c) => ['cache', 'logs', 'sessions', 'backups', 'projects', 'debug', 'todos', 'shell-snapshots', 'statsig', 'telemetry', 'session-env', 'paste-cache', 'file-history', 'ide', 'tmp'].map((d) => path.join(c, d)))
      .concat(['shell_snapshots', 'tmp', '.tmp', 'cache', 'sessions', 'log'].map((d) => path.join(x, d))),
    prefixes: cs.flatMap((c) => ['history.jsonl', 'mcp-needs-auth-cache.json', 'stats-cache.json', '.credentials.json', '.last-cleanup'].map((f) => path.join(c, f)))
      .concat(['logs_', 'state_', 'models_cache.json', 'auth.json', 'history.jsonl', 'version.json', 'installation_id', '.sqlite-maintenance.lock'].map((f) => path.join(x, f))),
    // Inside those folders, auto-memory is instructions for later sessions.
    noWriteRe: cs.map((c) => `^${reEsc(path.join(c, 'projects'))}/[^/]+/memory(/.*)?$`),
    // Codex loads these even with --ignore-user-config; unreadable, they are simply absent. (Its hooks, rules and
    // prompts folders cannot be hidden this way, codex exits, so hooks are switched off by flag instead.)
    hidden: [...['skills', 'plugins', 'config.toml', '.env.local'].map((f) => path.join(x, f))],
    hiddenRe: [`^${reEsc(x)}/AGENTS[^/]*\\.md$`, `^${reEsc(x)}/memories`],
  };
}
const SECRETS = ['.ssh', '.aws', '.gnupg', '.config/gh', '.netrc', '.docker', '.kube', '.config/gcloud', '.config/op', '.op', '.password-store', '.git-credentials', '.config/git/credentials', '.pypirc', '.npmrc', '.env'];

export function sandboxPrefix(rules) {
  const t = sandboxTool();
  if (!t) return null;
  const { hide = [], read = [], write = [], noWrite = [], noWriteRe = [], tmp = null, allowRead = [] } = rules;
  for (const w of write) fs.mkdirSync(w, { recursive: true });
  const st = agentState();
  const writable = [...write, ...(tmp ? [tmp] : [])];
  const secrets = SECRETS.map((s) => path.join(HOME, s)).filter((s) => !allowRead.some((a) => real(a) === real(s)));
  const roots = hide.map(real);
  const inHidden = (p) => roots.some((h) => real(p) === h || real(p).startsWith(`${h}/`));
  if (t.kind === 'seatbelt') {
    // Later rules win: allow writes, then deny what must stay protected, then re-open paths inside hidden folders.
    const sub = (p) => `(subpath ${sbq(p)})`;
    const prof = ['(version 1)', '(allow default)', '(deny file-write*)'];
    prof.push(`(allow file-write* ${[...writable, ...st.dirs].map(sub).join(' ')} ${st.prefixes.map((p) => sbre(`^${reEsc(p)}`)).join(' ')})`);
    // Terminals, and the here-document temp files /bin/bash 3.2 makes in /tmp whatever TMPDIR says.
    prof.push('(allow file-write* (literal "/dev/null") (literal "/dev/zero") (literal "/dev/dtracehelper") (literal "/dev/ptmx") (regex #"^/dev/(tty|fd/)") (literal "/private/tmp") (regex #"^/private/tmp/sh-thd") (literal "/private/var/tmp") (regex #"^/private/var/tmp/sh-thd"))');
    prof.push(`(deny file-write* ${st.noWriteRe.map(sbre).join(' ')})`);
    prof.push(`(deny file-read* file-write* ${[...secrets, ...st.hidden].map(sub).join(' ')} ${st.hiddenRe.map(sbre).join(' ')})`);
    for (const h of hide) prof.push(`(deny file-read* file-write* ${sub(h)})`);
    if (noWrite.length) prof.push(`(deny file-write* ${noWrite.map(sub).join(' ')})`);
    if (noWriteRe.length) prof.push(`(deny file-write* ${noWriteRe.map(sbre).join(' ')})`);
    for (const r of read) if (inHidden(r) && fs.existsSync(r)) prof.push(`(allow file-read* (${fs.statSync(r).isDirectory() ? 'subpath' : 'literal'} ${sbq(r)}))`);
    for (const w of writable) if (inHidden(w)) prof.push(`(allow file-read* file-write* ${sub(w)})`);
    // Runtimes stat every folder above a file they load (Node's realpath), so the hidden folders above an allowed path
    // stay stat-able. Listing them, or reading anything else inside, is still denied.
    const stat = new Set();
    for (const p of [...read, ...writable]) {
      for (let d = path.dirname(real(p)); d !== path.dirname(d); d = path.dirname(d)) if (roots.some((h) => d === h || d.startsWith(`${h}/`))) stat.add(d);
    }
    for (const d of stat) prof.push(`(allow file-read-metadata (literal ${sbq(d)}))`);
    return [t.bin, '-p', prof.join('\n')];
  }
  // bubblewrap: a read-only root with writable binds. It has no path patterns, so prefixes bind the files that exist
  // now, and regex rules cover only paths that exist when the child starts.
  const a = ['--ro-bind', '/', '/', '--dev', '/dev', '--proc', '/proc', '--unshare-pid', '--die-with-parent'];
  const bind = (flag, p) => { if (fs.existsSync(p)) a.push(flag, real(p), real(p)); };
  const matching = (res) => {
    const out = [];
    for (const src of res) {
      const re = new RegExp(src);
      let lit = '';
      for (let i = 1; i < src.length && !'[(.*+?|$'.includes(src[i]); i++) lit += src[i] === '\\' ? src[++i] : src[i];
      const dir = lit.endsWith('/') ? lit.slice(0, -1) : path.dirname(lit);
      const walkTo = (d, depth) => { if (depth > 3 || !fs.existsSync(d)) return; for (const n of fs.readdirSync(d)) { const f = path.join(d, n); if (re.test(f)) out.push(f); else if (fs.lstatSync(f).isDirectory()) walkTo(f, depth + 1); } };
      walkTo(dir, 0);
    }
    return out;
  };
  for (const w of [...writable, ...st.dirs]) bind('--bind', w);
  for (const p of st.prefixes) { const d = path.dirname(p), b = path.basename(p); if (fs.existsSync(d)) for (const n of fs.readdirSync(d)) if (n.startsWith(b)) bind('--bind', path.join(d, n)); }
  for (const f of matching(st.noWriteRe)) bind('--ro-bind', f);
  const blank = (p) => { if (!fs.existsSync(p)) return; if (fs.lstatSync(p).isDirectory()) a.push('--tmpfs', real(p)); else a.push('--ro-bind', '/dev/null', real(p)); };
  for (const s of [...secrets, ...st.hidden, ...matching(st.hiddenRe)]) blank(s);
  for (const h of hide) blank(h);
  for (const n of [...noWrite, ...matching(noWriteRe)]) bind('--ro-bind', n);
  for (const r of read) if (inHidden(r)) bind('--ro-bind', r);
  for (const w of writable) if (inHidden(w)) bind('--bind', w);
  return [t.bin, ...a, '--'];
}

// Paths in or behind the work folder that no child may write: git's admin folders (refs, objects, index, config,
// hooks), and scope_ignore paths, whose changes the diff never shows. Writes outside the work folder (a symlinked
// node_modules, other checkouts) are already denied.
export function workGuards(hill) {
  const W = hill.workdir;
  if (!W || !fs.existsSync(W)) return { noWrite: [], noWriteRe: [] };
  const noWrite = [path.join(W, '.git')];
  try { const { gitDir, commonDir } = gitDirs(W); noWrite.push(gitDir, commonDir); } catch { /* not a repo yet */ }
  const noWriteRe = (hill.scope_ignore ?? []).map((g) => `^${reEsc(real(W))}/${globToPosix(g)}(/.*)?$`);
  return { noWrite: [...new Set(noWrite)], noWriteRe };
}

// What each kind of process may see. The hill folder (hidden tests, runs, state) is hidden from all of them;
// producers and checks read the scorer and spec and write only their cache; climbers write the work folder.
// hill.json `sandbox_write` adds folders every child may write (a tool cache that cannot change the score);
// `sandbox_allow_read` re-opens owner secret paths a scorer genuinely needs (for example ~/.npmrc for npx).
export function sandboxRules(hill, kind, { inputsDir, outDir, agentDir } = {}) {
  if (hill.sandbox === 'off') return null;
  const H = hill._dir, W = hill.workdir ?? null;
  const cache = P(hill, 'cache', 'produce');
  const extra = (hill.sandbox_write ?? []).map((p) => path.resolve(W ?? H, p.replace(/^~(?=\/)/, HOME)));
  const allowRead = (hill.sandbox_allow_read ?? []).map((p) => path.resolve(p.replace(/^~(?=\/)/, HOME)));
  const base = { kind, hide: [H], allowRead, ...workGuards(hill) };
  if (kind === 'produce') return { ...base, read: [P(hill, 'scorer'), P(hill, 'hill.json')], write: [cache, ...extra, ...(hill.produce?.workdir_writable && W ? [W] : [])] };
  if (kind === 'scorer') return { ...base, read: [P(hill, 'scorer'), P(hill, 'hill.json'), ...(inputsDir ? [inputsDir] : [])], write: [cache, ...(outDir ? [outDir] : []), ...extra] };
  // The council's render command: like a producer, plus the fresh folder it writes the rendered files to.
  if (kind === 'render') return { ...base, read: [P(hill, 'scorer'), P(hill, 'hill.json')], write: [cache, ...(outDir ? [outDir] : []), ...extra] };
  if (kind === 'judge') return { ...base, write: extra };
  if (kind === 'climber') return { ...base, write: [...(W ? [W] : []), ...(agentDir ? [agentDir] : []), ...extra], orphanRoots: [...(W ? [W] : []), ...(agentDir ? [agentDir] : [])] };
  throw new Error(`unknown sandbox kind ${kind}`);
}

// ---------- processes ----------
// Every child runs in its own process group. When it exits, the whole group is stopped too, so background jobs a
// climber or producer started never outlive it. Jobs are recorded under run.jobsDir so a crashed runner's leftovers
// can be found and stopped on the next start. A process that leaves the group and outlives the child fails the run
// (exit 125 when it had exited 0) and is stopped; the result lists it under `escaped`.
export function run(command, { cwd, input = '', env = {}, passEnv = [], timeoutSec = 600, args = null, onSpawn = null, sandbox = null } = {}) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    const token = `${nonce()}${nonce()}`;
    let argv = args ? [command, ...args] : ['/bin/sh', '-c', command];
    let tmp = null;
    if (sandbox) {
      tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'hill-tmp-'));
      const pre = sandboxPrefix({ ...sandbox, tmp });
      if (!pre) { fs.rmSync(tmp, { recursive: true, force: true }); resolve({ code: null, stdout: '', stderr: 'no sandbox tool on this machine (sandbox-exec or bwrap); set sandbox "off" to run unsandboxed', ms: 0, timedOut: false, sandboxMissing: true }); return; }
      argv = [...pre, ...argv];
    }
    const e = { ...env, HILL_RUN_TOKEN: token, GIT_OPTIONAL_LOCKS: '0', ...(tmp ? { TMPDIR: tmp, TMP: tmp, TEMP: tmp } : {}) };
    // Climbers may also leave orphans working in the work folder (rules.orphanRoots).
    const orphanRoots = sandbox?.orphanRoots ?? [];
    let child;
    try { child = spawn(argv[0], argv.slice(1), { cwd, env: childEnv(e, passEnv), stdio: ['pipe', 'pipe', 'pipe'], detached: true }); }
    catch (err) { if (tmp) fs.rmSync(tmp, { recursive: true, force: true }); resolve({ code: null, stdout: '', stderr: err.message, ms: 0, timedOut: false }); return; }
    run.active.add(child);
    const job = trackJob(child.pid, argv.slice(-3).join(' '));
    if (onSpawn && child.pid) { try { onSpawn(child); } catch { /* bookkeeping only */ } }
    let stdout = '', stderr = '', timedOut = false, code = null;
    child.stdout.on('data', (d) => { if (stdout.length < 8e6) stdout += d; });
    child.stderr.on('data', (d) => { if (stderr.length < 2e6) stderr += d; });
    child.stdin.on('error', () => {});
    child.stdin.end(input);
    const timer = setTimeout(() => { timedOut = true; killGroup(child.pid, 'SIGTERM'); setTimeout(() => killGroup(child.pid, 'SIGKILL'), 5000); }, Math.max(1, timeoutSec) * 1000);
    child.on('error', (err) => { stderr += err.message; });
    // 'exit' fires when the leader exits; background children may still hold the pipes open, so stop the group now.
    child.on('exit', (c) => { code = c; clearTimeout(timer); reapGroup(child.pid); });
    child.on('close', (c) => {
      clearTimeout(timer); reapGroup(child.pid); run.active.delete(child); untrackJob(job);
      const escaped = stopEscapees(token, tmp, orphanRoots, t0);
      if (tmp) fs.rmSync(tmp, { recursive: true, force: true });
      let exit = code ?? c;
      if (escaped.length) { stderr += `\n[hill] stopped ${escaped.length} process(es) that escaped the run: ${escaped.map((x) => `${x.pid} (${x.why})`).join(', ')}`; if (exit === 0) exit = 125; }
      resolve({ code: exit, stdout, stderr, ms: Date.now() - t0, timedOut, escaped });
    });
  });
}
run.active = new Set();
// Processes that left the child's process group (setsid, double fork) and outlived it: found by the run token in
// their environment, by a working folder inside the run's private temp folder, or, for agents, by being an orphan
// (parent pid 1) working inside a folder the agent could write. All are stopped. `since` is when the child started.
const etimeSec = (s) => { const [d, hms] = s.includes('-') ? s.split('-') : ['0', s]; return Number(d) * 86400 + hms.split(':').map(Number).reduce((a, b) => a * 60 + b, 0); };
export function stopEscapees(token, tmp, orphanRoots = [], since = 0) {
  const found = new Map();
  const under = (p, roots) => roots.some((r) => p === r || p.startsWith(`${r}/`));
  const rtmp = tmp && fs.existsSync(tmp) ? [real(tmp)] : [], rroots = orphanRoots.filter((r) => fs.existsSync(r)).map(real);
  if (process.platform === 'linux') {
    for (const d of fs.readdirSync('/proc').filter((x) => /^\d+$/.test(x))) {
      const pid = Number(d);
      try { if (fs.readFileSync(`/proc/${d}/environ`, 'latin1').split('\0').includes(`HILL_RUN_TOKEN=${token}`)) { found.set(pid, 'token'); continue; } } catch { /* gone, or not ours */ }
      try {
        const cwd = fs.readlinkSync(`/proc/${d}/cwd`);
        if (under(cwd, rtmp)) found.set(pid, 'cwd');
        else if (rroots.length && under(cwd, rroots) && fs.readFileSync(`/proc/${d}/stat`, 'latin1').replace(/^.*\)\s+/, '').split(' ')[1] === '1') found.set(pid, 'orphan');
      } catch { /* gone */ }
    }
  } else {
    const ps = spawnSync('ps', ['-A', '-E', '-ww', '-o', 'pid=,ppid=,uid=,etime=,command='], { encoding: 'utf8', maxBuffer: 512 * 1024 * 1024 });
    const ppid = new Map(), recent = new Set();
    const uid = os.userInfo().uid, maxAge = since ? Math.ceil((Date.now() - since) / 1000) + 2 : Infinity;
    for (const line of (ps.stdout ?? '').split('\n')) {
      const m = line.match(/^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s/);
      if (!m) continue;
      const pid = Number(m[1]);
      ppid.set(pid, Number(m[2]));
      if (line.includes(` HILL_RUN_TOKEN=${token}`)) found.set(pid, 'token');
      else if (Number(m[3]) === uid && etimeSec(m[4]) <= maxAge) recent.add(pid);
    }
    // lsof costs seconds on a busy Mac, so only processes that could have escaped are looked up: started after the
    // child did and, its group gone, hanging off launchd (pid 1) directly or through other such processes.
    const offLaunchd = (pid) => { for (let p = pid, i = 0; i < 64; i++) { const q = ppid.get(p); if (q === 1) return true; if (!recent.has(q)) return false; p = q; } return false; };
    const cand = [...recent].filter((p) => p !== process.pid && offLaunchd(p));
    if (cand.length && (rtmp.length || rroots.length)) {
      const r = spawnSync('lsof', ['-nP', '-Fpn', '-a', '-d', 'cwd', '-p', cand.join(',')], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
      let pid = 0;
      for (const l of (r.stdout ?? '').split('\n')) {
        if (l[0] === 'p') pid = Number(l.slice(1));
        else if (l[0] === 'n' && pid) {
          const cwd = l.slice(1);
          if (under(cwd, rtmp)) found.set(pid, 'cwd');
          else if (ppid.get(pid) === 1 && under(cwd, rroots)) found.set(pid, 'orphan');
        }
      }
    }
  }
  found.delete(process.pid);
  for (const pid of found.keys()) { try { process.kill(pid, 'SIGKILL'); } catch { /* already gone */ } }
  return [...found].map(([pid, why]) => ({ pid, why }));
}
run.jobsDir = null;
function killGroup(pgid, sig) { try { process.kill(-pgid, sig); return true; } catch { return false; } }
function groupAlive(pgid) { try { process.kill(-pgid, 0); return true; } catch { return false; } }
function reapGroup(pgid) {
  if (!groupAlive(pgid)) return;
  killGroup(pgid, 'SIGTERM');
  for (let k = 0; k < 20 && groupAlive(pgid); k++) sleepSync(0.1);
  if (groupAlive(pgid)) killGroup(pgid, 'SIGKILL');
}
function trackJob(pid, label) {
  if (!run.jobsDir || !pid) return null;
  const f = path.join(run.jobsDir, `${pid}.json`);
  run.runnerStarted ??= processStart(process.pid);
  try { writeJSON(f, { pgid: pid, started: processStart(pid), label: clip(label, 200), runner: process.pid, runner_started: run.runnerStarted }); } catch { return null; }
  return f;
}
function untrackJob(f) { if (f) fs.rmSync(f, { force: true }); }
// Stops jobs a dead runner left behind. A job is stopped only when its group leader is the same process (pid + start
// time) or the leader is gone but its group still exists (a pid is never reused while its process group lives).
export function reapJobs(dir) {
  const stopped = [];
  if (!dir || !fs.existsSync(dir)) return stopped;
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.json'))) {
    const j = readJSON(path.join(dir, f), null);
    const runnerAlive = j?.runner === process.pid || (j?.runner_started && processStart(j.runner) === j.runner_started);
    if (runnerAlive) continue;
    if (j?.pgid) {
      const start = processStart(j.pgid);
      if ((start && start === j.started) || (!start && groupAlive(j.pgid))) { reapGroup(j.pgid); stopped.push(j); }
    }
    fs.rmSync(path.join(dir, f), { force: true });
  }
  return stopped;
}
// The command line of a process, or '' when it is gone or a zombie.
export function processCommand(pid) {
  const r = spawnSync('ps', ['-p', String(pid), '-o', 'stat=,command='], { encoding: 'utf8' });
  const line = (r.stdout ?? '').trim();
  if (!line || /^Z/.test(line)) return '';
  return line.replace(/^\S+\s+/, '');
}
// When a live process started (stable across exec), or '' when it is gone: pid + start time identifies it safely.
export function processStart(pid) {
  if (!processCommand(pid)) return '';
  const r = spawnSync('ps', ['-p', String(pid), '-o', 'lstart='], { encoding: 'utf8' });
  return (r.stdout ?? '').trim();
}
export function killActive() { for (const c of run.active) reapGroup(c.pid); }

export async function pool(items, n, fn) {
  const out = new Array(items.length);
  let i = 0;
  await Promise.all(Array.from({ length: Math.max(1, Math.min(n, items.length)) }, async () => {
    while (i < items.length) { const k = i++; out[k] = await fn(items[k], k); }
  }));
  return out;
}

// ---------- git ----------
// The runner's own git calls never run repo hooks, fsmonitor daemons or external diff/textconv programs.
// (Diff commands also pass --no-ext-diff --no-textconv.)
const GIT_SAFE = ['-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', '-c', 'commit.gpgSign=false'];
export function gitx({ cwd, env = {}, input } = {}, ...args) {
  const r = spawnSync('git', [...GIT_SAFE, ...args], { cwd, input, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024, env: { ...process.env, GIT_TERMINAL_PROMPT: '0', GIT_OPTIONAL_LOCKS: '0', ...env } });
  if (r.status !== 0) throw new Error(`git ${args.join(' ')} failed: ${(r.stderr || r.stdout).trim()}`);
  return r.stdout.replace(/\n$/, '');
}
export const git = (cwd, ...args) => gitx({ cwd }, ...args).trim();
export function gitOk(cwd, ...args) { return spawnSync('git', [...GIT_SAFE, ...args], { cwd, encoding: 'utf8' }).status === 0; }
export const ZERO = '0000000000000000000000000000000000000000';
export function currentBranch(W) { return gitOk(W, 'symbolic-ref', '-q', 'HEAD') ? git(W, 'symbolic-ref', '--short', 'HEAD') : null; }
export function gitDirs(W) {
  const gd = git(W, 'rev-parse', '--absolute-git-dir');
  const cd = path.resolve(W, git(W, 'rev-parse', '--git-common-dir'));
  return { gitDir: gd, commonDir: cd };
}
// Files whose edits could make git run code or hide changes (config, attributes, excludes, hooks). The runner
// snapshots them (hook folders recursively, with entry types) before each attempt and puts them back exactly afterwards:
// entries that appeared are deleted, changed ones rewritten. The sandbox already denies children writes to git's folders;
// this also covers sandbox "off".
export function gitGuardFiles(W) {
  const { gitDir, commonDir } = gitDirs(W);
  const files = [path.join(commonDir, 'config'), path.join(gitDir, 'config.worktree'), path.join(commonDir, 'config.worktree'),
    path.join(gitDir, 'info', 'attributes'), path.join(commonDir, 'info', 'attributes'), path.join(commonDir, 'info', 'exclude'),
    path.join(HOME, '.gitconfig'), path.join(HOME, '.config', 'git', 'config'), path.join(HOME, '.config', 'git', 'attributes'), path.join(HOME, '.config', 'git', 'ignore')];
  for (const key of ['core.excludesFile', 'core.attributesFile']) {
    const r = spawnSync('git', ['config', '--path', '--get', key], { cwd: W, encoding: 'utf8' });
    if (r.status === 0 && r.stdout.trim()) files.push(path.resolve(W, r.stdout.trim().replace(/^~(?=\/)/, HOME)));
  }
  return { files: [...new Set(files)], dirs: [...new Set([path.join(commonDir, 'hooks'), path.join(gitDir, 'hooks')])] };
}
const readOrNull = (f) => { try { return fs.readFileSync(f, 'latin1'); } catch { return null; } };
// Every entry under a guarded folder, recursively, with its type: files (bytes + mode), symlinks (target), folders
// (mode) and anything else (fifo, socket: mode only). The key '' is the folder itself.
function snapTree(root) {
  const out = {};
  const visit = (rel) => {
    const abs = rel ? path.join(root, rel) : root;
    let st;
    try { st = fs.lstatSync(abs); } catch { return; }
    if (st.isSymbolicLink()) out[rel] = { type: 'link', target: fs.readlinkSync(abs) };
    else if (st.isDirectory()) { out[rel] = { type: 'dir', mode: st.mode }; for (const n of fs.readdirSync(abs).sort()) visit(rel ? path.join(rel, n) : n); }
    else if (st.isFile()) out[rel] = { type: 'file', body: readOrNull(abs), mode: st.mode };
    else out[rel] = { type: 'other', mode: st.mode };
  };
  visit('');
  return out;
}
const sameEntry = (a, b) => !!a && !!b && a.type === b.type && a.mode === b.mode && a.body === b.body && a.target === b.target;
// Puts a folder back exactly as snapTree saw it: entries that appeared are removed, changed ones rewritten, removed
// ones recreated. Entries that existed before are never deleted unless they changed type.
function restoreTree(root, was) {
  const changed = [];
  const now = snapTree(root);
  const abs = (rel) => (rel ? path.join(root, rel) : root);
  for (const rel of Object.keys(now).sort((a, b) => b.length - a.length)) {
    if (sameEntry(now[rel], was[rel])) continue;
    if (!was[rel] || was[rel].type !== now[rel].type || now[rel].type === 'link' || now[rel].type === 'other') {
      changed.push(abs(rel)); fs.rmSync(abs(rel), { recursive: true, force: true });
    }
  }
  for (const rel of Object.keys(was).sort((a, b) => a.length - b.length)) {
    const w = was[rel], f = abs(rel);
    let cur = null;
    try { const st = fs.lstatSync(f); cur = st.isSymbolicLink() ? { type: 'link', target: fs.readlinkSync(f) } : st.isDirectory() ? { type: 'dir', mode: st.mode } : st.isFile() ? { type: 'file', body: readOrNull(f), mode: st.mode } : { type: 'other', mode: st.mode }; } catch { /* missing */ }
    if (sameEntry(cur, w)) continue;
    if (!changed.includes(f)) changed.push(f);
    if (w.type === 'dir') { fs.mkdirSync(f, { recursive: true }); fs.chmodSync(f, w.mode & 0o7777); }
    else if (w.type === 'file') { fs.mkdirSync(path.dirname(f), { recursive: true }); if (cur && cur.type !== 'file') fs.rmSync(f, { recursive: true, force: true }); fs.writeFileSync(f, w.body ?? '', 'latin1'); fs.chmodSync(f, w.mode & 0o7777); }
    else if (w.type === 'link') { fs.rmSync(f, { recursive: true, force: true }); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.symlinkSync(w.target, f); }
    // 'other' (fifo, socket) cannot be recreated byte for byte; it is reported as changed.
  }
  return changed;
}
export function snapshotGuard(W) {
  const g = gitGuardFiles(W);
  const files = Object.fromEntries(g.files.map((f) => [f, readOrNull(f)]));
  const dirs = Object.fromEntries(g.dirs.map((d) => [d, snapTree(d)]));
  return { files, dirs };
}
// Hashes only, for the state file: config can hold credentials, so contents stay in memory.
export const guardDigest = (snap) => sha256(JSON.stringify([Object.entries(snap.files).map(([f, b]) => [f, b == null ? null : sha256(b)]),
  Object.entries(snap.dirs).map(([d, m]) => [d, Object.entries(m).map(([n, x]) => [n, x.type, x.mode ?? null, x.target ?? null, x.body == null ? null : sha256(x.body)])])]));
export function restoreGuard(snap) {
  const changed = [];
  for (const [f, before] of Object.entries(snap.files)) {
    if (readOrNull(f) === before) continue;
    changed.push(f);
    if (before == null) fs.rmSync(f, { force: true });
    else { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, before, 'latin1'); }
  }
  for (const [d, was] of Object.entries(snap.dirs)) changed.push(...restoreTree(d, was));
  return changed;
}
export const currentGuardDigest = (W) => guardDigest(snapshotGuard(W));

// ---------- the work folder as a tree, byte for byte ----------
// The runner never lets git transform files on the way in or out: clean/smudge filters run programs, and text/eol
// conversion or ident would make the committed bytes differ from the scored ones. Trees are built by hashing the raw
// files, and the folder is restored by writing raw blobs. Repos that depend on such attributes are refused up front
// (filterAttrProblems).
const objectFormats = new Map();
function blobId(top, buf) {
  if (!objectFormats.has(top)) objectFormats.set(top, spawnSync('git', [...GIT_SAFE, 'rev-parse', '--show-object-format'], { cwd: top, encoding: 'utf8' }).stdout?.trim() || 'sha1');
  return crypto.createHash(objectFormats.get(top) === 'sha256' ? 'sha256' : 'sha1').update(`blob ${buf.length}\0`).update(buf).digest('hex');
}
function writeBlob(top, buf, oid) {
  const r = spawnSync('git', [...GIT_SAFE, 'hash-object', '-w', '--stdin', '--no-filters'], { cwd: top, input: buf, encoding: 'utf8', maxBuffer: 1024 * 1024 });
  if (r.status !== 0 || r.stdout.trim() !== oid) throw new Error(`git hash-object failed: ${(r.stderr || r.stdout).trim()}`);
}
function readBlob(top, oid) {
  const r = spawnSync('git', [...GIT_SAFE, 'cat-file', 'blob', oid], { cwd: top, maxBuffer: 2 * 1024 * 1024 * 1024 });
  if (r.status !== 0) throw new Error(`git cat-file blob ${oid} failed: ${r.stderr.toString().trim()}`);
  return r.stdout;
}
function indexEntries(top, env = {}) {
  const m = new Map();
  for (const rec of gitx({ cwd: top, env }, 'ls-files', '-s', '-z').split('\0').filter(Boolean)) {
    const t = rec.indexOf('\t'); const [mode, oid] = rec.slice(0, t).split(' ');
    m.set(rec.slice(t + 1), { mode, oid });
  }
  return m;
}
const gitConfig = (cwd, key) => { const r = spawnSync('git', [...GIT_SAFE, 'config', '--get', key], { cwd, encoding: 'utf8' }); return r.status === 0 ? r.stdout.trim().toLowerCase() : null; };
// True when every folder above `rel` is a real folder (not a symlink or file), so reading `rel` stays inside the repo.
function realParents(top, rel, cache) {
  let cur = top;
  for (const part of rel.split('/').slice(0, -1)) {
    cur = path.join(cur, part);
    if (!cache.has(cur)) { let ok = false; try { ok = fs.lstatSync(cur).isDirectory(); } catch { /* missing */ } cache.set(cur, ok); }
    if (!cache.get(cur)) return false;
  }
  return true;
}

// The tree the work folder holds right now, built in a private index (index flags such as assume-unchanged or
// skip-worktree cannot hide edits, and the owner's real index is untouched). Honours .gitignore like `git add -A`.
// Untracked paths in `skip` (ignored files that existed before the attempt) are left out, so un-ignoring a cache
// folder cannot pull it into the tree.
export function worktreeTree(W, base, indexFile, { skip = null } = {}) {
  const top = git(W, 'rev-parse', '--show-toplevel');
  const env = { GIT_INDEX_FILE: indexFile };
  fs.mkdirSync(path.dirname(indexFile), { recursive: true });
  fs.rmSync(indexFile, { force: true });
  gitx({ cwd: top, env }, 'read-tree', base);
  const known = indexEntries(top, env);
  const listed = new Set(gitx({ cwd: top, env }, 'ls-files', '-z', '-c', '-o', '--exclude-standard').split('\0').filter(Boolean));
  const fileMode = gitConfig(top, 'core.filemode') !== 'false';
  const parents = new Map();
  const entries = [];
  for (const p of listed) {
    const was = known.get(p);
    if (p.endsWith('/') || (!was && skip?.has(p))) continue; // a nested repository, or a pre-existing ignored file
    if (was?.mode === '160000') { entries.push(`160000 ${was.oid}\t${p}\0`); continue; } // submodules keep their recorded commit
    if (!realParents(top, p, parents)) continue; // a folder above it was replaced by a symlink or file: it is gone
    const abs = path.join(top, p);
    let st;
    try { st = fs.lstatSync(abs); } catch { continue; } // deleted
    let mode, buf;
    if (st.isSymbolicLink()) { mode = '120000'; buf = fs.readlinkSync(abs, { encoding: 'buffer' }); }
    else if (st.isFile()) { mode = fileMode ? (st.mode & 0o100 ? '100755' : '100644') : /^100/.test(was?.mode ?? '') ? was.mode : '100644'; buf = fs.readFileSync(abs); }
    else continue; // a folder where a file was, or a fifo/socket: git add leaves these out too
    const oid = blobId(top, buf);
    if (oid !== was?.oid) writeBlob(top, buf, oid);
    entries.push(`${mode} ${oid}\t${p}\0`);
  }
  fs.rmSync(indexFile, { force: true });
  gitx({ cwd: top, env, input: entries.join('') }, 'update-index', '-z', '--add', '--index-info');
  return gitx({ cwd: top, env }, 'write-tree').trim();
}
// Changes between two trees with their modes, so symlinks (120000) and submodules (160000) can be refused.
export function treeChanges(W, a, b) {
  const out = gitx({ cwd: W }, 'diff-tree', '-r', '-z', '--no-renames', '--raw', a, b);
  const parts = out.split('\0').filter((x, i, arr) => !(x === '' && i === arr.length - 1));
  const changes = [];
  for (let i = 0; i + 1 < parts.length; i += 2) {
    const m = parts[i].match(/^:(\d{6}) (\d{6}) \S+ \S+ (\w)/);
    if (m) changes.push({ file: parts[i + 1], oldMode: m[1], newMode: m[2], status: m[3] });
  }
  return changes;
}
// Points the work folder (files and the owner's index) at `tree` without moving any branch, writing raw blobs (no
// smudge filters). Files the folder holds that `tree` lacks are deleted, so a rejected attempt leaves nothing behind;
// `skip` is passed through to worktreeTree so pre-existing ignored files are never touched.
export function restoreWorktree(W, tree, indexFile, { skip = null } = {}) {
  const top = git(W, 'rev-parse', '--show-toplevel');
  const cur = worktreeTree(top, tree, indexFile, { skip });
  const changes = treeChanges(top, cur, tree);
  const prune = (rel) => { for (let d = path.dirname(rel); d !== '.'; d = path.dirname(d)) { try { fs.rmdirSync(path.join(top, d)); } catch { return; } } };
  for (const c of changes) if (c.status === 'D' && c.oldMode !== '160000') { fs.rmSync(path.join(top, c.file), { force: true }); prune(c.file); }
  const want = treeFiles(top, tree);
  for (const c of changes) {
    if (c.status === 'D' || c.newMode === '160000') continue; // a submodule's checkout is never rewritten
    const { mode, oid } = want.get(c.file);
    const abs = path.join(top, c.file);
    let dir = top;
    for (const part of c.file.split('/').slice(0, -1)) { // `tree` has a folder here: a symlink or file in the way goes
      dir = path.join(dir, part);
      let st = null;
      try { st = fs.lstatSync(dir); } catch { /* missing */ }
      if (st && !st.isDirectory()) fs.rmSync(dir, { force: true });
      if (!st?.isDirectory()) fs.mkdirSync(dir);
    }
    let st = null;
    try { st = fs.lstatSync(abs); } catch { /* missing */ }
    if (st?.isDirectory()) { try { fs.rmdirSync(abs); } catch { throw new Error(`cannot restore ${c.file}: a folder with other files is in the way`); } }
    else if (st) fs.rmSync(abs, { force: true }); // replaced, never written through a symlink
    const body = readBlob(top, oid);
    if (mode === '120000') fs.symlinkSync(body, abs);
    else { const m = mode === '100755' ? 0o755 : 0o644; fs.writeFileSync(abs, body, { mode: m }); fs.chmodSync(abs, m); }
  }
  const after = worktreeTree(top, tree, indexFile, { skip });
  if (after !== tree) throw new Error(`restoring the work folder to ${tree.slice(0, 10)} left differences: ${treeChanges(top, after, tree).slice(0, 6).map((c) => c.file).join(', ')}`);
  pointIndex(top, tree);
}
// Points the owner's index at `treeish`. The stat refresh can run clean filters, so it only runs when no attribute
// on disk asks for one; otherwise `git status` refreshes it later.
export function pointIndex(W, treeish) {
  gitx({ cwd: W }, 'read-tree', treeish);
  if (!filterAttrProblems(W).length) spawnSync('git', [...GIT_SAFE, 'update-index', '-q', '--refresh'], { cwd: W });
}
// Settings and attributes that make git run programs or change bytes between the folder and the repo (filters, LFS,
// ident, encodings, CRLF conversion, sparse checkout). The runner works on raw bytes, so it refuses such repos.
export function filterAttrProblems(W) {
  const top = git(W, 'rev-parse', '--show-toplevel');
  const problems = [];
  if (gitConfig(top, 'core.autocrlf') === 'true') problems.push('core.autocrlf is true');
  if (gitConfig(top, 'core.eol') === 'crlf') problems.push('core.eol is crlf');
  if (gitConfig(top, 'core.sparsecheckout') === 'true') problems.push('sparse checkout is on');
  if (fs.existsSync(path.join(top, '.lfsconfig'))) problems.push('Git LFS (.lfsconfig)');
  const files = gitx({ cwd: top }, 'ls-files', '-z').split('\0').filter(Boolean);
  if (files.length) {
    const out = gitx({ cwd: top, input: `${files.join('\0')}\0` }, 'check-attr', '-z', '--stdin', 'filter', 'ident', 'working-tree-encoding', 'eol').split('\0');
    const seen = new Map();
    for (let i = 0; i + 2 < out.length; i += 3) {
      const [f, attr, v] = [out[i], out[i + 1], out[i + 2]];
      const bad = attr === 'ident' ? v === 'set' : attr === 'eol' ? v === 'crlf' : !['unspecified', 'unset'].includes(v);
      if (bad && !seen.has(`${attr}=${v}`)) seen.set(`${attr}=${v}`, f);
    }
    for (const [a, f] of seen) problems.push(`attribute ${a} (e.g. ${f})`);
  }
  return problems;
}
// Paths whose staged content matches neither HEAD nor the file on disk. Pointing the index at a tree would lose it.
// alsoIn: commits whose content counts as saved too (the runner's last head: a stop right after a keep moved the
// branch leaves the index on the previous commit, which is not work at risk).
export function stagedOnlyProblems(W, { alsoIn = [] } = {}) {
  const top = git(W, 'rev-parse', '--show-toplevel');
  const staged = gitx({ cwd: top }, 'diff-index', '--cached', '-z', '--no-renames', '--name-only', 'HEAD').split('\0').filter(Boolean);
  if (!staged.length) return [];
  const idx = indexEntries(top);
  const known = alsoIn.filter(Boolean).map((t) => treeFiles(top, t));
  return staged.filter((p) => {
    const e = idx.get(p);
    if (!e || e.mode === '160000') return false; // staged deletions and submodules lose nothing
    if (known.some((m) => m.get(p)?.oid === e.oid)) return false;
    try {
      const abs = path.join(top, p), st = fs.lstatSync(abs);
      const buf = st.isSymbolicLink() ? fs.readlinkSync(abs, { encoding: 'buffer' }) : st.isFile() ? fs.readFileSync(abs) : null;
      return !buf || blobId(top, buf) !== e.oid;
    } catch { return true; }
  });
}
export function commitTree(W, tree, parent, message) {
  const id = gitOk(W, 'config', 'user.email') ? {} : { GIT_AUTHOR_NAME: 'hill-climb', GIT_AUTHOR_EMAIL: 'hill-climb@localhost', GIT_COMMITTER_NAME: 'hill-climb', GIT_COMMITTER_EMAIL: 'hill-climb@localhost' };
  return gitx({ cwd: W, env: id, input: message }, 'commit-tree', tree, '-p', parent).trim();
}
// Creates a ref only if it does not exist yet; returns the ref actually written.
export function createRef(W, ref, sha) {
  for (let k = 0; k < 5; k++) {
    const name = k ? `${ref}-${Date.now()}-${k}` : ref;
    if (gitOk(W, 'update-ref', name, sha, ZERO)) return name;
  }
  throw new Error(`could not create ${ref}`);
}

// ---------- agents (climbers and judges) ----------
// Any CLI that takes a prompt on stdin works. Built in: claude (fresh `claude -p`), codex (`codex exec`), cmd (any command).
export function claudeBin() {
  for (const b of [path.join(HOME, '.claude/bin/claude'), path.join(HOME, '.local/bin/claude')]) if (fs.existsSync(b)) return b;
  return 'claude';
}
let safeModeCache;
function claudeHasSafeMode() {
  if (safeModeCache === undefined) {
    const r = spawnSync(claudeBin(), ['--help'], { encoding: 'utf8', timeout: 20000, env: childEnv() });
    safeModeCache = /--safe-mode\b/.test(`${r.stdout ?? ''}${r.stderr ?? ''}`);
  }
  return safeModeCache;
}

// role: "climber" may edit the work folder; "judge" and "producer" are read-only.
// Codex features that reach outside the prompt and the files (hooks, MCP apps, plugins, memories, browser and
// computer use, sub-agents, background daemons). --ignore-user-config alone still loads hooks.json and app MCP servers.
export const CODEX_OFF = ['hooks', 'apps', 'memories', 'plugins', 'remote_plugin', 'plugin_sharing', 'browser_use', 'browser_use_external',
  'computer_use', 'chronicle', 'multi_agent', 'multi_agent_v2', 'skill_search', 'skill_mcp_dependency_install', 'image_generation',
  'in_app_browser', 'daemon_auto_start', 'goals'];
// images: absolute paths of image files the agent must see (codex attaches them with -i; claude reads them with its
// Read tool from the paths in the prompt; cmd agents get them in HILL_IMAGES, one per line).
export function agentInvocation(spec, role, { cwd, lastMessageFile, wrapped = false, images = [] }) {
  const cli = spec.cli ?? 'claude';
  if (cli === 'cmd') return { command: spec.command, shell: true };
  if (cli === 'codex') {
    // Inside the hill sandbox codex runs unconfined (macOS sandboxes cannot nest) and the hill sandbox is the boundary:
    // it hides the hill folder, codex's global AGENTS.md, skills and plugins, and denies writes outside the work folder.
    // Unwrapped (sandbox "off"), codex's own sandbox applies and the hill folder stays readable.
    const sandbox = wrapped ? 'danger-full-access' : role === 'climber' ? 'workspace-write' : 'read-only';
    // -i takes several files, so it goes right after exec, where the next flag ends the list.
    const args = ['exec', ...images.flatMap((f) => ['-i', f]), '-s', sandbox, '--skip-git-repo-check', '--ignore-user-config', '--ignore-rules', '--ephemeral',
      ...CODEX_OFF.flatMap((f) => ['--disable', f]), '-c', 'project_doc_max_bytes=0', '-C', cwd, '-o', lastMessageFile,
      '-m', spec.model ?? 'gpt-6.1-sol', ...(spec.effort ? ['-c', `model_reasoning_effort="${spec.effort}"`] : []), '-'];
    return { bin: 'codex', args };
  }
  if (cli === 'claude') {
    // --safe-mode: no CLAUDE.md, skills, hooks, plugins or MCP servers, so the session sees only this prompt and the files.
    // A build without it fails closed unless the spec accepts the nearest flag set (isolation: "flags").
    let iso;
    if (claudeHasSafeMode()) iso = ['--safe-mode'];
    else if (spec.isolation === 'flags') iso = ['--setting-sources', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--disable-slash-commands'];
    else throw new Error('this claude build has no --safe-mode, so a clean session cannot be guaranteed; update claude, or set isolation: "flags" on the agent spec to accept settings/MCP/skills off (CLAUDE.md may still load)');
    const args = ['-p', ...iso, '--output-format', 'json', '--no-session-persistence'];
    if (spec.model) args.push('--model', spec.model);
    if (spec.effort) args.push('--effort', spec.effort);
    if (role === 'climber') {
      args.push('--permission-mode', spec.permission_mode ?? 'acceptEdits', '--tools', spec.tools ?? 'Read,Edit,Write,Glob,Grep,Bash');
      if (spec.allowed_tools?.length) args.push('--allowed-tools', ...spec.allowed_tools);
    } else {
      args.push('--tools', role === 'judge' ? 'Read,Glob,Grep' : (spec.tools ?? ''));
    }
    return { bin: claudeBin(), args };
  }
  throw new Error(`unknown agent cli "${cli}" (use claude, codex or cmd)`);
}

export const wrapsAgent = (spec) => spec.sandbox !== 'off';

export async function runAgent(spec, role, { cwd, prompt, timeoutSec, dir, env = {}, onSpawn = null, sandbox = null, images = [] }) {
  fs.mkdirSync(dir, { recursive: true });
  const promptFile = path.join(dir, `${role}-prompt.md`);
  const lastMessageFile = path.join(dir, `${role}-last-message.txt`);
  fs.writeFileSync(promptFile, prompt);
  fs.rmSync(lastMessageFile, { force: true }); // a stale answer from an earlier run must never be read as this one
  // The agent may always write its own log folder (codex writes its last message there).
  const sb = sandbox && wrapsAgent(spec) ? { ...sandbox, write: [...(sandbox.write ?? []), dir] } : null;
  const inv = agentInvocation(spec, role, { cwd, lastMessageFile, wrapped: !!sb, images });
  const e = { HILL_PROMPT_FILE: promptFile, HILL_LAST_MESSAGE_FILE: lastMessageFile, ...(images.length ? { HILL_IMAGES: images.join('\n') } : {}), ...env };
  const opts = { cwd, input: prompt, env: e, passEnv: spec.pass_env ?? [], timeoutSec, onSpawn, sandbox: sb };
  const r = inv.shell ? await run(inv.command, opts) : await run(inv.bin, { ...opts, args: inv.args });
  let text = '';
  if ((spec.cli ?? 'claude') === 'claude') {
    // `--output-format json` prints either one result object or an array of events ending in {type:'result'}.
    try {
      const j = JSON.parse(r.stdout);
      const res = Array.isArray(j) ? j.findLast((x) => x?.type === 'result') : j;
      const init = Array.isArray(j) ? j.find((x) => x?.type === 'system' && x.subtype === 'init') : null;
      text = typeof res?.result === 'string' ? res.result : ''; r.is_error = !!res?.is_error || !res; r.cost_usd = res?.total_cost_usd; r.model = init?.model ?? null;
    } catch { text = ''; r.is_error = true; }
  } else if (spec.cli === 'codex') {
    text = fs.existsSync(lastMessageFile) ? fs.readFileSync(lastMessageFile, 'utf8') : '';
  } else {
    text = fs.existsSync(lastMessageFile) && fs.statSync(lastMessageFile).size ? fs.readFileSync(lastMessageFile, 'utf8') : r.stdout;
  }
  fs.writeFileSync(path.join(dir, `${role}-log.txt`), `exit ${r.code}${r.timedOut ? ' (timed out)' : ''} in ${r.ms}ms\n--- stdout\n${clip(r.stdout, 200000)}\n--- stderr\n${clip(r.stderr, 50000)}\n`);
  return { ...r, text };
}

export function parseJSONLoose(text) {
  if (text == null) return null;
  if (typeof text !== 'string') return text;
  const t = text.trim();
  try { return JSON.parse(t); } catch { /* fall through */ }
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) { try { return JSON.parse(fence[1]); } catch { /* fall through */ } }
  for (const [o, c] of [['{', '}'], ['[', ']']]) {
    const a = t.indexOf(o), b = t.lastIndexOf(c);
    if (a >= 0 && b > a) { try { return JSON.parse(t.slice(a, b + 1)); } catch { /* next */ } }
  }
  return null;
}
// Strict: the whole reply is one JSON value, optionally inside a single ```json fence. Nothing before or after.
export function parseJSONStrict(text) {
  const t = String(text ?? '').trim();
  const m = t.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/);
  try { return { ok: true, value: JSON.parse(m ? m[1] : t) }; } catch { return { ok: false }; }
}

// ---------- globs ----------
export function globToRegex(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === '*') {
      if (glob[i + 1] === '*') { re += glob[i + 2] === '/' ? '(?:.*/)?' : '.*'; i += glob[i + 2] === '/' ? 2 : 1; } else re += '[^/]*';
    } else if (c === '?') re += '[^/]';
    else re += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  }
  return new RegExp(`^${re}$`);
}
export const matchesAny = (file, globs) => globs.some((g) => globToRegex(g).test(file));

// Files under W (newer than `marker` when given), minus the cache globs in scope_ignore and the paths in `seen`.
// Directory globs like `node_modules/**` are pruned so big caches are never walked.
export function listFiles(W, scopeIgnore, { marker = null, seen = new Set() } = {}) {
  const pruneNames = [], prunePaths = [path.join(W, '.git')];
  for (const g of scopeIgnore) {
    let m;
    if ((m = g.match(/^\*\*\/([^*?/[\]]+)\/\*\*$/))) pruneNames.push(m[1]);
    else if ((m = g.match(/^([^*?[\]]+)\/\*\*$/))) prunePaths.push(path.join(W, m[1]));
  }
  const expr = ['(', ...prunePaths.flatMap((p, i) => [...(i ? ['-o'] : []), '-path', p]), ...pruneNames.flatMap((n) => ['-o', '-name', n]), ')', '-prune', '-o', '(', '-type', 'f', '-o', '-type', 'l', ')', ...(marker ? ['-newer', marker] : []), '-print0'];
  const r = spawnSync('find', [W, ...expr], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  return (r.stdout ?? '').split('\0').filter(Boolean).map((f) => path.relative(W, f)).filter((f) => !seen.has(f) && !matchesAny(f, scopeIgnore));
}

// Paths in a tree (commit or tree sha), with modes.
export function treeFiles(W, treeish) {
  const out = gitx({ cwd: W }, 'ls-tree', '-r', '-z', '--full-tree', treeish);
  const m = new Map();
  for (const rec of out.split('\0').filter(Boolean)) { const t = rec.indexOf('\t'); const [mode, , oid] = rec.slice(0, t).split(' '); m.set(rec.slice(t + 1), { mode, oid }); }
  return m;
}
export const treeOf = (W, rev) => git(W, 'rev-parse', `${rev}^{tree}`);
