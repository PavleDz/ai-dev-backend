// PostToolUse hook: after every file edit, formats that file.
// A "format the code" rule in CLAUDE.md would be a request; this hook is a guarantee.
// ruff + black through poetry (`poetry install` installed them): import sorting, lint fixes, black.
import { execFileSync } from 'node:child_process'
import path from 'node:path'

const root = process.env.CLAUDE_PROJECT_DIR ?? path.resolve(import.meta.dirname, '../..')
const backend = root

// Returns true when `file` is inside `dir`.
const inside = (dir, file) => {
  const relative = path.relative(dir, file)
  return !relative.startsWith('..') && !path.isAbsolute(relative)
}

let input = ''
process.stdin.on('data', (chunk) => (input += chunk))
process.stdin.on('end', () => {
  try {
    const file = path.resolve(root, JSON.parse(input).tool_input?.file_path ?? '')
    if (inside(backend, file) && !inside(path.join(backend, '.venv'), file) && /\.py$/.test(file)) {
      const poetry = ['--directory', backend, 'run']
      execFileSync('poetry', [...poetry, 'ruff', 'check', '--fix', file], { cwd: backend, stdio: 'ignore' })
      execFileSync('poetry', [...poetry, 'black', '-q', file], { cwd: backend, stdio: 'ignore' })
    }
  } catch {
    // A failed format must never stop the agent.
  }
})
