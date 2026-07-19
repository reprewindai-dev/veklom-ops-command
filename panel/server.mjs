import { createServer } from 'node:http';
import { readFile, appendFile, readdir, stat } from 'node:fs/promises';
import { existsSync, watch } from 'node:fs';
import { join, resolve, relative } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const exec = promisify(execFile);
const PANEL_DIR = resolve(fileURLToPath(new URL('.', import.meta.url)));
const ROOT = resolve(PANEL_DIR, '..');
const PORT = Number(process.env.VEKLOM_OPS_PANEL_PORT || 4173);
const HOST = process.env.VEKLOM_OPS_PANEL_HOST || '127.0.0.1';
const VERSION_FILE = join(ROOT, 'VERSION');
const INBOX = join(ROOT, 'reports', 'command-desk-inbox.jsonl');
const MISSIONS = join(ROOT, 'reports', 'toolbox-meetings');
const DEPARTMENT_REPORTS = join(ROOT, 'reports', 'departments');
const PANEL_DATA = join(PANEL_DIR, 'data');
const TEAMS = ['command-desk','poltergeist-platform','production-truth','release-control','build-devex','security-secrets','runtime-governance','evidence-ledger','edge-fleet-vnp'];
const clients = new Set();

async function text(path, fallback = '') { try { return await readFile(path, 'utf8'); } catch { return fallback; } }
async function git(args) { try { const { stdout } = await exec('git', ['-C', ROOT, ...args]); return stdout.trim(); } catch { return 'unavailable'; } }
async function teamState(team) {
  const dir = join(ROOT, 'teams', team);
  const config = JSON.parse(await text(join(dir, 'poltergeist.config.json'), '{}'));
  const reportDir = join(dir, 'reports');
  let reports = [];
  try { reports = (await readdir(reportDir)).filter((name) => !name.endsWith('.gitkeep')).slice(-5); } catch {}
  const departmentReport = await text(join(DEPARTMENT_REPORTS, `${team}.jsonl`), '');
  let latestReport = null;
  const latestLine = departmentReport.trim().split('\n').filter(Boolean).at(-1);
  if (latestLine) { try { latestReport = JSON.parse(latestLine); } catch {} }
  return { team, mission: (await text(join(dir, 'team.md'))).split('\n').find((line) => line.toLowerCase().startsWith('mission:'))?.replace(/^mission:\s*/i, '') || 'Mission recorded in team.md', targetCount: config.targets?.length || 0, reports, latestReport, report_url: `/reports/departments/${team}`, watcher: 'not running' };
}
async function latestMission() {
  try {
    const files = (await readdir(MISSIONS)).filter((name) => name.endsWith('.json')).sort();
    if (!files.length) return null;
    const mission = JSON.parse(await text(join(MISSIONS, files.at(-1)), '{}'));
    const departments = [mission.primary_department, ...(mission.supporting_departments || [])];
    mission.responses = await Promise.all(departments.map(async (department) => {
      const reportPath = join(DEPARTMENT_REPORTS, `${department}.jsonl`);
      const raw = await text(reportPath, '');
      const latest = raw.trim().split('\n').filter(Boolean).at(-1);
      return { department, status: latest ? 'reported' : 'awaiting_response', report_url: `/reports/departments/${department}`, report: latest ? JSON.parse(latest) : null };
    }));
    return mission;
  } catch { return null; }
}
async function state() {
  const [version, branch, sha, dirty, mission, capabilities, coreBackend4, security] = await Promise.all([text(VERSION_FILE, 'unversioned'), git(['branch','--show-current']), git(['rev-parse','--short','HEAD']), git(['status','--porcelain']), latestMission(), text(join(PANEL_DATA, 'capabilities.json'), '[]'), text(join(PANEL_DATA, 'core-backend-4.json'), '[]'), text(join(PANEL_DATA, 'security.json'), '{}')]);
  return { product: 'Veklom Ops Command', version: version.trim(), branch, commit: sha, dirty: Boolean(dirty), generatedAt: new Date().toISOString(), mission, capabilities: JSON.parse(capabilities), coreBackend4: JSON.parse(coreBackend4), security: JSON.parse(security), teams: await Promise.all(TEAMS.map(teamState)) };
}
function json(res, status, payload) { res.writeHead(status, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'}); res.end(JSON.stringify(payload)); }
function html(res, status, body) { res.writeHead(status, {'content-type':'text/html; charset=utf-8','cache-control':'no-store'}); res.end(body); }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char])); }
async function reportPage(title, value) { return `<!doctype html><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>body{background:#0b0e13;color:#eef3f8;font:15px/1.5 system-ui;padding:32px}main{max-width:1000px;margin:auto}pre{white-space:pre-wrap;background:#121720;border:1px solid #26303d;border-radius:12px;padding:20px;color:#c8f6e9}a{color:#66e3c4}</style><main><p><a href="/">← Back to Veklom Ops Command</a></p><h1>${escapeHtml(title)}</h1><pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre></main>`; }
function sendEvent(payload) { const message = `data: ${JSON.stringify(payload)}\n\n`; for (const client of clients) client.write(message); }
async function body(req) { let raw=''; for await (const chunk of req) raw += chunk; if (raw.length > 10000) throw new Error('message too large'); return JSON.parse(raw || '{}'); }
async function handler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (req.method === 'GET' && url.pathname === '/api/state') return json(res, 200, await state());
  if (req.method === 'GET' && url.pathname === '/api/events') { res.writeHead(200, {'content-type':'text/event-stream','cache-control':'no-cache','connection':'keep-alive'}); res.write(`data: ${JSON.stringify(await state())}\n\n`); clients.add(res); req.on('close', () => clients.delete(res)); return; }
  if (req.method === 'GET' && url.pathname.startsWith('/reports/departments/')) {
    const department = url.pathname.split('/').at(-1);
    if (!TEAMS.includes(department)) return json(res, 404, {error:'unknown department'});
    const raw = await text(join(DEPARTMENT_REPORTS, `${department}.jsonl`), '');
    const latest = raw.trim().split('\n').filter(Boolean).at(-1);
    if (!latest) return html(res, 404, await reportPage(`${department} report`, {status:'awaiting_response'}));
    return html(res, 200, await reportPage(`${department} report`, JSON.parse(latest)));
  }
  if (req.method === 'GET' && url.pathname.startsWith('/reports/toolbox-meetings/')) {
    const mission = url.pathname.split('/').at(-1);
    if (!/^mission-[a-z0-9-]+$/.test(mission)) return json(res, 404, {error:'invalid mission'});
    const value = JSON.parse(await text(join(MISSIONS, `${mission}.json`), '{}'));
    return html(res, 200, await reportPage(`${mission} toolbox meeting`, value));
  }
  if (req.method === 'POST' && url.pathname === '/api/messages') {
    try {
      const message = await body(req);
      if (typeof message.text !== 'string' || message.text.trim().length < 1) return json(res, 400, {error:'text is required'});
      const record = { id: crypto.randomUUID(), createdAt: new Date().toISOString(), from: 'founder-operator', to: 'command-desk', text: message.text.trim(), risk: message.risk || 'medium', requiresApproval: message.requiresApproval !== false, status: 'queued' };
      await appendFile(INBOX, JSON.stringify(record) + '\n', { encoding:'utf8' }); sendEvent({type:'message', record}); return json(res, 201, record);
    } catch (error) { return json(res, 400, {error: error.message}); }
  }
  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) { res.writeHead(200, {'content-type':'text/html; charset=utf-8'}); return res.end(await text(join(PANEL_DIR, 'public', 'index.html'))); }
  if (req.method === 'GET' && url.pathname.startsWith('/')) { const requested = resolve(PANEL_DIR, 'public', `.${url.pathname}`); if (relative(join(PANEL_DIR, 'public'), requested).startsWith('..')) return json(res, 403, {error:'forbidden'}); if (existsSync(requested)) { res.writeHead(200, {'content-type': requested.endsWith('.css') ? 'text/css' : 'text/javascript'}); return res.end(await readFile(requested)); } }
  return json(res, 404, {error:'not found'});
}

createServer((req,res) => handler(req,res).catch(error => json(res, 500, {error:'panel failure', detail:error.message}))).listen(PORT, HOST, () => console.log(`Veklom Ops Panel listening on http://${HOST}:${PORT}`));
try { watch(join(ROOT, 'teams'), { recursive: true }, () => sendEvent({type:'state', data: null})); } catch { setInterval(() => sendEvent({type:'state', data: null}), 5000); }
