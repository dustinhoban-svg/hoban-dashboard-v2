import streamlit as st
import os

try:
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
except Exception:
    FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
