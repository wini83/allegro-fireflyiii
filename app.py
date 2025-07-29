from dataclasses import asdict
from typing import List

import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
import aiohttp
import pandas as pd

from api import AllegroApiClient
from fireflyiii_enricher_core.firefly_client import FireflyClient
from get_order_result import SimplifiedPayment
from processor_gui import TransactionProcessorGUI, match_transactions, TxMatchResult

load_dotenv()

st.set_page_config(layout="wide")
st.title("📊 Allegro >> Firefly III")

FIREFLY_URL = os.getenv("FIREFLY_URL")
FIREFLY_TOKEN = os.getenv("FIREFLY_TOKEN")
COOKIE = os.getenv("QXLSESSID")
TAG = "allegro_done"
DESCRIPTION_FILTER = "allegro"

def get_orders():
    async def fetch():
        async with aiohttp.ClientSession() as session:
            client = AllegroApiClient(COOKIE, session)
            return await client.get_orders()
    return asyncio.run(fetch())

def render_matches(tx:TxMatchResult) -> None:
    if len(tx.matches)>0:
        st.write(f"Dopasowania do :")
        st.table([asdict(tx.tx)])
        for i, match in enumerate(tx.matches):
            with st.expander(f"{match.date} | {match.amount} PLN",expanded=True):
                st.write(match.details)
                if st.button(f"Zastosuj (id={tx.tx.id})", key=f"{tx.tx.id}-{i}"):
                    try:
                        st.session_state["processor"].apply_match(int(tx.tx.id), match.details)
                        st.success("✔️ Zaktualizowano opis i tag w Firefly")
                    except Exception as e:
                        st.error(f"❌ Błąd zapisu: {e}")
                        st.exception(e)

if "firefly" not in st.session_state:
    st.session_state["firefly"] = FireflyClient(FIREFLY_URL, FIREFLY_TOKEN)
    st.session_state["processor"] = TransactionProcessorGUI(st.session_state["firefly"],TAG)
    st.session_state["firefly_tx"] = st.session_state["processor"].fetch_unmatched_transactions(
        DESCRIPTION_FILTER,
        exact_match=False)
    st.session_state["selected_matches"] = {}

df = pd.DataFrame([{
    "ID": tx.tx.id,
    "Data": tx.tx.date,
    "Kwota": tx.tx.amount,
    "Opis": tx.tx.description,
    "Notes":tx.tx.notes,
    "Matches":len(tx.matches)
} for tx in st.session_state["firefly_tx"]])

with st.expander("🧪 Diagnostyka"):
    st.write("session_state:", dict(st.session_state))

if st.button("🔄 Pobierz dane z Allegro i dopasuj"):
    data = get_orders()
    allegro_payments = SimplifiedPayment.from_payments(data.payments)
    st.session_state["firefly_tx"] = match_transactions(
        st.session_state["firefly_tx"], allegro_payments
    )
    st.success("🔍 Dopasowano transakcje!")
    st.rerun()

dataframe = st.table(df)#, use_container_width=True, selection_mode="multi-row", on_select="rerun",key="ID")

# if len(dataframe["selection"]["rows"])>0:
#     txs:List[TxMatchResult] = st.session_state["firefly_tx"]
#     for row in dataframe["selection"]["rows"]:
#         tx = txs[row]
#         render_matches(tx)


txs:List[TxMatchResult] = st.session_state["firefly_tx"]
for tx in txs:
    render_matches(tx)
