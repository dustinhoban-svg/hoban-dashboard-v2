import streamlit as st
import os

try:
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
except Exception:
    FRED_API_KEY = os.environ.get("FRED_API_KEY", "be653bcbdccf503dc5a3cc2f67fbebcf")

try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.domacaqcpggjrtxbolud:SucmAkfmt4zjAnUB@aws-0-us-east-2.pooler.supabase.com:5432/postgres")
