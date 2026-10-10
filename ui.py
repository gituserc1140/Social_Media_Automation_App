"""UI layout module for Streamlit.

This keeps UI code separate from the API client and the main app control flow.
It uses Streamlit primitives to render a simple, easy-to-adapt layout.
"""

import streamlit as st
from typing import Dict, Any


def render_home(data: Dict[str, Any]):
    """Render the main page given a simple data dictionary.

    Expected shape (example):
      {
        "title": str,
        "description": str,
        "items": [{"id":..., "name":..., "value":...}, ...]
      }

    Adapt the rendering to your needs or replace entirely with custom
    components or a separate front-end.
    """
    title = data.get("title", "Micro-app")
    description = data.get("description", "")
    items = data.get("items", [])

    st.subheader(title)
    if description:
        st.write(description)

    if not items:
        st.info("No items to display. Implement api_client.fetch_data() to return real data.")
        return

    # display items in columns for a compact layout
    cols = st.columns(min(3, max(1, len(items))))
    for idx, item in enumerate(items):
        with cols[idx % len(cols)]:
            st.card = None
            st.markdown(f"**{item.get('name')}**")
            st.write(f"ID: {item.get('id')}")
            st.write(f"Value: {item.get('value')}")
