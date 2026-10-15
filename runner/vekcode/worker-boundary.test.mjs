import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,rm,access} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';

async function trial(sourcePath,{alignment,mode}={}) {
 const root=await mkdtemp(join(tmpdir(),'vek-worker-fixture-'));
 await mkdir(join(root,'runner'));await mkdir(join(root,'agents/fixture'),{recursive:true});
 await writeFile(join(root,'runner/department-agent.mjs'),await readFile(sourcePath));
 await writeFile(join(root,'runner/capi-client.mjs'),await readFile(new URL('../capi-client.mjs',import.meta.url)));
 await writeFile(join(root,'agents/fixture/AGENT.md'),'Fixture doctrine only.');await writeFile(join(root,'agents/fixture/TOOLS.md'),'Fixture tools only.');
 await writeFile(join(root,'mission.json'),JSON.stringify({mission_id:'fixture-mission'}));
 let requests=0,advertisedTools=false;
 const server=createServer(async(req,res)=>{
  let raw='';for await(const c of req)raw+=c;const body=JSON.parse(raw);requests++;advertisedTools ||= Array.isArray(body.tools)&&body.tools.length>0;
  const script="require('node:fs').writeFileSync('owned-fixture-marker.txt','changed')";
  const command=JSON.stringify(process.execPath)+' -e '+JSON.stringify(script);
  const msg=requests===1?{content:JSON.stringify(alignment??{status:'aligned',mission_id:'fixture-mission'})}:requests===2?{content:null,tool_calls:[{id:'fixture-call',type:'function',function:{name:'run_bash',arguments:JSON.stringify({command})}}]}:{content:'Fixture finished.'};
  res.setHeader('content-type','application/json');res.end(JSON.stringify({choices:[{message:msg}]}));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 let timer;
 try{
  const env={...process.env,VEKLOM_DEPARTMENT:'fixture',VEKLOM_MISSION_PATH:join(root,'mission.json'),VEKLOM_REPORT_PATH:join(root,'report.jsonl'),VEKLOM_AGENT_API_KEY:'fixture-only',VEKLOM_AGENT_MODEL:'fixture-only',VEKLOM_AGENT_BASE_URL:'http://127.0.0.1:'+server.address().port+'/v1',VEKLOM_CAPI_URL:'',VEKLOM_CAPI_TOKEN:''};
  delete env.VEKLOM_ALIGNMENT_ONLY;if(mode!==undefined)env.VEKLOM_ALIGNMENT_ONLY=mode;
  const result=await new Promise((resolve,reject)=>{
   const child=spawn(process.execPath,[join(root,'runner/department-agent.mjs')],{cwd:root,env,stdio:['ignore','pipe','pipe']});let stdout='',stderr='';
   timer=setTimeout(()=>{child.kill();reject(Error('fixture timeout'));},5000);
   child.stdout.on('data',d=>stdout+=d);child.stderr.on('data',d=>stderr+=d);child.on('error',reject);child.on('close',code=>resolve({code,stdout,stderr}));
  });
  let mutated=false;try{await access(join(root,'owned-fixture-marker.txt'));mutated=true;}catch{}
  const report=JSON.parse((await readFile(join(root,'report.jsonl'),'utf8')).trim());
  return {...result,requests,advertisedTools,mutated,report};
 }finally{clearTimeout(timer);server.closeAllConnections();await new Promise(r=>server.close(r));await rm(root,{recursive:true,force:true});}
}
const source=new URL('../department-agent.mjs',import.meta.url);
test('default worker does not execute model shell with cAPI unconfigured',async()=>{const r=await trial(source);assert.equal(r.mutated,false);assert.equal(r.requests,1);assert.equal(r.advertisedTools,false);assert.equal(r.code,0);assert.equal(r.report.capi_admission.status,'not_configured');assert.ok(r.stdout.includes('report_only'));});
test('explicit execution request fails closed rather than restoring shell fallback',async()=>{const r=await trial(source,{mode:'false'});assert.equal(r.mutated,false);assert.equal(r.requests,1);assert.equal(r.advertisedTools,false);assert.equal(r.code,1);assert.match(r.stderr,/GOVERNED_EXECUTION_NOT_CONNECTED/);});
test('alignment-only remains report-only',async()=>{const r=await trial(source,{mode:'true'});assert.equal(r.mutated,false);assert.equal(r.requests,1);assert.equal(r.code,0);});
test('omitted status is clarification, never automatic aligned',async()=>{const r=await trial(source,{alignment:{mission_id:'fixture-mission'}});assert.equal(r.report.status,'needs_clarification');assert.equal(r.mutated,false);assert.equal(r.requests,1);});
test('invalid status is clarification, never automatic aligned',async()=>{const r=await trial(source,{alignment:{mission_id:'fixture-mission',status:'probably_safe'}});assert.equal(r.report.status,'needs_clarification');assert.equal(r.mutated,false);assert.equal(r.requests,1);});
