#!/usr/bin/env node
// mine_tools.mjs --server <name> [--roots dir,dir] [--since YYYY-MM-DD] [--out file.jsonl] [--include-sidechains]
// Turns Claude Code and Codex transcripts into "the user asked X -> the agent called tools Y" turns: the raw
// material for tool-choice and agent-guidance hills. One JSONL row per user turn that called a tool of <server>.
// Obvious secrets (API keys, bearer tokens) are masked; the files stay on this machine.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';
import { spawn, spawnSync } from 'node:child_process';

const argv = process.argv.slice(2);
const flag = (n, d = null) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true) : d; };
const server = flag('server');
if (!server) { console.error('usage: mine_tools.mjs --server <mcp server name> [--roots a,b] [--since 2026-10-01] [--out turns.jsonl]'); process.exit(1); }
const roots = String(flag('roots', `${os.homedir()}/.claude/projects,${os.homedir()}/.codex/sessions`)).split(',').map((r) => r.replace(/^~/, os.homedir()));
const since = flag('since') ? new Date(flag('since')).getTime() : 0;
const outFile = flag('out');
const withSidechains = !!flag('include-sidechains');
const prefix = `mcp__${server}__`;

const SECRET = [/\b(sk|rk|pk)-[A-Za-z0-9_-]{16,}/g, /\bgh[pousr]_[A-Za-z0-9]{20,}/g, /\bfco_[A-Za-z0-9_-]{10,}/g, /\bxox[abpr]-[A-Za-z0-9-]{10,}/g, /Bearer\s+[A-Za-z0-9._~+/-]{16,}=*/g, /\bAIza[0-9A-Za-z_-]{30,}/g, /\b[a-f0-9]{40,}\b/g];
const mask = (s) => SECRET.reduce((t, re) => t.replace(re, '[secret]'), s);
const clip = (s, n) => (s.length > n ? `${s.slice(0, n)}…` : s);
const sortKeys = (x) => (Array.isArray(x) ? x.map(sortKeys) : x && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, sortKeys(x[k])])) : x);
const canon = (v) => { let x = v; if (typeof x === 'string') { try { x = JSON.parse(x); } catch { return x; } } return JSON.stringify(sortKeys(x ?? {})); };
// Text the person actually typed: drop harness wrappers (system reminders, command echoes, hook output).
function humanText(raw) {
  const t = String(raw)
    .replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, '')
    .replace(/<(command-[a-z]+|local-command-[a-z]+|bash-[a-z]+|task-notification|user-prompt-submit-hook)>[\s\S]*?<\/\1>/g, '')
    .trim();
  if (!t || /^\[Request interrupted/.test(t) || /^This session is being continued/.test(t)) return '';
  return t;
}

function* walk(dir) {
  let ents = [];
  try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else if (e.name.endsWith('.jsonl')) yield p;
  }
}

