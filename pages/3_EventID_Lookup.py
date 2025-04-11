import streamlit as st
import os
from sidebar import show_sidebar
from PIL import Image

st.set_page_config(
    page_title="Event ID Lookup",
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

st.title("🔍 Windows Event ID Lookup")
st.info("🚧 This feature is a work in progress. The data has not yet been fully mapped, stay tuned")

EVENTS_DIRECTORY = "ETW-Providers"  # Change this if needed

query_params = st.query_params
pre_selected_event = query_params.get("event_id", "")
pre_selected_provider = query_params.get("provider", "")

def get_available_providers():
    """Get the list of event providers (folder names)."""
    if os.path.exists(EVENTS_DIRECTORY):
        return sorted([d for d in os.listdir(EVENTS_DIRECTORY) if os.path.isdir(os.path.join(EVENTS_DIRECTORY, d))])
    return []

providers = get_available_providers()

event_id = st.text_input("Enter an Event ID:", value=pre_selected_event, placeholder="e.g., 4625")

selected_provider = st.selectbox("Select Provider:", providers, index=providers.index(pre_selected_provider) if pre_selected_provider in providers else 0)

if event_id and selected_provider:
    try:
        event_id = int(event_id)  # Convert input to integer
        event_md_path = os.path.join(EVENTS_DIRECTORY, selected_provider, f"{event_id}.md")

        if os.path.exists(event_md_path):
            with open(event_md_path, "r", encoding="utf-8") as f:
                event_details = f.read()

            st.success(f"✅ Loaded Event {event_id} from {selected_provider}")
            st.markdown(event_details, unsafe_allow_html=True)  # Render markdown content

        else:
            st.warning(f"⚠️ No documentation found for Event ID {event_id} under {selected_provider}.")

    except ValueError:
        st.error("⚠️ Please enter a valid numeric Event ID.")
