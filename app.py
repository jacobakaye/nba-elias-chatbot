from pathlib import Path
import re
import streamlit as st

st.set_page_config(page_title="NBA Elias Lookup", page_icon="🏀")

st.title("🏀 NBA Elias Lookup")
st.caption("Search player and team highs/lows from the daily NBA Elias master text file.")

DATA_FILE = Path("data/nba_elias_gamehigh_master.txt")

if not DATA_FILE.exists():
    st.error("Missing data/nba_elias_gamehigh_master.txt")
    st.stop()

text = DATA_FILE.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()

if "messages" not in st.session_state:
    st.session_state.messages = []

STAT_PREFIXES = [
    "Minutes",
    "Field Goals",
    "Field Goal Attempts",
    "Three-Point Field Goals",
    "Three-Point Attempts",
    "Free Throws",
    "Free Throw Attempts",
    "Offensive Rebounds",
    "Defensive Rebounds",
    "Rebounds",
    "Assists",
    "Steals",
    "Turnovers",
    "Blocked Shots",
    "Points",
]

STOPWORDS = {
    "what", "whats", "what's", "is", "the", "a", "an", "of", "in", "for", "to",
    "and", "show", "me", "with", "this", "that", "his", "her", "their", "please",
    "find", "tell", "give", "current", "regular", "single", "game", "whats",
    "whatre", "what's", "career", "season", "all", "time", "high", "highs",
    "low", "lows", "only", "teams"
}


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9\s\-/\.\']", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def is_stat_line(line: str) -> bool:
    stripped = line.strip()
    return any(stripped.startswith(prefix) for prefix in STAT_PREFIXES)


def is_header_line(line: str) -> bool:
    stripped = line.strip()
    if " / " not in stripped:
        return False
    if is_stat_line(stripped):
        return False
    return True


def extract_sections(lines_):
    sections = []
    i = 0
    while i < len(lines_):
        line = lines_[i].strip()
        if is_header_line(line):
            header = line
            section_lines = []
            j = i + 1
            while j < len(lines_):
                next_line = lines_[j].rstrip()
                if not next_line.strip():
                    break
                if is_header_line(next_line.strip()):
                    break
                section_lines.append(next_line)
                j += 1
            sections.append({
                "header": header,
                "lines": section_lines
            })
            i = j
        else:
            i += 1
    return sections


SECTIONS = extract_sections(lines)


def extract_stat_from_query(query: str):
    q = normalize(query)

    stat_aliases = {
        "points": "Points",
        "point": "Points",
        "pts": "Points",
        "pt": "Points",

        "rebounds": "Rebounds",
        "rebound": "Rebounds",
        "reb": "Rebounds",

        "assists": "Assists",
        "assist": "Assists",
        "ast": "Assists",

        "steals": "Steals",
        "stl": "Steals",

        "blocks": "Blocked Shots",
        "block": "Blocked Shots",
        "blk": "Blocked Shots",

        "turnovers": "Turnovers",
        "turnover": "Turnovers",
        "tov": "Turnovers",

        "minutes": "Minutes",
        "mins": "Minutes",
        "min": "Minutes",

        "field goals": "Field Goals",
        "fg": "Field Goals",

        "field goal attempts": "Field Goal Attempts",
        "fga": "Field Goal Attempts",

        "three point field goals": "Three-Point Field Goals",
        "three-point field goals": "Three-Point Field Goals",
        "three pointers": "Three-Point Field Goals",
        "three-pointers": "Three-Point Field Goals",
        "3pm": "Three-Point Field Goals",
        "3ptm": "Three-Point Field Goals",
        "3pt": "Three-Point Field Goals",
        "3pts": "Three-Point Field Goals",
        "threes": "Three-Point Field Goals",

        "three point attempts": "Three-Point Attempts",
        "three-point attempts": "Three-Point Attempts",
        "3pa": "Three-Point Attempts",
        "3pta": "Three-Point Attempts",

        "free throws": "Free Throws",
        "ft": "Free Throws",

        "free throw attempts": "Free Throw Attempts",
        "fta": "Free Throw Attempts",

        "offensive rebounds": "Offensive Rebounds",
        "oreb": "Offensive Rebounds",

        "defensive rebounds": "Defensive Rebounds",
        "dreb": "Defensive Rebounds",
    }

    for k in sorted(stat_aliases.keys(), key=len, reverse=True):
        if k in q:
            return stat_aliases[k]

    return None


def classify_query(query: str):
    q = normalize(query)

    return {
        "career": "career" in q,
        "season": ("season" in q) or ("this season" in q) or ("current season" in q),
        "all_time": ("all time" in q) or ("all-time" in q),
        "low": (" low" in f" {q}") or ("lows" in q),
        "high": (" high" in f" {q}") or ("highs" in q) or ("career high" in q) or ("season high" in q),
        "with_this_team_only": "with this team only" in q,
        "games_with_all_teams": "games with all teams" in q,
        "team_totals": "team totals" in q,
        "opponent_totals": "opponent totals" in q or "opponent" in q,
    }


