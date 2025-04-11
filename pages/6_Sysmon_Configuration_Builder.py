import os
import re
import streamlit as st
from lxml import etree
from sidebar import show_sidebar
from PIL import Image
import tempfile

SYSMON_MODULAR_DIR = "sysmon-modular"

SPECIAL_TITLES = {
    "12_13_14_registry_event": "Event ID 12/13/14 - Registry Event",
    "17_18_pipe_event": "Event ID 17/18 - Pipe Event",
    "19_20_21_wmi_event": "Event ID 19/20/21 - WMI Event"
}

st.set_page_config(
    page_title="Sysmon Configuration Builder",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("images/EventLog-Compendium.ico")
)

show_sidebar()

st.title("🧩 Sysmon Configuration Builder")
st.info("🚧 This feature is a work in progress. Things might change, break, or evolve as we enhance the builder!")

st.markdown("""
This builder lets you assemble a custom Sysmon configuration using Olaf Hartong's 
[Sysmon Modular](https://github.com/olafhartong/sysmon-modular) project.

Each section below represents a Sysmon Event ID and lets you preview, add, and merge 
configuration snippets into a final XML that you can download.
""")


if "sysmon_selected_configs" not in st.session_state:
    st.session_state.sysmon_selected_configs = {}
if "last_added_sysmon_snippet" not in st.session_state:
    st.session_state.last_added_sysmon_snippet = None

def get_sorted_event_folders():
    def sort_key(folder):
        match = re.match(r'^(\d+(?:_\d+)*)', folder)
        if match:
            return [int(n) for n in match.group(1).split("_")]
        return [9999]
    folders = [
        f for f in os.listdir(SYSMON_MODULAR_DIR)
        if f[0].isdigit() and os.path.isdir(os.path.join(SYSMON_MODULAR_DIR, f))
    ]
    return sorted(folders, key=sort_key)

def format_title(folder_name):
    if folder_name in SPECIAL_TITLES:
        return SPECIAL_TITLES[folder_name]
    parts = folder_name.split("_")
    event_id = parts[0]
    name = " ".join(p.capitalize() for p in parts[1:])
    return f"Event ID {event_id} - {name}"

def pretty_print_xml(xml_string):
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        xml = etree.fromstring(xml_string.encode(), parser=parser)
        return etree.tostring(xml, pretty_print=True, encoding='unicode')
    except Exception as e:
        return f"⚠️ Invalid XML:\n{str(e)}"

def merge_sysmon_xml(snippets):
    root = etree.Element("Sysmon", schemaversion="4.50")

    # Add static elements
    etree.SubElement(root, "HashAlgorithms").text = "*"
    etree.SubElement(root, "CheckRevocation").text = "False"
    etree.SubElement(root, "DnsLookup").text = "False"
    etree.SubElement(root, "ArchiveDirectory").text = "Sysmon"

    for xml_string in snippets:
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            snippet = etree.fromstring(xml_string.encode(), parser=parser)
            for element in snippet:
                root.append(element)
        except Exception as e:
            st.warning(f"Error merging XML: {e}")
    
    return etree.tostring(root, pretty_print=True, encoding="unicode")


for folder in get_sorted_event_folders():
    folder_path = os.path.join(SYSMON_MODULAR_DIR, folder)
    display_title = format_title(folder)

    with st.expander(f"⚙️ {display_title}", expanded=False):
        xml_files = [f for f in os.listdir(folder_path) if f.endswith(".xml")]
        if not xml_files:
            st.info("No XML files found in this folder.")
            continue

        xml_options = {
            f: " ".join(part.capitalize() for part in f.replace(".xml", "").split("_"))
            for f in xml_files
        }
        selected_label = st.selectbox(
            "Select a config snippet:",
            options=list(xml_options.values()),
            key=f"select_{folder}"
        )
        selected_xml = next(f for f, label in xml_options.items() if label == selected_label)
        selected_path = os.path.join(folder_path, selected_xml)

        with open(selected_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        st.code(pretty_print_xml(xml_content), language="xml")

        cols = st.columns([0.2, 0.8])
        with cols[0]:
            added = selected_path in st.session_state.sysmon_selected_configs
            if not added:
                if st.button("Add to Global Config", key=f"add_{folder}"):
                    st.session_state.sysmon_selected_configs[selected_path] = xml_content
                    st.session_state.last_added_sysmon_snippet = selected_path
                    st.success("Added to global config.")
            else:
                if st.button("Remove from Global Config", key=f"remove_{folder}"):
                    del st.session_state.sysmon_selected_configs[selected_path]
                    st.session_state.last_added_sysmon_snippet = None
                    st.info("Removed from global config.")

if st.session_state.last_added_sysmon_snippet:
    st.markdown("---")
    if st.button("Undo Last Add"):
        removed = st.session_state.last_added_sysmon_snippet
        if removed in st.session_state.sysmon_selected_configs:
            del st.session_state.sysmon_selected_configs[removed]
            st.session_state.last_added_sysmon_snippet = None
            st.success("Last added snippet has been removed.")

st.markdown("---")
st.header("🧱 Global Sysmon Configuration")

if st.session_state.sysmon_selected_configs:
    merged = merge_sysmon_xml(list(st.session_state.sysmon_selected_configs.values()))
    st.code(pretty_print_xml(merged), language="xml")

    st.download_button(
        label="⬇️ Download Merged Sysmon Config",
        data=merged,
        file_name="merged_sysmon_config.xml",
        mime="application/xml",
        use_container_width=True
    )
else:
    st.info("No config snippets added yet. Select some from above to start building your config.")
