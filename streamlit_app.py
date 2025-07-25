
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
st.title("📦 Allegro → Firefly III")

FIREFLY_URL = os.getenv("FIREFLY_URL")
FIREFLY_TOKEN = os.getenv("FIREFLY_TOKEN")
COOKIE = os.getenv("QXLSESSID")
TAG = "allegro_done"

@st.cache_data(show_spinner="Pobieranie zamówień z Allegro...")
def get_orders():
    async def fetch():
        async with aiohttp.ClientSession() as session:
            client = AllegroApiClient(COOKIE, session)
            return await client.get_orders()
    return asyncio.run(fetch())

# Diagnostyka session_state
with st.expander("🧪 Diagnostyka"):
    st.write("session_state:", dict(st.session_state))

# Pobieranie zamówień
if st.button("🔄 Pobierz zamówienia"):
    data = get_orders()
    payments = SimplifiedPayment.from_payments(data.payments)
    st.session_state["payments"] = payments
    st.success(f"Pobrano {len(payments)} płatności")

# Dopasowania
if "payments" in st.session_state:
    if "firefly" not in st.session_state:
        st.session_state["firefly"] = FireflyClient(FIREFLY_URL, FIREFLY_TOKEN)

    if "processor" not in st.session_state:
        st.session_state["processor"] = TransactionProcessorGUI(
            st.session_state["firefly"],
            st.session_state["payments"],
            TAG
        )

    processor = st.session_state["processor"]

    st.header("🔍 Dopasowywanie transakcji z Firefly")
    filter_text = st.text_input("Opis transakcji do filtrowania", value="allegro")

    if st.button("🔍 Znajdź dopasowania"):
        results = processor.find_matches(filter_text, exact_match=False)
        st.session_state["results"] = results

    if "results" in st.session_state:
        for r in st.session_state["results"]:
            st.markdown(f"### 🧾 {r.tx.date} | {r.tx.amount} PLN | {r.tx.description}")
            for i, match in enumerate(r.matches):
                with st.expander(f"Dopasowanie #{i+1} — {match.date} | {match.amount} PLN"):
                    st.code(match.details)
                    if st.button(f"✅ Zastosuj (tx.id={r.tx.id})", key=f"{r.tx.id}-{i}"):
                        try:
                            processor.apply_match(int(r.tx.id), match.details)
                            st.success("✔️ Zaktualizowano opis i tag w Firefly")
                        except Exception as e:
                            st.error(f"❌ Błąd zapisu: {e}")
                            st.exception(e)
