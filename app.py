"""Streamlit entry point for the Pixel Post Studio."""

import streamlit as st

from ui import render_app


st.set_page_config(
    page_title="Pixel Post Studio",
    page_icon="🟪",
    layout="wide",
)

render_app()
