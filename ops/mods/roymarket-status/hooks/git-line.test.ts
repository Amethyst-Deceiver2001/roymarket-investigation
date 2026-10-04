import { expect, test } from 'claude-code/testing'

import { formatGitLine, parseGitStatus } from './git-line'

test('parses branch, ahead, behind and dirty count', () => {
  const out = '## main...origin/main [ahead 2, behind 1]\n M a.py\n?? b.py\n'
  expect(parseGitStatus(out)).toEqual({ branch: 'main', ahead: 2, behind: 1, dirty: 2 })
})

test('a clean branch with no upstream', () => {
  expect(parseGitStatus('## claude/x\n')).toEqual({ branch: 'claude/x', ahead: 0, behind: 0, dirty: 0 })
})

test('output that is not a status header gives null', () => {
  expect(parseGitStatus('fatal: not a git repository')).toBeNull()
})

test('formats only what is non-zero and appends the check', () => {
  const g = { branch: 'main', ahead: 0, behind: 0, dirty: 3 }
  expect(formatGitLine(g, 'ok')).toBe('main | 3 uncommitted | registry ok')
  expect(formatGitLine({ ...g, dirty: 0 }, undefined)).toBe('main')
})
