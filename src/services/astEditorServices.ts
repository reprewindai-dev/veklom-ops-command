// PowerShell Editor Services & AST Analysis Engine
// Implements Find-Ast, Get-Token, Set-ScriptExtent, ConvertTo-ScriptExtent, Register-EditorCommand

export interface ScriptExtent {
  startLine: number;
  startColumn: number;
  endLine: number;
  endColumn: number;
  startOffset: number;
  endOffset: number;
  text: string;
}

export interface AstNode {
  id: string;
  kind: 'FunctionDeclaration' | 'ClassDeclaration' | 'VariableExpression' | 'CommandAst' | 'IfStatement' | 'ImportStatement' | 'Comment' | 'Block';
  name?: string;
  extent: ScriptExtent;
  children: AstNode[];
  parent?: string;
}

export interface AstToken {
  text: string;
  kind: 'Keyword' | 'Identifier' | 'String' | 'Number' | 'Operator' | 'Comment' | 'Whitespace' | 'Delimiter';
  extent: ScriptExtent;
}

export interface EditorCommand {
  name: string;
  displayName: string;
  suppressOutput?: boolean;
  execute: (context: { fileText: string; selection?: ScriptExtent }) => { modifiedText?: string; output?: string };
}

// Tokenize source code into discrete tokens with line/column extents
export function getTokens(code: string): AstToken[] {
  const tokens: AstToken[] = [];
  const lines = code.split('\n');
  let currentOffset = 0;

  const KEYWORDS = new Set([
    'function', 'class', 'import', 'export', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
    'param', 'filter', 'workflow', 'switch', 'process', 'begin', 'end', 'try', 'catch', 'finally', 'using'
  ]);

  for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
    const line = lines[lineIdx];
    let col = 0;

    while (col < line.length) {
      const remaining = line.slice(col);

      // 1. Whitespace
      const wsMatch = remaining.match(/^(\s+)/);
      if (wsMatch) {
        const text = wsMatch[1];
        col += text.length;
        currentOffset += text.length;
        continue;
      }

      // 2. Comments (// or #)
      if (remaining.startsWith('//') || remaining.startsWith('#') || remaining.startsWith('/*')) {
        const text = remaining;
        tokens.push({
          text,
          kind: 'Comment',
          extent: {
            startLine: lineIdx + 1,
            startColumn: col + 1,
            endLine: lineIdx + 1,
            endColumn: col + text.length + 1,
            startOffset: currentOffset,
            endOffset: currentOffset + text.length,
            text
          }
        });
        currentOffset += text.length;
        break;
      }

      // 3. String literals ("..." or '...')
      const strMatch = remaining.match(/^("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`[^`]*`)/);
      if (strMatch) {
        const text = strMatch[1];
        tokens.push({
          text,
          kind: 'String',
          extent: {
            startLine: lineIdx + 1,
            startColumn: col + 1,
            endLine: lineIdx + 1,
            endColumn: col + text.length + 1,
            startOffset: currentOffset,
            endOffset: currentOffset + text.length,
            text
          }
        });
        col += text.length;
        currentOffset += text.length;
        continue;
      }

      // 4. Numbers
      const numMatch = remaining.match(/^(\d+(?:\.\d+)?)/);
      if (numMatch) {
        const text = numMatch[1];
        tokens.push({
          text,
          kind: 'Number',
          extent: {
            startLine: lineIdx + 1,
            startColumn: col + 1,
            endLine: lineIdx + 1,
            endColumn: col + text.length + 1,
            startOffset: currentOffset,
            endOffset: currentOffset + text.length,
            text
          }
        });
        col += text.length;
        currentOffset += text.length;
        continue;
      }

      // 5. Identifiers / Keywords / Variables ($var or words)
      const identMatch = remaining.match(/^(\$?[a-zA-Z_][a-zA-Z0-9_\-]*)/);
      if (identMatch) {
        const text = identMatch[1];
        const kind = KEYWORDS.has(text.toLowerCase()) ? 'Keyword' : 'Identifier';
        tokens.push({
          text,
          kind,
          extent: {
            startLine: lineIdx + 1,
            startColumn: col + 1,
            endLine: lineIdx + 1,
            endColumn: col + text.length + 1,
            startOffset: currentOffset,
            endOffset: currentOffset + text.length,
            text
          }
        });
        col += text.length;
        currentOffset += text.length;
        continue;
      }

      // 6. Operators & Delimiters
      const opMatch = remaining.match(/^([=+\-*\/%&|<>!?:;.,(){}\[\]])/);
      if (opMatch) {
        const text = opMatch[1];
        const kind = '(){}[];,'.includes(text) ? 'Delimiter' : 'Operator';
        tokens.push({
          text,
          kind,
          extent: {
            startLine: lineIdx + 1,
            startColumn: col + 1,
            endLine: lineIdx + 1,
            endColumn: col + text.length + 1,
            startOffset: currentOffset,
            endOffset: currentOffset + text.length,
            text
          }
        });
        col += text.length;
        currentOffset += text.length;
        continue;
      }

      // Single fallback character
      const char = line[col];
      col += 1;
      currentOffset += 1;
    }

    currentOffset += 1; // newline
  }

  return tokens;
}

// Find AST elements in source code
export function findAst(code: string, filter?: (node: AstNode) => boolean): AstNode[] {
  const nodes: AstNode[] = [];
  const lines = code.split('\n');

  lines.forEach((line, idx) => {
    const lineNum = idx + 1;

    // Function definition
    const fnMatch = line.match(/^\s*(?:function|export\s+function|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\()/i);
    if (fnMatch) {
      const name = fnMatch[1] || line.match(/function\s+([a-zA-Z0-9_]+)/i)?.[1] || 'anonymous';
      nodes.push({
        id: `ast_fn_${lineNum}`,
        kind: 'FunctionDeclaration',
        name,
        extent: {
          startLine: lineNum,
          startColumn: 1,
          endLine: lineNum,
          endColumn: line.length + 1,
          startOffset: 0,
          endOffset: line.length,
          text: line.trim()
        },
        children: []
      });
    }

    // Class definition
    const classMatch = line.match(/^\s*class\s+([a-zA-Z0-9_]+)/i);
    if (classMatch) {
      nodes.push({
        id: `ast_class_${lineNum}`,
        kind: 'ClassDeclaration',
        name: classMatch[1],
        extent: {
          startLine: lineNum,
          startColumn: 1,
          endLine: lineNum,
          endColumn: line.length + 1,
          startOffset: 0,
          endOffset: line.length,
          text: line.trim()
        },
        children: []
      });
    }

    // Command invocation / console.log
    const cmdMatch = line.match(/^\s*([a-zA-Z0-9_.$]+(?:\.[a-zA-Z0-9_$]+)*)\s*\(/);
    if (cmdMatch) {
      nodes.push({
        id: `ast_cmd_${lineNum}`,
        kind: 'CommandAst',
        name: cmdMatch[1],
        extent: {
          startLine: lineNum,
          startColumn: 1,
          endLine: lineNum,
          endColumn: line.length + 1,
          startOffset: 0,
          endOffset: line.length,
          text: line.trim()
        },
        children: []
      });
    }

    // Variable declaration or assignment
    const varMatch = line.match(/^\s*(?:const|let|var|\$)([a-zA-Z0-9_]+)\s*=/);
    if (varMatch) {
      nodes.push({
        id: `ast_var_${lineNum}`,
        kind: 'VariableExpression',
        name: varMatch[1],
        extent: {
          startLine: lineNum,
          startColumn: 1,
          endLine: lineNum,
          endColumn: line.length + 1,
          startOffset: 0,
          endOffset: line.length,
          text: line.trim()
        },
        children: []
      });
    }
  });

  return filter ? nodes.filter(filter) : nodes;
}

// Set-ScriptExtent: Replaces code at targeted line/column or offset range
export function setScriptExtent(
  originalCode: string,
  extent: { startLine: number; startColumn: number; endLine: number; endColumn: number },
  newText: string
): string {
  const lines = originalCode.split('\n');

  if (extent.startLine === extent.endLine) {
    const targetLine = lines[extent.startLine - 1] || '';
    const before = targetLine.slice(0, extent.startColumn - 1);
    const after = targetLine.slice(extent.endColumn - 1);
    lines[extent.startLine - 1] = before + newText + after;
    return lines.join('\n');
  }

  // Multi-line replacement
  const firstLine = lines[extent.startLine - 1] || '';
  const lastLine = lines[extent.endLine - 1] || '';
  const before = firstLine.slice(0, extent.startColumn - 1);
  const after = lastLine.slice(extent.endColumn - 1);

  const middleLines = newText.split('\n');
  middleLines[0] = before + middleLines[0];
  middleLines[middleLines.length - 1] = middleLines[middleLines.length - 1] + after;

  lines.splice(extent.startLine - 1, extent.endLine - extent.startLine + 1, ...middleLines);
  return lines.join('\n');
}

// Built-in registered editor commands (Register-EditorCommand)
export const REGISTERED_EDITOR_COMMANDS: EditorCommand[] = [
  {
    name: 'PowerShell.ExpandAlias',
    displayName: 'Expand Aliases',
    execute: ({ fileText }) => {
      let res = fileText;
      const ALIASES: Record<string, string> = {
        gci: 'Get-ChildItem',
        select: 'Select-Object',
        where: 'Where-Object',
        ls: 'Get-ChildItem',
        cat: 'Get-Content',
        rm: 'Remove-Item',
        cp: 'Copy-Item',
        mv: 'Move-Item'
      };
      for (const [alias, full] of Object.entries(ALIASES)) {
        const regex = new RegExp(`\\b${alias}\\b`, 'g');
        res = res.replace(regex, full);
      }
      return { modifiedText: res, output: 'Expanded aliases in document.' };
    }
  },
  {
    name: 'PowerShell.FormatDocument',
    displayName: 'Format Document (OTBS Style)',
    execute: ({ fileText }) => {
      // Basic indentation and brace formatting
      const lines = fileText.split('\n');
      let indent = 0;
      const formatted = lines.map(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('}') || trimmed.startsWith(']') || trimmed.startsWith(')')) {
          indent = Math.max(0, indent - 1);
        }
        const indented = '  '.repeat(indent) + trimmed;
        if (trimmed.endsWith('{') || trimmed.endsWith('[') || trimmed.endsWith('(')) {
          indent++;
        }
        return indented;
      });
      return { modifiedText: formatted.join('\n'), output: 'Formatted document with OTBS style.' };
    }
  },
  {
    name: 'Visual Studio.GenerateLaunchJson',
    displayName: 'Export Visual Studio 2026 launch.json',
    execute: () => {
      const launchJson = JSON.stringify(
        {
          version: '0.2.0',
          configurations: [
            {
              name: 'PowerShell: Launch Current File',
              type: 'PowerShell',
              request: 'launch',
              script: '${file}',
              cwd: '${workspaceFolder}'
            },
            {
              name: 'PowerShell: Interactive Session',
              type: 'PowerShell',
              request: 'launch',
              cwd: '${workspaceFolder}'
            },
            {
              name: 'Local Ollama: Optimize Output Pipeline',
              type: 'node',
              request: 'launch',
              program: '${workspaceFolder}/scripts/runLocalLlmPipeline.mjs'
            }
          ]
        },
        null,
        2
      );
      return { output: launchJson };
    }
  }
];
