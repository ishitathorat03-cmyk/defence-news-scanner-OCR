import streamlit as st
from PIL import Image
import pytesseract
import fitz
import re
import pandas as pd
from langdetect import detect

pytesseract.pytesseract.tesseract_cmd = "tesseract"

st.set_page_config(
    page_title="Defence News Scanner OCR",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Defence News Scanner OCR")
st.write("Upload a newspaper image or PDF and extract defence-related news using OCR.")

file = st.file_uploader(
    "📂 Upload News File",
    type=["png", "jpg", "jpeg", "pdf"]
)

KEYWORDS = [
    "army", "military", "defence", "defense", "navy",
    "air force", "missile", "border", "soldier", "drone",
    "security", "weapon", "operation", "armed forces",
    "ministry of defence", "india", "military exercise",
    "iaf", "indian army", "indian navy"
]

if file:

    st.success(f"✅ File uploaded: {file.name}")

    text = ""

    # IMAGE OCR
    if file.type.startswith("image"):

        image = Image.open(file)

        st.image(
            image,
            caption="Uploaded Newspaper",
            use_container_width=True
        )

        with st.spinner("🔍 Extracting newspaper text..."):
            text = pytesseract.image_to_string(image)

    # PDF OCR
    elif file.type == "application/pdf":

        with st.spinner("📄 Scanning newspaper PDF with OCR..."):

            pdf_bytes = file.read()
 doc = fitz.open(
     stream=pdf_bytes,
     filetype="pdf"
 )

 pages_text = []

 max_pages = st.number_input(
     "📄 Pages to scan",
     min_value=1,
     max_value=len(doc),
     value=len(doc)
 )

 for page_number, page in enumerate(
     list(doc)[:int(max_pages)],
     start=1
 ):

                st.write(f"🔍 Scanning page {page_number}...")

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
                    f"--- PAGE {page_number} ---\n{page_text}"
                )

            text = "\n\n".join(pages_text)

    # RESULTS
    if text.strip():

        st.divider()

        st.header("📰 Extracted Newspaper News")

        st.text_area(
            "Complete OCR Text",
            text,
            height=350
        )

        # Split OCR into lines
        lines = [
            line.strip()
            for line in text.splitlines()
            if len(line.strip()) > 20
        ]

        defence_lines = []

        for line in lines:

            line_lower = line.lower()

            matched = [
                keyword
                for keyword in KEYWORDS
                if keyword in line_lower
            ]

            if matched:
                defence_lines.append({
                    "News / Content": line,
                    "Detected Keywords": ", ".join(matched)
                })

        st.divider()

        st.header("🛡️ Defence-Related News")

        if defence_lines:

            st.success(
                f"✅ {len(defence_lines)} defence-related news/content lines detected"
            )

            df = pd.DataFrame(defence_lines)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📌 News Headlines / Key Content")

            for i, item in enumerate(defence_lines, start=1):

                st.markdown(
                    f"**{i}. {item['News / Content']}**"
                )

        else:

            st.warning(
                "No defence-related news was detected in the scanned pages."
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
            int(max_pages)
        )

        col3.metric(
            "Defence Items",
            len(defence_lines)
        )

    else:

        st.error(
            "❌ No readable text was extracted from this file."
        )
