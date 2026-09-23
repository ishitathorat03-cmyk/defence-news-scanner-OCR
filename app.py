import streamlit as st
import feedparser
import hashlib
import sqlite3
import re
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Defence News Intelligence",
    page_icon="🛡️",
    layout="wide"
)

# =========================================================
# DATABASE
# =========================================================

DB_NAME = "defence_news.db"


def init_database():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            source TEXT,
            url TEXT,
            published TEXT,
            category TEXT,
            relevance INTEGER,
            fetched_at TEXT
        )
    """)

    conn.commit()
    conn.close()


init_database()

# =========================================================
# NEWS SOURCES
# =========================================================

NEWS_SOURCES = {

    "PIB India": [
        "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1"
    ],

    "Google News - Defence India": [
        "https://news.google.com/rss/search?q=defence+India&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Google News - Indian Army": [
        "https://news.google.com/rss/search?q=Indian+Army&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Google News - Indian Navy": [
        "https://news.google.com/rss/search?q=Indian+Navy&hl=en-IN&gl=IN&ceid=IN:en"
    ],

    "Google News - Indian Air Force": [
        "https://news.google.com/rss/search?q=Indian+Air+Force&hl=en-IN&gl=IN&ceid=IN:en"
    ]
}

# =========================================================
# DEFENCE CLASSIFICATION
# =========================================================

DEFENCE_KEYWORDS = {

    "Army": [
        "indian army",
        "army",
        "soldier",
        "troops",
        "military exercise",
        "army exercise",
        "regiment",
        "battalion",
        "border forces",
        "army chief"
    ],

    "Navy": [
        "indian navy",
        "navy",
        "naval",
        "warship",
        "submarine",
        "frigate",
        "destroyer",
        "aircraft carrier",
        "naval exercise",
        "navy chief"
    ],

    "Air Force": [
        "indian air force",
        "air force",
        "iaf",
        "fighter aircraft",
        "military aircraft",
        "air force exercise",
        "air chief"
    ],

    "Defence Technology": [
        "missile",
        "drdo",
        "defence technology",
        "defense technology",
        "radar",
        "defence research",
        "military technology",
        "defence system"
    ],

    "Defence Policy": [
        "ministry of defence",
        "defence ministry",
        "defence deal",
        "defence procurement",
        "military",
        "armed forces",
        "defence budget",
        "defence production"
    ],

    "Security": [
        "border security",
        "paramilitary",
        "bsf",
        "crpf",
        "coast guard",
        "counter terrorism",
        "counter-terrorism"
    ]
}


def analyse_article(title, summary):

    text = f"{title} {summary}".lower()

    category_scores = {}

    for category, keywords in DEFENCE_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        category_scores[category] = score

    best_category = max(
        category_scores,
        key=category_scores.get
    )

    score = category_scores[best_category]

    # Convert to relevance percentage
    relevance = min(score * 20, 100)

    return best_category, relevance


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# FETCH RSS
# =========================================================

def fetch_news():

    all_articles = []

    for source_name, feeds in NEWS_SOURCES.items():

        for feed_url in feeds:

            try:

                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:30]:

                    title = clean_text(
                        entry.get("title", "")
                    )

                    summary = clean_text(
                        entry.get(
                            "summary",
                            entry.get(
                                "description",
                                ""
                            )
                        )
                    )

                    url = entry.get(
                        "link",
                        ""
                    )

                    published = entry.get(
                        "published",
                        entry.get(
                            "updated",
                            ""
                        )
                    )

                    if not title:
                        continue

                    category, relevance = analyse_article(
                        title,
                        summary
                    )

                    # Only keep defence-related articles
                    if relevance < 20:
                        continue

                    unique_string = (
                        title.lower()
                        + source_name
                    )

                    article_id = hashlib.sha256(
                        unique_string.encode(
                            "utf-8"
                        )
                    ).hexdigest()

                    all_articles.append({

                        "id": article_id,

                        "title": title,

                        "summary": summary,

                        "source": source_name,

                        "url": url,

                        "published": published,

                        "category": category,

                        "relevance": relevance

                    })

            except Exception:
                continue

    return all_articles


# =========================================================
# SAVE NEWS
# =========================================================

def save_news(articles):

    conn = sqlite3.connect(DB_NAME)

    new_count = 0

    for article in articles:

        try:

            conn.execute("""
                INSERT INTO news
                (
                    id,
                    title,
                    summary,
                    source,
                    url,
                    published,
                    category,
                    relevance,
                    fetched_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (

                article["id"],
                article["title"],
                article["summary"],
                article["source"],
                article["url"],
                article["published"],
                article["category"],
                article["relevance"],
                datetime.now().isoformat()

            ))

            new_count += 1

        except sqlite3.IntegrityError:

            # Already exists
            pass

    conn.commit()
    conn.close()

    return new_count


