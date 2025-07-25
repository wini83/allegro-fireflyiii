
import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
import aiohttp

from api import AllegroApiClient
from fireflyiii_enricher_core.firefly_client import FireflyClient
from get_order_result import SimplifiedPayment
from processor_gui import TransactionProcessorGUI

load_dotenv()

st.set_page_config(layout="wide")
st.title("📊 Firefly III – Dopasuj Transakcje Allegro")

FIREFLY_URL = os.getenv("FIREFLY_URL")
FIREFLY_TOKEN = os.getenv("FIREFLY_TOKEN")
COOKIE = os.getenv("QXLSESSID")
TAG = "allegro_done"
DESCRIPTION_FILTER = "allegro"

# 1. Inicjalizacja klienta Firefly i procesora
if "firefly" not in st.session_state:
    st.session_state["firefly"] = FireflyClient(FIREFLY_URL, FIREFLY_TOKEN)
    st.session_state["processor"] = TransactionProcessorGUI(st.session_state["firefly"])
    st.session_state["firefly_tx"] = st.session_state["processor"].fetch_unmatched_transactions(
        DESCRIPTION_FILTER,
        TAG,exact_match=False)

with st.expander("🧪 Diagnostyka"):
    st.write("session_state:", dict(st.session_state))

# 2. Pokazujemy transakcje z Firefly do dopasowania
st.subheader("🧾 Nieuzupełnione transakcje z Firefly")
for tx in st.session_state["firefly_tx"]:
    st.markdown(f"- `{tx.date}` | `{tx.amount}` PLN | `{tx.description}`")

# 3. Pobierz zamówienia z Allegro i dopasuj
def get_orders():
    async def fetch():
        async with aiohttp.ClientSession() as session:
            client = AllegroApiClient(COOKIE, session)
            return await client.get_orders()
    return asyncio.run(fetch())

if st.button("🔄 Pobierz z Allegro i dopasuj"):
    data = get_orders()
    allegro_payments = SimplifiedPayment.from_payments(data.payments)
    st.session_state["matches"] = st.session_state["processor"].match_transactions(
        st.session_state["firefly_tx"], allegro_payments
    )
    st.success("Dopasowano transakcje!")

# 4. Pokazujemy wyniki dopasowań
if "matches" in st.session_state:
    st.subheader("✅ Dopasowania")
    for r in st.session_state["matches"]:
        st.markdown(f"### 🔹 {r.tx.date} | {r.tx.amount} PLN | {r.tx.description}")
        for i, match in enumerate(r.matches):
            with st.expander(f"Dopasowanie #{i+1} — {match.date} | {match.amount} PLN"):
                st.code(match.details)
                if st.button(f"Zastosuj (tx.id={r.tx.id})", key=f"{r.tx.id}-{i}"):
                    try:
                        st.session_state["processor"].apply_match(int(r.tx.id), match.details)
                        st.success("✔️ Zaktualizowano opis i tag w Firefly")
                    except Exception as e:
                        st.error(f"❌ Błąd zapisu: {e}")
                        st.exception(e)
