import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pytesseract import Output
import fitz
import pandas as pd
import re

# =========================================================
# TESSERACT
# =========================================================

pytesseract.pytesseract.tesseract_cmd = "tesseract"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Defence News Scanner OCR",
    page_icon="🛡️",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🛡️ Defence News Scanner OCR")

st.write(
    "Upload a newspaper image or PDF. "
    "The system scans the complete material and extracts "
    "defence-related news, including small articles."
)


# =========================================================
# DEFENCE VOCABULARY
# =========================================================

DEFENCE_STRONG = [
    "indian army",
    "indian navy",
    "indian air force",
    "air force",
    "iaf",
    "indian armed forces",
    "armed forces",
    "ministry of defence",
    "defence ministry",
    "defense ministry",
    "defence forces",
    "defense forces",
    "military operation",
    "military exercise",
    "military deployment",
    "military training",
    "naval exercise",
    "army exercise",
    "air force exercise",
    "defence deal",
    "defense deal",
    "defence procurement",
    "defense procurement",
    "defence equipment",
    "defense equipment",
    "counter terrorism",
    "counter-terrorism",
    "anti-terror operation",
    "anti terror operation",
    "terrorist attack",
    "terrorist group",
    "terrorist organisation",
    "terrorist organization",
    "militant group",
    "military operation",
    "military strike"
]


DEFENCE_SPECIFIC = [
    "missile",
    "rockets",
    "rocket system",
    "warship",
    "fighter aircraft",
    "fighter jet",
    "military aircraft",
    "aircraft carrier",
    "submarine",
    "frigate",
    "destroyer",
    "military helicopter",
    "helicopter",
    "army regiment",
    "regiment",
    "battalion",
    "military base",
    "air base",
    "naval base",
    "military command",
    "defence command",
    "defense command",
    "defence equipment",
    "defense equipment",
    "defence technology",
    "defense technology",
    "weapons system",
    "weapon system",
    "ammunition",
    "artillery",
    "tank",
    "armoured",
    "armored",
    "drone",
    "uav",
    "unmanned aerial vehicle",
    "border security force",
    "border forces",
    "bsf",
    "crpf",
    "itbp",
    "cisf",
    "sashastra seema bal",
    "coast guard",
    "paramilitary",
    "special forces",
    "commando",
    "troops",
    "soldiers",
    "military personnel",
    "militants",
    "terrorists",
    "terrorist",
    "terrorism",
    "terror attack",
    "terror attack",
    "counterterrorism",
    "insurgency",
    "insurgent",
    "cross border",
    "cross-border",
    "ceasefire",
    "infiltration",
    "infiltrators",
    "line of control",
    "loc",
    "line of actual control",
    "lac",
    "military intelligence",
    "intelligence agency",
    "strategic forces"
]


DEFENCE_CONTEXT = [
    "operation",
    "exercise",
    "deployment",
    "training",
    "procurement",
    "security forces",
    "security personnel",
    "border",
    "border security",
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
    "defense",
    "soldiers",
    "terrorist",
    "terrorists",
    "terrorism",
    "militant",
    "militants",
    "counter terror",
    "counter-terror",
    "anti-terror",
    "infiltration",
    "army personnel",
    "naval personnel",
    "air force personnel"
]


# =========================================================
# NON-DEFENCE WORDS
# These help reduce obvious false positives.
# =========================================================

NON_DEFENCE = [
    "school admission",
    "college admission",
    "exam result",
    "stock market",
    "share market",
    "real estate",
    "movie review",
    "film review",
    "celebrity",
    "fashion show",
    "cricket match",
    "football match",
    "recipe",
    "restaurant",
    "wedding",
    "horoscope",
    "weather forecast",
    "property prices",
    "job fair",
    "shopping",
    "television serial"
]


# =========================================================
# NORMALIZE OCR TEXT
# =========================================================

def normalize_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s\-]",
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
# DEFENCE SCORE
# =========================================================

def defence_score(text):

    t = normalize_text(text)

    strong_hits = [
        word for word in DEFENCE_STRONG
        if word in t
    ]

    specific_hits = [
        word for word in DEFENCE_SPECIFIC
        if word in t
    ]

    context_hits = [
        word for word in DEFENCE_CONTEXT
        if word in t
    ]

    negative_hits = [
        word for word in NON_DEFENCE
        if word in t
    ]

    score = (
        len(strong_hits) * 6
        + len(specific_hits) * 3
        + len(context_hits)
        - len(negative_hits) * 4
    )

    return score


# =========================================================
# CHECK IF ARTICLE IS DEFENCE RELATED
# =========================================================

