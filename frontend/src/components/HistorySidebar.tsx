'use client'

import { HistoryItem } from '@/lib/api'

const LANG_LABEL: Record<string, string> = {
  python: 'PY', javascript: 'JS', java: 'JV', cpp: 'C++',
}

function formatTime(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    const diffMins = Math.floor((Date.now() - d.getTime()) / 60000)
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const h = Math.floor(diffMins / 60)
    if (h < 24) return `${h}h ago`
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  } catch { return '' }
}

export default function HistorySidebar({ items }: { items: HistoryItem[] }) {
  return (
    <aside className="w-56 border-r border-paper-border p-5 flex-col gap-4 overflow-y-auto hidden lg:flex flex-shrink-0 bg-paper">
      <p className="text-xs font-semibold text-ink-faint uppercase tracking-widest">History</p>

      {items.length === 0 ? (
        <p className="text-xs text-ink-faint mt-1">Your reviews will appear here.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {items.map(item => {
            const langKey = item.language.toLowerCase()
            return (
              <div key={item.id} className="p-3 border border-paper-border rounded-lg bg-paper-warm flex flex-col gap-1.5 cursor-default hover:bg-paper-muted transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-ink bg-paper-muted px-1.5 py-0.5 rounded">
                    {LANG_LABEL[langKey] ?? langKey.toUpperCase().slice(0, 3)}
                  </span>
                  <span className="text-xs text-ink-faint">{formatTime(item.created_at)}</span>
                </div>
                <p className="text-xs text-ink-faint font-mono truncate">{item.code_preview}</p>
              </div>
            )
          })}
        </div>
      )}

      <div className="mt-auto pt-4 border-t border-paper-border">
        <p className="text-xs text-ink-faint">Stores your last 5 reviews locally.</p>
      </div>
    </aside>
  )
}
