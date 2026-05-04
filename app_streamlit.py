import streamlit as st

st.set_page_config(
    page_title="PROMIX PDF Reader",
    page_icon="📊",
    layout="wide",
)

home_page = st.Page(
    "halaman_utama.py",
    title="PROMIX PDF Reader",
    icon="📊",
    url_path="",
    default=True,
)

tutorial_page = st.Page(
    "tutorial.py",
    title="Tutorial Penggunaan",
    icon="📘",
    url_path="tutorial",
)

page = st.navigation([home_page, tutorial_page])
page.run()