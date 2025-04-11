import streamlit as st

def show_sidebar():
    """Custom sidebar navigation with icons."""
    
    with st.sidebar:
        
        st.sidebar.title("📜 Eventlog Compendium", help="")

        st.sidebar.page_link("Eventlog_Compendium.py", label="🔹 Home")
        
        #st.markdown("---")

        st.sidebar.title("🪟 Audit Policy Toolkit", help="Work with Windows Advanced Audit Policy settings and mappings.")

        st.sidebar.page_link("pages/1_Advanced_Audit_Policy_Documentation.py", label="🔹Advanced Audit Policy Documentation")
        st.sidebar.page_link("pages/2_Advanced_Audit_Policy_Generator.py", label="🔹Advanced Audit Policy Generator")
        st.sidebar.page_link("pages/5_Audit_Policy_To_Event_ID_Mapping.py", label="🔹Audit Policy to Event ID Mapping")
        st.sidebar.page_link("pages/10_MITRE_To_Event_ID_Mapping.py", label="🔹 MITRE ATT&CK to Event ID Mapping Explorer")
        
        #st.markdown("---")

        st.sidebar.title("🧠 Sysmon Toolkit", help=".")

        st.sidebar.page_link("pages/6_Sysmon_Configuration_Builder.py", label="🔹 Sysmon Configuration Builder")

        #st.markdown("---")

        st.sidebar.title("🪵 Event Log Tools", help="Utilities to explore and analyze Windows Event Logs and Event Trace Providers.")
        
        st.sidebar.page_link("pages/3_EventID_Lookup.py", label="🔹Event ID Lookup")
        st.sidebar.page_link("pages/4_ETW_Providers_Visualizer.py", label="🔹 ETW Providers Visualizer")
        st.sidebar.page_link("pages/7_EVTX_Baseline_Search.py", label="🔹EVTX Baseline Search")
        st.sidebar.page_link("pages/8_Event_Field_Decoder.py", label="🔹 Event Field Decoder")
        st.sidebar.page_link("pages/9_Built-In_SACL_Explorer.py", label="🔹 Built-In SACL Explorer")

        st.markdown("<hr style='border-top: 4px solid #bbb;'>", unsafe_allow_html=True)