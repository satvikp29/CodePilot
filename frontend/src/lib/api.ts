const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Issue {
  title: string;
  severity: 'low' | 'medium' | 'high';
  explanation: string;
  suggested_fix: string;
  line_number?: number;
}

export interface ReviewResult {
  issues: Issue[];
  overall_quality: string;
  summary: string;
  improved_code: string;
  mode: 'ai' | 'mock' | 'ai-fallback';
}

export interface HistoryItem {
  id: number;
  language: string;
  code_preview: string;
  summary: string;
  created_at: string;
}

export async function reviewCode(code: string, language: string): Promise<ReviewResult> {
  const res = await fetch(`${API_URL}/api/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Review failed');
  }
  return res.json();
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_URL}/api/history`);
  if (!res.ok) return [];
  return res.json();
}
