"""Streamlit-based micro-app entrypoint.

This lightweight app preserves the original repository architecture but removes
any Weather-specific logic. It demonstrates how to gather minimal inputs from
an end user (optional API base URL and API key) and calls api_client.fetch_data()
as an integration point. The UI is rendered via ui.render_home().

Run locally:
  pip install -r requirements.txt
  streamlit run app.py
"""

import streamlit as st
from config import settings
import api_client
import ui

st.set_page_config(page_title="Micro-app", layout="centered")

st.header("Micro-app Template")
st.write("A lightweight template for building small API-driven micro-apps using Streamlit.")

# allow overriding API base and API key for quick testing; they default to config values
api_base = st.text_input("API base URL", value=settings.API_BASE_URL or "")
api_key = st.text_input("API key (optional)", value="", type="password")

params_input = st.text_area("Parameters (JSON)", value='{}', help="Optional JSON to pass to fetch_data as params")

if st.button("Fetch data"):
    # parse params safely
    import json

    try:
        params = json.loads(params_input or "{}")
    except Exception as exc:
        st.error(f"Could not parse parameters as JSON: {exc}")
        params = {}

    # Temporary override of settings for this run (non-persistent)
    if api_base:
        settings.API_BASE_URL = api_base
    if api_key:
        # pass explicit api_key to fetch_data (preferred) and do not modify global settings
        data = api_client.fetch_data(params=params, api_key=api_key)
    else:
        data = api_client.fetch_data(params=params)

    ui.render_home(data)
else:
    st.info("Enter an API base URL or use the default configured in config/settings.py, provide any parameters, then click Fetch data.")