async function mineFile(file) {
  const turns = [];
  let cur = null, lineNo = 0, cwd = null;
  const results = new Map();
  const flush = () => { if (cur?.calls.some((c) => c.mine)) turns.push(cur); cur = null; };
  const startTurn = (text, source, at) => {
    const prev = cur; flush();
    if (prev?.calls.some((c) => c.mine)) prev.next_user = text;
    cur = { source, at, cwd, user: text, tools: [], calls: [], first_in_session: !sawMine };
  };
  let sawMine = false;
  // Codex can log one MCP call twice: as a direct function_call and as an McpToolCall item. Keep one; the item's id
  // wins so its status carries the error.
  const addCall = (name, id, input, from) => {
    const key = `${name}\0${canon(input)}`;
    const twin = from && cur.calls.find((c) => c.key === key && c.from && c.from !== from && !c.paired);
    if (twin) { twin.paired = true; if (from === 'item') twin.id = id; return; }
    cur.calls.push({ name, id, mine: name.startsWith(prefix), input, key, from });
    if (name.startsWith(prefix)) sawMine = true;
  };
  // Older Codex sessions are stored zstd-compressed (.jsonl.zst); stream them through zstdcat.
  const input = file.endsWith('.zst') ? spawn('zstdcat', [file], { stdio: ['ignore', 'pipe', 'ignore'] }).stdout : fs.createReadStream(file);
  const rl = readline.createInterface({ input, crlfDelay: Infinity });
  for await (const line of rl) {
    lineNo++;
    let e; try { e = JSON.parse(line); } catch { continue; }
    const at = e.timestamp ?? null;
    // ---- Claude Code transcript
    if (e.type === 'user' || e.type === 'assistant') {
      if (e.isSidechain && !withSidechains) continue;
      cwd = e.cwd ?? cwd;
      const c = e.message?.content;
      if (e.type === 'user') {
        if (Array.isArray(c) && c.some((x) => x?.type === 'tool_result')) {
          for (const x of c) if (x?.type === 'tool_result') results.set(x.tool_use_id, x.is_error ? resultText(x.content) || 'error' : null);
          continue;
        }
        const text = humanText(typeof c === 'string' ? c : (c ?? []).filter((x) => x?.type === 'text').map((x) => x.text).join('\n'));
        if (!text) continue;
        startTurn(text, `${file}#L${lineNo}`, at);
      } else if (cur && Array.isArray(c)) {
        for (const x of c) {
          if (x?.type !== 'tool_use') continue;
          const name = String(x.name);
          addCall(name, x.id, x.input, null);
        }
      }
      continue;
    }
    // ---- Codex rollout
    if (e.type === 'session_meta') { cwd = e.payload?.cwd ?? cwd; continue; }
    // Codex logs every MCP call (direct or from a code-mode `exec` block) as one McpToolCall item.
    if (e.type === 'event_msg' && e.payload?.type === 'item_completed' && e.payload.item?.type === 'McpToolCall') {
      const it = e.payload.item;
      if (cur) {
        const name = `mcp__${it.server}__${it.tool}`;
        addCall(name, it.id, it.arguments, 'item');
        results.set(it.id, it.status !== 'completed' || it.result?.isError || it.error ? resultText(it.result?.content ?? it.error ?? it.result) || 'error' : null);
      }
      continue;
    }
    if (e.type === 'response_item') {
      const p = e.payload ?? {};
      if (p.type === 'message' && p.role === 'user') {
        const text = humanText((p.content ?? []).filter((x) => /text/.test(x?.type)).map((x) => x.text).join('\n'));
        if (!text || text.startsWith('<environment_context>') || text.startsWith('# AGENTS.md')) continue;
        startTurn(text, `${file}#L${lineNo}`, at);
      } else if (cur && (p.type === 'function_call' || p.type === 'custom_tool_call')) {
        // Codex writes direct MCP calls either as name "mcp__S__tool" or as namespace "mcp__S" + name "tool".
        const name = p.namespace ? `${String(p.namespace).replace(/__$/, '')}__${p.name}` : String(p.name);
        let input = p.arguments ?? p.input; try { input = JSON.parse(input); } catch { /* keep text */ }
        addCall(name, p.call_id, input, name.startsWith('mcp__') ? 'call' : null);
      } else if (p.type === 'function_call_output' || p.type === 'custom_tool_call_output') {
        const o = typeof p.output === 'string' ? p.output : JSON.stringify(p.output ?? '');
        results.set(p.call_id, /"is_error":\s*true|^Error:|"isError":\s*true/.test(o.slice(0, 400)) ? o : null);
      }
    }
  }
  flush();
  const rows = [];
  for (const t of turns) {
    if (since && t.at && new Date(t.at).getTime() < since) continue;
    const mine = t.calls.filter((c) => c.mine);
    if (!mine.length) continue;
    rows.push({
      source: t.source, at: t.at, cwd: t.cwd,
      user: mask(clip(t.user, 4000)),
      tools: mine.map((c) => c.name.slice(prefix.length)),
      first_tool: mine[0].name.slice(prefix.length),
      first_input: mask(clip(JSON.stringify(mine[0].input ?? {}), 1500)),
      errors: mine.filter((c) => results.get(c.id)).map((c) => c.name.slice(prefix.length)),
      error_text: mine.filter((c) => results.get(c.id)).map((c) => mask(clip(String(results.get(c.id)), 300))).slice(0, 5),
      next_user: t.next_user ? mask(clip(t.next_user, 600)) : null,
      first_in_session: t.first_in_session,
      other_tools_before_first: t.calls.slice(0, t.calls.indexOf(mine[0])).map((c) => c.name).slice(0, 12),
    });
  }
  return rows;
}