# =========================================================
# LOAD DATABASE
# =========================================================

def load_news():

    conn = sqlite3.connect(DB_NAME)

    rows = conn.execute("""
        SELECT
            title,
            summary,
            source,
            url,
            published,
            category,
            relevance
        FROM news
        ORDER BY rowid DESC
    """).fetchall()

    conn.close()

    return rows


# =========================================================
# HEADER
# =========================================================

st.title("🛡️ Defence News Intelligence")

st.caption(
    "Automatically collecting and analysing defence-related news"
)

# =========================================================
# FETCH BUTTON
# =========================================================

col1, col2 = st.columns([1, 5])

with col1:

    refresh = st.button(
        "🔄 Fetch Latest News",
        use_container_width=True
    )

if refresh:

    with st.spinner(
        "🌐 Fetching latest news..."
    ):

        articles = fetch_news()

        new_count = save_news(
            articles
        )

    st.success(
        f"✅ Fetch completed — {new_count} new articles added."
    )

# =========================================================
# LOAD DATA
# =========================================================

news = load_news()

# =========================================================
# DASHBOARD METRICS
# =========================================================

st.divider()

total_news = len(news)

categories = set()

for item in news:

    categories.add(
        item[5]
    )

col1, col2, col3 = st.columns(3)

col1.metric(
    "📰 Total Defence News",
    total_news
)

col2.metric(
    "📂 Categories",
    len(categories)
)

col3.metric(
    "🔄 Data Mode",
    "Live RSS"
)

# =========================================================
# FILTERS
# =========================================================

st.divider()

st.subheader(
    "🔎 Defence News"
)

col1, col2 = st.columns(2)

with col1:

    search = st.text_input(
        "Search news",
        placeholder="Army, Navy, DRDO..."
    )

with col2:

    category_options = [
        "All"
    ] + sorted(
        list(categories)
    )

    selected_category = st.selectbox(
        "Category",
        category_options
    )

# =========================================================
# DISPLAY
# =========================================================

shown = 0

for item in news:

    title = item[0]
    summary = item[1]
    source = item[2]
    url = item[3]
    published = item[4]
    category = item[5]
    relevance = item[6]

    searchable_text = (
        title + " " + summary
    ).lower()

    if search:

        if search.lower() not in searchable_text:
            continue

    if selected_category != "All":

        if category != selected_category:
            continue

    shown += 1

    with st.container():

        st.markdown(
            f"### 📰 {title}"
        )

        st.caption(
            f"📌 {source}  |  "
            f"📅 {published}  |  "
            f"🏷️ {category}  |  "
            f"🎯 Relevance: {relevance}%"
        )

        if summary:

            st.write(
                summary
            )

        if url:

            st.markdown(
                f"[🔗 Read Original Source]({url})"
            )

        st.divider()


if shown == 0:

    st.info(
        "No matching defence news found."
    )

# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Defence News Intelligence System • "
    "Automated source ingestion + defence relevance analysis"
)
