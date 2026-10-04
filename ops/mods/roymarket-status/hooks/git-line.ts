export type GitLine = { branch: string; ahead: number; behind: number; dirty: number }

export function parseGitStatus(out: string): GitLine | null {
  const lines = out.split('\n').filter(l => l.length > 0)
  const head = lines[0]
  if (head === undefined || !head.startsWith('## ')) return null

  const branch = head.slice(3).split('...')[0]!.split(' ')[0]!
  const ahead = Number(/ahead (\d+)/.exec(head)?.[1] ?? 0)
  const behind = Number(/behind (\d+)/.exec(head)?.[1] ?? 0)

  return { branch, ahead, behind, dirty: lines.length - 1 }
}

export function formatGitLine(g: GitLine, check: string | undefined): string {
  const parts = [g.branch]
  if (g.ahead > 0) parts.push(`${g.ahead} unpushed`)
  if (g.behind > 0) parts.push(`${g.behind} behind`)
  if (g.dirty > 0) parts.push(`${g.dirty} uncommitted`)
  if (check !== undefined) parts.push(`registry ${check}`)

  return parts.join(' | ')
}
