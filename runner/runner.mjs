import { readFile, writeFile, appendFile, mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const TEAMS = ['command-desk','poltergeist-platform','production-truth','release-control','build-devex','security-secrets','runtime-governance','evidence-ledger','edge-fleet-vnp'];
const inboxPath = join(ROOT, 'reports', 'command-desk-inbox.jsonl');
const reportsDir = join(ROOT, 'reports', 'departments');
const missionsDir = join(ROOT, 'reports', 'toolbox-meetings');
const runsDir = join(ROOT, 'reports', 'agent-runs');

const env = process.env;
const key = env.VEKLOM_AGENT_API_KEY || env.OPENAI_API_KEY;
const baseUrl = (env.VEKLOM_AGENT_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
const model = env.VEKLOM_AGENT_MODEL;
if (!key || !model) { console.error('Agent runner requires VEKLOM_AGENT_API_KEY (or OPENAI_API_KEY) and VEKLOM_AGENT_MODEL. No agent work was run.'); process.exit(2); }

async function read(path, fallback = '') { try { return await readFile(path, 'utf8'); } catch { return fallback; } }
async function json(path, fallback = {}) { try { return JSON.parse(await read(path)); } catch { return fallback; } }
function latestJsonLine(raw) { const line = raw.trim().split('\n').filter(Boolean).at(-1); return line ? JSON.parse(line) : null; }
function contractPrompt(team, mission, teamDoc, roster) { return `You are the ${team} department in Chris's private Veklom Ops Command. This is an alignment/operations task, not a production mutation task.\n\nMISSION:\n${JSON.stringify(mission)}\n\nTEAM DOCTRINE:\n${teamDoc}\n\nAGENT ROSTER:\n${roster}\n\nReturn exactly one JSON object with these keys: mission_id, department, captain, mission_understanding, owned_systems (array), risks (array), forbidden_actions (array), definition_of_done (array), handoff_to, status. status must be aligned, blocked, or needs_clarification. Never claim live production status, deployment, secret rotation, or evidence persistence unless it is included in the supplied files. Do not use tools. Do not modify files. Keep the response specific to your department.`; }
async function callModel(input) {
  const response = await fetch(`${baseUrl}/chat/completions`, { method:'POST', headers:{'content-type':'application/json','authorization':`Bearer ${key}`}, body:JSON.stringify({model, temperature:0.1, messages:[{role:'system',content:'You are a strict Veklom operations department. Output valid JSON only.'},{role:'user',content:input}]}) });
  const body = await response.json();
  if (!response.ok) throw new Error(`model request failed (${response.status}): ${body.error?.message || 'unknown error'}`);
  const content = body.choices?.[0]?.message?.content;
  if (!content) throw new Error('model returned no content');
  const fenced = content.match(/```(?:json)?\s*([\s\S]*?)```/i)?.[1] || content;
  return JSON.parse(fenced.trim());
}
function validate(report, team, missionId) {
  const required = ['mission_id','department','captain','mission_understanding','owned_systems','risks','forbidden_actions','definition_of_done','handoff_to','status'];
  for (const field of required) if (!(field in report)) throw new Error(`${team}: missing ${field}`);
  if (report.mission_id !== missionId || report.department !== team) throw new Error(`${team}: mission or department mismatch`);
  if (!['aligned','blocked','needs_clarification'].includes(report.status)) throw new Error(`${team}: invalid status`);
  for (const field of ['owned_systems','risks','forbidden_actions','definition_of_done']) if (!Array.isArray(report[field])) throw new Error(`${team}: ${field} must be an array`);
}
async function main() {
  const runId = randomUUID();
  const mission = latestJsonLine(await read(inboxPath));
  if (!mission) throw new Error('No queued founder instruction found in reports/command-desk-inbox.jsonl');
  const missionId = env.VEKLOM_AGENT_MISSION_ID || 'mission-001';
  await mkdir(reportsDir, {recursive:true}); await mkdir(runsDir, {recursive:true});
  const results = [];
  for (const team of TEAMS) {
    try {
      const teamDoc = await read(join(ROOT,'teams',team,'team.md'));
      const roster = await read(join(ROOT,'teams',team,'agents','roster.md'));
      const report = await callModel(contractPrompt(team, mission, teamDoc, roster));
      validate(report, team, missionId);
      report.reported_at = new Date().toISOString();
      await writeFile(join(reportsDir, `${team}.jsonl`), JSON.stringify(report)+'\n');
      results.push({team,status:report.status}); console.log(`${team}: ${report.status}`);
    } catch (error) { results.push({team,status:'failed',error:error.message}); console.error(`${team}: failed — ${error.message}`); }
  }
  const allResponded = results.length === TEAMS.length && results.every((item) => item.status !== 'failed');
  const missionPath = join(missionsDir, `${missionId}.json`);
  const missionRecord = await json(missionPath, {mission_id:missionId});
  missionRecord.status = allResponded ? 'department_reports_received' : 'partial_department_reports';
  missionRecord.processed_at = new Date().toISOString(); missionRecord.processed_by = 'veklom-agent-runner'; missionRecord.runner_run_id = runId;
  await writeFile(missionPath, JSON.stringify(missionRecord, null, 2)+'\n');
  const run = {run_id:runId,mission_id:missionId,model,provider:baseUrl,started_at:new Date().toISOString(),results,production_mutation:false};
  await writeFile(join(runsDir, `${runId}.json`), JSON.stringify(run, null, 2)+'\n');
  console.log(JSON.stringify(run, null, 2));
  if (env.VEKLOM_AGENT_COMMIT === 'true') { await exec('git',['-C',ROOT,'add','reports/departments','reports/toolbox-meetings','reports/agent-runs']); await exec('git',['-C',ROOT,'commit','-m',`Process ${missionId} with governed department runner`]); console.log('Committed reports. Push remains explicit: git push origin main'); }
  if (!allResponded) process.exitCode = 1;
}
main().catch((error) => { console.error(error.message); process.exitCode = 1; });
