import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const TEAMS = ['command-desk','poltergeist-platform','production-truth','release-control','build-devex','security-secrets','runtime-governance','evidence-ledger','edge-fleet-vnp'];
const inboxPath = join(ROOT,'reports','command-desk-inbox.jsonl');
const reportsDir = join(ROOT,'reports','departments');
const missionsDir = join(ROOT,'reports','toolbox-meetings');
const runsDir = join(ROOT,'reports','agent-runs');
const key = process.env.VEKLOM_AGENT_API_KEY || process.env.OPENAI_API_KEY;
if (!key || !process.env.VEKLOM_AGENT_MODEL) { console.error('Command Desk runner requires VEKLOM_AGENT_API_KEY/OPENAI_API_KEY and VEKLOM_AGENT_MODEL. No workers spawned.'); process.exit(2); }
async function read(path, fallback='') { try { return await readFile(path,'utf8'); } catch { return fallback; } }
function latestJsonLine(raw) { const line=raw.trim().split('\n').filter(Boolean).at(-1); return line ? JSON.parse(line) : null; }
function spawnWorker(team, mission, runId) { return new Promise((resolvePromise) => { const env={...process.env, VEKLOM_DEPARTMENT:team, VEKLOM_MISSION_PATH:join(missionsDir,`${mission.mission_id}.json`), VEKLOM_REPORT_PATH:join(reportsDir,`${team}.jsonl`), VEKLOM_PARENT_RUN_ID:runId}; const child=spawn(process.execPath,[join(ROOT,'runner','department-agent.mjs')],{cwd:ROOT,env,stdio:['ignore','pipe','pipe']}); let output=''; let error=''; child.stdout.on('data',d=>output+=d); child.stderr.on('data',d=>error+=d); child.on('exit',code=>resolvePromise({team,status:code===0?'reported':'failed',output:output.trim(),error:error.trim()})); }); }
async function main() { const mission=latestJsonLine(await read(inboxPath)); if(!mission) throw new Error('No queued founder instruction found'); const missionId=process.env.VEKLOM_AGENT_MISSION_ID||'mission-001'; const missionFile=join(missionsDir,`${missionId}.json`); if(!(await read(missionFile,''))) throw new Error(`Mission file missing: ${missionFile}`); await mkdir(reportsDir,{recursive:true}); await mkdir(runsDir,{recursive:true}); const runId=randomUUID(); const results=await Promise.all(TEAMS.map(team=>spawnWorker(team,mission,runId))); const all=results.every(r=>r.status==='reported'); const record=JSON.parse(await read(missionFile,'{}')); record.status=all?'department_reports_received':'partial_department_reports'; record.processed_at=new Date().toISOString(); record.processed_by='command-desk-parent-agent'; record.parent_run_id=runId; await writeFile(missionFile,JSON.stringify(record,null,2)+'\n'); const run={run_id:runId,parent:'command-desk',mission_id:missionId,children:results,child_count:TEAMS.length,production_mutation:false,capi_boundary:'required for capabilities',started_at:new Date().toISOString()}; await writeFile(join(runsDir,`${runId}.json`),JSON.stringify(run,null,2)+'\n'); for(const result of results) console.log(`${result.team}: ${result.status}`); if(process.env.VEKLOM_AGENT_COMMIT==='true'){const {execFile}=await import('node:child_process');const {promisify}=await import('node:util');const exec=promisify(execFile);await exec('git',['-C',ROOT,'add','reports/departments','reports/toolbox-meetings','reports/agent-runs']);await exec('git',['-C',ROOT,'commit','-m',`Process ${missionId} through Command Desk child agents`]);} if(!all)process.exitCode=1; }
main().catch(error=>{console.error(error.message);process.exitCode=1;});
