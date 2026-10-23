// Stop hook: when the agent says it is done, check that what it changed actually passes.
// "Run the tests before you finish" in CLAUDE.md is a request; this hook is a guarantee.
// Looks at every changed or new file compared with HEAD:
//   **/*.py -> ruff check + black --check on those files, mypy, then pytest -q -x
// Exit 0 (silently) when everything passes or there is nothing to check.
// Exit 2 with the tool output on stderr when something fails: the agent reads it and keeps working.
// Defensive by design: no git, no poetry, or a parse error -> exit 0, never wedge the agent.
import { execFileSync, spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const root = process.env.CLAUDE_PROJECT_DIR ?? path.resolve(import.meta.dirname, '../..')
const backend = root
const MAX_LINES = 60
const TIMEOUT = 170_000 // settings.json gives this hook 180 s

const has = (bin) => {
  try {
    execFileSync(bin, ['--version'], { stdio: 'ignore', shell: process.platform === 'win32' })
    return true
  } catch {
    return false
  }
}

const git = (args) =>
  execFileSync('git', args, { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] })
    .toString()
    .split(/\r?\n/)
    .filter(Boolean)

// Runs a command; returns null on success or the (truncated) output on failure.
const run = (cmd, args, options = {}) => {
  const result = spawnSync(cmd, args, { cwd: root, encoding: 'utf8', timeout: TIMEOUT, ...options })
  if (result.status === 0) return null
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}`.split(/\r?\n/).filter(Boolean)
  const shown = output.slice(-MAX_LINES).join('\n')
  const reason = result.error ? `(${result.error.code ?? result.error.message})` : `(exit ${result.status})`
  return `$ ${cmd} ${args.join(' ')} ${reason}\n${shown}`
}

let input = ''
process.stdin.on('data', (chunk) => (input += chunk))
process.stdin.on('end', () => {
  try {
    const payload = input.trim() ? JSON.parse(input) : {}
    // Claude Code sets this when the agent is already continuing because of a Stop hook:
    // one round of fixing is enough, do not loop forever.
    if (payload.stop_hook_active) process.exit(0)

    let changed
    try {
      changed = [...new Set([...git(['diff', '--name-only', 'HEAD']), ...git(['ls-files', '--others', '--exclude-standard'])])]
    } catch {
      process.exit(0) // no git: nothing to compare against
    }
    const existing = changed.filter((file) => fs.existsSync(path.join(root, file)))
    const py = existing.filter((file) => file.endsWith('.py') && !file.startsWith('.venv/'))

    const failures = []
    if (py.length > 0 && has('poetry')) {
      const files = py.map((file) => path.join(root, file))
      const poetry = ['--directory', backend, 'run']
      const ruff = run('poetry', [...poetry, 'ruff', 'check', ...files], { cwd: backend })
      if (ruff) failures.push(ruff)
      const black = run('poetry', [...poetry, 'black', '--check', '-q', ...files], { cwd: backend })
      if (black) failures.push(black)
      const mypy = run('poetry', [...poetry, 'mypy', '.'], { cwd: backend })
      if (mypy) failures.push(mypy)
      const pytest = run('poetry', [...poetry, 'pytest', '-q', '-x'], { cwd: backend })
      if (pytest) failures.push(pytest)
    }

    if (failures.length === 0) process.exit(0)
    process.stderr.write(
      `Stop hook (verify-changes): the changed files do not pass yet. Fix this before finishing:\n\n${failures.join('\n\n')}\n`
    )
    process.exit(2)
  } catch {
    process.exit(0)
  }
})
