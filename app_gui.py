"""Streamlit user interface for matching Allegro payments with Firefly III."""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from fireflyiii_enricher_core.firefly_client import FireflyClient

import log_db  # moduł z load_matched_log
from processor_gui import TransactionProcessorGUI

load_dotenv()

st.set_page_config(layout="wide")
st.title("📊 Allegro → Firefly III (GUI)")

FIREFLY_URL = os.environ["FIREFLY_URL"]
FIREFLY_TOKEN = os.environ["FIREFLY_TOKEN"]
COOKIE = os.environ["QXLSESSID"]
TAG = os.environ["TAG"]
DESCRIPTION_FILTER = os.environ['DESCRIPTION_FILTER']
ALLEGRO_COOKIE = os.environ["QXLSESSID"]

# Inicjalizacja
if "firefly" not in st.session_state:
    st.session_state["firefly"] = FireflyClient(FIREFLY_URL, FIREFLY_TOKEN)
    st.session_state["processor"] = TransactionProcessorGUI(
        st.session_state["firefly"], TAG
    )
    st.session_state["firefly_tx"] = []
    st.session_state["matches"] = []

# Sidebar z filtrami
with st.sidebar:
    st.header("🔍 Filtry")
    filter_tagged = st.checkbox("Wyklucz już otagowane", True)
    name_filter = st.text_input("Opis zawiera", "")

# 1) Pobranie Firefly
st.subheader("📥 Krok 1: Pobierz z Firefly")
if st.button("Pobierz transakcje"):
    st.session_state["firefly_tx"] = st.session_state[
        "processor"
    ].fetch_unmatched_transactions(DESCRIPTION_FILTER, exact_match=False)
    st.success("Transakcje pobrane")
    df = pd.DataFrame(
        [
            {
                "ID": tx.tx.id,
                "Data": tx.tx.date,
                "Kwota": tx.tx.amount,
                "Opis": tx.tx.description,
                "Notes": tx.tx.notes,
                "Matches": len(tx.matches),
            }
            for tx in st.session_state["firefly_tx"]
        ]
    )

    dataframe = st.table(df)

# 2) Filtrowanie lokalne
filtered = []
for tx in st.session_state["firefly_tx"]:
    if filter_tagged and TAG in tx.tx.tags:
        continue
    if name_filter and name_filter.lower() not in tx.tx.description.lower():
        continue
    filtered.append(tx)

# 5) Diagnostyka logów
st.subheader("📄 Historia dopasowań")
df_log = log_db.load_matched_log(limit=50)
if df_log is not None and not df_log.empty:
    st.dataframe(df_log, use_container_width=True)
else:
    st.info("Brak zapisanych dopasowań w bazie.")
