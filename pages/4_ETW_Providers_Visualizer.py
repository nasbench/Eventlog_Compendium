import streamlit as st
import pandas as pd
import os
import re
from sidebar import show_sidebar
from PIL import Image

st.set_page_config(
    page_title="ETW Provider Visualizer",
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
            text-align: center !important;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: left;
            word-wrap: break-word;
            white-space: pre-wrap;
            max-width: 500px;
        }
        tr:nth-child(even) {
            background-color: rgba(255, 255, 255, 0.05);
        }
        tr:hover {
            background-color: rgba(255, 255, 255, 0.15);
        }
        .highlight {
            color: #90EE90;
            font-weight: bold;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 ETW Provider Visualizer")

BASE_PATH = "data/EVTX-ETW-Resources/ETWEventsList/CSV"

def get_folders(path):
    return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

def get_csvs(path):
    return {f.replace(".csv.gz", ""): f
            for f in os.listdir(path)
            if f.endswith(".csv.gz")}

def highlight_message(message):
    return re.sub(r"\{(.*?)\}", r'<span class="highlight">{\1}</span>', str(message))

st.session_state.setdefault("df", None)
st.session_state.setdefault("csv_loaded", False)

# Windows Version
windows_versions = get_folders(BASE_PATH)
selected_version = st.selectbox("Select Windows Version:", windows_versions, key="windows_version")

if selected_version:
    version_path = os.path.join(BASE_PATH, selected_version)
    # Release Version
    release_versions = get_folders(version_path)
    selected_release = st.selectbox("Select Windows Release Version:", release_versions, key="release_version")

    if selected_release:
        release_path = os.path.join(version_path, selected_release)
        # System Folder
        system_infos = get_folders(release_path)
        selected_sys = st.selectbox("Select System Folder:", system_infos, key="system_info")

        if selected_sys:
            sys_path = os.path.join(release_path, selected_sys)
            provider_path = os.path.join(sys_path, "Providers")

            if os.path.exists(provider_path):
                provider_files = get_csvs(provider_path)

                if provider_files:
                    # Clear out old DataFrame when user picks a different CSV
                    def _clear_df():
                        st.session_state.df = None
                        st.session_state.csv_loaded = False

                    selected_label = st.selectbox(
                        "Select CSV File:",
                        list(provider_files.keys()),
                        key="csv_file",
                        on_change=_clear_df
                    )

                    if st.button("📂 Load CSV File"):
                        try:
                            full_csv_path = os.path.join(provider_path, provider_files[selected_label])
                            df = pd.read_csv(full_csv_path, compression="gzip")
                            if "Message" in df.columns:
                                df["Message"] = df["Message"].apply(highlight_message)
                            st.session_state.df = df
                            st.session_state.csv_loaded = True
                            st.success(f"✅ Loaded data from {provider_files[selected_label]}")
                        except Exception as e:
                            st.error(f"⚠️ Failed to load CSV: {e}")

                else:
                    st.warning("⚠️ No .csv.gz files found in the Providers folder.")
            else:
                st.warning("⚠️ No Providers folder found in the selected system folder.")

if st.session_state.csv_loaded:
    df = st.session_state.df.copy()

    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        st.markdown("### 🔍 Filter Data")
        filter_col = st.selectbox("Select column:", df.columns, key="filter_column")
        filter_val = st.text_input("Filter value:", key="filter_value")
    with col2:
        st.markdown("### 🔽 Sort Data")
        sort_col = st.selectbox("Sort by:", df.columns, key="sort_column")
        sort_asc = st.radio("Sort Order:", ["Ascending", "Descending"], key="sort_order", horizontal=True)

    # Apply filter
    if filter_val:
        df = df[df[filter_col].astype(str)
                  .str.contains(filter_val, case=False, na=False)]

    # Apply sort
    df = df.sort_values(by=sort_col, ascending=(sort_asc == "Ascending"))

    # Render table
    clean_name = selected_label
    st.markdown(f"### 📋 {clean_name}")
    table_html = df.to_html(index=False, escape=False)
    table_html = table_html.replace("<th>", '<th style="text-align:center;">')
    st.markdown(table_html, unsafe_allow_html=True)
