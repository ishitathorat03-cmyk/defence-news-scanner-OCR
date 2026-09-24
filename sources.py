# ==========================================================
# DEFENCE NEWS SOURCE REGISTRY
# ==========================================================

LANGUAGES = [
    "All",
    "English",
    "Hindi",
    "Marathi",
    "Gujarati",
    "Tamil",
    "Telugu",
    "Kannada",
    "Malayalam",
    "Bengali",
    "Assamese",
    "Punjabi",
    "Odia",
    "Urdu"
]


# Sources that we can expand over time.
# We do NOT pretend a source is available until
# its feed/archive is actually verified.

SOURCES = {

    "PIB": {
        "type": "RSS",
        "languages": [
            "English",
            "Hindi",
            "Marathi",
            "Kannada",
            "Assamese"
        ]
    },

    "New India Samachar": {
        "type": "E-PAPER",
        "languages": [
            "English",
            "Hindi",
            "Marathi",
            "Gujarati",
            "Tamil",
            "Telugu",
            "Kannada",
            "Malayalam",
            "Bengali",
            "Assamese",
            "Punjabi",
            "Odia",
            "Urdu"
        ]
    }

}


def get_languages():

    return LANGUAGES


def get_sources():

    return [
        "All",
        *SOURCES.keys()
    ]
