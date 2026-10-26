import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { Script, createContext } from 'node:vm';
const source=await readFile(new URL('../src/workspace.ts',import.meta.url),'utf8');
const signature='function safeWorkspaceUri(context: WorkspaceContext, relativePath: string): vscode.Uri {';
const start=source.indexOf(signature),end=source.indexOf('\nexport async function applyProposedEdits',start);
assert.ok(start>=0&&end>start);
const resolver=source.slice(start,end).replace(signature,'function safeWorkspaceUri(context, relativePath) {');
function load(folders,platformPath){const vscode={workspace:{workspaceFolders:folders},Uri:{file:fsPath=>({fsPath})}};const scope=createContext({vscode,path:platformPath});new Script(resolver+'\nthis.resolveWorkspace=safeWorkspaceUri;').runInContext(scope);return scope.resolveWorkspace;}
function folder(uri,fsPath){return {uri:{fsPath,toString:()=>uri}};}
for(const [platform,p,root,other]of[['posix',path.posix,'/repo/one','/repo/two'],['windows',path.win32,'C:\\repo\\one','C:\\repo\\two']]){
 const mounted=folder('file:///mounted',root),different=folder('file:///different',other),ctx={rootUri:'file:///mounted'};
 test(platform+': exact mount',()=>assert.equal(load([mounted],p)(ctx,'src/main.py').fsPath,p.resolve(root,'src/main.py')));
 test(platform+': removed mount rejects',()=>assert.throws(()=>load([different],p)(ctx,'src/main.py'),/Mounted workspace is no longer open/));
 test(platform+': reorder preserves binding',()=>assert.equal(load([different,mounted],p)(ctx,'main.py').fsPath,p.resolve(root,'main.py')));
 test(platform+': empty roots reject',()=>assert.throws(()=>load([],p)(ctx,'main.py'),/Mounted workspace is no longer open/));
 test(platform+': undefined roots reject',()=>assert.throws(()=>load(undefined,p)(ctx,'main.py'),/Mounted workspace is no longer open/));
 test(platform+': replacement identity rejects',()=>assert.throws(()=>load([folder('file:///replacement',root)],p)(ctx,'main.py'),/Mounted workspace is no longer open/));
 test(platform+': traversal rejects',()=>assert.throws(()=>load([mounted],p)(ctx,'../two/main.py'),/Rejected edit outside workspace/));
}