function resultText(v) {
  if (v == null) return '';
  if (typeof v === 'string') return v;
  if (Array.isArray(v)) return v.map((x) => (typeof x === 'string' ? x : x?.text ?? '')).join(' ').trim();
  if (Array.isArray(v.content)) return resultText(v.content);
  return v.message ?? JSON.stringify(v);
}

// grep finds candidate files fast (and copes with logs too big to load), zstdcat+grep does the same for
// compressed sessions; each match is then streamed.
const rows = [];
let files = 0;
// One extended regex (spaces after the colon tolerated) for each record shape that names a call to <server>:
// "name":"mcp__S__tool", "server":"S", and "namespace":"mcp__S" (with "name":"tool" beside it).
const reEsc = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const needle = `"name":[[:space:]]*"${reEsc(prefix)}|"server":[[:space:]]*"${reEsc(server)}"|"namespace":[[:space:]]*"mcp__${reEsc(server)}(__)?"`;
// Compressed sessions need zstdcat. Without it they are counted and reported, never skipped in silence.
const hasZstd = spawnSync('/bin/sh', ['-c', 'command -v zstdcat'], { encoding: 'utf8' }).status === 0;
let unreadZst = 0;
for (const root of roots) {
  if (!fs.existsSync(root)) continue;
  if (!hasZstd) unreadZst += Number(spawnSync('/bin/sh', ['-c', `find "$1" -name '*.jsonl.zst' | wc -l`, 'sh', root], { encoding: 'utf8' }).stdout.trim()) || 0;
  const g = spawnSync('grep', ['-rlE', '--include=*.jsonl', '-e', needle, root], { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  const z = spawnSync('/bin/sh', ['-c', `find "$1" -name '*.jsonl.zst' -print0 | xargs -0 -P 8 -n 25 sh -c 'a="$0"; for f; do zstdcat "$f" 2>/dev/null | grep -qE -e "$a" && echo "$f"; done' "$2"`, 'sh', root, needle], { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  for (const f of [...g.stdout.split('\n'), ...z.stdout.split('\n')].filter(Boolean)) {
    if (!withSidechains && f.includes('/subagents/')) continue;
    if (since && fs.statSync(f).mtimeMs < since) continue;
    files++;
    try { rows.push(...await mineFile(f)); } catch (err) { console.error(`skip ${f}: ${err.message}`); }
  }
}
rows.sort((a, b) => String(a.at).localeCompare(String(b.at)));
if (unreadZst) console.error(`INCOMPLETE: ${unreadZst} compressed session file(s) (.jsonl.zst) were not read because zstdcat is not installed. Install zstd and run again.`);
if (outFile) {
  fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
  const tmp = `${outFile}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, rows.map((r) => JSON.stringify(r)).join('\n') + (rows.length ? '\n' : ''));
  fs.renameSync(tmp, outFile);
}
const count = (k) => Object.entries(rows.reduce((m, r) => { m[r[k]] = (m[r[k]] ?? 0) + 1; return m; }, {})).sort((a, b) => b[1] - a[1]);
process.stdout.write(`${JSON.stringify({
  server, files_with_calls: files, turns: rows.length,
  turns_with_errors: rows.filter((r) => r.errors.length).length,
  first_tool: Object.fromEntries(count('first_tool').slice(0, 25)),
  out: outFile ?? null,
}, null, 2)}\n`);