def is_defence_article(text):

    t = normalize_text(text)

    strong = any(
        word in t
        for word in DEFENCE_STRONG
    )

    specific_count = sum(
        1
        for word in DEFENCE_SPECIFIC
        if word in t
    )

    context_count = sum(
        1
        for word in DEFENCE_CONTEXT
        if word in t
    )

    negative_count = sum(
        1
        for word in NON_DEFENCE
        if word in t
    )

    # Strong defence article
    if strong and negative_count <= 1:
        return True

    # Multiple specific defence signals
    if specific_count >= 2 and context_count >= 1:
        return True

    # Terrorism / counter-terrorism stories
    terror_words = [
        "terrorist",
        "terrorists",
        "terrorism",
        "terror attack",
        "militant",
        "militants",
        "insurgent",
        "insurgency",
        "counter terror",
        "counter-terror",
        "anti-terror"
    ]

    terror_found = any(
        word in t
        for word in terror_words
    )

    security_words = [
        "security forces",
        "armed forces",
        "troops",
        "army personnel",
        "military personnel",
        "operation",
        "captured",
        "arrested",
        "neutralised",
        "neutralized"
    ]

    security_found = any(
        word in t
        for word in security_words
    )

    if terror_found and security_found:
        return True

    return False


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image):

    image = image.convert("RGB")

    # Increase resolution for small newspaper text
    width, height = image.size

    target_width = max(
        width,
        2500
    )

    if width < target_width:

        scale = target_width / width

        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            ),
            Image.Resampling.LANCZOS
        )

    # Grayscale
    gray = image.convert("L")

    # Improve contrast
    gray = ImageEnhance.Contrast(gray).enhance(1.8)

    # Slight sharpening
    gray = gray.filter(
        ImageFilter.SHARPEN
    )

    return gray


# =========================================================
# OCR
# =========================================================

def perform_ocr(image):

    processed = preprocess_image(image)

    config = "--oem 3 --psm 3"

    text = pytesseract.image_to_string(
        processed,
        config=config
    )

    return text


# =========================================================
# OCR WITH WORD POSITIONS
# =========================================================

def perform_layout_ocr(image):

    processed = preprocess_image(image)

    config = (
        "--oem 3 "
        "--psm 3"
    )

    data = pytesseract.image_to_data(
        processed,
        output_type=Output.DATAFRAME,
        config=config
    )

    data = data.dropna(
        subset=["text"]
    )

    data["text"] = data["text"].astype(str)

    data = data[
        data["text"].str.strip() != ""
    ]

    return data, processed


# =========================================================
# ARTICLE EXTRACTION
# =========================================================

def extract_defence_articles(text):

    # =====================================================
    # CLEAN OCR TEXT
    # =====================================================

    raw_lines = text.splitlines()

    lines = []

    for line in raw_lines:

        line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        if len(line) >= 3:
            lines.append(line)


    # =====================================================
    # STEP 1
    # FIND DEFENCE-RELATED AREAS
    # =====================================================

    defence_indexes = []

    for i, line in enumerate(lines):

        if is_defence_article(line):

            defence_indexes.append(i)


    # =====================================================
    # STEP 2
    # GROUP NEIGHBOURING LINES
    #
    # Lines close to each other are treated as one article.
    # =====================================================

    groups = []

    if defence_indexes:

        current_group = [
            defence_indexes[0]
        ]

        for index in defence_indexes[1:]:

            previous = current_group[-1]

            # Newspaper article lines are normally
            # close together in OCR output.
            if index - previous <= 5:

                current_group.append(index)

            else:

                groups.append(
                    current_group
                )

                current_group = [
                    index
                ]

        groups.append(
            current_group
        )


    # =====================================================
    # STEP 3
    # EXPAND EACH GROUP
    #
    # If a defence line is found, include the surrounding
    # article lines instead of returning only that line.
    # =====================================================

    articles = []

    for group in groups:

        first = min(group)
        last = max(group)

        # Expand around detected defence content
        start = max(
            0,
            first - 3
        )

        end = min(
            len(lines),
            last + 4
        )

        article_lines = lines[start:end]

        article = " ".join(
            article_lines
        )

        article = re.sub(
            r"\s+",
            " ",
            article
        ).strip()


        # =================================================
        # ONLY KEEP ACTUAL DEFENCE ARTICLES
        # =================================================

        if is_defence_article(article):

            articles.append(
                article
            )


    # =====================================================
    # STEP 4
    # MERGE OVERLAPPING ARTICLES
    #
    # This prevents:
    #
    # Line 1 → News 1
    # Line 2 → News 2
    # Line 3 → News 3
    #
    # from the SAME newspaper article.
    # =====================================================

    merged_articles = []

    for article in articles:

        article_words = set(
            normalize_text(article).split()
        )

        merged = False

        for i, existing in enumerate(
            merged_articles
        ):

            existing_words = set(
                normalize_text(existing).split()
            )

            if not article_words or not existing_words:
                continue

            intersection = (
                article_words.intersection(
                    existing_words
                )
            )

            union = (
                article_words.union(
                    existing_words
                )
            )

            similarity = (
                len(intersection)
                / len(union)
            )

            # Same article
            if similarity >= 0.35:

                merged_articles[i] = (
                    existing + " " + article
                )

                merged = True
                break


        if not merged:

            merged_articles.append(
                article
            )


    # =====================================================
    # STEP 5
    # REMOVE DUPLICATES
    # =====================================================

    final_articles = []

    for article in merged_articles:

        article = re.sub(
            r"\s+",
            " ",
            article
        ).strip()

        if len(article) < 20:
            continue

        duplicate = False

        article_words = set(
            normalize_text(article).split()
        )

        for existing in final_articles:

            existing_words = set(
                normalize_text(existing).split()
            )

            if not article_words or not existing_words:
                continue

            overlap = (
                len(
                    article_words.intersection(
                        existing_words
                    )
                )
                /
                len(
                    article_words.union(
                        existing_words
                    )
                )
            )

            if overlap >= 0.55:

                duplicate = True
                break


        if not duplicate:

            final_articles.append(
                article
            )


    return final_articles


