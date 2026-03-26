'use client'

import { useState, useRef } from 'react'

const LANGUAGES = ['Python', 'JavaScript', 'Java', 'C++']

const SAMPLES: Record<string, string> = {
  Python: `def get_user(db, user_id):
    query = "SELECT * FROM users WHERE id=" + user_id
    result = db.execute(query)
    try:
        data = result[0]
        discount = 0
        if data['type'] == 'premium':
            discount = data['price'] * 0.2
        return data['price'] - discount
    except:
        return None`,

  JavaScript: `var userData = null

async function loadUser(id) {
  var response = await fetch('/api/users/' + id)
  var data = await response.json()
  if (data.user.profile.name == null) {
    userData = 'Anonymous'
  } else {
    userData = data.user.profile.name
  }
  return userData
}`,

  Java: `import java.util.*;

public class DataProcessor {
    private List data;

    public Object processItem(String input) {
        if (input == "null") return null;
        data.add(input);
        return data.get(0);
    }

    public void loadFile(String path) throws Exception {
        FileInputStream fis = new FileInputStream(path);
        int b;
        while ((b = fis.read()) != -1) {
            System.out.print((char) b);
        }
    }
}`,

  'C++': `#include <iostream>
using namespace std;

int* createArray(int size) {
    int* arr = new int[size];
    for (int i = 0; i <= size; i++) {
        arr[i] = i * 2;
    }
    return arr;
}

int main() {
    int* data = createArray(5);
    cout << data[0] << endl;
    return 0;
}`,
}

interface Props {
  onSubmit: (code: string, language: string) => void
  loading: boolean
}

export default function CodeInput({ onSubmit, loading }: Props) {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('Python')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const lineNumsRef = useRef<HTMLDivElement>(null)

  const syncScroll = () => {
    if (lineNumsRef.current && textareaRef.current) {
      lineNumsRef.current.scrollTop = textareaRef.current.scrollTop
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const start = e.currentTarget.selectionStart
      const end = e.currentTarget.selectionEnd
      const next = code.substring(0, start) + '  ' + code.substring(end)
      setCode(next)
      setTimeout(() => {
        e.currentTarget.selectionStart = start + 2
        e.currentTarget.selectionEnd = start + 2
      }, 0)
    }
  }

  const lineCount = Math.max(1, code.split('\n').length)
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1)

  return (
    <div className="flex flex-col gap-5 h-full">
      <div>
        <h2 className="font-serif text-xl font-semibold text-ink mb-1">Your Code</h2>
        <p className="text-sm text-ink-faint">Paste anything. We will take it from here.</p>
      </div>

      {/* Language + actions */}
      <div className="flex items-center gap-3">
        <select
          value={language}
          onChange={e => setLanguage(e.target.value)}
          className="border border-paper-border bg-paper text-ink text-sm rounded-md px-3 py-2 focus:outline-none focus:border-ink-faint cursor-pointer"
        >
          {LANGUAGES.map(l => <option key={l}>{l}</option>)}
        </select>

        <button
          onClick={() => setCode(SAMPLES[language] || SAMPLES.Python)}
          className="text-sm text-ink-faint hover:text-ink border border-paper-border rounded-md px-3 py-2 transition-colors hover:bg-paper-muted"
        >
          Load sample
        </button>

        {code && (
          <button
            onClick={() => setCode('')}
            className="text-sm text-ink-faint hover:text-severity-high transition-colors ml-auto"
          >
            Clear
          </button>
        )}
      </div>

      {/* Editor with line numbers */}
      <div className="relative flex-1 min-h-72 flex rounded-xl overflow-hidden bg-ink">
        {/* Line number gutter */}
        <div
          ref={lineNumsRef}
          aria-hidden="true"
          className="select-none py-5 px-3 text-right text-xs font-mono leading-relaxed min-w-[2.5rem] bg-ink border-r border-white/5 overflow-hidden flex-shrink-0"
          style={{ color: 'rgba(250,250,248,0.2)' }}
        >
          {lineNumbers.map(n => (
            <div key={n}>{n}</div>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={code}
          onChange={e => setCode(e.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={syncScroll}
          spellCheck={false}
          placeholder={`Paste your ${language} code here...\n\nOr click "Load sample" to try with a real example.`}
          className="flex-1 h-full min-h-72 text-sm bg-ink text-paper-warm placeholder-ink-faint/60 py-5 pl-3 pr-5 resize-none focus:outline-none leading-relaxed"
        />
      </div>

      <button
        onClick={() => code.trim() && !loading && onSubmit(code, language.toLowerCase().replace('++', 'pp'))}
        disabled={loading || !code.trim()}
        className="w-full py-3 rounded-xl bg-ink text-paper font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:bg-ink-soft flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="w-4 h-4 border-2 border-paper/30 border-t-paper rounded-full animate-spin" />
            Reviewing your code...
          </>
        ) : 'Review Code'}
      </button>
    </div>
  )
}
