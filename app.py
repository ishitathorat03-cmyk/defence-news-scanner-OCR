import streamlit as st
import feedparser
import hashlib
import re
from datetime import datetime

from database import init_database, insert_news, get_news
from sources import get_languages, get_sources


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Defence News Intelligence",
    page_icon="🛡️",
    layout="wide"
)

# ==========================================================
# DATABASE
# ==========================================================

init_database()


# ==========================================================
# RSS SOURCES
# ==========================================================

RSS_SOURCES = {

    "PIB": {
        "language": "English",
        "url": "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1"
    },

    "Google News - Defence India": {
        "language": "English",
        "url": "https://news.google.com/rss/search?q=defence+India&hl=en-IN&gl=IN&ceid=IN:en"
    },

    "Google News - Indian Army": {
        "language": "English",
        "url": "https://news.google.com/rss/search?q=Indian+Army&hl=en-IN&gl=IN&ceid=IN:en"
    },

    "Google News - Indian Navy": {
        "language": "English",
        "url": "https://news.google.com/rss/search?q=Indian+Navy&hl=en-IN&gl=IN&ceid=IN:en"
    },

    "Google News - Indian Air Force": {
        "language": "English",
        "url": "https://news.google.com/rss/search?q=Indian+Air+Force&hl=en-IN&gl=IN&ceid=IN:en"
    }
}


# ==========================================================
# DEFENCE KEYWORDS
# ==========================================================

DEFENCE_KEYWORDS = {

    "Army": [
        "indian army",
        "army",
        "soldier",
        "soldiers",
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
        "defence system",
        "weapon system"
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


# ==========================================================
# TEXT CLEANING
# ==========================================================

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


# ==========================================================
# ARTICLE ANALYSIS
# ==========================================================

def analyse_article(title, summary):

    text = (
        f"{title} {summary}"
    ).lower()

    category_scores = {}

    for category, keywords in DEFENCE_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        category_scores[
            category
        ] = score

    best_category = max(
        category_scores,
        key=category_scores.get
    )

    score = category_scores[
        best_category
    ]

    relevance = min(
        score * 20,
        100
    )

    return (
        best_category,
        relevance
    )


# ==========================================================
# FETCH RSS NEWS
# ==========================================================

def fetch_rss_news():

    collected = []

    for source, config in RSS_SOURCES.items():

        try:

            feed = feedparser.parse(
                config["url"]
            )

            for entry in feed.entries[:40]:

                title = clean_text(
                    entry.get(
                        "title",
                        ""
                    )
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

                article_url = entry.get(
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

                category, relevance = (
                    analyse_article(
                        title,
                        summary
                    )
                )

                if relevance < 20:
                    continue

                article_id = hashlib.sha256(
                    (
                        title.lower()
                        + source
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()

                article = {

                    "id": article_id,

                    "title": title,

                    "content": summary,

                    "summary": summary,

                    "source": source,

                    "language": config[
                        "language"
                    ],

                    "published_date": (
                        published[:25]
                        if published
                        else datetime.now().strftime(
                            "%Y-%m-%d"
                        )
                    ),

                    "category": category,

                    "relevance": relevance,

                    "source_type": "RSS",

                    "source_url": config[
                        "url"
                    ],

                    "article_url": article_url
                }

                collected.append(
                    article
                )

        except Exception:
            continue

    return collected


# ==========================================================
# SAVE ARTICLES
# ==========================================================

def save_articles(articles):

    count = 0

    for article in articles:

        before = len(
            get_news()
        )

        insert_news(
            article
        )

        after = len(
            get_news()
        )

        if after > before:
            count += 1

    return count


# ==========================================================
# HEADER
# ==========================================================

st.title(
    "🛡️ Defence News Intelligence"
)

st.write(
    "Multilingual defence news collection, "
    "analysis and searchable archive."
)


# ==========================================================
# FETCH
# ==========================================================

if st.button(
    "🔄 Fetch Latest News",
    type="primary"
):

    with st.spinner(
        "🌐 Collecting latest defence news..."
    ):

        articles = fetch_rss_news()

        new_articles = 0

        for article in articles:

            insert_news(
                article
            )

            new_articles += 1

    st.success(
        f"✅ Collection completed. "
        f"{new_articles} articles processed."
    )


# ==========================================================
# LOAD DATABASE
# ==========================================================

all_news = get_news()


# ==========================================================
# FILTER VALUES
# ==========================================================

languages_available = sorted(
    list(
        set(
            row[5]
            for row in all_news
            if row[5]
        )
    )
)

sources_available = sorted(
    list(
        set(
            row[4]
            for row in all_news
            if row[4]
        )
    )
)

dates_available = sorted(
    list(
        set(
            row[6]
            for row in all_news
            if row[6]
        )
    ),
    reverse=True
)

categories_available = sorted(
    list(
        set(
            row[7]
            for row in all_news
            if row[7]
        )
    )
)


# ==========================================================
# FILTER PANEL
# ==========================================================

st.divider()

st.subheader(
    "🔎 Search Defence News"
)

col1, col2 = st.columns(2)

with col1:

    selected_language = st.selectbox(
        "🌐 Language",
        ["All"] + languages_available
    )

with col2:

    selected_source = st.selectbox(
        "📰 Newspaper / Source",
        ["All"] + sources_available
    )


col3, col4 = st.columns(2)

with col3:

    selected_date = st.selectbox(
        "📅 Date",
        ["All"] + dates_available
    )

with col4:

    selected_category = st.selectbox(
        "🛡️ Defence Category",
        ["All"] + categories_available
    )


search_text = st.text_input(
    "🔍 Search within articles",
    placeholder="Army, missile, DRDO, Navy..."
)


# ==========================================================
# FILTER DATABASE
# ==========================================================

filtered_news = []

for row in all_news:

    language = row[5]
    source = row[4]
    date = row[6]
    category = row[7]

    if (
        selected_language != "All"
        and language != selected_language
    ):
        continue

    if (
        selected_source != "All"
        and source != selected_source
    ):
        continue

    if (
        selected_date != "All"
        and date != selected_date
    ):
        continue

    if (
        selected_category != "All"
        and category != selected_category
    ):
        continue

    if search_text:

        searchable = (
            str(row[1])
            + " "
            + str(row[2])
        ).lower()

        if (
            search_text.lower()
            not in searchable
        ):
            continue

    filtered_news.append(
        row
    )


# ==========================================================
# DASHBOARD METRICS
# ==========================================================

st.divider()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "📰 Total Articles",
    len(all_news)
)

c2.metric(
    "🔎 Matching",
    len(filtered_news)
)

c3.metric(
    "🌐 Languages",
    len(languages_available)
)

c4.metric(
    "📰 Sources",
    len(sources_available)
)


# ==========================================================
# RESULTS
# ==========================================================

st.divider()

st.subheader(
    "📰 Defence News"
)

if not filtered_news:

    st.info(
        "No matching defence news found. "
        "Click 'Fetch Latest News' first."
    )

else:

    for row in filtered_news:

        (
            article_id,
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
        ) = row

        st.markdown(
            f"### 📰 {title}"
        )

        st.caption(
            f"🌐 {language}  |  "
            f"📰 {source}  |  "
            f"📅 {published_date}  |  "
            f"🏷️ {category}  |  "
            f"🎯 {relevance}% relevance"
        )

        if content:

            st.write(
                content
            )

        if article_url:

            st.markdown(
                f"[🔗 Read Original Article]"
                f"({article_url})"
            )

        st.divider()
