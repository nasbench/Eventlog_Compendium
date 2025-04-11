import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
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

st.title("\U0001F4CA ETW Provider Visualizer")

GITHUB_API_URL = "https://api.github.com/repos/nasbench/EVTX-ETW-Resources/contents/ETWEventsList/CSV"

for key in ["windows_version", "release_version", "build_number", "csv_file"]:
    st.session_state.setdefault(key, None)
    st.session_state.setdefault(f"{key}_prev", None)

for param in ["windows_version", "release_version", "build_number", "csv_file"]:
    if st.session_state[param] != st.session_state[f"{param}_prev"]:
        st.session_state.pop("csv_loaded", None)
        st.session_state.pop("df", None)

@st.cache_data
def fetch_directory_contents(path):
    url = f"{GITHUB_API_URL}/{path}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data from GitHub API: {response.status_code}")
        return []

def extract_folders(contents):
    return [item['name'] for item in contents if item['type'] == 'dir']

def extract_csv_files(contents):
    return [item['name'] for item in contents if item['type'] == 'file' and item['name'].endswith('.csv')]

def highlight_message(message):
    return re.sub(r"\{(.*?)\}", r'<span class="highlight">{\1}</span>', str(message))

windows_versions = extract_folders(fetch_directory_contents(""))
selected_version = st.selectbox("Select Windows Version:", windows_versions, key="windows_version")

if selected_version:
    st.session_state["windows_version_prev"] = selected_version

    # Step 2: Select Release Version
    release_versions = extract_folders(fetch_directory_contents(selected_version))
    selected_release = st.selectbox("Select Windows Release Version:", release_versions, key="release_version")

    if selected_release:
        st.session_state["release_version_prev"] = selected_release

        # Step 3: Select Build Number
        build_numbers = extract_folders(fetch_directory_contents(f"{selected_version}/{selected_release}"))
        selected_build = st.selectbox("Select Build Number:", build_numbers, key="build_number")

        if selected_build:
            st.session_state["build_number_prev"] = selected_build

            # Step 4: Select Provider CSV
            provider_files = extract_csv_files(fetch_directory_contents(f"{selected_version}/{selected_release}/{selected_build}/Providers"))

            if provider_files:
                selected_csv = st.selectbox("Select CSV File:", provider_files, key="csv_file")
                st.session_state["csv_file_prev"] = selected_csv

                # Load CSV Button
                if st.button("\U0001F4C2 Load CSV File"):
                    st.session_state.pop("filter_column", None)
                    st.session_state.pop("filter_value", None)
                    st.session_state.pop("sort_column", None)
                    st.session_state.pop("sort_order", None)

                    encoded_csv = quote(selected_csv)
                    csv_url = f"https://raw.githubusercontent.com/nasbench/EVTX-ETW-Resources/main/ETWEventsList/CSV/{selected_version}/{selected_release}/{selected_build}/Providers/{encoded_csv}"

                    try:
                        df = pd.read_csv(csv_url)
                        if "Message" in df.columns:
                            df["Message"] = df["Message"].apply(lambda x: highlight_message(x))
                        st.session_state.df = df
                        st.session_state.csv_loaded = True
                        st.success(f"\u2705 Loaded Data from {selected_csv}", icon="✅")
                    except Exception as e:
                        st.error(f"⚠️ Failed to load CSV: {str(e)}")
                        st.session_state.csv_loaded = False
            else:
                st.warning("No CSV files found in the selected Providers folder.")

if "csv_loaded" in st.session_state and st.session_state.csv_loaded:
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
