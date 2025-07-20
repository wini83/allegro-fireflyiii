import asyncio
import os

import aiohttp
import streamlit as st
from dotenv import load_dotenv
from fireflyiii_enricher_core.firefly_client import FireflyClient

from api import AllegroApiClient
from get_order_result import SimplifiedPayment
from processor_gui import TransactionProcessorGUI

load_dotenv()

st.set_page_config(layout="wide")
st.title("📦 Allegro → Firefly III")

# Konfiguracja
FIREFLY_URL = os.getenv("FIREFLY_URL")
FIREFLY_TOKEN = os.getenv("FIREFLY_TOKEN")
COOKIE = os.getenv("QXLSESSID")
TAG = "allegro_done"

print(f"{FIREFLY_URL}")


@st.cache_data(show_spinner="Pobieranie zamówień z Allegro...")
def get_orders():
    async def fetch():
        async with aiohttp.ClientSession() as session:
            client = AllegroApiClient(session=session, cookie=COOKIE)
            return await client.get_orders()

    return asyncio.run(fetch())


# Pobierz dane
if st.button("🔄 Pobierz zamówienia"):
    data = get_orders()
    payments = SimplifiedPayment.from_payments(data.payments)
    st.session_state["payments"] = payments
    st.success(f"Pobrano {len(payments)} płatności")

if "payments" in st.session_state:
    firefly = FireflyClient(FIREFLY_URL, FIREFLY_TOKEN)
    processor = TransactionProcessorGUI(firefly, st.session_state["payments"], TAG)

    st.header("🔍 Dopasowywanie transakcji z Firefly")
    filter_text = st.text_input("Opis transakcji do filtrowania", value="allegro")
    if st.button("🔍 Znajdź dopasowania"):
        results = processor.find_matches(filter_text, exact_match=False)

        for r in results:
            st.markdown(f"### 🧾 {r.tx.date} | {r.tx.amount} PLN | {r.tx.description}")
            for i, match in enumerate(r.matches):
                with st.expander(
                    f"Dopasowanie #{i + 1} — {match.date} | {match.amount} PLN"
                ):
                    st.code(match.details)
                    if st.button(
                        f"✅ Zastosuj to dopasowanie (tx.id={r.tx.id})",
                        key=f"{r.tx.id}-{i}",
                    ):
                        processor.apply_match(int(r.tx.id), match.details)
                        st.success("Zaktualizowano opis i tag w Firefly")
