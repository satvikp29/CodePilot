# CodePilot

Static analysis meets a clean UI. Paste code, get structured feedback — bugs flagged by line number, quality score, and a ready-to-copy improved version.

Built with Next.js + FastAPI. Runs entirely in Docker. Optionally plugs into OpenAI for deeper analysis.

---

## Getting started

You need Docker and Docker Compose. That's the whole dependency list.

```bash
git clone https://github.com/satvikp29/codepilot
cd codepilot
docker-compose up --build
```

Open **http://localhost:3000**, click **Load sample**, hit **Review Code**.

No accounts, no setup, no API key required to see it working.

---

## Add an OpenAI key

The built-in analyzer catches real issues without any API key. If you want GPT-4o-mini doing the review instead:

```bash
echo "OPENAI_API_KEY=sk-proj-..." > .env
docker-compose up --build
```

The app picks up the key automatically and switches modes. Remove the key and it falls back to static analysis.

---

## Workflows

**Before opening a PR** — paste the function you changed, verify nothing obviously broken slipped through. Takes five seconds and catches the stuff code review comments point out anyway.

**Onboarding to a new codebase** — drop in a file you're trying to understand. The review surfaces the anti-patterns and explains why they're problems, which is faster than grepping docs.

**Security audit pass** — the analyzer specifically checks for SQL injection, unsafe buffer functions, and resource leaks with severity ratings. Good for a first-pass before a proper audit.

**Teaching / pair programming** — each issue comes with an explanation of *why* it matters and a concrete fix. Useful when you want to show someone what's wrong without writing it out yourself.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python 3.11) |
| AI | OpenAI GPT-4o-mini (optional) |
| Database | SQLite |
| Infra | Docker Compose |

---

## Structure

```
codepilot/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── review.py          # POST /api/review
│   │   └── history.py         # GET /api/history
│   ├── services/
│   │   ├── ai_service.py      # static analysis + OpenAI
│   │   └── history_service.py
│   └── models/
│       ├── database.py
│       └── schemas.py
└── frontend/
    └── src/
        ├── app/
        ├── components/
        │   ├── CodeInput.tsx
        │   ├── ResultPanel.tsx
        │   └── HistorySidebar.tsx
        └── lib/
            └── api.ts
```

---

