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
    "find", "tell", "give", "current", "regular", "single", "game", "season",
    "career", "all", "time", "high", "highs", "low", "lows", "only", "teams"
}

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


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9\s\-/\.\']", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def singularize_token(token: str) -> str:
    token = token.strip()
    if token.endswith("'s"):
        token = token[:-2]
    elif token.endswith("s") and len(token) > 3:
        token = token[:-1]
    return token


def normalize_for_match(s: str) -> str:
    s = normalize(s)
    tokens = [singularize_token(tok) for tok in s.split()]
    return " ".join(tokens)


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

ENTITY_NAMES = []
for section in SECTIONS:
    header_name = section["header"].split(" / ")[0].strip()
    parts = section["header"].split(" / ")
    if len(parts) >= 2 and header_name in {"Team Totals", "Opponent Totals"}:
        ENTITY_NAMES.append(parts[1].strip())
    else:
        ENTITY_NAMES.append(header_name)

ENTITY_NAMES.extend(TEAM_CANONICALS)
ENTITY_NAMES = sorted(set(ENTITY_NAMES), key=len, reverse=True)


def extract_stat_from_query(query: str):
    q = normalize_for_match(query)

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
    q = normalize_for_match(query)
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
    words = re.findall(r"[a-zA-Z0-9\.\-']+", normalize_for_match(query))
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


def detect_entity_name(query: str):
    q = normalize_for_match(query)

    for alias, canonical in TEAM_ALIASES.items():
        if normalize_for_match(alias) in q:
            return canonical

    for entity in ENTITY_NAMES:
        entity_norm = normalize_for_match(entity)
        if entity_norm in q:
            return entity

    cleaned = q
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
        "career low",
        "season high",
        "season low",
        "all time high",
        "all time low",
        "all-time high",
        "all-time low",
        "points", "point", "pts", "pt",
        "rebounds", "rebound", "reb",
        "assists", "assist", "ast",
        "steals", "stl",
        "turnovers", "turnover", "tov",
        "blocks", "block", "blk", "blocked shots",
        "minutes", "mins", "min",
        "field goals", "fg",
        "field goal attempts", "fga",
        "three point field goals", "three-point field goals",
        "three pointers", "three-pointers", "3pm", "3ptm", "3pt", "3pts", "threes",
        "three point attempts", "three-point attempts", "3pa", "3pta",
        "free throws", "ft",
        "free throw attempts", "fta",
        "offensive rebounds", "oreb",
        "defensive rebounds", "dreb",
        "what's", "whats", "what is", "show me", "give me", "tell me",
        "highs", "high", "lows", "low", "season", "career",
    ]
    for phrase in sorted(remove_phrases, key=len, reverse=True):
        cleaned = cleaned.replace(phrase, " ")

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None

    cleaned_tokens = cleaned.split()
    best_entity = None
    best_score = 0
    for entity in ENTITY_NAMES:
        entity_norm = normalize_for_match(entity)
        entity_tokens = set(entity_norm.split())
        score = sum(1 for tok in cleaned_tokens if tok in entity_tokens)
        if score > best_score:
            best_score = score
            best_entity = entity

    if best_score >= 2:
        return best_entity

    return None


def infer_query_scope(query: str, entity_name: str | None):
    q = normalize_for_match(query)

    if "team totals" in q:
        return "team"
    if "opponent totals" in q or "opponent" in q:
        return "opponent"

    if entity_name and entity_name in TEAM_CANONICALS:
        return "team"

    return "player"


def score_section(section, query):
    header = section["header"]
    header_norm = normalize_for_match(header)
    parts = section["header"].split(" / ")
    first_part = parts[0].strip()
    second_part = parts[1].strip() if len(parts) > 1 else ""

    score = 0
    flags = classify_query(query)
    stat_name = extract_stat_from_query(query)
    entity_name = detect_entity_name(query)
    query_scope = infer_query_scope(query, entity_name)

    header_name = normalize_for_match(first_part)
    team_name = normalize_for_match(second_part)

    is_team_totals_section = first_part == "Team Totals"
    is_opponent_totals_section = first_part == "Opponent Totals"
    is_player_section = not is_team_totals_section and not is_opponent_totals_section

    if entity_name:
        entity_norm = normalize_for_match(entity_name)

        if is_team_totals_section or is_opponent_totals_section:
            if entity_norm == team_name:
                score += 220
            elif entity_norm in team_name:
                score += 140
        else:
            if entity_norm == header_name:
                score += 200
            elif entity_norm in header_name:
                score += 120
            elif entity_norm in header_norm:
                score += 80

            entity_tokens = entity_norm.split()
            overlap = sum(1 for tok in entity_tokens if tok in header_name)
            score += overlap * 15
            if overlap > 0 and entity_norm not in header_name:
                score -= 40

    terms = query_terms(query)
    for term in terms:
        if term in header_norm:
            score += 2

    if flags["career"] and "career" in header_norm:
        score += 20
    if flags["season"] and "career" not in header_norm and "all-time" not in header_norm:
        score += 20
    if flags["all_time"] and "all-time" in header_norm:
        score += 20

    if flags["low"]:
        if "lows" in header_norm:
            score += 40
        if "highs" in header_norm:
            score -= 40

    if flags["high"]:
        if "highs" in header_norm:
            score += 40
        if "lows" in header_norm:
            score -= 40

    if flags["with_this_team_only"] and "with this team only" in header_norm:
        score += 15
    if flags["games_with_all_teams"] and "games with all teams" in header_norm:
        score += 15

    if is_team_totals_section:
        score += 25
    if is_opponent_totals_section:
        score += 10

    if query_scope == "team":
        if is_team_totals_section:
            score += 120
        if is_player_section:
            score -= 120
        if is_opponent_totals_section and not flags["opponent_totals"]:
            score -= 50

    if query_scope == "opponent":
        if is_opponent_totals_section:
            score += 120
        if is_team_totals_section:
            score -= 40
        if is_player_section:
            score -= 120

    if query_scope == "player":
        if is_player_section:
            score += 30
        if is_team_totals_section or is_opponent_totals_section:
            score -= 80

    if flags["team_totals"] and is_team_totals_section:
        score += 50
    if flags["opponent_totals"] and is_opponent_totals_section:
        score += 50

    if stat_name:
        for line in section["lines"]:
            if normalize_for_match(line).startswith(normalize_for_match(stat_name)):
                score += 10
                break

    return score


def best_stat_line(section_lines, stat_name):
    if stat_name:
        for line in section_lines:
            if normalize_for_match(line).startswith(normalize_for_match(stat_name)):
                return line

    for preferred in ["Points", "Rebounds", "Assists"]:
        for line in section_lines:
            if normalize_for_match(line).startswith(normalize_for_match(preferred)):
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
            second_score = scored[1][0] if len(scored) > 1 else None

            if second_score is None or (top_score - second_score >= 35):
                best_section = scored[0][1]
                stat_line = best_stat_line(best_section["lines"], stat_name)
                answer = format_answer(best_section, stat_line)
            else:
                top_sections = [sec for score, sec in scored if score >= max(top_score - 15, 1)][:5]

                blocks = []
                for i, section in enumerate(top_sections, start=1):
                    stat_line = best_stat_line(section["lines"], stat_name)
                    block = f"### Match {i}\n\n{format_answer(section, stat_line)}"
                    blocks.append(block)

                answer = "\n\n---\n\n".join(blocks)

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
