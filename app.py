import streamlit as st
from PIL import Image
import pytesseract
import fitz
import pandas as pd
import re

pytesseract.pytesseract.tesseract_cmd = "tesseract"

st.set_page_config(
    page_title="Defence News Scanner OCR",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Defence News Scanner OCR")
st.write("Upload a newspaper image or PDF and extract defence-related news using OCR.")

DEFENCE_STRONG = [
    "indian army",
    "indian navy",
    "indian air force",
    "iaf",
    "ministry of defence",
    "defence ministry",
    "armed forces",
    "military exercise",
    "naval exercise",
    "army exercise",
    "air force exercise",
    "defence deal",
    "defence forces",
    "military operation",
    "military deployment",
    "military training"
]

DEFENCE_SPECIFIC = [
    "missile",
    "warship",
    "fighter aircraft",
    "military aircraft",
    "aircraft carrier",
    "submarine",
    "frigate",
    "destroyer",
    "military helicopter",
    "army regiment",
    "battalion",
    "military base",
    "military command",
    "defence procurement",
    "defence equipment",
    "border forces",
    "troops",
    "soldiers",
    "bsf",
    "crpf",
    "coast guard",
    "paramilitary"
]

DEFENCE_CONTEXT = [
    "operation",
    "exercise",
    "deployment",
    "training",
    "procurement",
    "security",
    "border",
    "troops",
    "forces",
    "command",
    "regiment",
    "battalion",
    "aircraft",
    "warship",
    "missile",
    "military",
    "defence",
    "defense"
]


def defence_score(text):

    t = text.lower()

    strong = sum(
        1 for word in DEFENCE_STRONG
        if word in t
    )

    specific = sum(
        1 for word in DEFENCE_SPECIFIC
        if word in t
    )

    context = sum(
        1 for word in DEFENCE_CONTEXT
        if word in t
    )

    score = (
        strong * 4
        + specific * 2
        + context
    )

    return score


def extract_defence_articles(text):

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if len(line.strip()) > 8
    ]

    articles = []
    current = []

    for line in lines:

        current.append(line)

        block = " ".join(current)

        score = defence_score(block)

        # Accept even short defence articles
        if score >= 7:
            articles.append(block)
            current = []

        # Don't allow one article to become huge
        elif len(current) >= 7:
            if defence_score(block) >= 4:
                articles.append(block)

            current = []

    # Check remaining text
    if current:
        block = " ".join(current)

        if defence_score(block) >= 4:
            articles.append(block)

    # Remove duplicates
    final_articles = []
    seen = set()

    for article in articles:

        article = article.strip()

        # MUCH lower minimum size
        if len(article) < 25:
            continue

        key = article[:120].lower()

        if key not in seen:
            seen.add(key)
            final_articles.append(article)

    return final_articles


file = st.file_uploader(
    "📂 Upload News File",
    type=["png", "jpg", "jpeg", "pdf"]
)

if file:

    st.success("✅ File uploaded: " + file.name)

    text = ""
    total_pages = 1
    pages_scanned = 1

    # IMAGE
    if file.type.startswith("image"):

        image = Image.open(file)

        st.image(
            image,
            caption="Uploaded Newspaper",
            use_container_width=True
        )

        with st.spinner("🔍 Extracting newspaper text..."):
            text = pytesseract.image_to_string(image)

    # PDF
    elif file.type == "application/pdf":

        pdf_bytes = file.read()

        doc = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        total_pages = len(doc)

        max_pages = st.number_input(
            "📄 Pages to scan",
            min_value=1,
            max_value=total_pages,
            value=total_pages,
            step=1
        )

        pages_text = []

        progress = st.progress(0)

        for page_number, page in enumerate(
            doc,
            start=1
        ):

            if page_number > int(max_pages):
                break

            st.write(
                f"🔍 Scanning page {page_number} of {int(max_pages)}..."
            )

            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.3, 1.3)
            )

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            page_text = pytesseract.image_to_string(img)

            pages_text.append(
                f"\n--- PAGE {page_number} ---\n{page_text}"
            )

            progress.progress(
                page_number / int(max_pages)
            )

        pages_scanned = int(max_pages)
        text = "\n".join(pages_text)

    # RESULTS

    if text.strip():

        st.divider()

        st.header("📰 Defence News Extracted")

        defence_articles = extract_defence_articles(text)

        if defence_articles:

            st.success(
                f"🛡️ {len(defence_articles)} defence-related news items extracted"
            )

            for number, article in enumerate(
                defence_articles,
                start=1
            ):

                st.markdown(
                    f"### 📰 News {number}"
                )

                st.write(article)

                st.divider()

            # Download extracted defence news
            download_text = "\n\n".join(
                [
                    f"NEWS {i}\n{article}"
                    for i, article in enumerate(
                        defence_articles,
                        start=1
                    )
                ]
            )

            st.download_button(
                "⬇️ Download Defence News",
                download_text,
                file_name="defence_news_extracted.txt",
                mime="text/plain"
            )

        else:

            st.warning(
                "No defence-related news was detected."
            )

        with st.expander("🔎 View Complete OCR Text"):

            st.text_area(
                "Complete Newspaper OCR",
                text,
                height=400
            )

        st.divider()

        st.subheader("📊 Scanner Status")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "OCR Engine",
            "Tesseract"
        )

        col2.metric(
            "Pages Scanned",
            pages_scanned
        )

        col3.metric(
            "Defence News",
            len(defence_articles)
        )

    else:

        st.error(
            "❌ No readable text was extracted."
        )
