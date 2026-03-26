import json
from models.database import get_connection
from models.schemas import HistoryItem

def save_review(language: str, code: str, result: dict):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reviews (language, code, result) VALUES (?, ?, ?)",
        (language, code, json.dumps(result))
    )
    conn.commit()
    # Keep only last 20 reviews
    conn.execute("""
        DELETE FROM reviews WHERE id NOT IN (
            SELECT id FROM reviews ORDER BY created_at DESC LIMIT 20
        )
    """)
    conn.commit()
    conn.close()

def get_recent_reviews(limit: int = 5) -> list[HistoryItem]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, language, code, result, created_at FROM reviews ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        id_, lang, code, result_json, created_at = row
        result = json.loads(result_json)
        items.append(HistoryItem(
            id=id_,
            language=lang,
            code_preview=code[:120] + ("..." if len(code) > 120 else ""),
            summary=result.get("summary", "")[:100],
            created_at=created_at
        ))
    return items
