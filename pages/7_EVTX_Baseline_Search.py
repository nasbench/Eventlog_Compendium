import streamlit as st
import os
import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from sidebar import show_sidebar
from PIL import Image

st.set_page_config(
    page_title="EVTX Baseline Search",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("images/EventLog-Compendium.ico")
)

show_sidebar()

st.title("📄 EVTX Baseline Search & Match")
st.markdown("""
This utility allows you to search and browse known-good events from the
[Nextron EVTX Baseline](https://github.com/NextronSystems/evtx-baseline) project.
""")

BASELINE_DIR = "evtx-baseline-db"

def load_json_gz(file_path):
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load {file_path}: {e}")
        return []

def parse_event_json(text):
    try:
        return json.loads(text)
    except Exception as e:
        st.error(f"Failed to parse JSON: {e}")
        return None

def parse_event_xml(text):
    try:
        root = ET.fromstring(text.replace("- <", "<"))
        ns = {'ns': 'http://schemas.microsoft.com/win/2004/08/events/event'}
        system = root.find("ns:System", ns)
        provider = system.find("ns:Provider", ns).attrib.get("Name")
        event_id = system.findtext("ns:EventID", namespaces=ns)

        event_data = {}
        for data_el in root.findall(".//ns:EventData/ns:Data", ns):
            key = data_el.attrib.get("Name")
            value = data_el.text
            if key:
                event_data[key] = value

        return {
            "System": {
                "Provider": {"#attributes": {"Name": provider}},
                "EventID": int(event_id)
            },
            "Event": {
                "EventData": event_data
            }
        }
    except Exception as e:
        st.error(f"Failed to parse XML: {e}")
        return None

def find_match(event, filter_fields, logic_operator="AND"):
    try:
        provider = event.get("System", {}).get("Provider", {}).get("#attributes", {}).get("Name")
        event_id = str(event.get("System", {}).get("EventID"))
        file_path = Path(BASELINE_DIR, provider.replace("/", "_"), f"{event_id}.json.gz")
        if not file_path.exists():
            return [], []

        data = load_json_gz(file_path)
        if not filter_fields:
            return data, []

        event_fields = event.get("Event", {}).get("EventData", {})

        exact_matches = []
        partial_matches = []

        for record in data:
            eventdata = record.get("Event", {}).get("EventData", {})
            match_results = []

            for field in filter_fields:
                pasted_value = event_fields.get(field)
                baseline_value = eventdata.get(field)

                if pasted_value is None or baseline_value is None:
                    match_results.append((field, "missing"))
                elif str(pasted_value).lower() == str(baseline_value).lower():
                    match_results.append((field, "exact"))
                elif str(pasted_value).lower() in str(baseline_value).lower():
                    match_results.append((field, "partial"))
                else:
                    match_results.append((field, "no_match"))

            statuses = [s for _, s in match_results]

            if logic_operator == "AND":
                if all(s == "exact" for s in statuses):
                    exact_matches.append((record, match_results))
                elif all(s in ["exact", "partial"] for s in statuses):
                    partial_matches.append((record, match_results))
            elif logic_operator == "OR":
                if any(s == "exact" for s in statuses):
                    exact_matches.append((record, match_results))
                elif any(s == "partial" for s in statuses):
                    partial_matches.append((record, match_results))

        return exact_matches, partial_matches

    except Exception as e:
        st.error(f"Error during match: {e}")
        return [], []

tab1, tab2 = st.tabs(["Search by Pasted Event", "Browse Baseline Events"])

