from pathlib import Path
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="NBA Elias Chatbot", page_icon="🏀")

st.title("NBA Elias Chatbot")
st.caption("Ask questions based on the daily Elias stat file")

DATA_FILE = Path("data/nba_elias_gamehigh_master.txt")

SYSTEM_PROMPT = """
You are an NBA Elias research assistant.

Use ONLY the text file provided.

Do not guess.
Do not use outside knowledge.

If the answer is not in the file say:
Not found in file.

Return results like this:

Answer:
Section:
Match:
"""

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

if not DATA_FILE.exists():
    st.error("Data file missing.")
    st.stop()

file_text = DATA_FILE.read_text()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Ask about the Elias stats")

if prompt:

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    response = client.responses.create(
        model="gpt-5.4",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{file_text}\n\nQuestion: {prompt}"
            }
        ]
    )

    answer = response.output_text

    with st.chat_message("assistant"):
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
