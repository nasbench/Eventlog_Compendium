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
    return sorted([f for f in os.listdir(path) if f.endswith(".csv")])

def highlight_message(message):
    return re.sub(r"\{(.*?)\}", r'<span class="highlight">{\1}</span>', str(message))

for key in ["windows_version", "release_version", "build_number", "csv_file"]:
    st.session_state.setdefault(key, None)
    st.session_state.setdefault(f"{key}_prev", None)

for param in ["windows_version", "release_version", "build_number", "csv_file"]:
    if st.session_state[param] != st.session_state[f"{param}_prev"]:
        st.session_state.pop("csv_loaded", None)
        st.session_state.pop("df", None)

windows_versions = get_folders(BASE_PATH)
selected_version = st.selectbox("Select Windows Version:", windows_versions, key="windows_version")

if selected_version:
    st.session_state["windows_version_prev"] = selected_version

    release_path = os.path.join(BASE_PATH, selected_version)
    release_versions = get_folders(release_path)
    selected_release = st.selectbox("Select Windows Release Version:", release_versions, key="release_version")

    if selected_release:
        st.session_state["release_version_prev"] = selected_release

        full_release_path = os.path.join(release_path, selected_release)
        direct_provider_path = os.path.join(full_release_path, "Providers")

        # Check if Providers folder exists directly under release path (Windows 8 edge case)
        if os.path.exists(direct_provider_path):
            provider_path = direct_provider_path
        else:
            build_numbers = get_folders(full_release_path)
            selected_build = st.selectbox("Select Build Number:", build_numbers, key="build_number")

            if selected_build:
                st.session_state["build_number_prev"] = selected_build
                provider_path = os.path.join(full_release_path, selected_build, "Providers")
            else:
                provider_path = None

        # Load CSV from provider_path
        if provider_path and os.path.exists(provider_path):
            provider_files = get_csvs(provider_path)

            if provider_files:
                selected_csv = st.selectbox("Select CSV File:", provider_files, key="csv_file")
                st.session_state["csv_file_prev"] = selected_csv

                if st.button("📂 Load CSV File"):
                    st.session_state.pop("filter_column", None)
                    st.session_state.pop("filter_value", None)
                    st.session_state.pop("sort_column", None)
                    st.session_state.pop("sort_order", None)

                    try:
                        full_csv_path = os.path.join(provider_path, selected_csv)
                        df = pd.read_csv(full_csv_path)

                        if "Message" in df.columns:
                            df["Message"] = df["Message"].apply(lambda x: highlight_message(x))

                        st.session_state.df = df
                        st.session_state.csv_loaded = True
                        st.success(f"✅ Loaded Data from {selected_csv}", icon="✅")
                    except Exception as e:
                        st.error(f"⚠️ Failed to load CSV: {str(e)}")
                        st.session_state.csv_loaded = False
            else:
                st.warning("⚠️ No CSV files found in the selected Providers folder.")
        else:
            st.warning("⚠️ No Providers folder found in selected path.")

# --- Display CSV Table ---
if st.session_state.get("csv_loaded"):
    df = st.session_state.df

    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        st.markdown("### 🔍 Filter Data")
        column_to_filter = st.selectbox("Select column:", df.columns, key="filter_column")
        filter_value = st.text_input("Filter value:", key="filter_value")
        if filter_value:
            df = df[df[column_to_filter].astype(str).str.contains(filter_value, case=False, na=False)]

    with col2:
        st.markdown("### 🔽 Sort Data")
        sort_column = st.selectbox("Sort by:", df.columns, key="sort_column")
        sort_order = st.radio("Sort Order:", ["Ascending", "Descending"], key="sort_order", horizontal=True)
        df = df.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))

    st.markdown(f"### 📋 {selected_csv.replace('.csv', '')}")
    table_html = df.to_html(index=False, escape=False)
    table_html = table_html.replace("<th>", '<th style="text-align:center;">')
    st.markdown(table_html, unsafe_allow_html=True)
