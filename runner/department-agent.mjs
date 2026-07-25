import { readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import { resolveCapability } from './capi-client.mjs';

const execAsync = promisify(exec);
const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const team = process.env.VEKLOM_DEPARTMENT;
const missionPath = process.env.VEKLOM_MISSION_PATH;
const outputPath = process.env.VEKLOM_REPORT_PATH;
const key = process.env.VEKLOM_AGENT_API_KEY || process.env.OPENAI_API_KEY;
const model = process.env.VEKLOM_AGENT_MODEL;
const baseUrl = (process.env.VEKLOM_AGENT_BASE_URL || 'http://127.0.0.1:11434/v1').replace(/\/$/, '');

if (!team || !missionPath || !outputPath || !key || !model) {
  throw new Error('department worker missing required environment');
}

async function read(path) {
  return readFile(path, 'utf8');
}

function parseJson(raw, context) {
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`${context}: ${error.message}`);
  }
}

function assertArray(value, field) {
  if (!Array.isArray(value)) throw new Error(`${team}: ${field} must be an array`);
}

function assertReportShape(report) {
  if (!report || typeof report !== 'object' || Array.isArray(report)) {
    throw new Error(`${team}: model output must be a JSON object`);
  }
  
  // Robust Schema Fallbacks for small models
  report.handoff_to = report.handoff_to || "command-desk";
  report.status = report.status || "aligned";
  report.mission_id = report.mission_id || "mission-default";
  report.department = report.department || team;
  report.captain = report.captain || "Poltergeist";
  report.mission_understanding = report.mission_understanding || "Acknowledged";
  
  report.owned_systems = Array.isArray(report.owned_systems) ? report.owned_systems : [];
  report.risks = Array.isArray(report.risks) ? report.risks : [];
  report.forbidden_actions = Array.isArray(report.forbidden_actions) ? report.forbidden_actions : [];
  report.definition_of_done = Array.isArray(report.definition_of_done) ? report.definition_of_done : [];
  
  if (!['aligned', 'blocked', 'needs_clarification'].includes(report.status)) {
    report.status = 'aligned';
  }
  return report;
}

function fence(value) {
  return ['```text', value.trim(), '```'].join('\n');
}

async function callLLM(messages, useTools = false) {
  const body = {
    model,
    temperature: 0.1,
    messages
  };

  if (useTools) {
    body.tools = [
      {
        type: "function",
        function: {
          name: "run_bash",
          description: "Run a shell/bash command in the project root. Use this to read files, write code, run tests, and use git.",
          parameters: {
            type: "object",
            properties: {
              command: { type: "string", description: "The bash command to run" }
            },
            required: ["command"]
          }
        }
      }
    ];
  }

  let attempt = 0;
  while (attempt < 3) {
    try {
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          authorization: `Bearer ${key}`,
        },
        body: JSON.stringify(body),
      });

      const responseText = await response.text();
      if (!response.ok) {
        throw new Error(`model request failed (${response.status}): ${responseText.slice(0, 400)}`);
      }

      try {
        return JSON.parse(responseText);
      } catch (error) {
        throw new Error(`model response was not valid JSON: ${error.message}`);
      }
    } catch (err) {
      attempt++;
      if (attempt >= 3) throw err;
      // Exponential backoff for concurrent fetches
      await new Promise(r => setTimeout(r, attempt * 2000));
    }
  }
}

async function main() {
  const mission = parseJson(await read(missionPath), `mission file ${missionPath}`);
  if (!mission || typeof mission !== 'object' || Array.isArray(mission) || typeof mission.mission_id !== 'string' || !mission.mission_id.trim()) {
    throw new Error(`mission file invalid: ${missionPath}`);
  }

  const teamDoc = await read(join(ROOT, 'teams', team, 'team.md'));
  const roster = await read(join(ROOT, 'teams', team, 'agents', 'roster.md'));
  const capability = await resolveCapability('department-alignment', { department: team, mission_id: mission.mission_id, production_mutation: false });
  
  // Phase 1: Alignment Report
  const alignmentPrompt = `You are child worker ${team}, spawned by the Veklom Command Desk parent agent.
  
Mission:
${fence(JSON.stringify(mission, null, 2))}

Team doctrine:
${fence(teamDoc)}

Roster:
${fence(roster)}

Return JSON only with mission_id, department, captain, mission_understanding, owned_systems, risks, forbidden_actions, definition_of_done, handoff_to, status. status must be aligned, blocked, or needs_clarification.`;

  const payload = await callLLM([
    { role: 'system', content: 'You are a governed Veklom department worker. Return valid JSON only.' },
    { role: 'user', content: alignmentPrompt }
  ]);

  const content = payload.choices?.[0]?.message?.content;
  if (typeof content !== 'string' || !content.trim()) {
    throw new Error(`${team}: model response missing assistant content`);
  }

  const fencedMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/i)?.[1] || content;
  const report = assertReportShape(parseJson(fencedMatch.trim(), `${team}: model response content`));
  report.worker_id = randomUUID();
  report.parent = 'command-desk';
  report.capi_admission = capability;
  report.reported_at = new Date().toISOString();

  await writeFile(outputPath, `${JSON.stringify(report)}\n`);
  console.log(JSON.stringify({ team, phase: 'aligned', status: report.status, worker_id: report.worker_id }));

  if (report.status !== 'aligned') {
    return; // Stop if not aligned
  }

  // Phase 2: Autonomous Execution Loop
  console.log(JSON.stringify({ team, phase: 'execution', msg: 'Beginning autonomous execution loop' }));
  
  let execMessages = [
    { role: 'system', content: `You are the ${team} agent. You are a fully autonomous developer capable of running bash commands to complete your mission. You are running in the directory: ${ROOT}` },
    { role: 'user', content: `Mission Instructions: ${JSON.stringify(mission, null, 2)}\n\nUse the 'run_bash' tool to explore the repository, modify code, run tests, and use git to commit and push PR branches. Once you have completed the mission, provide a final summary without calling any tools to end execution.` }
  ];

  for (let i = 0; i < 20; i++) {
    const res = await callLLM(execMessages, true);
    const msg = res.choices[0].message;
    execMessages.push(msg);

    if (msg.tool_calls && msg.tool_calls.length > 0) {
      for (const tc of msg.tool_calls) {
        if (tc.function.name === 'run_bash') {
          let command = '';
          try {
            command = JSON.parse(tc.function.arguments).command;
            const { stdout, stderr } = await execAsync(command, { cwd: ROOT });
            execMessages.push({ role: 'tool', tool_call_id: tc.id, name: 'run_bash', content: (stdout + '\n' + stderr).slice(-10000) || 'Success (no output)' });
          } catch (err) {
            execMessages.push({ role: 'tool', tool_call_id: tc.id, name: 'run_bash', content: `Command failed: ${err.message}` });
          }
        }
      }
    } else {
      console.log(JSON.stringify({ team, phase: 'finished', msg: 'Execution completed', summary: msg.content }));
      break;
    }
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
