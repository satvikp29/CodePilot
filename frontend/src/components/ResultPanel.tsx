'use client'

import { useState } from 'react'
import { ReviewResult } from '@/lib/api'

const SEVERITY_STYLES: Record<string, string> = {
  high:   'text-severity-high   bg-severity-high/8   border-severity-high/25',
  medium: 'text-severity-medium bg-severity-medium/8 border-severity-medium/25',
  low:    'text-severity-low    bg-severity-low/8    border-severity-low/25',
}

const QUALITY_COLOR: Record<string, string> = {
  'Poor':             'text-severity-high',
  'Needs Improvement':'text-severity-medium',
  'Fair':             'text-ink-faint',
  'Good':             'text-severity-low',
  'Excellent':        'text-severity-low',
}

const QUALITY_SCORE: Record<string, number> = {
  'Poor': 10, 'Needs Improvement': 32, 'Fair': 55, 'Good': 78, 'Excellent': 100,
}

function Skeleton() {
  return (
    <div className="flex flex-col gap-5 animate-pulse">
      <div className="h-5 bg-paper-muted rounded w-2/5" />
      <div className="h-3 bg-paper-muted rounded-full w-full" />
      <div className="h-20 bg-paper-muted rounded-xl" />
      {[1,2,3].map(i => <div key={i} className="h-24 bg-paper-muted rounded-xl" />)}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center gap-3 py-20">
      <p className="font-serif text-2xl text-ink-muted">No review yet</p>
      <p className="text-sm text-ink-faint max-w-xs leading-relaxed">
        Paste your code on the left and hit Review. Results will show up here.
      </p>
    </div>
  )
}

export default function ResultPanel({ result, loading }: { result: ReviewResult | null; loading: boolean }) {
  const [showImproved, setShowImproved] = useState(false)
  const [copied, setCopied] = useState(false)
  const [openIssue, setOpenIssue] = useState<number | null>(null)

  const copy = async () => {
    if (!result) return
    await navigator.clipboard.writeText(result.improved_code)
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  if (loading) return <Skeleton />
  if (!result) return <EmptyState />

  const score = QUALITY_SCORE[result.overall_quality] ?? 50

  return (
    <div className="flex flex-col gap-6 animate-slide-up">

      {/* Title row */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-serif text-xl font-semibold text-ink mb-0.5">Review Results</h2>
          <p className="text-sm text-ink-faint">
            {result.issues.length === 0
              ? 'No issues found'
              : `${result.issues.length} issue${result.issues.length === 1 ? '' : 's'} found`}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <span className={`font-serif text-lg font-semibold ${QUALITY_COLOR[result.overall_quality] ?? 'text-ink'}`}>
            {result.overall_quality}
          </span>
        </div>
      </div>

      {/* Quality bar */}
      <div className="h-1 bg-paper-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-ink rounded-full transition-all duration-700"
          style={{ width: `${score}%` }}
        />
      </div>

      {/* Summary */}
      <p className="text-sm text-ink leading-relaxed border-l-2 border-paper-border pl-4 italic">
        {result.summary}
      </p>

      {/* Issues */}
      {result.issues.length === 0 ? (
        <div className="p-4 border border-severity-low/30 bg-severity-low/5 rounded-xl text-sm text-severity-low text-center">
          Everything looks good. Clean code.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-xs uppercase tracking-widest text-ink-faint font-semibold">Issues</p>
          {result.issues.map((issue, i) => {
            const isOpen = openIssue === i
            return (
              <div key={i} className="border border-paper-border rounded-xl overflow-hidden bg-paper">
                <button
                  onClick={() => setOpenIssue(isOpen ? null : i)}
                  className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-paper-warm transition-colors"
                >
                  <span className={`text-xs px-2 py-0.5 rounded border font-medium flex-shrink-0 ${SEVERITY_STYLES[issue.severity]}`}>
                    {issue.severity}
                  </span>
                  {issue.line_number && (
                    <span className="text-xs font-mono text-ink-faint bg-paper-muted border border-paper-border rounded px-1.5 py-0.5 flex-shrink-0">
                      L{issue.line_number}
                    </span>
                  )}
                  <span className="flex-1 text-sm font-medium text-ink">{issue.title}</span>
                  <span className="text-ink-faint text-xs">{isOpen ? '▲' : '▼'}</span>
                </button>
                {isOpen && (
                  <div className="px-4 pb-4 border-t border-paper-border flex flex-col gap-3 bg-paper-warm">
                    {issue.line_number && (
                      <p className="text-xs text-ink-faint pt-3 font-mono">
                        → Line {issue.line_number}
                      </p>
                    )}
                    <p className="text-sm text-ink-muted leading-relaxed pt-3">{issue.explanation}</p>
                    <div className="p-3 bg-paper border border-paper-border rounded-lg">
                      <p className="text-xs text-ink-faint uppercase tracking-wide mb-1.5">How to fix it</p>
                      <p className="text-sm text-ink leading-relaxed">{issue.suggested_fix}</p>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Improved code */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowImproved(v => !v)}
            className="text-sm font-medium text-ink hover:text-ink-soft transition-colors underline underline-offset-2"
          >
            {showImproved ? 'Hide improved version' : 'Show improved version'}
          </button>
          {showImproved && (
            <button
              onClick={copy}
              className="text-xs px-3 py-1.5 border border-paper-border rounded-lg text-ink-faint hover:text-ink hover:bg-paper-muted transition-colors"
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
          )}
        </div>

        {showImproved && (
          <div className="animate-fade-in rounded-xl overflow-hidden border border-paper-border">
            <div className="flex items-center justify-between px-4 py-2 bg-ink border-b border-ink-border">
              <span className="text-xs text-paper-muted font-mono">improved version</span>
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-paper/20" />
                <span className="w-2.5 h-2.5 rounded-full bg-paper/20" />
                <span className="w-2.5 h-2.5 rounded-full bg-paper/20" />
              </div>
            </div>
            <pre className="p-5 bg-ink-soft text-sm text-paper-warm overflow-x-auto whitespace-pre-wrap leading-relaxed">
              {result.improved_code}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
