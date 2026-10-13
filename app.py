"""Streamlit entry point for the Pixel Post Studio."""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from ui import render_app


load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(
    page_title="Pixel Post Studio",
    page_icon="🟪",
    layout="wide",
)

render_app()
