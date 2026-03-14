from pathlib import Path
import re

import streamlit as st
from openai import OpenAI, RateLimitError, APIError


# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(
    page_title="NBA Elias Chatbot",
    page_icon="🏀",
    layout="centered",
)

st.title("🏀 NBA Elias Chatbot")
st.caption("Ask questions based only on the daily Elias master text file.")


# -----------------------------
# CONFIG
# -----------------------------
DATA_FILE = Path("data/nba_elias_gamehigh_master.txt")

SYSTEM_PROMPT = """
You are an NBA Elias research assistant.

Use ONLY the file excerpt provided in the prompt.
Do not use outside basketball knowledge.
Do not guess.

Before answering, determine whether the question refers to:
- player vs team
- high vs low
- season vs career vs all-time
- with this team only vs games with all teams
- team totals vs opponent totals

Rules:
- If the answer is not clearly in the excerpt, say: Not found in file excerpt.
- If the question says "season high," assume current season only unless specified otherwise.
- Keep answers concise and research-friendly.
- Prefer exact wording from the file.

Return answers in this format:

Answer:
Section:
Match:
"""


# -----------------------------
# HELPERS
# -----------------------------
def load_api_key() -> str | None:
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


def load_file_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="ignore")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def query_terms(query: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9\.\-']+", query.lower())
    stopwords = {
        "what", "is", "the", "a", "an", "of", "in", "for", "to", "and", "show",
        "me", "with", "this", "that", "his", "her", "their", "season", "career",
        "high", "low", "team", "only", "all", "games", "game", "current"
    }
    cleaned = [w for w in words if len(w) > 2 and w not in stopwords]
    return cleaned


def score_line(line: str, terms: list[str]) -> int:
    line_norm = normalize_text(line)
    return sum(1 for term in terms if term in line_norm)


def find_relevant_excerpt(text: str, query: str, max_chars: int = 12000) -> str:
    """
    Finds the most relevant area of the file by scoring lines against query terms,
    then returns a nearby excerpt instead of the entire file.
    """
    lines = text.splitlines()
    terms = query_terms(query)

    if not terms:
        return text[:max_chars]

    scored = []
    for i, line in enumerate(lines):
        score = score_line(line, terms)
        if score > 0:
            scored.append((score, i))

    # No obvious match: return top slice of file
    if not scored:
        return text[:max_chars]

    # Best matching line
    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    best_index = scored[0][1]

    # Pull surrounding context
    start = max(0, best_index - 60)
    end = min(len(lines), best_index + 120)
    excerpt = "\n".join(lines[start:end])

    # If still too large, trim
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars]

    return excerpt


def build_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def ask_openai(client: OpenAI, excerpt: str, question: str) -> str:
    response = client.responses.create(
        model="gpt-5.4",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is the relevant excerpt from the NBA Elias master file:\n\n"
                    f"{excerpt}\n\n"
                    f"Question: {question}"
                ),
            },
        ],
    )
    return response.output_text


# -----------------------------
# APP STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_excerpt" not in st.session_state:
    st.session_state.last_excerpt = ""


# -----------------------------
# VALIDATION
# -----------------------------
api_key = load_api_key()
if not api_key:
    st.error("Missing OPENAI_API_KEY in Streamlit secrets.")
    st.info('Add this in Streamlit secrets: OPENAI_API_KEY="your_api_key_here"')
    st.stop()

file_text = load_file_text(DATA_FILE)
if not file_text:
    st.error("Data file missing or empty.")
    st.info("Expected file path: data/nba_elias_gamehigh_master.txt")
    st.stop()

client = build_client(api_key)


# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.subheader("File status")
    st.write(f"Path: `{DATA_FILE}`")
    st.write(f"Characters: {len(file_text):,}")

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.last_excerpt = ""
        st.rerun()

    if st.session_state.last_excerpt:
        with st.expander("Last excerpt sent to model"):
            st.text(st.session_state.last_excerpt[:8000])


# -----------------------------
# CHAT HISTORY
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------
# CHAT INPUT
# -----------------------------
prompt = st.chat_input("Ask about the Elias stats")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            excerpt = find_relevant_excerpt(file_text, prompt)
            st.session_state.last_excerpt = excerpt

            with st.spinner("Searching file..."):
                answer = ask_openai(client, excerpt, prompt)

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except RateLimitError:
            error_msg = (
                "OpenAI rate limit reached.\n\n"
                "This usually means your API billing, quota, or rate limits need attention. "
                "Try again later, reduce usage, or check your OpenAI billing and limits settings."
            )
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

        except APIError:
            error_msg = (
                "OpenAI API error.\n\n"
                "Please try again in a moment. If it keeps happening, check your API key, billing, and model access."
            )
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
