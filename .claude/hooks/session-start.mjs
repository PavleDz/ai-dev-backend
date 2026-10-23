// SessionStart hook: prints where the repo stands and where the rules live.
// Whatever this prints is added to the agent's context at the start of every session.
// Exit 0 always; a missing git only shortens the output.
import { execFileSync } from 'node:child_process'
import path from 'node:path'

const root = process.env.CLAUDE_PROJECT_DIR ?? path.resolve(import.meta.dirname, '../..')

const git = (...args) => {
  try {
    return execFileSync('git', args, { cwd: root, stdio: ['ignore', 'pipe', 'ignore'], timeout: 10_000 }).toString().trim()
  } catch {
    return ''
  }
}

try {
  const lines = []
  const branch = git('branch', '--show-current') || git('rev-parse', '--short', 'HEAD')
  if (branch) {
    const changed = git('status', '--short').split('\n').filter(Boolean).length
    lines.push(`Branch: ${branch} · ${changed} changed file(s)`)
    const log = git('log', '--oneline', '-5')
    if (log) lines.push('Last commits:', ...log.split('\n').map((line) => `  ${line}`))
  }
  lines.push(
    'Rules: .claude/rules · decisions: .claude/decisions.md · mistakes log: .claude/frequent-mistakes.md · before a feature: /brief · before commit: /review-changes'
  )
  process.stdout.write(lines.join('\n') + '\n')
} catch {
  // Context is a convenience; never fail the session over it.
}
process.exit(0)
