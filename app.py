import streamlit as st
from PIL import Image
import pytesseract
import fitz

# Tesseract
pytesseract.pytesseract.tesseract_cmd = "tesseract"

# Page settings
st.set_page_config(
    page_title="Defence News Scanner OCR",
    page_icon="🛡️"
)

# Title
st.title("🛡️ Defence News Scanner OCR")
st.write("Upload a newspaper image or PDF and extract defence-related news using OCR.")

# Upload
file = st.file_uploader(
    "📂 Upload News File",
    type=["png", "jpg", "jpeg", "pdf"]
)

if file:

    st.success("✅ File uploaded: " + file.name)

    text = ""

    # IMAGE OCR
    if file.type.startswith("image"):

        image = Image.open(file)

        st.image(
            image,
            caption="Uploaded News",
            use_container_width=True
        )

        with st.spinner("🔍 Running OCR..."):
            text = pytesseract.image_to_string(image)

    # PDF OCR
    elif file.type == "application/pdf":

        with st.spinner("📄 Scanning PDF with OCR..."):

            pdf_bytes = file.read()

            doc = fitz.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            pages_text = []

            for page in list(doc)[:3]:

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(1.2, 1.2)
                )

                img = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                page_text = pytesseract.image_to_string(img)

                pages_text.append(page_text)

            text = "\n\n".join(pages_text)

    # RESULTS
    if text.strip():

        st.subheader("📝 Extracted News")

        st.text_area(
            "OCR Text",
            text,
            height=300
        )

        keywords = [
            "army",
            "military",
            "defence",
            "defense",
            "navy",
            "air force",
            "missile",
            "border",
            "soldier",
            "drone",
            "security",
            "weapon",
            "operation",
            "armed forces",
            "ministry of defence"
        ]

        found = [
            word
            for word in keywords
            if word.lower() in text.lower()
        ]

        st.subheader("🔎 Defence Relevance")

        if found:

            st.success(
                "🛡️ Defence-related content detected"
            )

            st.write(
                "Detected keywords:",
                ", ".join(sorted(set(found)))
            )

        else:

            st.info(
                "ℹ️ No major defence keywords detected."
            )

        # Status
        st.subheader("📊 Scanner Status")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "OCR Engine",
            "Tesseract 5.5.3"
        )

        col2.metric(
            "File",
            file.name.split(".")[-1].upper()
        )

        col3.metric(
            "Status",
            "READY ✅"
        )

    else:

        st.warning(
            "⚠️ No readable text detected."
        )