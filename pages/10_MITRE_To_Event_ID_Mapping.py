import streamlit as st
import json
import pandas as pd
import plotly.express as px
import re
from sidebar import show_sidebar

st.set_page_config(
    page_title="MITRE ATT&CK to Event ID Mapping Explorer",
    layout="wide",
    initial_sidebar_state="expanded"
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

st.title("🧭 MITRE ATT&CK to Event ID Mapping Explorer")

st.markdown("""
This page allows you to explore the mapping between Windows Event IDs and MITRE ATT&CK techniques and tactics.
You can view statistics, filter by technique, tactic, or Event ID, and inspect detailed audit mappings with messages.
""")

with open("data/eventid_mitre_mapping_by_technique.json", "r", encoding="utf-8") as f:
    mitre_by_technique = json.load(f)

with open("data/eventid_mitre_mapping_by_tactic.json", "r", encoding="utf-8") as f:
    mitre_by_tactic = json.load(f)

with open("data/eventid_message_mapping.json", "r", encoding="utf-8") as f:
    eventid_messages = json.load(f)

def prettify_tactic(t: str) -> str:
    return t.replace("-", " ").title()

tactic_label_to_key = {prettify_tactic(t): t for t in mitre_by_tactic.keys()}

tab1, tab2 = st.tabs(["Statistics", "Explore Mappings"])

with tab2:
    st.markdown("### Filter Options")

    col1, col2, col3 = st.columns([0.33, 0.33, 0.34])

    with col1:
        mitre_technique_options = [
            f"{tid} - {data['technique']} [{', '.join(data['tactics'])}]"
            for tid, data in mitre_by_technique.items()
        ]
        selected_techniques = st.multiselect("Select Technique(s)", mitre_technique_options)

    with col2:
        tactic_labels = sorted(tactic_label_to_key.keys())
        selected_tactic_labels = st.multiselect("Select Tactic(s)", tactic_labels)
        selected_tactics = [tactic_label_to_key[label] for label in selected_tactic_labels]

    with col3:
        event_id_filter = st.text_input("🔢 Filter by Event ID", placeholder="e.g. 4688")
        search_query = st.text_input("🔍 Search (Technique, Sub-Category...)", placeholder="Search table text")

    # Apply filters
    filtered_mappings = []

    if selected_techniques:
        for label in selected_techniques:
            tid = re.match(r"^(T\d{4,5})", label).group(1)
            if tid in mitre_by_technique:
                for m in mitre_by_technique[tid]["mappings"]:
                    m["technique_id"] = tid
                    m["technique"] = mitre_by_technique[tid]["technique"]
                    m["tactics"] = mitre_by_technique[tid]["tactics"]
                    filtered_mappings.append(m)

    elif selected_tactics:
        for tactic in selected_tactics:
            for m in mitre_by_tactic[tactic]["mappings"]:
                m["tactic"] = tactic
                filtered_mappings.append(m)

    else:
        for tid, data in mitre_by_technique.items():
            for m in data["mappings"]:
                m["technique_id"] = tid
                m["technique"] = data["technique"]
                m["tactics"] = data["tactics"]
                filtered_mappings.append(m)

    # Convert to DataFrame
    df = pd.DataFrame(filtered_mappings)

    # Add tactic column
    if "tactic" not in df.columns and not df.empty:
        df["tactic"] = df["tactics"].apply(lambda x: prettify_tactic(x[0]) if isinstance(x, list) and x else "N/A")

    # Add event message
    if not df.empty:
        df["message"] = df["event_id"].astype(str).map(eventid_messages).fillna("N/A")

    # Apply Event ID filter
    if event_id_filter:
        df = df[df["event_id"].astype(str).str.contains(event_id_filter.strip())]

    # Apply Search filter
    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    if not df.empty:
        st.markdown(f"### Mapped Events ({len(df)} rows)")

        # Reorder and format columns
        display_df = df[[
            "tactic", "technique_id", "technique", "audit_category", "audit_sub_category", "event_id", "message"
        ]].copy()

        # Make event ID clickable
        display_df["event_id"] = display_df["event_id"].apply(
            lambda eid: f'<a href="EventID_Lookup?event_id={eid}&provider=Microsoft-Security-Auditing" target="_blank">{eid}</a>'
        )

        # Export full filtered data (not paginated)
        export_df = df[[
            "tactic", "technique_id", "technique", "audit_category", "audit_sub_category", "event_id", "message"
        ]]

        col_1, col_2, col_3 = st.columns([0.33, 0.33, 0.3])
        
        with col_3:
            csv = export_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export to CSV", csv, "filtered_mitre_mappings.csv", "text/csv", use_container_width=True)

        # --- Pagination State Setup ---
        if "page_size" not in st.session_state:
            st.session_state["page_size"] = 25
        if "page_number" not in st.session_state:
            st.session_state["page_number"] = 1

        batch_size = st.session_state["page_size"]
        total_pages = (len(display_df) - 1) // batch_size + 1
        # Ensure current page is within bounds:
        if st.session_state["page_number"] > total_pages:
            st.session_state["page_number"] = total_pages
        current_page = st.session_state["page_number"]

        # --- Compute the Paginated Table ---
        start = (current_page - 1) * batch_size
        end = start + batch_size
        page_df = display_df.iloc[start:end]

        page_df.columns = [col.replace("_", " ").title() for col in page_df.columns]

        table_html = page_df.to_html(escape=False, index=False).replace("<th>", '<th style="text-align:center;">')
        st.markdown(table_html, unsafe_allow_html=True)

        # --- Pagination Controls (Rendered Below the Table) ---
        pag_col1, pag_col2, pag_col3 = st.columns((4, 1, 1))
        # "Rows per page" control:
        new_batch_size = pag_col3.selectbox(
            "Rows per page", options=[10, 25, 50, 100],
            index=[10, 25, 50, 100].index(batch_size),
            key="page_size_bottom"
        )
        if new_batch_size != st.session_state["page_size"]:
            st.session_state["page_size"] = new_batch_size
            st.session_state["page_number"] = 1
            st.rerun()

        # Recalculate total pages in case batch size changed
        total_pages = (len(display_df) - 1) // st.session_state["page_size"] + 1

        # "Page" control:
        new_current_page = pag_col2.number_input(
            "Page", min_value=1, max_value=total_pages,
            value=current_page, step=1,
            key="page_number_bottom"
        )
        if new_current_page != st.session_state["page_number"]:
            st.session_state["page_number"] = new_current_page
            st.rerun()

        pag_col1.markdown(f"Page **{st.session_state['page_number']}** of **{total_pages}**")


    else:
        st.warning("No mappings match your filters or search query.")

with tab1:
    st.markdown("### Visualize Mapping Coverage")
    # Flatten all mappings
    all_mappings = []
    for tid, data in mitre_by_technique.items():
        for m in data["mappings"]:
            all_mappings.append({
                "technique_id": tid,
                "technique": data["technique"],
                "audit_category": m["audit_category"],
                "audit_sub_category": m["audit_sub_category"],
                "event_id": m["event_id"]
            })

    full_df = pd.DataFrame(all_mappings)

    if not full_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            cat_counts = full_df["audit_category"].value_counts().reset_index()
            cat_counts.columns = ["Audit Category", "Count"]
            fig = px.bar(cat_counts, x="Audit Category", y="Count", title="Top Audit Categories (by Mapping Count)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            subcat_counts = full_df["audit_sub_category"].value_counts().reset_index()
            subcat_counts.columns = ["Audit Sub-Category", "Count"]
            fig = px.bar(subcat_counts.head(15), x="Audit Sub-Category", y="Count", title="Top Audit Sub-Categories")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Event ID Coverage (Top 10 by Technique Count)")
        pie_data = full_df.groupby("event_id")["technique_id"].nunique().reset_index()
        pie_data.columns = ["Event ID", "Technique Count"]
        pie_data = pie_data.sort_values("Technique Count", ascending=False)

        fig = px.pie(pie_data.head(10), names="Event ID", values="Technique Count", title="Top 10 Event IDs by Technique Coverage")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No data available for visualization.")
