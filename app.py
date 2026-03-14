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

TEAM_ALIASES = {
    "hawks": "Atlanta Hawks",
    "celtics": "Boston Celtics",
    "nets": "Brooklyn Nets",
    "hornets": "Charlotte Hornets",
    "bulls": "Chicago Bulls",
    "cavs": "Cleveland Cavaliers",
    "cavaliers": "Cleveland Cavaliers",
    "mavs": "Dallas Mavericks",
    "mavericks": "Dallas Mavericks",
    "nuggets": "Denver Nuggets",
    "pistons": "Detroit Pistons",
    "warriors": "Golden State Warriors",
    "rockets": "Houston Rockets",
    "pacers": "Indiana Pacers",
    "clippers": "L.A. Clippers",
    "lakers": "L.A. Lakers",
    "grizzlies": "Memphis Grizzlies",
    "heat": "Miami Heat",
    "bucks": "Milwaukee Bucks",
    "timberwolves": "Minnesota Timberwolves",
    "wolves": "Minnesota Timberwolves",
    "pelicans": "New Orleans Pelicans",
    "knicks": "New York Knickerbockers",
    "thunder": "Oklahoma City Thunder",
    "magic": "Orlando Magic",
    "sixers": "Philadelphia 76ers",
    "76ers": "Philadelphia 76ers",
    "suns": "Phoenix Suns",
    "blazers": "Portland Trail Blazers",
    "trail blazers": "Portland Trail Blazers",
    "kings": "Sacramento Kings",
    "spurs": "San Antonio Spurs",
    "raptors": "Toronto Raptors",
    "jazz": "Utah Jazz",
    "wizards": "Washington Wizards",
}

TEAM_CANONICALS = set(TEAM_ALIASES.values())


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9\s\-/\.\']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_name(text: str) -> str:
    """
    Name-friendly normalization:
    - lowercases
    - removes punctuation noise
    - converts possessive brunson's -> brunson
    - converts brunsons -> brunson only for query-style names
    """
    text = normalize(text)
    text = re.sub(r"\b([a-z]+)'s\b", r"\1", text)
    text = re.sub(r"\b([a-z]{4,})s\b", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_stat_line(line: str) -> bool:
    stripped = line.strip()
    return any(stripped.startswith(prefix) for prefix in STAT_PREFIXES)


def is_header_line(line: str) -> bool:
    stripped = line.strip()
    return " / " in stripped and not is_stat_line(stripped)


def extract_sections(all_lines):
    sections = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i].strip()
        if is_header_line(line):
            header = line
            section_lines = []
            j = i + 1
            while j < len(all_lines):
                nxt = all_lines[j].rstrip()
                if not nxt.strip():
                    break
                if is_header_line(nxt.strip()):
                    break
                section_lines.append(nxt)
                j += 1
            sections.append({"header": header, "lines": section_lines})
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

    for key in sorted(stat_aliases.keys(), key=len, reverse=True):
        if key in q:
            return stat_aliases[key]

    return None


def classify_query(query: str):
    q = normalize(query)
    return {
        "career": "career" in q,
        "season": ("season" in q) or ("this season" in q) or ("current season" in q),
        "all_time": ("all time" in q) or ("all-time" in q),
        "high": (" high" in f" {q}") or ("highs" in q) or ("career high" in q) or ("season high" in q),
        "low": (" low" in f" {q}") or ("lows" in q) or ("career low" in q) or ("season low" in q),
        "with_this_team_only": "with this team only" in q,
        "games_with_all_teams": "games with all teams" in q,
        "team_totals": "team totals" in q,
        "opponent_totals": "opponent totals" in q or "opponent" in q,
    }


def detect_entity_name(query: str):
    q_norm = normalize(query)
    q_name = normalize_name(query)

    for alias, canonical in TEAM_ALIASES.items():
        if normalize(alias) in q_norm:
            return canonical

    candidates = []

    for section in SECTIONS:
        parts = section["header"].split(" / ")
        first = parts[0].strip()
        second = parts[1].strip() if len(parts) > 1 else ""

        if first in {"Team Totals", "Opponent Totals"}:
            entity = second
        else:
            entity = first

        candidates.append(entity)

    candidates.extend(list(TEAM_CANONICALS))
    candidates = sorted(set(candidates), key=len, reverse=True)

    for candidate in candidates:
        if normalize_name(candidate) in q_name:
            return candidate

    # fallback token overlap
    q_tokens = set(q_name.split())
    best_candidate = None
    best_score = 0

    for candidate in candidates:
        c_tokens = set(normalize_name(candidate).split())
        score = len(q_tokens & c_tokens)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    if best_score >= 2:
        return best_candidate

    return None