def query_terms(query: str):
    words = re.findall(r"[a-zA-Z0-9\.\-']+", normalize(query))
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


def detect_name_phrase(query: str):
    q = normalize(query)

    q = re.sub(r"\bwhat's\b", " ", q)
    q = re.sub(r"\bwhats\b", " ", q)
    q = re.sub(r"\bwhat is\b", " ", q)
    q = re.sub(r"\bshow me\b", " ", q)
    q = re.sub(r"\bgive me\b", " ", q)
    q = re.sub(r"\btell me\b", " ", q)

    remove_phrases = [
        "career regular season single-game highs",
        "career regular season single-game lows",
        "regular season single-game highs",
        "regular season single-game lows",
        "all-time regular season single-game highs",
        "all-time regular season single-game lows",
        "games with all teams",
        "with this team only",
        "team totals",
        "opponent totals",
        "career high",
        "career lows",
        "career low",
        "season high",
        "season lows",
        "season low",
        "all time high",
        "all time low",
        "all-time high",
        "all-time low",
        "highs",
        "high",
        "lows",
        "low",
        "points",
        "point",
        "pts",
        "pt",
        "rebounds",
        "rebound",
        "reb",
        "assists",
        "assist",
        "ast",
        "steals",
        "stl",
        "turnovers",
        "turnover",
        "tov",
        "blocks",
        "block",
        "blk",
        "blocked shots",
        "minutes",
        "mins",
        "min",
        "field goals",
        "fg",
        "field goal attempts",
        "fga",
        "three point field goals",
        "three-point field goals",
        "three pointers",
        "three-pointers",
        "3pm",
        "3ptm",
        "3pt",
        "3pts",
        "threes",
        "three point attempts",
        "three-point attempts",
        "3pa",
        "3pta",
        "free throws",
        "ft",
        "free throw attempts",
        "fta",
        "offensive rebounds",
        "oreb",
        "defensive rebounds",
        "dreb",
    ]

    for phrase in sorted(remove_phrases, key=len, reverse=True):
        q = q.replace(phrase, " ")

    q = re.sub(r"\s+", " ", q).strip()

    if not q:
        return None

    return q


def score_section(section, query):
    header = section["header"]
    header_norm = normalize(header)
    score = 0

    flags = classify_query(query)
    stat_name = extract_stat_from_query(query)
    name_phrase = detect_name_phrase(query)
    terms = query_terms(query)

    header_name = header_norm.split(" / ")[0] if " / " in header_norm else header_norm

    if name_phrase:
        if name_phrase == header_name:
            score += 120
        elif name_phrase in header_name:
            score += 70
        elif name_phrase in header_norm:
            score += 50

        for token in name_phrase.split():
            if token in header_name:
                score += 12

    for term in terms:
        if term in header_norm:
            score += 3

    if flags["career"] and "career" in header_norm:
        score += 20
    if flags["season"] and "career" not in header_norm and "all-time" not in header_norm:
        score += 20
    if flags["all_time"] and "all-time" in header_norm:
        score += 20
    if flags["low"] and "lows" in header_norm:
        score += 15
    if flags["high"] and "highs" in header_norm:
        score += 15
    if flags["with_this_team_only"] and "with this team only" in header_norm:
        score += 15
    if flags["games_with_all_teams"] and "games with all teams" in header_norm:
        score += 15
    if flags["team_totals"] and header_norm.startswith("team totals"):
        score += 25
    if flags["opponent_totals"] and header_norm.startswith("opponent totals"):
        score += 25

    if name_phrase and name_phrase not in header_name:
        if any(tok in header_name for tok in name_phrase.split()):
            score -= 10

    if stat_name:
        for line in section["lines"]:
            if normalize(line).startswith(normalize(stat_name)):
                score += 10
                break

    return score


def best_stat_line(section_lines, stat_name):
    if stat_name:
        for line in section_lines:
            if normalize(line).startswith(normalize(stat_name)):
                return line

    for preferred in ["Points", "Rebounds", "Assists"]:
        for line in section_lines:
            if normalize(line).startswith(normalize(preferred)):
                return line

    return section_lines[0] if section_lines else None


def format_answer(section, stat_line):
    if stat_line:
        return f"**Section:** {section['header']}\n\n**Line:** {stat_line}"
    return f"**Section:** {section['header']}\n\nNo stat line found."


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


prompt = st.chat_input("Ask about the Elias stats")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    stat_name = extract_stat_from_query(prompt)

    scored = []
    for section in SECTIONS:
        score = score_section(section, prompt)
        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: x[0], reverse=True)

    with st.chat_message("assistant"):
        if not scored:
            answer = "Not found in file."
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            top_score = scored[0][0]
            top_sections = [sec for score, sec in scored if score >= max(top_score - 10, 1)][:5]

            blocks = []
            for i, section in enumerate(top_sections, start=1):
                stat_line = best_stat_line(section["lines"], stat_name)
                block = f"### Match {i}\n\n{format_answer(section, stat_line)}"
                blocks.append(block)

            answer = "\n\n---\n\n".join(blocks)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