# =========================================================
# FILE UPLOADER
# =========================================================

file = st.file_uploader(
    "📂 Upload News File",
    type=[
        "png",
        "jpg",
        "jpeg",
        "pdf"
    ]
)


# =========================================================
# PROCESS FILE
# =========================================================

if file:

    st.success(
        "✅ File uploaded: " + file.name
    )

    text = ""

    total_pages = 1
    pages_scanned = 1

    # =====================================================
    # IMAGE
    # =====================================================

    if file.type.startswith("image"):

        image = Image.open(file)

        st.image(
            image,
            caption="Uploaded Newspaper",
            use_container_width=True
        )

        with st.spinner(
            "🔍 Reading newspaper image..."
        ):

            text = perform_ocr(image)

    # =====================================================
    # PDF
    # =====================================================

    elif file.type == "application/pdf":

        pdf_bytes = file.read()

        doc = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        total_pages = len(doc)

        st.info(
            f"📑 PDF contains {total_pages} pages."
        )

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
                f"🔍 Scanning page "
                f"{page_number} of "
                f"{int(max_pages)}..."
            )

            # HIGHER RESOLUTION
            pix = page.get_pixmap(
                matrix=fitz.Matrix(
                    2.5,
                    2.5
                )
            )

            img = Image.frombytes(
                "RGB",
                [
                    pix.width,
                    pix.height
                ],
                pix.samples
            )

            page_text = perform_ocr(
                img
            )

            pages_text.append(
                f"\n--- PAGE {page_number} ---\n"
                f"{page_text}"
            )

            progress.progress(
                page_number /
                int(max_pages)
            )

        pages_scanned = int(
            max_pages
        )

        text = "\n".join(
            pages_text
        )


# =========================================================
# RESULTS
# =========================================================

if file and text.strip():

    st.divider()

    st.header(
        "📰 Defence News Extracted"
    )

    defence_articles = (
        extract_defence_articles(text)
    )

    # =====================================================
    # DEFENCE NEWS FOUND
    # =====================================================

    if defence_articles:

        st.success(
            f"🛡️ {len(defence_articles)} "
            f"defence-related news items detected"
        )

        for number, article in enumerate(
            defence_articles,
            start=1
        ):

            st.markdown(
                f"### 📰 News {number}"
            )

            score = defence_score(
                article
            )

            st.caption(
                f"Defence relevance score: {score}"
            )

            st.write(
                article
            )

            st.divider()

        # =================================================
        # DOWNLOAD
        # =================================================

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
            file_name=(
                "defence_news_extracted.txt"
            ),
            mime="text/plain"
        )

    # =====================================================
    # NOTHING FOUND
    # =====================================================

    else:

        st.warning(
            "⚠️ No defence-related news was detected."
        )

        st.info(
            "The OCR text is shown below so you can "
            "check whether the newspaper text was read correctly."
        )

    # =====================================================
    # OCR TEXT
    # =====================================================

    with st.expander(
        "🔎 View Complete OCR Text"
    ):

        st.text_area(
            "Complete Newspaper OCR",
            text,
            height=500
        )

    # =====================================================
    # STATUS
    # =====================================================

    st.divider()

    st.subheader(
        "📊 Scanner Status"
    )

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

elif file:

    st.error(
        "❌ No readable text was extracted."
    )
