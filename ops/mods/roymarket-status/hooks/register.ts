import type { Register } from 'claude-code'

import { formatGitLine, parseGitStatus } from './git-line'

const REFRESH_MS = 60_000
const CHECK_TIMEOUT_MS = 180_000

export const register: Register = on => {
  let check: string | undefined

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'rcheck',
      description: 'Run scripts/check_registry.py and show the result',
    })

    const refresh = async () => {
      const git = await $.process.run(['git', 'status', '--porcelain=v1', '-b'])
      const parsed = git.exitCode === 0 ? parseGitStatus(git.stdout) : null
      $.ui.status(parsed === null ? undefined : formatGitLine(parsed, check))
    }

    await refresh()
    $.clock.every(REFRESH_MS, refresh)

    return next(e)
  })

  on('command.run', { command: 'rcheck' }, async $ => {
    const hasSources = (await $.process.run(['test', '-d', 'data/sources'])).exitCode === 0
    const argv = ['python3', 'scripts/check_registry.py', ...(hasSources ? [] : ['--no-local-files'])]
    const run = await $.process.run(argv, { timeoutMs: CHECK_TIMEOUT_MS })

    check = run.exitCode === 0 ? 'ok' : 'FAILED'
    const tail = (run.stdout + run.stderr).trim().split('\n').slice(-15).join('\n')

    return { text: `${argv.join(' ')}\nexit ${run.exitCode}\n${tail}` }
  })
}
