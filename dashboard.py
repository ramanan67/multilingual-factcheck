import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Fact-Check Dashboard", page_icon="🔍", layout="centered")

st.title("🔍 Multilingual Fact-Check")
st.caption("Cross-verifies claims against The Hindu, Indian Express, Times of India, "
           "Hindustan Times, Daily Thanthi, Polimer News, and Puthiya Thalaimurai.")

claim_text = st.text_area(
    "Paste a claim or headline (English or Tamil)",
    height=100,
    placeholder="e.g. மத்திய அரசு புதிய திட்டத்தை அறிவித்தது...",
)

col1, col2 = st.columns([1, 3])
with col1:
    submit = st.button("Verify", type="primary", use_container_width=True)
with col2:
    if st.button("Refresh source index now"):
        with st.spinner("Pulling latest headlines from all 7 outlets..."):
            try:
                r = requests.post(f"{API_BASE_URL}/api/ingest/run", timeout=120)
                r.raise_for_status()
                st.success(f"Indexed {r.json().get('indexed', 0)} new items.")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

if submit:
    if not claim_text.strip():
        st.warning("Enter a claim first.")
    else:
        with st.spinner("Checking against whitelisted sources..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/api/check",
                    json={"text": claim_text.strip()},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                st.error(f"Request failed: {e}")
                data = None

        if data:
            # --- Step 1: lead with a single, unambiguous True/Fake call ---
            if data["is_true"]:
                st.markdown("## ✅ TRUE")
                st.success(data["note"])
            elif data["verdict"] == "Directly Refuted":
                st.markdown("## ❌ FAKE")
                st.error(data["note"])
            else:
                st.markdown("## ⚠️ UNVERIFIED")
                st.warning(data["note"])

            st.caption(f"Language detected: {data['language_detected'].upper()}")

            # --- Step 2: only when confirmed true, show the matching articles ---
            if data["is_true"]:
                st.divider()
                st.subheader("Related articles")
                for ev in data["evidence"]:
                    with st.container(border=True):
                        st.markdown(f"**{ev['outlet']}**")
                        st.write(ev["headline"])
                        st.caption(f"Published: {ev.get('published', 'n/a')}")
                        st.markdown(f"[Read source]({ev['url']})")
