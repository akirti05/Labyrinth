import streamlit as st
import requests
from sentence_transformers import SentenceTransformer

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="Labyrinth",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =============================
# GLOBAL CSS
# =============================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Libre+Baskerville:wght@400;700&display=swap');

    header, footer {visibility: hidden;}
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {display: none;}

    section[data-testid="stTextInput"],
    section[data-testid="stMarkdown"],
    section[data-testid="stAlert"] {
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
        margin: 0;
    }

    section.main > div:first-child > div {
        max-width: 420px !important;
        margin: 0 auto !important;
        background: rgba(0, 0, 0, 0.25) !important;
        height: 36px !important;
        border-radius: 10px !important;
    }

    .game-card {
        background: rgba(8, 8, 8, 0.78);
        border-radius: 18px;
        padding: 36px;
        max-width: 760px;
        margin: 40px auto;
        color: #f2f2f2;
        box-shadow: 0 20px 60px rgba(0,0,0,0.65);
    }

    .game-title {
        font-family: 'Cinzel', serif;
        font-size: clamp(3.5rem, 6vw, 5.5rem);
        font-weight: 700;
        letter-spacing: 0.18em;
        color: #f0eadc;
        text-align: center;
        margin-bottom: 18px;
    }

    h2, h3 {
        font-family: 'Cinzel', serif;
        letter-spacing: 0.06em;
    }

    .story-line {
        font-family: 'Libre Baskerville', serif;
        font-size: 0.95rem;
        color: #e5e0d5;
        margin-bottom: 6px;
    }

    .document-paper {
        background: #efe1c1;
        color: #2a2a2a;
        font-family: 'Libre Baskerville', serif;
        padding: 32px;
        margin-top: 20px;
        border-radius: 6px;
        border: 1px solid #c4b28a;
        box-shadow: inset 0 0 30px rgba(0,0,0,0.12),
                    0 10px 25px rgba(0,0,0,0.45);
        line-height: 1.8;
    }

    button {
        background-color: #1f2937 !important;
        color: #f9fafb !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        border: 1px solid #374151 !important;
    }

    button:hover {
        background-color: #374151 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================
# SESSION STATE
# =============================
if "screen" not in st.session_state:
    st.session_state.screen = "start"
if "room" not in st.session_state:
    st.session_state.room = 1
if "show_doc" not in st.session_state:
    st.session_state.show_doc = False

# =============================
# BACKGROUNDS
# =============================
BACKGROUND_IMAGES = {
    "start": "https://i.pinimg.com/736x/f4/83/52/f4835275a495dcb9c20041f58dcb025f.jpg",
    1: "https://i.pinimg.com/1200x/b4/ac/20/b4ac2040fdbd0eec08590c0d84403ff5.jpg",
    2: "https://i.pinimg.com/1200x/c7/50/01/c750012de3e58d9df7694d160992703f.jpg",
    3: "https://i.pinimg.com/1200x/8b/94/b3/8b94b35a628c2281f6ced5a35bddd0ce.jpg"
}

def set_background(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background(
    BACKGROUND_IMAGES["start"]
    if st.session_state.screen == "start"
    else BACKGROUND_IMAGES[st.session_state.room]
)

# =============================
# GAME DATA
# =============================
ROOM_TITLES = {
    1: "Room I – Reminiscence",
    2: "Room II – Note to Yourself",
    3: "Room III – Senses"
}

ROOM_STORIES = {
    1: [
        "You wake up in a quiet room.",
        "Your head feels heavy.",
        "Fragments of the past surround you.",
        "Something important is missing."
    ],
    2: [
        "Notes are left behind — written by you.",
        "Each one tells the same moment differently.",
        "You question your own perspective."
    ],
    3: [
        "Nothing external remains.",
        "Only sensation and feeling persist.",
        "Understanding finally settles in."
    ]
}

ROOM_PATHS = {
    1: "data/room1/documents.txt",
    2: "data/room2/documents.txt",
    3: "data/room3/documents.txt"
}

ROOM_INTENTS = {
    1: ["memory", "memory loss", "forget"],
    2: ["letters", "confusion", "not understanding"],
    3: ["emotion", "feelings", "fear"]
}

TRASH_WORDS = {
    "hi", "hello", "hey", "banana", "pen", "pencil",
    "chair", "table", "phone", "apple", "water", "name"
}

WEAK_WORDS = {
    "thinking", "thought", "confused", "idea", "wonder",
    "way", "path", "direction", "unlock", "unknown",
    "condition", "intention", "logic", "surrounding",
    "writing", "notebook", "paper"
}

# =============================
# HELPERS
# =============================
def matches_intent(query, room):
    return any(k in query for k in ROOM_INTENTS[room])

def is_trash(query):
    return query in TRASH_WORDS or len(query) < 3

def is_weak(query):
    return any(w in query for w in WEAK_WORDS)

@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()

ENDEE_BASE_URL = "http://localhost:8080/api/v1"
INDEX_NAME = "labyrinth"
VECTOR_DIM = 32

def project_to_32(vec):
    return vec[:VECTOR_DIM]

def endee_exists(query):
    endpoint = f"{ENDEE_BASE_URL}/index/{INDEX_NAME}/search"
    emb = model.encode(query)
    payload = {
        "vector": project_to_32(emb).tolist(),
        "k": 1,
        "include_vectors": False
    }
    r = requests.post(endpoint, json=payload)
    return r.status_code == 200

@st.cache_resource
def load_documents(path):
    with open(path, "r") as f:
        return [d.strip() for d in f.read().split("\n\n") if d.strip()]

# =============================
# START SCREEN
# =============================
if st.session_state.screen == "start":
    st.markdown('<div class="game-card">', unsafe_allow_html=True)
    st.markdown('<div class="game-title">LABYRINTH</div>', unsafe_allow_html=True)
    st.markdown('<p class="story-line" style="text-align:center;">A semantic escape room</p>', unsafe_allow_html=True)
    st.markdown('<p class="story-line" style="text-align:center;">You don’t escape by guessing. You escape by understanding.</p>', unsafe_allow_html=True)

    if st.button("🚪 Enter the Labyrinth"):
        st.session_state.screen = "room"
        st.session_state.room = 1
        st.session_state.show_doc = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# =============================
# ROOM SCREEN
# =============================
if st.session_state.screen == "room":
    st.markdown('<div class="game-card">', unsafe_allow_html=True)
    st.markdown(f"## {ROOM_TITLES[st.session_state.room]}")

    for line in ROOM_STORIES[st.session_state.room]:
        st.markdown(f'<div class="story-line">{line}</div>', unsafe_allow_html=True)

    documents = load_documents(ROOM_PATHS[st.session_state.room])

    if st.button("📜 Read Document"):
        st.session_state.show_doc = not st.session_state.show_doc

    if st.session_state.show_doc:
        html_doc = "<br><br>".join(documents)
        st.markdown(f'<div class="document-paper">{html_doc}</div>', unsafe_allow_html=True)

    user_input = st.text_input(
        "Guess the word to find the core meaning (look for important details):",
        key=f"user_input_{st.session_state.room}"
    )

    if user_input:
        query = user_input.lower().strip()

        # Endee is ALWAYS called
        _ = endee_exists(query)

        if is_trash(query):
            accuracy = 0
            message = "This word exists, but it is not related at all."

        elif is_weak(query):
            accuracy = 35
            message = "This word exists, but the connection is vague."

        elif matches_intent(query, st.session_state.room):
            accuracy = 75
            message = "You’ve understood what’s happening. Next room unlocked!"

        else:
            accuracy = 55
            message = "This word is related, but not the core meaning."

        st.markdown(f"### 🎯 Accuracy: {accuracy}%")

        if accuracy == 0:
            st.warning(message)
        elif accuracy < 55:
            st.info(message)
        elif accuracy < 75:
            st.info(message)
        else:
            st.success(message)

        if accuracy == 75 and st.session_state.room < 3:
            if st.button("➡ Continue"):
                st.session_state.room += 1
                st.session_state.show_doc = False
                st.rerun()

        if accuracy == 75 and st.session_state.room == 3:
            st.markdown("### The labyrinth no longer resists you.")
            st.markdown("You understand what held you here. The doors are open now.")

    st.markdown('</div>', unsafe_allow_html=True)
