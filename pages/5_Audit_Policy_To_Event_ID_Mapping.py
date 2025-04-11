import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from sidebar import show_sidebar
from PIL import Image
from urllib.parse import quote

st.set_page_config(
    page_title="Audit Policy to Event ID Mapping",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("images/EventLog-Compendium.ico")
)

show_sidebar()

custom_css = """
    <style>
        body {
            background-color: #11252F;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            table-layout: fixed;
        }
        th {
            background-color: #2E3B4E;
            color: white;
            font-size: 16px;
            padding: 12px;
            border-bottom: 2px solid #ddd;
            text-align: center;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: center;
            word-wrap: break-word;
            white-space: normal;
        }
        td:last-child {
            max-width: 300px;
        }
        tr:nth-child(even) {
            background-color: rgba(255, 255, 255, 0.05);
        }
        tr:hover {
            background-color: rgba(255, 255, 255, 0.15);
        }
    </style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Audit Policy to Event ID Mapping")

def load_mapping():
    json_path = "data/audit_policy_category_to_event_mapping.json"
    if not os.path.exists(json_path):
        st.error(f"⚠️ JSON file not found: {json_path}")
        return {}
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_eventid_messages():
    message_path = "data/eventid_message_mapping.json"
    if not os.path.exists(message_path):
        st.warning(f"⚠️ Message mapping file not found: {message_path}")
        return {}
    with open(message_path, "r", encoding="utf-8") as f:
        return json.load(f)

raw_data = load_mapping()
eventid_messages = load_eventid_messages()

raw_df = pd.DataFrame([
    {
        "Category": category,
        "Sub-Category": subcat_info.get("Name", "Unknown"),
        "Sub-Category GUID": guid,
        "Event ID": eid,
        "Message": eventid_messages.get(str(eid), "N/A")
    }
    for category, subcats in raw_data.items()
    for guid, subcat_info in subcats.items()
    for eid in subcat_info.get("EventIDs", [])
])

col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])

with col1:
    selected_category = st.selectbox("Filter by Category:", ["All"] + sorted(raw_df["Category"].unique()))

with col2:
    subcategory_options = raw_df[raw_df["Category"] == selected_category]["Sub-Category"].unique() if selected_category != "All" else raw_df["Sub-Category"].unique()
    selected_subcategory = st.selectbox("Filter by Sub-Category:", ["All"] + sorted(subcategory_options))

with col3:
    search_event_id = st.text_input("Search by Event ID:", placeholder="e.g., 4624")

with col4:
    search_message = st.text_input("Search by Message Content:", placeholder="e.g., logon, kerberos")

filtered_raw_df = raw_df.copy()
if selected_category != "All":
    filtered_raw_df = filtered_raw_df[filtered_raw_df["Category"] == selected_category]
if selected_subcategory != "All":
    filtered_raw_df = filtered_raw_df[filtered_raw_df["Sub-Category"] == selected_subcategory]
if search_event_id:
    try:
        eid = int(search_event_id)
        filtered_raw_df = filtered_raw_df[filtered_raw_df["Event ID"] == eid]
    except ValueError:
        st.warning("⚠️ Please enter a valid numeric Event ID.")
if search_message:
    filtered_raw_df = filtered_raw_df[filtered_raw_df["Message"].str.contains(search_message, case=False, na=False)]

data_list = []
for _, row in filtered_raw_df.iterrows():
    cat_url = f"/Advanced_Audit_Policy_Documentation?category={quote(row['Category'].replace('/', '_').replace(' ', '_'))}"
    sub_url = f"{cat_url}&sub_category={quote(row['Sub-Category'].replace('Audit ', '').replace('/', '_').replace(' ', '_'))}"
    eid_url = f"/EventID_Lookup?event_id={row['Event ID']}&provider=Microsoft-Security-Auditing"

    data_list.append({
        "Category": f'<a href="{cat_url}" target="_self">{row["Category"]}</a>',
        "Sub-Category": f'<a href="{sub_url}" target="_self">{row["Sub-Category"]}</a>',
        "Sub-Category GUID": row["Sub-Category GUID"],
        "Event ID": f'<a href="{eid_url}" target="_self">{row["Event ID"]}</a>',
        "Message": row["Message"]
    })

df = pd.DataFrame(data_list)

_, _, _, col_export = st.columns([0.3, 0.3, 0.3, 0.3])
with col_export:
    csv_buffer = BytesIO()
    filtered_raw_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📅 Export as CSV",
        data=csv_buffer.getvalue(),
        file_name="audit_policy_event_mapping.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("### 🔎 Filtered Results")
st.markdown(
    df.to_html(index=False, escape=False).replace("<th>", '<th style="text-align:center;">'),
    unsafe_allow_html=True
)
