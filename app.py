from pathlib import Path
import re
import streamlit as st

st.set_page_config(page_title="NBA Elias Chatbot", page_icon="🏀")

st.title("🏀 NBA Elias Lookup")
st.caption("Free version: searches the daily Elias master text file with no API costs.")

DATA_FILE = Path("data/nba_elias_gamehigh_master.txt")

if not DATA_FILE.exists():
    st.error("Missing data/nba_elias_gamehigh_master.txt")
    st.stop()

text = DATA_FILE.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()

if "messages" not in st.session_state:
    st.session_state.messages = []


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def extract_query_terms(query: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9\.\-']+", query.lower())
    stop = {
        "what", "is", "the", "a", "an", "of", "in", "for", "to", "and", "show", "me",
        "with", "this", "that", "his", "her", "their", "please", "find"
    }
    return [w for w in words if len(w) > 2 and w not in stop]


def line_score(line: str, terms: list[str]) -> int:
    ln = normalize(line)
    return sum(1 for t in terms if t in ln)


def find_headers_and_matches(query: str, max_results: int = 5):
    terms = extract_query_terms(query)

    headers = []
    for i, line in enumerate(lines):
        if " / " in line and not re.match(r"^\s*(Minutes|Field Goals|Field Goal Attempts|Three-Point|Free Throws|Offensive Rebounds|Defensive Rebounds|Rebounds|Assists|Steals|Turnovers|Blocked Shots|Points)", line):
            score = line_score(line, terms)
            if score > 0:
                headers.append((score, i, line))

    headers.sort(key=lambda x: x[0], reverse=True)

    results = []
    used = set()

    for _, idx, header in headers:
        if header in used:
            continue
        used.add(header)

        section_lines = [header]
        j = idx + 1
        while j < len(lines):
            next_line = lines[j]
            if not next_line.strip():
                break
            if " / " in next_line and not next_line.startswith(" "):
                break
            section_lines.append(next_line)
            j += 1

        section_text = "\n".join(section_lines)
        section_score = line_score(section_text, terms)

        results.append((section_score, header, section_lines))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:max_results]


def extract_stat_from_query(query: str):
    q = query.lower()

    stat_aliases = {
        "points": "Points",
        "rebounds": "Rebounds",
        "assists": "Assists",
        "steals": "Steals",
        "blocks": "Blocked Shots",
        "blocked shots": "Blocked Shots",
        "turnovers": "Turnovers",
        "minutes": "Minutes",
        "field goals": "Field Goals",
        "field goal attempts": "Field Goal Attempts",
        "three-point field goals": "Three-Point Field Goals",
        "three point field goals": "Three-Point Field Goals",
        "three-pointers": "Three-Point Field Goals",
        "threes": "Three-Point Field Goals",
        "three-point attempts": "Three-Point Attempts",
        "free throws": "Free Throws",
        "free throw attempts": "Free Throw Attempts",
    }

    for k, v in stat_aliases.items():
        if k in q:
            return v
    return None


def find_best_stat_line(section_lines, stat_name):
    if not stat_name:
        return None
    for line in section_lines[1:]:
        if normalize(line).startswith(normalize(stat_name)):
            return line
    return None


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask about the Elias stats")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    matches = find_headers_and_matches(prompt)
    stat_name = extract_stat_from_query(prompt)

    with st.chat_message("assistant"):
        if not matches:
            answer = "Not found in file."
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            output_parts = []

            for i, (_, header, section_lines) in enumerate(matches, start=1):
                stat_line = find_best_stat_line(section_lines, stat_name)

                block = [f"**Match {i}**", f"**Section:** {header}"]
                if stat_line:
                    block.append(f"**Line:** {stat_line}")
                else:
                    block.append("**Relevant lines:**")
                    for ln in section_lines[1:6]:
                        block.append(f"- {ln}")

                output_parts.append("\n".join(block))

            answer = "\n\n---\n\n".join(output_parts)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
