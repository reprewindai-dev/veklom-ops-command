import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:http';
import { selectContext, workspaceReader, planWithRepositoryIndex } from './repository-context.mjs';
const code=Buffer.from('def validate():\n    return True\n\ndef other():\n    return False\n');
const hash=b=>createHash('sha256').update(b).digest('hex');
const index=()=>({schema_version:'vekcode.python-index/v1',files:[{path:'auth.py',sha256:hash(code)}],symbols:[{id:'auth.py::validate@1:0',qualified_name:'validate',file:'auth.py',line:1,end_line:2},{id:'auth.py::other@4:0',qualified_name:'other',file:'auth.py',line:4,end_line:5}],edges:[]});
const read=async()=>code;
async function workspace(fn){const path=await mkdtemp(join(tmpdir(),'vek-context-'));try{await writeFile(join(path,'auth.py'),code);await fn(path);}finally{await rm(path,{recursive:true,force:true});}}
test('select relevant symbol and bounded excerpt',async()=>{const r=await selectContext(index(),'validate',read);assert.equal(r.excerpts.length,1);assert.match(r.excerpts[0].text,/def validate/);assert(!r.excerpts[0].text.includes('def other'));assert.equal(r.authority,'none');});
test('stale source fails closed',async()=>{await assert.rejects(selectContext(index(),'validate',async()=>Buffer.from('changed')),/CONTEXT_SOURCE_CHANGED/);});
test('no invented matches',async()=>{const r=await selectContext(index(),'unrelated',read);assert.equal(r.excerpts.length,0);});
test('budget never overflows',async()=>{const r=await selectContext(index(),'validate',read,{maxChars:1});assert.equal(r.characters,0);assert(r.partial);});
test('resolved dependency is labelled',async()=>{const i=index();i.edges=[{source:i.symbols[0].id,target:i.symbols[1].id,resolution:'resolved'}];const r=await selectContext(i,'validate',read);assert.equal(r.excerpts[1].reason,'declared_resolved_dependency');});
test('unresolved calls do not invent impact results',async()=>{const i=index();i.edges=[{source:i.symbols[0].id,target:'unknown',resolution:'unresolved'}];const r=await selectContext(i,'validate',read);assert.equal(r.unresolved_edges,1);assert.equal(r.excerpts.length,1);assert.equal(r.affected_tests,undefined);});
test('symbol order does not change selection',async()=>{const i=index();const a=await selectContext(i,'auth',read);i.symbols.reverse();assert.deepEqual(await selectContext(i,'auth',read),a);});
test('duplicate identities fail',async()=>{const i=index();i.symbols.push({...i.symbols[0]});await assert.rejects(selectContext(i,'validate',read),/SYMBOL_INVALID/);});
test('invalid line ranges fail',async()=>{const i=index();i.symbols[0].line=0;await assert.rejects(selectContext(i,'validate',read),/SYMBOL_INVALID/);});
test('source reader rejects escapes and secrets',()=>workspace(async path=>{const reader=await workspaceReader(path);for(const value of ['../auth.py','/etc/passwd','.env','credentials.py','C:\\auth.py'])await assert.rejects(reader(value));}));
test('source reader rejects symlinks', {skip:process.platform==='win32'?'Requires Windows symlink-enabled runner':false},()=>workspace(async path=>{await symlink(join(path,'auth.py'),join(path,'alias.py'));await assert.rejects((await workspaceReader(path))('alias.py'),/SYMLINK/);}));
test('oversize input rejected before model request',()=>workspace(async path=>{await writeFile(join(path,'large.py'),'x'.repeat(256001));await assert.rejects((await workspaceReader(path))('large.py'),/TOO_LARGE/);}));
test('no model request without relevant verified context',()=>workspace(async path=>{let called=false;await assert.rejects(planWithRepositoryIndex({index:index(),workspace:path,objective:'unrelated',model:'fixture',fetchImpl:async()=>{called=true;}}),/NO_RELEVANT/);assert(!called);}));
test('full context-to-provider proposal with real HTTP fixture',()=>workspace(async path=>{
 let received;const server=createServer(async(req,res)=>{let s='';for await(const c of req)s+=c;received=JSON.parse(s);res.setHeader('content-type','application/json');res.end(JSON.stringify({message:{content:JSON.stringify({summary:'Review validation',steps:['Inspect matching function']})}}));});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{const r=await planWithRepositoryIndex({index:index(),workspace:path,objective:'validate',model:'fixture-model',ollama:`http://127.0.0.1:${server.address().port}`});assert.equal(r.execution,'not_started');assert.equal(r.context.excerpts.length,1);const payload=JSON.parse(received.messages[1].content);assert.equal(payload.context.excerpts[0].symbol_id,index().symbols[0].id);assert.equal(received.model,'fixture-model');}finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
}));
test('reject source change while model responds',()=>workspace(async path=>{await assert.rejects(planWithRepositoryIndex({index:index(),workspace:path,objective:'validate',model:'fixture-model',fetchImpl:async()=>{await writeFile(join(path,'auth.py'),'changed');return new Response(JSON.stringify({message:{content:JSON.stringify({summary:'x',steps:['x']})}}));}}),/SOURCE_CHANGED/);}));
test('remote model not silently selected',()=>workspace(async path=>{await assert.rejects(planWithRepositoryIndex({index:index(),workspace:path,objective:'validate',model:'fixture',ollama:'https://public.example'}),/LOCAL_MODEL/);}));