def infer_query_scope(query: str, entity_name: str | None):
    q = normalize(query)

    if "opponent totals" in q or "opponent" in q:
        return "opponent"

    if "team totals" in q:
        return "team"

    if entity_name and entity_name in TEAM_CANONICALS:
        return "team"

    return "player"


def header_matches_high_low(header: str, flags: dict) -> bool:
    h = normalize(header)

    if flags["high"] and not flags["low"]:
        return "highs" in h

    if flags["low"] and not flags["high"]:
        return "lows" in h

    return True


def header_matches_time_scope(header: str, flags: dict) -> bool:
    h = normalize(header)

    if flags["career"]:
        return "career" in h

    if flags["all_time"]:
        return "all-time" in h

    if flags["season"]:
        return ("career" not in h) and ("all-time" not in h)

    return True


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
    return f"**Section:** {section['header']}\n\n**Line:** {stat_line}"


def score_section(section, query):
    header = section["header"]
    header_norm = normalize(header)
    parts = header.split(" / ")
    first = parts[0].strip()
    second = parts[1].strip() if len(parts) > 1 else ""

    flags = classify_query(query)
    stat_name = extract_stat_from_query(query)
    entity_name = detect_entity_name(query)
    query_scope = infer_query_scope(query, entity_name)

    if not header_matches_high_low(header, flags):
        return None

    if not header_matches_time_scope(header, flags):
        return None

    is_team_totals = first == "Team Totals"
    is_opponent_totals = first == "Opponent Totals"
    is_player = not is_team_totals and not is_opponent_totals

    score = 0

    if entity_name:
        entity_norm = normalize_name(entity_name)

        if is_team_totals or is_opponent_totals:
            if normalize_name(second) == entity_norm:
                score += 300
            elif entity_norm in normalize_name(second):
                score += 180
        else:
            player_name_norm = normalize_name(first)
            if player_name_norm == entity_norm:
                score += 320
            elif entity_norm in player_name_norm:
                score += 200
            else:
                overlap = len(set(entity_norm.split()) & set(player_name_norm.split()))
                score += overlap * 20
                if overlap > 0:
                    score -= 40

    if flags["career"] and "career" in header_norm:
        score += 60
    if flags["all_time"] and "all-time" in header_norm:
        score += 60
    if flags["season"] and "career" not in header_norm and "all-time" not in header_norm:
        score += 60

    if flags["high"] and "highs" in header_norm:
        score += 80
    if flags["low"] and "lows" in header_norm:
        score += 80

    if flags["with_this_team_only"] and "with this team only" in header_norm:
        score += 40
    if flags["games_with_all_teams"] and "games with all teams" in header_norm:
        score += 40

    if query_scope == "team":
        if is_team_totals:
            score += 140
        if is_player:
            score -= 180
        if is_opponent_totals and not flags["opponent_totals"]:
            score -= 80

    if query_scope == "opponent":
        if is_opponent_totals:
            score += 140
        if is_team_totals:
            score -= 80
        if is_player:
            score -= 180

    if query_scope == "player":
        if is_player:
            score += 60
        if is_team_totals or is_opponent_totals:
            score -= 120

    if flags["team_totals"] and is_team_totals:
        score += 80
    if flags["opponent_totals"] and is_opponent_totals:
        score += 80

    if stat_name:
        matched_stat = False
        for line in section["lines"]:
            if normalize(line).startswith(normalize(stat_name)):
                matched_stat = True
                break
        if matched_stat:
            score += 25

    return score


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
        if score is not None and score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: x[0], reverse=True)

    with st.chat_message("assistant"):
        if not scored:
            answer = "Not found in file."
        else:
            top_score = scored[0][0]
            second_score = scored[1][0] if len(scored) > 1 else None

            if second_score is None or (top_score - second_score >= 60):
                best_section = scored[0][1]
                stat_line = best_stat_line(best_section["lines"], stat_name)
                answer = format_answer(best_section, stat_line)
            else:
                top_sections = [sec for score, sec in scored if score >= max(top_score - 20, 1)][:5]
                blocks = []
                for i, section in enumerate(top_sections, start=1):
                    stat_line = best_stat_line(section["lines"], stat_name)
                    blocks.append(f"### Match {i}\n\n{format_answer(section, stat_line)}")
                answer = "\n\n---\n\n".join(blocks)

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
