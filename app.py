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

KEYWORDS = [
    "army", "military", "defence", "defense", "navy",
    "air force", "missile", "border", "soldier", "drone",
    "security", "weapon", "operation", "armed forces",
    "ministry of defence", "indian army", "indian navy",
    "iaf", "military exercise", "bsf", "crpf", "paramilitary",
    "aircraft", "fighter", "warship", "troops", "forces"
]

def is_defence_line(line):
    line_lower = line.lower()
    return any(keyword in line_lower for keyword in KEYWORDS)

def extract_defence_articles(text):
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    articles = []
    current = []

    for line in lines:

        if is_defence_line(line):
            current.append(line)

        elif current:
            if len(line) > 15:
                current.append(line)

            if len(current) >= 4:
                articles.append(" ".join(current))
                current = []

    if current:
        articles.append(" ".join(current))

    # Remove very short/duplicate results
    cleaned = []
    seen = set()

    for article in articles:
        article = article.strip()

        if len(article) >= 50:
            key = article[:150].lower()

            if key not in seen:
                seen.add(key)
                cleaned.append(article)

    return cleaned


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
