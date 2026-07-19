import { watch, existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const INBOX = join(ROOT, 'reports', 'command-desk-inbox.jsonl');
const watched = ['teams','runbooks','matrices','standards','panel/data','reports/command-desk-inbox.jsonl'];
let busy = false; let lastInbox = '';
async function inboxChanged() { try { const value = await readFile(INBOX, 'utf8'); if (value !== lastInbox) { lastInbox = value; return true; } } catch {} return false; }
function runOnce(reason) { if (busy) return; busy = true; console.log(`[veklom-agent-watch] processing trigger: ${reason}`); const child = spawn(process.execPath, [join(ROOT,'runner','runner.mjs')], {cwd:ROOT, stdio:'inherit', env:process.env}); child.on('exit', (code) => { busy = false; if (code) console.error(`[veklom-agent-watch] runner exited ${code}`); }); }
console.log(`[veklom-agent-watch] watching ${ROOT}`);
for (const path of watched) { const absolute = join(ROOT, path); const target = existsSync(absolute) ? absolute : ROOT; try { watch(target, {recursive:true}, (_event, filename) => { if (filename && String(filename).includes('command-desk-inbox')) runOnce('founder inbox changed'); }); } catch (error) { console.warn(`[veklom-agent-watch] unable to watch ${target}: ${error.message}`); } }
setInterval(async () => { if (await inboxChanged()) runOnce('founder inbox changed'); }, 5000);
await new Promise(() => {});
