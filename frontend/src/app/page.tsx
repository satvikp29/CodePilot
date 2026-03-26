'use client'

import { useState, useEffect, useCallback } from 'react'
import { reviewCode, getHistory, ReviewResult, HistoryItem } from '@/lib/api'
import CodeInput from '@/components/CodeInput'
import ResultPanel from '@/components/ResultPanel'
import HistorySidebar from '@/components/HistorySidebar'

export default function Home() {
  const [result, setResult] = useState<ReviewResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<HistoryItem[]>([])

  const fetchHistory = useCallback(async () => {
    try { setHistory(await getHistory()) } catch {}
  }, [])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  const handleReview = async (code: string, language: string) => {
    setLoading(true); setError(''); setResult(null)
    try {
      const r = await reviewCode(code, language)
      setResult(r)
      fetchHistory()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Is the backend running?')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-paper-border px-8 py-5 flex items-center gap-4 bg-paper sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <span className="font-serif text-2xl font-semibold tracking-tight text-ink">CodePilot</span>
          <span className="text-paper-border text-lg font-light select-none">|</span>
          <span className="text-sm text-ink-faint font-sans">AI Code Review</span>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <HistorySidebar items={history} />
        <main className="flex-1 flex flex-col xl:flex-row overflow-auto divide-y xl:divide-y-0 xl:divide-x divide-paper-border">
          <div className="flex-1 p-8 min-w-0">
            <CodeInput onSubmit={handleReview} loading={loading} />
            {error && (
              <div className="mt-5 p-4 border border-severity-high/30 bg-severity-high/5 rounded-lg text-severity-high text-sm">
                {error}
              </div>
            )}
          </div>
          <div className="flex-1 p-8 min-w-0 bg-paper-warm">
            <ResultPanel result={result} loading={loading} />
          </div>
        </main>
      </div>
    </div>
  )
}
