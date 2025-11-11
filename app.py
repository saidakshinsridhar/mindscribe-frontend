import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict, Optional
import html

# ========== CONFIG ==========
BASE_URL = "http://localhost:8080/journals"  # <-- your backend base URL

# ========== STYLES ==========
st.set_page_config(page_title="MindScribe — Journal", layout="wide")
st.markdown(
    """
    <style>
    /* page background + app container */
    body { background: #fbf6ed; }
    .app-title { font-family: 'Georgia', serif; font-size:36px; font-weight:700; color:#7d3b18; margin: 10px 0 20px 0; }
    .subtitle { color: #9b6b3f; font-style: italic; margin-bottom: 16px; }
    .form-card { background: white; border-radius: 10px; padding: 22px; box-shadow: 0 6px 14px rgba(0,0,0,0.08); }
    .journal-card { background: #fff; padding: 18px; border-radius: 8px; box-shadow: 0 6px 12px rgba(0,0,0,0.06); margin-bottom: 18px; }
    .muted { color:#6b6b6b; font-size:13px; }
    .big-title { font-family: Georgia, serif; font-size:22px; color:#222; margin:0 0 6px 0; }
    .btn-delete { color: #b91c1c; background: #fff0f0; border: 1px solid #ffdede; padding:6px 10px; border-radius:6px; }
    .btn-edit { color: #7b4b00; background: #fff7ed; border:1px solid #f7dcc3; padding:6px 10px; border-radius:6px; margin-right:8px;}
    .small { font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ========== HELPERS ==========
def fetch_journals() -> List[Dict]:
    try:
        r = requests.get(BASE_URL, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Could not fetch journals: {e}")
        return []

def create_journal(payload: Dict) -> Optional[Dict]:
    try:
        r = requests.post(BASE_URL, json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Create failed: {e}")
        return None

def update_journal(jid: int, payload: Dict) -> bool:
    try:
        url = f"{BASE_URL}/{jid}"
        r = requests.put(url, json=payload, timeout=30)
        r.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False

def delete_journal(jid: int) -> bool:
    try:
        url = f"{BASE_URL}/{jid}"
        r = requests.delete(url, timeout=5)
        r.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False

def iso_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

# ========== UI ==========
st.markdown('<div class="app-title">MindScribe</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Create new entry — jot down your thoughts</div>', unsafe_allow_html=True)

# layout: left form, right preview or spacing
col1, col2 = st.columns([2, 1])

with col1:
    with st.form("create_form", clear_on_submit=True):
        st.markdown('<div class="form-card">', unsafe_allow_html=True)
        title = st.text_input("Title", "", placeholder="A new adventure")
        content = st.text_area("Content", "", height=160, placeholder="Write your journal content here...")
        date_input = st.date_input("Date", value=datetime.today())
        submitted = st.form_submit_button("Submit Entry")
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        payload = {"title": title, "content": content, "date": iso_date(date_input)}
        created = create_journal(payload)
        if created:
            st.success("Journal created.")
            st.rerun()



st.markdown("---")
st.markdown('<h3 style="font-family:Georgia, serif; color:#6b3b1a;">My Past Musings — Existing Journal Entries</h3>', unsafe_allow_html=True)

journals = fetch_journals()

if not journals:
    st.info("No journal entries found (or couldn't fetch). Create one above.")
else:
    # show entries in a 2-col grid
    cols = st.columns(2)
    for idx, j in enumerate(journals):
        c = cols[idx % 2]
        with c:
            st.markdown('<div class="journal-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="muted">{j.get("date", "")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-title">{html.escape(j.get("title",""))}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small">{html.escape(j.get("content",""))}</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # action buttons
            cols_actions = st.columns([0.3,0.3,1])
            with cols_actions[0]:
                if st.button("Edit", key=f"edit_{j.get('id')}", help="Edit this entry"):
                    # show editable form under this card using session state
                    st.session_state["edit_id"] = j.get("id")
                    st.session_state["edit_title"] = j.get("title")
                    st.session_state["edit_content"] = j.get("content")
                    # store date as ISO
                    try:
                        st.session_state["edit_date"] = datetime.strptime(j.get("date",""), "%Y-%m-%d").date()
                    except Exception:
                        st.session_state["edit_date"] = datetime.today().date()
                    st.rerun()

            with cols_actions[1]:
                if st.button("Delete", key=f"del_{j.get('id')}", help="Delete this entry"):
                    ok = delete_journal(j.get("id"))
                    if ok:
                        st.success("Deleted.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            # if this card is in edit mode, show inline edit form
            if st.session_state.get("edit_id") == j.get("id"):
                with st.form(f"update_form_{j.get('id')}"):
                    st.text_input("Title", key="edit_title")
                    st.text_area("Content", key="edit_content", height=140)
                    st.date_input("Date", key="edit_date")
                    if st.form_submit_button("Save Changes"):
                        payload = {
                            "title": st.session_state["edit_title"],
                            "content": st.session_state["edit_content"],
                            "date": st.session_state["edit_date"].strftime("%Y-%m-%d"),
                        }
                        success = update_journal(j.get("id"), payload)
                        if success:
                            st.success("Updated.")
                            # clear edit state
                            st.session_state.pop("edit_id", None)
                            st.rerun()
                # cancel button
                if st.button("Cancel edit", key=f"cancel_{j.get('id')}"):
                    st.session_state.pop("edit_id", None)
                    st.rerun()