with tab1:
    st.subheader("🔍 Paste an Event to Match Against Baseline")
    input_type = st.selectbox("Select Event Format", ["JSON", "XML"], key="event_type")

    if input_type == "JSON":
        st.caption("🛈 JSON format should be generated via this [evtx](https://github.com/omerbenamram/evtx) project")
    else:
        st.caption("🛈 XML format is expected to be copied from the XML tab in the Windows Event Viewer")

    st.markdown("""
    #### Matching Options
    Select which fields from your event you'd like to use to find similar events in the baseline.
    Matching is case-insensitive and can be partial or exact.
    """)

    col_logic, col_count = st.columns([0.3, 0.7])
    with col_logic:
        paste_logic = st.radio("Filter Logic", ["AND", "OR"], horizontal=True, key="paste_logic")
    with col_count:
        filter_count = st.selectbox("Number of fields to match", options=list(range(0, 6)), index=1, key="search_filter_count")

    filters = []
    for i in range(filter_count):
        field = st.text_input(f"Field Name {i+1}", key=f"paste_field_{i}", help="Case-sensitive field name from EventData")
        if field:
            filters.append(field)

    pasted_event = st.text_area("Paste your event here:", height=300)

    if "stored_exact" not in st.session_state:
        st.session_state.stored_exact = []
        st.session_state.stored_partial = []
        st.session_state.selected_match_index = 0

    if st.button("🔎 Search Baseline"):
        if not pasted_event.strip():
            st.warning("Please paste a valid event.")
        elif filter_count > 0 and len(filters) < filter_count:
            st.warning("Please fill in all selected field name(s) before searching.")
        else:
            parsed_event = parse_event_json(pasted_event) if input_type == "JSON" else parse_event_xml(pasted_event)
            if parsed_event:
                exact, partial = find_match(parsed_event, filters, paste_logic)
                st.session_state.stored_exact = exact
                st.session_state.stored_partial = partial
                st.session_state.selected_match_index = 0


    all_matches = st.session_state.stored_exact + st.session_state.stored_partial

    if all_matches:
        match_labels = [f"✅ Exact Match {i+1}" for i in range(len(st.session_state.stored_exact))] + \
                       [f"🟡 Partial Match {i+1}" for i in range(len(st.session_state.stored_partial))]

        left_col, right_col = st.columns([0.35, 0.65])
        with left_col:
            st.markdown("#### 📋 Matched Records")
            with st.container(height=1100):
                st.session_state.selected_match_index = st.radio(
                    "Select a Match:",
                    options=list(range(len(match_labels))),
                    format_func=lambda i: match_labels[i],
                    index=st.session_state.selected_match_index,
                    key="match_radio"
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with right_col:
            st.markdown("#### 🧾 Match Details")

            selected_index = st.session_state.selected_match_index
            record, match_info = all_matches[selected_index]

            with st.expander("🔍 Field Matching Explanation", expanded=False):
                for field, status in match_info:
                    if status == "exact":
                        st.markdown(f"✅ **{field}** matched exactly.")
                    elif status == "partial":
                        st.markdown(f"🟡 **{field}** partially matched.")
                    elif status == "missing":
                        st.markdown(f"⚠️ **{field}** was not found in one of the records.")
                    else:
                        st.markdown(f"❌ **{field}** did not match.")

            st.json(record)
    elif pasted_event:
        st.info("No matching baseline events found.")

with tab2:
    st.subheader("📂 Browse Events from the Baseline Database")

    providers = sorted([p.name for p in Path(BASELINE_DIR).iterdir() if p.is_dir()])
    selected_provider = st.selectbox("Select a Provider:", providers, key="browse_provider")

    event_files = sorted(Path(BASELINE_DIR, selected_provider).glob("*.json.gz"))
    event_ids = [f.stem.strip(".json") for f in event_files]
    selected_event_id = st.selectbox("Select an Event ID:", event_ids, key="browse_event")

    file_path = Path(BASELINE_DIR, selected_provider, f"{selected_event_id}.json.gz")
    data = load_json_gz(file_path)

    if data:
        flattened = [entry.get("Event", {}).get("EventData", {}) for entry in data]
        df = pd.DataFrame(flattened)

        st.markdown("### 🔍 Add Filter(s) for EventData")
        if not df.empty:
            available_fields = df.columns.tolist()
            col_logic, col_add = st.columns([0.3, 0.7])
            with col_logic:
                logic_operator = st.radio("Filter Logic", ["AND", "OR"], horizontal=True, key="logic")
            with col_add:
                filter_count = st.selectbox("Number of filters", options=list(range(1, 6)), index=0, key="filter_count")

            filters = []
            for i in range(filter_count):
                cols = st.columns([0.3, 0.7])
                with cols[0]:
                    selected_field = st.selectbox(f"Field {i+1}", available_fields, key=f"field_{i}")
                with cols[1]:
                    search_term = st.text_input(f"Value {i+1}", key=f"value_{i}")
                filters.append((selected_field, search_term))

            if logic_operator == "AND":
                for field, term in filters:
                    if field and term:
                        df = df[df[field].astype(str).str.contains(term, case=False, na=False)]
            else:
                if any(term for _, term in filters):
                    or_conditions = pd.Series([False] * len(df))
                    for field, term in filters:
                        if field and term:
                            or_conditions |= df[field].astype(str).str.contains(term, case=False, na=False)
                    df = df[or_conditions]

        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records found for this selection.")
