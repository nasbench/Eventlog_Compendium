import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image
import re
from sidebar import show_sidebar

pd.set_option("styler.render.max_elements", 200000000)

st.set_page_config(
    page_title="SACL Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("images/EventLog-Compendium.ico")
)

show_sidebar()

custom_css = """
<style>
    body {
        background-color: #11252F;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        padding: 10px;
        text-align: left;
        border: 1px solid #ddd;
    }
    th {
        background-color: #2E3B4E;
        color: white;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

SACL_FILE_PATH = Path("data/builtin_sacls.txt")
if not SACL_FILE_PATH.exists():
    st.error("SACL file not found at data/builtin_sacls.txt")
    st.stop()

def parse_sacl_text(content: str) -> pd.DataFrame:
    entries = []
    current_entry = {}
    current_audit_flags = []

    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"(SACL|ACL) found on (file/directory|service|registry key): (.+)", line)
        if match:
            if current_entry:
                current_entry["Auditing"] = ", ".join(current_audit_flags)
                entries.append(current_entry)
                current_entry = {}
                current_audit_flags = []

            acl_type = match.group(1)
            object_type = match.group(2)
            object_path = match.group(3)

            current_entry = {
                "Object_Type": object_type.title(),
                "Object": object_path,
                "Audit_Flags": "",
                "Principal": "",
                "Auditing": ""
            }

        elif line.startswith("SACL Entry"):
            entry_match = re.search(r"Auditing on:\s*(.+)", line)
            if entry_match:
                current_entry["Audit_Flags"] = entry_match.group(1).strip()

        elif line.startswith("User/Group:"):
            current_entry["Principal"] = line.split(":", 1)[1].strip()

        elif line.startswith("Auditing:"):
            right = line.replace("Auditing:", "").strip()
            current_audit_flags.append(right)

    if current_entry:
        current_entry["Auditing"] = ", ".join(current_audit_flags)
        entries.append(current_entry)
    
    return pd.DataFrame(entries)

#@st.cache_data(show_spinner=False)
def load_sacl_data(file_path: str) -> pd.DataFrame:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_sacl_text(content)

df = load_sacl_data(str(SACL_FILE_PATH))

st.title("🔒 Built-in SACL Explorer")
st.markdown("""
This page visualizes built-in **System Access Control Lists (SACLs)** for key system objects like files, registry keys, and services.
Use the filters below to narrow down by object type or principal.
""")

col1, col2 = st.columns([0.5, 0.5])
with col1:
    object_types = ["All"] + sorted(df["Object_Type"].dropna().unique().tolist())
    selected_type = st.selectbox("Filter by Object Type", object_types)
with col2:
    principals = ["All"] + sorted(df["Principal"].dropna().unique().tolist())
    selected_principal = st.selectbox("Filter by User/Group", principals)

filtered_df = df.copy()
if selected_type != "All":
    filtered_df = filtered_df[filtered_df["Object_Type"] == selected_type]
if selected_principal != "All":
    filtered_df = filtered_df[filtered_df["Principal"] == selected_principal]

def title_case_columns(df):
    df.columns = [col.replace("_", " ").title() for col in df.columns]
    return df

display_df = filtered_df.copy()
display_df = title_case_columns(display_df)

if "page_size" not in st.session_state:
    st.session_state["page_size"] = 25
if "page_number" not in st.session_state:
    st.session_state["page_number"] = 1

batch_size = st.session_state["page_size"]
total_pages = (len(display_df) - 1) // batch_size + 1
if st.session_state["page_number"] > total_pages:
    st.session_state["page_number"] = total_pages
current_page = st.session_state["page_number"]

start = (current_page - 1) * batch_size
end = start + batch_size
page_df = display_df.iloc[start:end]

table_html = page_df.to_html(escape=False).replace("<th>", '<th style="text-align:center;">')
st.markdown(table_html, unsafe_allow_html=True)

pag_col1, pag_col2, pag_col3 = st.columns((4, 1, 1))
with pag_col3:
    new_batch_size = st.selectbox(
        "Rows per page", options=[10, 25, 50, 100],
        index=[10, 25, 50, 100].index(batch_size),
        key="page_size_bottom"
    )
    if new_batch_size != st.session_state["page_size"]:
        st.session_state["page_size"] = new_batch_size
        st.session_state["page_number"] = 1
        st.rerun()

total_pages = (len(display_df) - 1) // st.session_state["page_size"] + 1
with pag_col2:
    new_current_page = st.number_input(
        "Page", min_value=1, max_value=total_pages,
        value=current_page, step=1, key="page_number_bottom"
    )
    if new_current_page != st.session_state["page_number"]:
        st.session_state["page_number"] = new_current_page
        st.rerun()

with pag_col1:
    st.markdown(f"Page **{st.session_state['page_number']}** of **{total_pages}**")

st.download_button(
    label="📥 Download Filtered SACLs as CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_sacls.csv",
    mime="text/csv"
)
