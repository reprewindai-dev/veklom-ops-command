import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const TEAMS = [
  'backend-chief',
  'security-chief',
  'platform-chief',
  'runtime-chief',
  'qa-chief',
  'release-chief',
  'frontend-chief',
  'devex-chief',
  'protocol-mesh-captain',
  'abide-governance-engineer',
  'terminal-nexus-commander',
  'codebase-architect',
  'abide-truth-auditor',
  'cappo-truth-auditor',
  'byos-truth-auditor',
  'vnp-truth-auditor',
  'frontend-truth-auditor',
  'abide-execution-ops',
  'byos-execution-ops',
  'vnp-execution-ops',
  'cappo-execution-ops',
  'frontend-execution-ops',
  'cappo-service-restorer',
  'byos-service-restorer',
  'gnomledger-service-restorer',
  'abide-deployment-monitor'
];
const inboxPath = join(ROOT, 'reports', 'command-desk-inbox.jsonl');
const reportsDir = join(ROOT, 'reports', 'departments');
const missionsDir = join(ROOT, 'reports', 'toolbox-meetings');
const runsDir = join(ROOT, 'reports', 'agent-runs');
const key = process.env.VEKLOM_AGENT_API_KEY || process.env.OPENAI_API_KEY;

if (!key || !process.env.VEKLOM_AGENT_MODEL) {
  console.error('Command Desk runner requires VEKLOM_AGENT_API_KEY/OPENAI_API_KEY and VEKLOM_AGENT_MODEL. No workers spawned.');
  process.exit(2);
}

async function read(path, fallback = '') {
  try {
    return await readFile(path, 'utf8');
  } catch {
    return fallback;
  }
}

function parseJson(raw, context) {
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`${context}: ${error.message}`);
  }
}

function latestJsonLine(raw) {
  const line = raw.trim().split('\n').filter(Boolean).at(-1);
  if (!line) return null;
  return parseJson(line, 'command desk inbox has malformed JSONL');
}

function assertMission(value, context) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${context}: mission must be a JSON object`);
  }
  if (typeof value.mission_id !== 'string' || !value.mission_id.trim()) {
    throw new Error(`${context}: mission_id is required`);
  }
  return value;
}

function spawnWorker(team, mission, runId) {
  return new Promise((resolvePromise) => {
    const missionPath = join(missionsDir, `${mission.mission_id}.json`);
    const env = {
      ...process.env,
      VEKLOM_DEPARTMENT: team,
      VEKLOM_MISSION_PATH: missionPath,
      VEKLOM_REPORT_PATH: join(reportsDir, `${team}.jsonl`),
      VEKLOM_PARENT_RUN_ID: runId,
    };

    const child = spawn(process.execPath, [join(ROOT, 'runner', 'department-agent.mjs')], {
      cwd: ROOT,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let output = '';
    let error = '';
    child.stdout.on('data', (d) => (output += d));
    child.stderr.on('data', (d) => (error += d));
    child.on('exit', (code) => resolvePromise({
      team,
      status: code === 0 ? 'reported' : 'failed',
      output: output.trim(),
      error: error.trim(),
    }));
  });
}

async function main() {
  const inbox = await read(inboxPath);
  const trigger = latestJsonLine(inbox);
  if (!trigger) throw new Error('No queued founder instruction found');

  const missionId = process.env.VEKLOM_AGENT_MISSION_ID || 'mission-001';
  const missionFile = join(missionsDir, `${missionId}.json`);
  const mission = assertMission(parseJson(await read(missionFile, ''), `Mission file missing or unreadable: ${missionFile}`), `Mission file ${missionFile}`);
  if (mission.mission_id !== missionId) {
    throw new Error(`Mission file mission_id (${mission.mission_id}) does not match expected ${missionId}`);
  }

  await mkdir(reportsDir, { recursive: true });
  await mkdir(runsDir, { recursive: true });

  const runId = randomUUID();

  // Concurrency-limited batch runner — prevents OOM on the Ollama 3.2B node.
  // Default: 3 agents at a time. Override via VEKLOM_AGENT_CONCURRENCY env var.
  const concurrency = Math.max(1, parseInt(process.env.VEKLOM_AGENT_CONCURRENCY || '3', 10));
  const results = [];
  for (let i = 0; i < TEAMS.length; i += concurrency) {
    const batch = TEAMS.slice(i, i + concurrency);
    console.log(`[runner] Batch ${Math.floor(i / concurrency) + 1}: spawning ${batch.join(', ')}`);
    const batchResults = await Promise.all(batch.map((team) => spawnWorker(team, mission, runId)));
    results.push(...batchResults);
  }

  const all = results.every((r) => r.status === 'reported');

  mission.status = all ? 'department_reports_received' : 'partial_department_reports';
  mission.processed_at = new Date().toISOString();
  mission.processed_by = 'command-desk-parent-agent';
  mission.parent_run_id = runId;
  mission.trigger = trigger;

  await writeFile(missionFile, `${JSON.stringify(mission, null, 2)}\n`);

  const run = {
    run_id: runId,
    parent: 'command-desk',
    mission_id: mission.mission_id,
    trigger,
    children: results,
    child_count: TEAMS.length,
    production_mutation: false,
    capi_boundary: 'required for capabilities',
    started_at: new Date().toISOString(),
  };
  await writeFile(join(runsDir, `${runId}.json`), `${JSON.stringify(run, null, 2)}\n`);

  for (const result of results) console.log(`${result.team}: ${result.status}`);

  if (process.env.VEKLOM_AGENT_COMMIT === 'true') {
    const { execFile } = await import('node:child_process');
    const { promisify } = await import('node:util');
    const exec = promisify(execFile);
    await exec('git', ['-C', ROOT, 'add', 'reports/departments', 'reports/toolbox-meetings', 'reports/agent-runs']);
    await exec('git', ['-C', ROOT, 'commit', '-m', `Process ${mission.mission_id} through Command Desk child agents`]);
  }

  if (!all) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
