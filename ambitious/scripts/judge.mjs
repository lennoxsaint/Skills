#!/usr/bin/env node
// judge.mjs: the outside judge for /ambitious. A different model scores the work; the author never does.
//
//   node judge.mjs score   --brief <brief.md|text> --artifact <path> [--artifact <path> ...] [--run <run-dir>] [--round N | --concept]
//                          [--bar "all>=8,truth>=9"] [--judge auto|codex|claude] [--model <codex model>]
//                          [--author-model <your model id>] [--timeout-sec 900] [--no-transcribe]
//   node judge.mjs compare --brief <brief.md|text> --a <path>... --b <path>... --out <verdict.json> [--swap|--one-order] [same options]
//                          (runs both blind orders and names a winner only when they agree; --swap/--one-order run one order)
//   node judge.mjs prepare --artifact <path>... --dir <folder>      (only builds the judge's view: sheets, screenshots, transcript)
//
// Judges, in order (--judge auto): Codex (codex exec, read-only sandbox, no user config, nothing persisted); if Codex
// is missing, stops, or returns no valid verdict, a fresh Claude process with read-only file tools and no conversation.
// Every attempt is reported. Artifacts are copied into a neutral scratch folder, secret-looking strings are redacted,
// and each medium is prepared for a model that can only read text and images:
//   video -> ffprobe summary, loudness, contact sheet, hook sheet (first 3 s), CTA sheet (last 6 s), whisper transcript
//   html  -> full-page screenshots at 390 px and 1440 px (Playwright, else headless Chrome), sliced, plus the source
//   image -> as is;  text/code/data -> as is (redacted)
// Fails closed: a reply only counts when every dimension has a 1-10 score and a line of evidence. The pass/fail verdict
// is computed here from those scores and the bar, never taken from the judge's prose. Independence is reported, not
// assumed: the judge's model family is compared with the author's (--author-model, else flight.json author_model,
// else $AMBITIOUS_AUTHOR_MODEL). Each verdict carries a digest of the artifacts it saw, so "two judges passed the final
// version" can be checked. Verdict files are never overwritten.
// JSON on stdout. Exit 0 when a valid verdict was produced, 3 when no judge gave one, 1 on usage errors. Node 18+.
import { createHash } from 'node:crypto';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const DIMENSIONS = ['fit', 'depth', 'craft', 'money_moment', 'truth', 'delight'];
const VIDEO = new Set(['.mp4', '.mov', '.webm', '.m4v', '.mkv']);
const IMAGE = new Set(['.png', '.jpg', '.jpeg', '.webp', '.gif']);
const HTML = new Set(['.html', '.htm']);
const TEXT = new Set(['.md', '.markdown', '.txt', '.json', '.jsonl', '.csv', '.tsv', '.html', '.htm', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx',
  '.py', '.css', '.scss', '.yaml', '.yml', '.toml', '.srt', '.vtt', '.sql', '.xml', '.svg', '.sh', '.swift', '.go', '.rs', '.rb', '.java', '.kt', '.php', '.env.example']);
const SKIP_DIRS = new Set(['node_modules', '.git', '.next', 'dist', '.cache', '__pycache__', '.venv', 'venv']);
const MAX_TEXT_BYTES = 2_000_000;
const MAX_IMAGES = 16;

const SECRETS = [
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
  /\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}/g,
  /\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{16,}/g,
  /\bwhsec_[A-Za-z0-9]{16,}/g,
  /\bgh[pousr]_[A-Za-z0-9]{30,}/g,
  /\bgithub_pat_[A-Za-z0-9_]{30,}/g,
  /\bxox[abprs]-[A-Za-z0-9-]{10,}/g,
  /\bAKIA[0-9A-Z]{16}\b/g,
  /\bAIza[0-9A-Za-z_-]{35}\b/g,
  /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g,
  /(Bearer\s+)[A-Za-z0-9._~+/-]{20,}=*/g,
  /((?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|password|passwd)["']?\s*[:=]\s*["']?)[^\s"',;]{8,}/gi,
];

const argValue = (args, flag, fallback = null) => { const i = args.indexOf(flag); return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback; };
const argValues = (args, flag) => args.flatMap((a, i) => (a === flag && i + 1 < args.length ? [args[i + 1]] : []));
const has = (args, flag) => args.includes(flag);
const expand = (p) => (p && p.startsWith('~/') ? path.join(os.homedir(), p.slice(2)) : p);
const round1 = (n) => Math.round(n * 10) / 10;
const ext = (p) => path.extname(p).toLowerCase();
// writeSync, not process.stdout.write: a pipe write is async and process.exit would cut a long reply short.
const out = (obj, code = 0) => { fs.writeSync(1, JSON.stringify(obj, null, 2) + '\n'); process.exit(code); };

export function redact(text) {
  let count = 0;
  let result = String(text);
  for (const re of SECRETS) {
    result = result.replace(re, (match, prefix) => { count += 1; return (typeof prefix === 'string' && match.startsWith(prefix) ? prefix : '') + '[REDACTED]'; });
  }
  return { text: result, count };
}

function run(bin, args, opts = {}) {
  const r = spawnSync(bin, args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: opts.timeout ?? 300_000, cwd: opts.cwd });
  return { ok: !r.error && r.status === 0, stdout: r.stdout ?? '', stderr: r.stderr ?? '', error: r.error?.message };
}
// Look the binary up on PATH instead of running it: a slow first launch on a busy machine must not read as "not installed".
const exists = (bin) => {
  const isExe = (f) => { try { fs.accessSync(f, fs.constants.X_OK); return fs.statSync(f).isFile(); } catch { return false; } };
  if (bin.includes('/')) return isExe(bin);
  return (process.env.PATH ?? '').split(path.delimiter).filter(Boolean).some((dir) => isExe(path.join(dir, bin)));
};

