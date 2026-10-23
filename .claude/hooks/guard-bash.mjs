// PreToolUse hook (matcher: Bash): blocks the commands that rules/safety.md forbids.
// A rule in a markdown file is a request; this hook is a guarantee.
// Reads the hook payload as JSON on stdin and looks at `tool_input.command`.
// Exit 0 lets the command run. Exit 2 blocks it and sends the stderr message back to the agent.
// Any parse or runtime failure exits 0, so a broken hook can never wedge the agent.

// Each rule is tested against one command segment (the text between `&&`, `||`, `;`, `|` or a newline),
// anchored at the command position, so "git commit -m 'never run git reset --hard'" is not a false positive:
// single-quoted strings are removed first and the message is only an argument.
const RULES = [
  [/^git\s+push\b(?:.*\s)?(?:-f|--force|--force-with-lease)(?:\s|$)/, 'git push --force rewrites shared history; ask the user and let them run it'],
  [/^git\s+reset\s+(?:.*\s)?--hard\b/, 'git reset --hard destroys uncommitted work; ask the user first'],
  [/^git\s+clean\s+(?:.*\s)?(?:-[a-zA-Z]*f[a-zA-Z]*|--force)\b/, 'git clean -f deletes untracked files; ask the user first'],
  [/^git\s+(?:checkout|restore)\s+(?:--\s+|--staged\s+|--worktree\s+)*\.(?:\s|$)/, 'git checkout . / git restore . throws away every uncommitted change; ask the user first'],
  [/^git\s+branch\s+(?:.*\s)?-D(?:\s|$)/, 'git branch -D deletes a branch for good; ask the user first'],
  [/^(?:poetry\s+run\s+)?alembic\s+downgrade\b/, 'alembic downgrade drops tables and columns with their data; ask the user first (rules/backend-db.md)'],
  [/^docker(?:\s+compose|-compose)\s+down\b(?:.*\s)?(?:-v|--volumes|-[a-zA-Z]*v[a-zA-Z]*)(?:\s|$)/, 'docker compose down -v deletes the database volume; ask the user first'],
  [/^docker\s+volume\s+(?:rm|prune)\b/, 'deleting Docker volumes deletes data; ask the user first'],
  [/^(?:cat|less|more|head|tail|bat|type|Get-Content|strings)\s+(?:-\S+\s+)*\S*\.env(?!\.example)(?:\.\w+)?(?:\s|$)/, '.env holds secrets and is never printed; read .env.example instead (rules/safety.md)'],
  [/^(?:uv\s+add|uv\s+pip\s+install|pip3?\s+install|poetry\s+add)\b/, 'a new backend dependency needs approval: name the package, why it is needed and the alternative, then let the user run `poetry add <package>` themselves (rules/safety.md, ADR-013)'],
]

// `rm -r` (any flag spelling) aimed at a source tree, the repo root, the home folder or a bare wildcard.
// `rm -rf .venv` or `rm -rf data/*.db` stay allowed.
const PROTECTED_RM_TARGET =
  /^(?:\.\/)?(?:(?:app|tests|alembic|docs)(?:\/|$)|\.claude(?:\/|$)|\.git(?:\/|$)|\/$|~\/?$|\*$|\.\.?\/?$)|\/(?:app|tests|alembic|\.claude)\/?$/

// Destructive SQL handed to a database shell (`psql -c "..."`, `sqlite3 data/app.db "..."`).
const DB_SHELL = /^(?:psql|sqlite3|pgcli|litecli)\b/
const DESTRUCTIVE_SQL = /\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA|INDEX)|TRUNCATE|DELETE\s+FROM)\b/i

const segments = (command) =>
  command
    .split(/&&|\|\||[;|\n]/)
    .map((segment) => segment.trim().replace(/^(?:sudo|time|nohup|env(?:\s+\w+=\S*)*)\s+/, ''))
    .filter(Boolean)

const rmHitsProtectedTarget = (segment) => {
  const [cmd, ...args] = segment.split(/\s+/)
  if (cmd !== 'rm') return false
  const recursive = args.some((arg) => /^-[a-zA-Z]*[rR]/.test(arg) || arg === '--recursive')
  const targets = args.filter((arg) => !arg.startsWith('-'))
  return recursive && targets.some((target) => PROTECTED_RM_TARGET.test(target.replace(/^["']|["']$/g, '')))
}

const block = (why, command) => {
  process.stderr.write(`BLOCKED by guard-bash: ${why}\nCommand: ${command}\n`)
  process.exit(2)
}

let input = ''
process.stdin.on('data', (chunk) => (input += chunk))
process.stdin.on('end', () => {
  try {
    const command = String(JSON.parse(input).tool_input?.command ?? '')
    if (!command) process.exit(0)

    const scrubbed = command.replace(/'[^']*'/g, "''")
    for (const segment of segments(scrubbed)) {
      for (const [pattern, why] of RULES) {
        if (pattern.test(segment)) block(why, command)
      }
      if (rmHitsProtectedTarget(segment)) block('rm -r on a source tree, the repo root or a wildcard; delete single files, or ask the user', command)
    }
    // SQL is checked on the raw command: the statement is usually inside quotes.
    if (segments(command).some((segment) => DB_SHELL.test(segment)) && DESTRUCTIVE_SQL.test(command)) {
      block('DROP / TRUNCATE / DELETE FROM through a database shell; schema changes are migrations, data deletes go through the API or a --dry-run script (rules/safety.md, ADR-004)', command)
    }
    process.exit(0)
  } catch {
    process.exit(0)
  }
})
