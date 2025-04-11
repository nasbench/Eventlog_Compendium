import streamlit as st
import json
from sidebar import show_sidebar
from PIL import Image
from pathlib import Path
import pandas as pd

st.set_page_config(
    page_title="Event Field Decoder",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("images/EventLog-Compendium.ico")
)

show_sidebar()

st.title("🧮 Event Field Decoder")
st.markdown("""
This utility helps decode common Windows Security Event fields such as **Logon Types**, **Access Masks**, **Privileges**, **SIDs**, **GUIDs**, and **SACL/DACL rights**.
Choose a field type or let the tool auto-detect based on the input.
""")

FIELD_DICT_PATH = Path("data/event_field_lookup.json")
if not FIELD_DICT_PATH.exists():
    st.error("Field decoder dictionary not found.")
    st.stop()

with open(FIELD_DICT_PATH, "r", encoding="utf-8") as f:
    FIELD_DICTIONARIES = json.load(f)

custom_css = """
<style>
.card {
    background-color: #1E3A4C;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.05);
    margin-bottom: 10px;
    color: white;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.15);
}
.card h4 {
    margin: 0 0 5px 0;
}
.card p {
    margin: 2px 0;
    font-size: 14px;
}
.card .category {
    font-size: 13px;
    font-style: italic;
    color: #a0aec0;
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

def decode_field(field_type, value):
    results = []
    dictionary = FIELD_DICTIONARIES.get(field_type, {})

    if field_type == "access_mask":
        try:
            mask = int(value, 16) if value.startswith("0x") else int(value)
            exact_matches = []
            bitwise_matches = []

            for category, rights in dictionary.items():
                for name, info in rights.items():
                    right_value = int(info["Value"])
                    match_data = {
                        "Category": category,
                        "Hex": info["HexValue"],
                        "Name": name,
                        "Description": info["Description"]
                    }
                    if mask == right_value:
                        exact_matches.append(match_data)
                    elif mask & right_value:
                        bitwise_matches.append(match_data)

            if exact_matches:
                results.append("### ✅ Exact Match(es)")
                for match in exact_matches:
                    results.append(render_card(match))

            if bitwise_matches:
                results.append("### 🔹 Bitwise Matches (Rights included in mask)")
                for match in bitwise_matches:
                    if match not in exact_matches:
                        results.append(render_card(match))

            if not exact_matches and not bitwise_matches:
                results.append("🟡 No matches found for this access mask.")
        except:
            results.append("❌ Failed to parse the provided value as an access mask.")

    elif field_type == "privileges":
        match = dictionary.get(value)
        if match:
            results.append(render_card({
                "Name": value,
                "Description": match['Description'],
                "Category": match['user_right_group_policy_name']
            }))
        else:
            results.append("🟡 No privilege match found.")

    elif field_type == "logon_type":
        match = dictionary.get(value)
        if match:
            results.append(render_card({
                "Name": match,
                "Category": "Logon Type",
                "Description": f"Used when a user logs in using method #{value}."
            }))
        else:
            results.append("🟡 No logon type match found.")

    elif field_type == "sid":
        found = False
        for sid_type, sid_map in dictionary.items():
            match = sid_map.get(value)
            if match:
                results.append(render_card({
                    "Name": match['name'],
                    "Category": sid_type.replace("_", " ").title(),
                    "Description": match['description'],
                }))
                found = True
        if not found:
            results.append("🟡 No SID match found.")

    elif field_type == "active_directory_guids":
        match = None
        for category, guid_map in dictionary.items():
            if value.lower().replace("{", "").replace("}", "") in guid_map:
                match = {
                    "Name": guid_map[value.lower().replace("{", "").replace("}", "")],
                    "Category": category.replace("_", " ").title(),
                    "Hex": value.upper(),
                    "Description": "Active Directory GUID related permission."
                }
                break

    elif field_type == "audit_policy_guid":
        match = dictionary.get(value.upper().replace("{", "").replace("}", ""))
        if match:
            results.append(render_card({
                "Name": match,
                "Category": "Audit Policy GUID",
                "Description": f"{value.upper()}."
            }))
        else:
            results.append("🟡 No logon type match found.")

    return results

def render_card(data):
    name = f"<h4>{data.get('Name')}</h4>"
    category = f"<div class='category'>{data.get('Category')}</div>" if data.get("Category") else ""
    description = f"<p>{data.get('Description')}</p>" if data.get("Description") else ""
    hexval = f"<p><strong>Hex:</strong> {data.get('Hex')}</p>" if data.get("Hex") else ""
    return f"<div class='card'>{name}{category}{hexval}{description}</div>"

tab1, tab2 = st.tabs(["Decode Field", "Explore Data"])

with tab1:
    mode = st.radio("Select Mode:", ["Auto-Detect", "Manual"], horizontal=False, captions=["Try all field types to find any possible matches for your input.", "Select a specific field type to search within (e.g., Logon Type or Access Mask)."])
    input_value = st.text_input("Enter field value to decode:")

    FIELD_TYPE_LABELS = {
        "logon_type": "Logon Type",
        "access_mask": "Access Mask",
        "privileges": "Privileges",
        "sid": "Security Identifier (SID)",
        "active_directory_guids": "Active Directory GUID",
        "audit_policy_guid": "Audit Policy GUID",
    }

    if mode == "Manual":
        friendly_keys = [(k, FIELD_TYPE_LABELS.get(k, k.replace("_", " ").title())) for k in FIELD_DICTIONARIES.keys()]
        key_map = {label: key for key, label in friendly_keys}
        selected_label = st.selectbox("Field Type", [label for _, label in friendly_keys])
        selected_type = key_map[selected_label]

        if input_value:
            st.markdown("---")
            st.subheader("🔍 Decode Result")
            decoded = decode_field(selected_type, input_value)
            for d in decoded:
                st.markdown(d, unsafe_allow_html=True)

    else:
        if input_value:
            st.markdown("---")
            st.subheader("🔎 Auto Detection Results")
            found_any = False
            for field_type, dictionary in FIELD_DICTIONARIES.items():
                result = decode_field(field_type, input_value)
                if result:
                    found_any = True
                    label = FIELD_TYPE_LABELS.get(field_type, field_type.replace("_", " ").title())
                    st.markdown(f"#### {label}")
                    for r in result:
                        st.markdown(r, unsafe_allow_html=True)
            if not found_any:
                st.warning("No matches found across all field types.")
with tab2:
    st.subheader("📂 Explore Field Dictionaries")
    category_keys = list(FIELD_DICTIONARIES.keys())
    display_names = {k: FIELD_TYPE_LABELS.get(k, k.replace("_", " ").title()) for k in category_keys}
    selected_category = st.selectbox("Select a field category to explore:", [display_names[k] for k in category_keys])
    selected_key = [k for k, v in display_names.items() if v == selected_category][0]

    data = FIELD_DICTIONARIES[selected_key]

    if selected_key == "access_mask":
        rows = []
        for group, rights in data.items():
            for name, detail in rights.items():
                rows.append({"Category": group.replace("_", " ").title(), "Name": name, **detail})
        df = pd.DataFrame(rows)
    elif selected_key == "sid":
        rows = []
        for sid_type, entries in data.items():
            for sid, info in entries.items():
                rows.append({"SID Type": sid_type.replace("_", " ").title(), "SID": sid, "Name": info['name'], "Description": info['description']})
        df = pd.DataFrame(rows)
    elif selected_key == "privileges":
        df = pd.DataFrame([
            {"Privilege": k, "Description": v['Description'], "Group Policy Name": v['user_right_group_policy_name']}
            for k, v in data.items()
        ])
    elif selected_key == "active_directory_guids":
        res = []
        for k, v in data.items():
            for k_, v_ in v.items():
                res.append({"Type": k, "Name": v_ ,"GUID": k_})
        df = pd.DataFrame(res)
    elif selected_key == "audit_policy_guid":
        df = pd.DataFrame([{"Audit Policy": v, "Value": k} for k, v in data.items()])
    elif selected_key == "logon_type":
        df = pd.DataFrame([{"Logon Type": v, "Value": k} for k, v in data.items()])

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        sort_by = st.selectbox("Sort by column", df.columns.tolist(), index=0)
    with col2:
        search_term = st.text_input("Search (case-insensitive string match)", "")

    if search_term:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)]

    if sort_by:
        df = df.sort_values(by=sort_by)

    st.markdown(df.to_html(index=False, escape=False).replace("<th>", '<th style="text-align:center;">'), unsafe_allow_html=True)
