import sqlite3
from datetime import datetime

DB_NAME = "defence_news.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            source TEXT,
            language TEXT,
            published_date TEXT,
            category TEXT,
            relevance INTEGER,
            source_type TEXT,
            source_url TEXT,
            article_url TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_language
        ON news(language)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_source
        ON news(source)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_date
        ON news(published_date)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_category
        ON news(category)
    """)

    conn.commit()
    conn.close()


def insert_news(article):

    conn = get_connection()

    try:

        conn.execute("""
            INSERT OR IGNORE INTO news
            (
                id,
                title,
                content,
                summary,
                source,
                language,
                published_date,
                category,
                relevance,
                source_type,
                source_url,
                article_url,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            article["id"],
            article["title"],
            article.get("content", ""),
            article.get("summary", ""),
            article["source"],
            article["language"],
            article["published_date"],
            article["category"],
            article["relevance"],
            article["source_type"],
            article.get("source_url", ""),
            article.get("article_url", ""),
            datetime.now().isoformat()

        ))

        conn.commit()

    finally:

        conn.close()


def get_news(
    language="All",
    source="All",
    date="All",
    category="All"
):

    conn = get_connection()

    query = """
        SELECT
            id,
            title,
            content,
            summary,
            source,
            language,
            published_date,
            category,
            relevance,
            source_type,
            source_url,
            article_url
        FROM news
        WHERE 1=1
    """

    params = []

    if language != "All":

        query += " AND language = ?"
        params.append(language)

    if source != "All":

        query += " AND source = ?"
        params.append(source)

    if date != "All":

        query += " AND published_date = ?"
        params.append(date)

    if category != "All":

        query += " AND category = ?"
        params.append(category)

    query += """
        ORDER BY published_date DESC, created_at DESC
    """

    rows = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return rows