// ---------------------------------------------------------------------------
// Preparing artifacts so a text-and-image model can judge them
// ---------------------------------------------------------------------------
function probeVideo(file) {
  const r = run('ffprobe', ['-v', 'error', '-show_entries', 'format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels', '-of', 'json', file]);
  if (!r.ok) return null;
  try {
    const j = JSON.parse(r.stdout);
    const v = (j.streams ?? []).find((s) => s.codec_type === 'video');
    const a = (j.streams ?? []).find((s) => s.codec_type === 'audio');
    const [num, den] = String(v?.r_frame_rate ?? '0/1').split('/').map(Number);
    return {
      duration_s: round1(Number(j.format?.duration ?? 0)),
      width: v?.width ?? null, height: v?.height ?? null, fps: den ? round1(num / den) : null, video_codec: v?.codec_name ?? null,
      audio: a ? { codec: a.codec_name, sample_rate: Number(a.sample_rate), channels: a.channels } : null,
      size_mb: round1(Number(j.format?.size ?? 0) / 1e6),
    };
  } catch { return null; }
}

function loudness(file) {
  const r = run('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], { timeout: 600_000 });
  const m = (r.stderr || '').match(/\{[\s\S]*?"input_i"[\s\S]*?\}/);
  if (!m) return null;
  try { const j = JSON.parse(m[0]); return { integrated_lufs: Number(j.input_i), true_peak_dbtp: Number(j.input_tp) }; } catch { return null; }
}

function sheet(file, outFile, { start = null, fromEnd = null, seconds = null, fps, cols, rows }) {
  const args = ['-hide_banner', '-loglevel', 'error', '-y'];
  if (fromEnd !== null) args.push('-sseof', String(-fromEnd));
  if (start !== null) args.push('-ss', String(start));
  args.push('-i', file);
  if (seconds !== null) args.push('-t', String(seconds));
  args.push('-vf', `fps=${fps},scale=360:-2,tile=${cols}x${rows}:padding=4:color=white`, '-frames:v', '1', outFile);
  return run('ffmpeg', args, { timeout: 300_000 }).ok && fs.existsSync(outFile);
}

function transcribe(file, outDir) {
  if (!exists('whisper')) return { ok: false, note: 'whisper not installed' };
  const r = run('whisper', [file, '--model', 'small.en', '--language', 'en', '--fp16', 'False', '--output_format', 'srt', '--output_dir', outDir], { timeout: 900_000 });
  const srt = path.join(outDir, path.basename(file, path.extname(file)) + '.srt');
  return fs.existsSync(srt) ? { ok: true, file: srt } : { ok: false, note: `whisper failed: ${(r.stderr || r.error || '').slice(-300)}` };
}

function prepareVideo(file, dest, opts, notes, images) {
  const base = path.basename(file);
  const probe = probeVideo(file);
  if (!probe) { notes.push(`${base}: ffprobe could not read it`); return; }
  const loud = probe.audio ? loudness(file) : null;
  const report = { file: base, ...probe, loudness: loud };
  fs.writeFileSync(path.join(dest, `${base}.probe.json`), JSON.stringify(report, null, 2));
  const d = Math.max(probe.duration_s, 0.5);
  const contact = path.join(dest, `${base}.contact-sheet.png`);
  if (sheet(file, contact, { fps: `${24}/${d}`, cols: 6, rows: 4 })) { images.push(contact); notes.push(`${base}: contact-sheet.png = 24 frames evenly spaced every ${round1(d / 24)} s, left to right, top to bottom`); }
  const hook = path.join(dest, `${base}.hook-sheet.png`);
  if (sheet(file, hook, { start: 0, seconds: Math.min(3, d), fps: 4, cols: 6, rows: 2 })) { images.push(hook); notes.push(`${base}: hook-sheet.png = the first 3 s at 4 frames per second`); }
  const cta = path.join(dest, `${base}.cta-sheet.png`);
  if (d > 6 && sheet(file, cta, { fromEnd: 6, fps: 2, cols: 6, rows: 2 })) { images.push(cta); notes.push(`${base}: cta-sheet.png = the last 6 s at 2 frames per second`); }
  if (opts.transcribe && probe.audio) {
    const t = transcribe(file, dest);
    if (t.ok) { fs.renameSync(t.file, path.join(dest, `${base}.transcript.srt`)); notes.push(`${base}: transcript.srt = whisper small.en transcript with timestamps (machine transcription, may contain errors)`); }
    else notes.push(`${base}: no transcript (${t.note})`);
  }
  notes.push(`${base}: probe.json = duration ${probe.duration_s} s, ${probe.width}x${probe.height} @ ${probe.fps} fps, audio ${probe.audio ? 'yes' : 'NONE'}${loud ? `, ${loud.integrated_lufs} LUFS integrated, ${loud.true_peak_dbtp} dBTP true peak` : ''}`);
}

function screenshotPage(htmlFile, outFile, width) {
  const url = 'file://' + path.resolve(htmlFile);
  const pw = run('playwright', ['screenshot', '--full-page', '--viewport-size', `${width}, ${width < 600 ? 844 : 900}`, '--wait-for-timeout', '1500', url, outFile], { timeout: 120_000 });
  if (pw.ok && fs.existsSync(outFile)) return 'playwright';
  const chrome = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium'].find((b) => exists(b));
  if (!chrome) return null;
  const r = run(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--window-size=${width},${width < 600 ? 3600 : 3200}`, `--screenshot=${outFile}`, url], { timeout: 120_000 });
  return r.ok && fs.existsSync(outFile) ? 'chrome (fixed height, not full page)' : null;
}

function slice(png, maxSlices, sliceHeight) {
  if (!exists('magick')) return [png];
  const dims = run('magick', ['identify', '-format', '%w %h', png]).stdout.trim().split(' ').map(Number);
  if (!dims[1] || dims[1] <= sliceHeight * 1.2) return [png];
  const pattern = png.replace(/\.png$/, '-part-%02d.png');
  run('magick', [png, '-crop', `${dims[0]}x${sliceHeight}`, '+repage', pattern]);
  const parts = fs.readdirSync(path.dirname(png)).filter((f) => f.startsWith(path.basename(png, '.png') + '-part-')).sort().map((f) => path.join(path.dirname(png), f));
  return parts.length ? parts.slice(0, maxSlices) : [png];
}

function prepareHtml(file, dest, notes, images) {
  const base = path.basename(file);
  for (const [label, width, sliceH, maxSlices] of [['mobile-390', 390, 2400, 3], ['desktop-1440', 1440, 1800, 4]]) {
    const shot = path.join(dest, `${base}.${label}.png`);
    const how = screenshotPage(file, shot, width);
    if (!how) { notes.push(`${base}: could not render at ${width} px (no Playwright or Chrome)`); continue; }
    const parts = slice(shot, maxSlices, sliceH);
    images.push(...parts);
    notes.push(`${base}: ${label} screenshot via ${how}${parts.length > 1 ? `, in ${parts.length} slices from the top` : ''}`);
  }
}

function copyText(src, destFile, stats) {
  const raw = fs.readFileSync(src, 'utf8');
  const { text, count } = redact(raw.length > MAX_TEXT_BYTES ? raw.slice(0, MAX_TEXT_BYTES) + '\n[TRUNCATED]' : raw);
  stats.redactions += count;
  fs.mkdirSync(path.dirname(destFile), { recursive: true });
  fs.writeFileSync(destFile, text);
}

function walk(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') && entry.name !== '.env.example') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) { if (!SKIP_DIRS.has(entry.name)) files.push(...walk(full)); } else files.push(full);
  }
  return files;
}

export function prepare(artifacts, dest, opts = {}) {
  fs.mkdirSync(dest, { recursive: true });
  const notes = [];
  const images = [];
  const stats = { redactions: 0, files: 0 };
  for (const raw of artifacts) {
    const src = path.resolve(expand(raw));
    if (!fs.existsSync(src)) { notes.push(`missing artifact: ${path.basename(src)}`); continue; }
    const entries = fs.statSync(src).isDirectory() ? walk(src).map((f) => [f, path.join(path.basename(src), path.relative(src, f))]) : [[src, path.basename(src)]];
    for (const [file, rel] of entries) {
      const e = ext(file);
      const target = path.join(dest, rel);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      stats.files += 1;
      if (VIDEO.has(e)) prepareVideo(file, path.dirname(target), opts, notes, images);
      else if (IMAGE.has(e)) { fs.copyFileSync(file, target); images.push(target); }
      else if (TEXT.has(e) || e === '') {
        try { copyText(file, target, stats); } catch { notes.push(`${rel}: unreadable, skipped`); }
        if (HTML.has(e)) prepareHtml(file, path.dirname(target), notes, images);
      } else if (['.mp3', '.wav', '.m4a', '.aac'].includes(e) && opts.transcribe) {
        const t = transcribe(file, path.dirname(target));
        notes.push(t.ok ? `${rel}: audio transcribed to ${path.basename(t.file)}` : `${rel}: audio not transcribed (${t.note})`);
      } else notes.push(`${rel}: ${e || 'binary'} file not shown to the judge`);
    }
  }
  if (images.length > MAX_IMAGES) notes.push(`${images.length} images prepared; the first ${MAX_IMAGES} are attached, the rest are in the folder`);
  return { notes, images: images.slice(0, MAX_IMAGES), stats };
}

// A fingerprint of exactly what was judged (relative names + bytes), so verdicts on different versions never get mixed.
export function artifactDigest(artifacts) {
  const hash = createHash('sha256');
  for (const raw of [...artifacts].sort()) {
    const src = path.resolve(expand(raw));
    if (!fs.existsSync(src)) { hash.update(`missing:${path.basename(src)}\n`); continue; }
    const files = fs.statSync(src).isDirectory() ? walk(src).sort() : [src];
    for (const f of files) {
      hash.update(`${path.basename(src)}/${path.relative(fs.statSync(src).isDirectory() ? src : path.dirname(src), f)}\n`);
      hash.update(fs.readFileSync(f));
    }
  }
  return hash.digest('hex').slice(0, 16);
}

// Which lab a model id belongs to. Same family = shared blind spots, so a judge from the author's family is weaker.
export function modelFamily(id) {
  const s = String(id ?? '').toLowerCase();
  if (!s || s === 'unknown') return null;
  if (/claude|opus|sonnet|haiku|fable|anthropic/.test(s)) return 'anthropic';
  if (/gpt|codex|\bo[1-9]\b|openai|\bsol\b|\bluna\b|\bastra\b/.test(s)) return 'openai';
  if (/gemini|google/.test(s)) return 'google';
  if (/grok|xai/.test(s)) return 'xai';
  return 'other';
}

export function independence(judgeModel, judgeKind, authorModel) {
  const jf = modelFamily(judgeModel) ?? (judgeKind === 'codex' ? 'openai' : judgeKind === 'claude' ? 'anthropic' : null);
  const af = modelFamily(authorModel);
  if (!af) return { independence: 'unknown', why: 'author model not given (pass --author-model or set author_model in flight.json), so independence is unverified' };
  if (!jf) return { independence: 'unknown', why: `judge model family unknown (${judgeModel ?? 'no model reported'})` };
  if (jf !== af) return { independence: 'different_family', why: `judge ${jf} vs author ${af}` };
  return { independence: 'same_family_fresh_context', why: `judge and author are both ${af}: fresh context, but shared blind spots` };
}

// ---------------------------------------------------------------------------
// Prompts
// ---------------------------------------------------------------------------
const RUBRIC = [
  'fit: does it do exactly what was asked, for the person and audience in the brief?',
  'depth: is a top professional\'s method visible (raw material, real instruments)? is it correct?',
  'craft: no rough edges; intentional, bespoke choices; follows the fundamentals of its medium?',
  'money_moment: how well does it drive the decision it exists to cause (the CTA, the buy, the yes)?',
  'truth: is every claim sourced or verifiable, nothing invented, unknowns labelled?',
  'delight: is there something unasked-for that is obviously right and that the person would keep?',
];

function fileList(root) {
  return walk(root).map((f) => path.relative(root, f)).sort().map((f) => `- ${f}`).join('\n');
}

export function scorePrompt(brief, root, notes) {
  return [
    'You are an outside judge. You did not make this work, you have not seen how it was made, and you owe the author nothing.',
    'Judge it as the person who asked for it will experience it, and as its real audience will. Read the files in this folder (you may run read-only shell commands such as ls, cat, sed, head). The attached images are part of the evidence (screenshots, contact sheets).',
    'Be specific and unsentimental. A generic or merely competent result is a 6. An 8 means a demanding professional in this field would ship it. A 10 means it would teach that professional something.',
    'Check claims against the evidence you can see; anything you cannot verify is not evidence of truth.',
    '',
    '## Brief', brief.trim(), '',
    '## What was prepared for you', ...notes.map((n) => `- ${n}`), '',
    '## Files', fileList(root), '',
    '## Score each dimension 1-10, with one line of evidence each', ...RUBRIC.map((r) => `- ${r}`), '',
    'Then name the single top_fault (the change that would most improve the work), the concrete fix, and would_keep: unasked-for things in the work that the person would keep (empty list if none).',
    'Reply with JSON only, no other text:',
    '{"scores": {"fit": 0, "depth": 0, "craft": 0, "money_moment": 0, "truth": 0, "delight": 0}, "evidence": {"fit": "", "depth": "", "craft": "", "money_moment": "", "truth": "", "delight": ""}, "top_fault": "", "fix": "", "would_keep": [], "summary": "two sentences"}',
  ].join('\n');
}

export function comparePrompt(brief, root, notes) {
  return [
    'You are an outside judge comparing two candidate deliverables, A and B, made for the same brief. You do not know who made either, and you owe neither anything.',
    'Folder A/ holds candidate A and folder B/ holds candidate B. Read the files (you may run read-only shell commands such as ls, cat, sed, head). Attached images are evidence: their file names say which candidate they belong to (A/... or B/...).',
    'Judge as the person who asked will experience each, and as the real audience will. Ignore process notes and logs: judge the work as delivered. Do not prefer the longer one for being longer.',
    '',
    '## Brief', brief.trim(), '',
    '## What was prepared for you', ...notes.map((n) => `- ${n}`), '',
    '## Files', fileList(root), '',
    '## For each dimension pick A, B or tie, with one line why', ...RUBRIC.map((r) => `- ${r}`), '',
    'Then the overall winner, the margin (slight, clear or decisive), why in two sentences, each candidate\'s top fault, and what in each the person would keep.',
    'Reply with JSON only, no other text:',
    '{"dimensions": {"fit": {"winner": "A", "why": ""}, "depth": {"winner": "A", "why": ""}, "craft": {"winner": "A", "why": ""}, "money_moment": {"winner": "A", "why": ""}, "truth": {"winner": "A", "why": ""}, "delight": {"winner": "A", "why": ""}}, "winner": "A", "margin": "clear", "why": "", "top_fault": {"A": "", "B": ""}, "would_keep": {"A": [], "B": []}}',
  ].join('\n');
}

// ---------------------------------------------------------------------------
// Running the judge
// ---------------------------------------------------------------------------
function claudeBin() {
  for (const b of ['claude', path.join(os.homedir(), '.claude/bin/claude'), path.join(os.homedir(), '.local/bin/claude')]) if (exists(b)) return b;
  return null;
}

// --safe-mode turns off the owner's CLAUDE.md, skills, plugins, hooks and MCP servers but keeps the login, so the
// fallback judge sees only the brief and the work. Older CLIs lack it; the label then says the setup may load.
const safeModeCache = new Map();
function claudeSafeMode(bin) {
  if (!safeModeCache.has(bin)) {
    const r = spawnSync(bin, ['--help'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 15000 });
    safeModeCache.set(bin, /--safe-mode\b/.test(`${r.stdout ?? ''}${r.stderr ?? ''}`));
  }
  return safeModeCache.get(bin);
}

export function judgeCommand(kind, { cwd, images, lastMessageFile, model }) {
  if (kind === 'codex') {
    // Images first: -i takes several values, so it must not swallow the flags or the stdin marker after it.
    const args = ['exec', ...images.flatMap((i) => ['-i', i]), '-s', 'read-only', '--skip-git-repo-check', '--ignore-user-config', '--ephemeral', '-C', cwd, '-o', lastMessageFile, ...(model ? ['-m', model] : []), '-'];
    return { bin: 'codex', args, stdinPrompt: true, label: 'Codex (codex exec, read-only sandbox, no user config, nothing persisted)' };
  }
  const bin = claudeBin();
  const safe = bin ? claudeSafeMode(bin) : false;
  const args = ['-p', ...(safe ? ['--safe-mode'] : []), '--output-format', 'json', '--no-session-persistence', '--strict-mcp-config', '--tools', 'Read,Glob,Grep,LS', '--add-dir', cwd];
  const label = safe
    ? 'a fresh Claude process (claude -p --safe-mode: no conversation history, no CLAUDE.md, skills, hooks, plugins or MCP; read-only file tools)'
    : 'a fresh Claude process (claude -p, read-only file tools, no conversation history; this CLI has no --safe-mode, so the owner\'s CLAUDE.md and skills may load)';
  return { bin, args, stdinPrompt: true, label, safe_mode: safe };
}

function runJudge({ bin, args, cwd, prompt, timeoutMs, silenceMs }) {
  return new Promise((resolve) => {
    const started = Date.now();
    const env = { ...process.env };
    delete env.CLAUDECODE; // a nested `claude -p` refuses to start when this is set
    let child;
    try { child = spawn(bin, args, { cwd, env, stdio: ['pipe', 'pipe', 'pipe'] }); } catch (error) { resolve({ code: null, stdout: '', stderr: error.message, killed: 'could not start', ms: 0 }); return; }
    let stdout = '';
    let stderr = '';
    let last = Date.now();
    let killed = null;
    const stop = (why) => { killed = why; child.kill('SIGTERM'); };
    const watchdog = setInterval(() => { if (Date.now() - last > silenceMs) stop(`silent for ${Math.round(silenceMs / 1000)} s`); }, 2000);
    const cap = setTimeout(() => stop(`over the ${Math.round(timeoutMs / 1000)} s limit`), timeoutMs);
    child.stdout.on('data', (c) => { last = Date.now(); stdout += c; });
    child.stderr.on('data', (c) => { last = Date.now(); stderr += c; });
    child.on('error', (e) => { stderr += e.message; });
    child.on('close', (code) => { clearInterval(watchdog); clearTimeout(cap); resolve({ code, stdout, stderr, killed, ms: Date.now() - started }); });
    child.stdin.on('error', () => {});
    child.stdin.end(prompt);
  });
}

const stripAnsi = (t) => String(t ?? '').replace(/\x1b\[[0-9;?]*[A-Za-z]/g, '').replace(/\r/g, '');
const codexModel = (...o) => (stripAnsi(o.join('\n')).match(/^\s*model:\s*(\S+)/m) ?? [])[1] ?? null;

// Returns the last top-level JSON object that has `key`. Objects nested inside a match are skipped, so a
// dimension like {"winner":"A","why":".."} can never replace the verdict that contains it.
export function extractJson(text, key) {
  const s = String(text ?? '');
  let found = null;
  for (let i = s.indexOf('{'); i !== -1; i = s.indexOf('{', i + 1)) {
    let depth = 0; let inString = false;
    for (let j = i; j < s.length; j += 1) {
      const ch = s[j];
      if (inString) { if (ch === '\\') j += 1; else if (ch === '"') inString = false; } else if (ch === '"') inString = true;
      else if (ch === '{') depth += 1;
      else if (ch === '}') {
        depth -= 1;
        if (depth === 0) {
          try { const v = JSON.parse(s.slice(i, j + 1)); if (v && v[key] !== undefined) { found = v; i = j; } } catch { /* not JSON */ }
          break;
        }
      }
    }
  }
  return found;
}

// `claude -p --output-format json` prints one result object on some builds and an array of every event on others
// (and stream-json prints one event per line). Find the result event in any of these shapes.
export function parseClaudeReply(stdout) {
  const raw = String(stdout ?? '');
  let parsed = null;
  try { parsed = JSON.parse(raw); } catch {
    const lines = raw.split('\n').map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    parsed = lines.length ? lines : null;
  }
  if (!parsed || typeof parsed !== 'object') return null;
  const events = Array.isArray(parsed) ? parsed : [parsed];
  const res = [...events].reverse().find((e) => e && e.type === 'result') ?? (Array.isArray(parsed) ? null : parsed);
  if (!res || res.result === undefined) return null;
  const init = events.find((e) => e && e.type === 'system' && e.subtype === 'init');
  return { text: String(res.result ?? ''), model: res.model ?? init?.model ?? Object.keys(res.modelUsage ?? {})[0] ?? null, isError: Boolean(res.is_error) };
}

export function parseBar(bar) {
  const rules = { all: 8, truth: 9 };
  for (const part of String(bar ?? '').split(',').map((p) => p.trim()).filter(Boolean)) {
    const m = part.match(/^([a-z_]+)\s*>=\s*(\d+(?:\.\d+)?)$/);
    if (m) rules[m[1]] = Number(m[2]);
  }
  return rules;
}

const validScore = (v) => typeof v === 'number' && Number.isFinite(v) && v >= 1 && v <= 10;
const filled = (v) => typeof v === 'string' && v.trim().length > 0;

export function applyBar(scores, rules) {
  const misses = [];
  for (const d of DIMENSIONS) {
    const v = scores?.[d];
    const need = rules[d] ?? rules.all;
    if (!validScore(v)) misses.push(`${d}: no valid 1-10 score (${JSON.stringify(v)})`);
    else if (v < need) misses.push(`${d} ${v} < ${need}`);
  }
  return { verdict: misses.length ? 'fail' : 'pass', misses };
}

// Fail closed: a reply is a verdict only if it is complete. Anything else is reported as invalid, never patched up.
export function validateScore(v) {
  const problems = [];
  if (!v || typeof v !== 'object') return ['reply is not a JSON object'];
  for (const d of DIMENSIONS) {
    if (!validScore(v.scores?.[d])) problems.push(`scores.${d} must be a number from 1 to 10 (got ${JSON.stringify(v.scores?.[d])})`);
    if (!filled(v.evidence?.[d])) problems.push(`evidence.${d} is missing`);
  }
  if (!filled(v.top_fault)) problems.push('top_fault is missing');
  if (!filled(v.fix)) problems.push('fix is missing');
  if (v.would_keep !== undefined && !Array.isArray(v.would_keep)) problems.push('would_keep must be a list');
  return problems;
}

export function validateCompare(v) {
  const problems = [];
  const pick = new Set(['A', 'B', 'tie']);
  if (!v || typeof v !== 'object') return ['reply is not a JSON object'];
  if (!pick.has(v.winner)) problems.push(`winner must be A, B or tie (got ${JSON.stringify(v.winner)})`);
  if (!['slight', 'clear', 'decisive'].includes(String(v.margin).toLowerCase()) && v.winner !== 'tie') problems.push(`margin must be slight, clear or decisive (got ${JSON.stringify(v.margin)})`);
  for (const d of DIMENSIONS) if (!pick.has(v.dimensions?.[d]?.winner)) problems.push(`dimensions.${d}.winner must be A, B or tie`);
  if (!filled(v.why)) problems.push('why is missing');
  return problems;
}

// Codex first; on a missing binary, a stop or an invalid reply, a fresh Claude (auto mode only). Every attempt is kept.
async function judgeWithFallback(kindWanted, ctx, key, validate) {
  const order = kindWanted === 'auto' ? ['codex', 'claude'] : [kindWanted];
  const attempts = [];
  let last = null;
  judges: for (const kind of order) {
    if (kind === 'codex' && !exists('codex')) { attempts.push({ kind, status: 'unavailable', note: 'codex not installed' }); continue; }
    // A judge that exits cleanly but whose reply has no readable verdict gets one more try: in our own runs a fresh
    // Claude did this once and gave a valid verdict on the retry. Stops, crashes and out-of-range scores are not retried.
    for (let tryNo = 1; tryNo <= 2; tryNo += 1) {
      const j = await callJudge(kind, ctx);
      const parsed = j.killed ? null : extractJson(j.text, key);
      const problems = parsed ? validate(parsed) : [];
      const status = j.killed ? 'stopped' : !parsed ? 'no_verdict' : problems.length ? 'invalid' : 'ok';
      const attempt = { kind, try: tryNo, model: j.model ?? 'UNKNOWN', status, seconds: round1(j.ms / 1000), note: j.killed ?? (problems.length ? problems.slice(0, 6).join('; ') : !parsed ? `no readable JSON (exit ${j.code})` : null) };
      // A failed attempt keeps what the judge said (secrets redacted; only the last 200k characters of a huge reply), so
      // the failure can be diagnosed later. It lives in the verdict file, not in flight.json.
      if (status !== 'ok') Object.assign(attempt, { reply_tail: redact(j.text ?? '').text.slice(-200000), stderr_tail: redact(j.stderrTail ?? '').text.slice(-400) });
      attempts.push(attempt);
      last = { j, parsed: status === 'ok' ? parsed : null, status, problems };
      if (status === 'ok') break judges;
      if (status !== 'no_verdict' || j.code !== 0) break;
    }
  }
  if (!last) last = { j: { kind: order[order.length - 1], label: 'none', model: null, ms: 0, text: '', killed: 'no judge available (codex and claude not found)', code: null }, parsed: null, status: 'unavailable', problems: [] };
  return { ...last, attempts };
}

async function callJudge(kind, { cwd, prompt, images, model, timeoutSec }) {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'ambitious-judge-msg-'));
  const lastMessageFile = path.join(scratch, 'last.txt');
  let finalPrompt = prompt;
  if (kind === 'claude' && images.length) finalPrompt += `\n\nThe images to look at (open each with the Read tool):\n${images.map((i) => `- ${i}`).join('\n')}`;
  const cmd = judgeCommand(kind, { cwd, images: kind === 'codex' ? images : [], lastMessageFile, model });
  if (!cmd.bin) return { kind, label: 'none', model: null, ms: 0, text: '', killed: 'no judge available (codex and claude not found)', code: null };
  const timeoutMs = timeoutSec * 1000;
  const r = await runJudge({ bin: cmd.bin, args: cmd.args, cwd, prompt: finalPrompt, timeoutMs, silenceMs: Math.min(timeoutMs, 420_000) });
  let text = stripAnsi(r.stdout);
  let usedModel = null;
  if (kind === 'claude') {
    const p = parseClaudeReply(r.stdout);
    if (p) { text = p.text; usedModel = p.model; }
  } else {
    usedModel = model ?? codexModel(r.stderr, r.stdout);
    const last = fs.existsSync(lastMessageFile) ? fs.readFileSync(lastMessageFile, 'utf8').trim() : '';
    if (last) text = last;
  }
  fs.rmSync(scratch, { recursive: true, force: true });
  return { kind, label: cmd.label, model: usedModel, ms: r.ms, text, killed: r.killed, code: r.code, stderrTail: stripAnsi(r.stderr).slice(-600) };
}

function readBrief(value) {
  if (!value) out({ status: 'usage', error: '--brief is required (a file path or the brief text)' }, 1);
  const p = expand(value);
  return fs.existsSync(p) && fs.statSync(p).isFile() ? fs.readFileSync(p, 'utf8') : value;
}

function appendToFlight(runDir, entry) {
  const file = path.join(runDir, 'flight.json');
  if (!fs.existsSync(file)) return false;
  try {
    const flight = JSON.parse(fs.readFileSync(file, 'utf8'));
    flight.judges = [...(flight.judges ?? []), entry];
    fs.writeFileSync(file, JSON.stringify(flight, null, 2) + '\n');
    return true;
  } catch { return false; }
}

function readFlight(runDir) {
  try { return JSON.parse(fs.readFileSync(path.join(runDir, 'flight.json'), 'utf8')); } catch { return null; }
}

// judge-<round>-<kind>.json, then -2, -3...: an earlier verdict is never overwritten.
function freshName(runDir, roundNo, kind) {
  for (let n = 1; ; n += 1) {
    const name = `judge-${roundNo}-${kind}${n > 1 ? `-${n}` : ''}.json`;
    if (!fs.existsSync(path.join(runDir, name))) return name;
  }
}

const noVerdictNote = (status, j, problems) => (
  status === 'stopped' ? `The judge was stopped (${j.killed}). There is no verdict: report that, do not guess one.`
    : status === 'invalid' ? `The judge's reply was incomplete or out of range (${problems.slice(0, 4).join('; ')}). It does not count as a verdict.`
      : status === 'unavailable' ? 'No judge could run. Record "judge: none available - <reason>" in gaps.'
        : status === 'no_verdict' ? `The judge replied without readable JSON (exit ${j.code}).` : null);

async function score(args) {
  const brief = readBrief(argValue(args, '--brief'));
  const artifacts = argValues(args, '--artifact');
  if (!artifacts.length) out({ status: 'usage', error: 'give at least one --artifact' }, 1);
  const runDir = argValue(args, '--run') ? path.resolve(expand(argValue(args, '--run'))) : null;
  const flight = runDir ? readFlight(runDir) : null;
  const lastRound = Math.max(0, ...((flight?.judges ?? []).map((x) => Number(x?.round) || 0)));
  // --concept judges a plan, script or storyboard before an expensive build. It is logged as round 0 and never counts
  // as the verdict on the finished work.
  const concept = has(args, '--concept');
  const roundNo = concept ? 0 : Number(argValue(args, '--round', lastRound + 1));
  const authorModel = argValue(args, '--author-model') ?? (flight?.author_model || null) ?? process.env.AMBITIOUS_AUTHOR_MODEL ?? null;
  const rules = parseBar(argValue(args, '--bar', 'all>=8,truth>=9'));
  const view = fs.mkdtempSync(path.join(os.tmpdir(), 'ambitious-judge-'));
  const prep = prepare(artifacts, view, { transcribe: !has(args, '--no-transcribe') });
  const digest = artifactDigest(artifacts);
  const prompt = scorePrompt(brief, view, prep.notes);
  const { j, parsed, status, problems, attempts } = await judgeWithFallback(argValue(args, '--judge', 'auto'),
    { cwd: view, prompt, images: prep.images, model: argValue(args, '--model'), timeoutSec: Number(argValue(args, '--timeout-sec', 900)) }, 'scores', validateScore);
  const bar = parsed ? applyBar(parsed.scores, rules) : null;
  const indep = independence(j.model, j.kind, authorModel);
  const result = {
    mode: 'score', stage: concept ? 'concept' : 'work', round: roundNo, kind: j.kind, label: j.label, model: j.model ?? 'UNKNOWN', seconds: round1(j.ms / 1000),
    status, note: noVerdictNote(status, j, problems), attempts,
    independence: indep.independence, independence_why: indep.why, author_model: authorModel ?? 'UNKNOWN', artifact_digest: digest,
    verdict: bar?.verdict ?? null, bar: rules, misses: bar?.misses ?? [],
    scores: parsed?.scores ?? null, evidence: parsed?.evidence ?? null, top_fault: parsed?.top_fault ?? null, fix: parsed?.fix ?? null,
    would_keep: parsed?.would_keep ?? [], summary: parsed?.summary ?? null,
    prepared: prep.notes, redactions: prep.stats.redactions, judge_view: view,
    raw_reply: parsed ? undefined : redact(j.text || j.stderrTail || '').text.slice(-200000),
  };
  if (runDir) {
    fs.mkdirSync(runDir, { recursive: true });
    const name = freshName(runDir, roundNo, result.kind);
    fs.writeFileSync(path.join(runDir, name), JSON.stringify(result, null, 2));
    result.file = name;
    result.logged_in_flight = appendToFlight(runDir, {
      round: roundNo, stage: result.stage, kind: result.kind, label: result.label, model: result.model, file: name, status: result.status, verdict: result.verdict,
      scores: result.scores, top_fault: result.top_fault, independence: result.independence, artifact_digest: digest,
      artifacts: artifacts.map((p) => path.resolve(expand(p))), attempts: attempts.map((a) => `${a.kind}:${a.status}`),
    });
  }
  out(result, result.status === 'ok' ? 0 : 3);
}

// Folds two blind orders into one result. A winner counts only when both orders name the same input; two orders that
// both pick the same shown slot (first or second) are position bias, not a preference.
export function combineOrders(r1, r2) {
  const ok = r1.status === 'ok' && r2.status === 'ok';
  const agree = ok && r1.winner_input === r2.winner_input;
  const bias = ok && !agree && r1.winner_shown === r2.winner_shown && r1.winner_shown !== 'tie';
  const winner = !ok ? null : agree ? r1.winner_input : 'no_consistent_winner';
  const note = !ok ? 'no verdict: at least one order gave no valid reply, so there is no winner'
    : agree ? `both orders picked ${winner === 'tie' ? 'a tie' : `input ${winner}`}`
    : bias ? `both orders picked the ${r1.winner_shown === 'A' ? 'first' : 'second'}-shown entry: position bias, no winner`
    : 'the orders disagree: no winner';
  const dims = ok ? Object.fromEntries(Object.keys(r1.dimensions_input ?? {}).map((k) => {
    const w1 = r1.dimensions_input[k]?.winner; const w2 = r2.dimensions_input?.[k]?.winner;
    return [k, w1 === w2 ? w1 : 'split'];
  })) : null;
  return {
    mode: 'compare', orders_run: 2, status: ok ? 'ok' : (r1.status !== 'ok' ? r1.status : r2.status),
    winner_input: winner, consistent: agree, position_bias: bias, note, dimensions_agreed: dims,
    top_fault_input: { a: [r1.top_fault_input?.a, r2.top_fault_input?.a].filter(Boolean), b: [r1.top_fault_input?.b, r2.top_fault_input?.b].filter(Boolean) },
    would_keep_input: { a: [...new Set([...(r1.would_keep_input?.a ?? []), ...(r2.would_keep_input?.a ?? [])])], b: [...new Set([...(r1.would_keep_input?.b ?? []), ...(r2.would_keep_input?.b ?? [])])] },
    digest_a: r1.digest_a, digest_b: r1.digest_b, orders: [r1, r2],
  };
}

async function compareOnce(args, a, b, swap) {
  const brief = readBrief(argValue(args, '--brief'));
  const view = fs.mkdtempSync(path.join(os.tmpdir(), 'ambitious-compare-'));
  const opts = { transcribe: !has(args, '--no-transcribe') };
  const shownA = swap ? b : a;
  const shownB = swap ? a : b;
  const pa = prepare(shownA, path.join(view, 'A'), opts);
  const pb = prepare(shownB, path.join(view, 'B'), opts);
  const notes = [...pa.notes.map((n) => `A/ ${n}`), ...pb.notes.map((n) => `B/ ${n}`)];
  const prompt = comparePrompt(brief, view, notes);
  const { j, parsed, status, problems, attempts } = await judgeWithFallback(argValue(args, '--judge', 'auto'),
    { cwd: view, prompt, images: [...pa.images.slice(0, 8), ...pb.images.slice(0, 8)], model: argValue(args, '--model'), timeoutSec: Number(argValue(args, '--timeout-sec', 1200)) }, 'winner', validateCompare);
  const toInput = (w) => (w === 'A' ? (swap ? 'b' : 'a') : w === 'B' ? (swap ? 'a' : 'b') : 'tie');
  const indep = independence(j.model, j.kind, argValue(args, '--author-model') ?? process.env.AMBITIOUS_AUTHOR_MODEL ?? null);
  return {
    mode: 'compare', swapped: swap, kind: j.kind, label: j.label, model: j.model ?? 'UNKNOWN', seconds: round1(j.ms / 1000),
    status, note: noVerdictNote(status, j, problems), attempts, independence: indep.independence, independence_why: indep.why,
    digest_a: artifactDigest(a), digest_b: artifactDigest(b),
    winner_shown: parsed?.winner ?? null, winner_input: parsed ? toInput(parsed.winner) : null, margin: parsed?.margin ?? null, why: parsed?.why ?? null,
    dimensions_input: parsed?.dimensions ? Object.fromEntries(Object.entries(parsed.dimensions).map(([k, v]) => [k, { winner: toInput(v?.winner), why: v?.why ?? '' }])) : null,
    top_fault_input: parsed?.top_fault ? { a: parsed.top_fault[swap ? 'B' : 'A'] ?? null, b: parsed.top_fault[swap ? 'A' : 'B'] ?? null } : null,
    would_keep_input: parsed?.would_keep ? { a: parsed.would_keep[swap ? 'B' : 'A'] ?? [], b: parsed.would_keep[swap ? 'A' : 'B'] ?? [] } : null,
    prepared: notes, redactions: pa.stats.redactions + pb.stats.redactions, judge_view: view,
    raw_reply: parsed ? undefined : redact(j.text || j.stderrTail || '').text.slice(-200000),
  };
}

// Both orders by default: a single blind order mostly measures which slot the judge prefers. --swap or --one-order
// runs a single order (swapped or not), for when the two orders run as separate jobs.
async function compare(args) {
  const a = argValues(args, '--a');
  const b = argValues(args, '--b');
  const outFile = argValue(args, '--out');
  if (!a.length || !b.length || !outFile) out({ status: 'usage', error: 'compare needs --a <path>..., --b <path>... and --out <file>' }, 1);
  const single = has(args, '--swap') || has(args, '--one-order');
  const result = single ? await compareOnce(args, a, b, has(args, '--swap'))
    : combineOrders(...(await Promise.all([compareOnce(args, a, b, false), compareOnce(args, a, b, true)])));
  fs.mkdirSync(path.dirname(path.resolve(expand(outFile))), { recursive: true });
  fs.writeFileSync(path.resolve(expand(outFile)), JSON.stringify(result, null, 2));
  out(result, result.status === 'ok' ? 0 : 3);
}

async function main() {
  const [cmd, ...args] = process.argv.slice(2);
  if (cmd === 'score') return score(args);
  if (cmd === 'compare') return compare(args);
  if (cmd === 'prepare') {
    const dir = argValue(args, '--dir');
    if (!dir) out({ status: 'usage', error: 'prepare needs --dir' }, 1);
    const p = prepare(argValues(args, '--artifact'), path.resolve(expand(dir)), { transcribe: !has(args, '--no-transcribe') });
    return out({ status: 'ok', dir: path.resolve(expand(dir)), ...p });
  }
  out({ status: 'usage', usage: 'judge.mjs score|compare|prepare (see the header of this file)' }, 1);
}

// pathToFileURL, not a hand-built file:// string: a folder name with a space is %20 in import.meta.url.
if (process.argv[1] && import.meta.url === pathToFileURL(fs.realpathSync(process.argv[1])).href) main();
