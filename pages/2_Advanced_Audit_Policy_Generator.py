import streamlit as st
import pandas as pd
import json
from sidebar import show_sidebar
from PIL import Image
import re

st.set_page_config(
    page_title="Advanced Audit Policy Generator",
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
            table-layout: fixed;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border: 1px solid #ddd;
            word-wrap: break-word;
            white-space: normal;
        }
        th {
            background-color: #2E3B4E;
            color: white;
            text-align: left;
        }
        .success {
            background: rgba(76, 175, 80, 0.15);
            color: #2E7D32;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 5px;
            text-align: center;
        }
        .failure {
            background: rgba(244, 67, 54, 0.15);
            color: #C62828;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 5px;
            text-align: center;
        }
        .both {
            background: rgba(255, 193, 7, 0.15);
            color: #FF8F00;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 5px;
            text-align: center;
        }
        .na {
            background: rgba(150, 150, 150, 0.15);
            color: #6c757d;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 5px;
            text-align: center;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("⚙️ Advanced Audit Policy Generator")

selected_tab = st.radio(
    "Select Mode:", 
    ["Generate Custom Recommendation", "Prebuilt Recommendations"], 
    horizontal=True
)

def add_explanation(reasons_dict, explanation_lines, selected_roles, selected_windows_features, selected_detection_frameworks):

    explanation_lines.append("#### System Type")
    if reasons_dict["Client"]:
        explanation_lines.append("- This recommendation is tailored for **end-user systems**, focusing on audit events relevant to workstation activity like process creation and logon events.")
    elif reasons_dict["Server"]:
        explanation_lines.append("- Audit settings include broader coverage for **server-specific services**, with focus on account usage, service access, and directory activities.")

    if selected_roles:
        explanation_lines.append("#### Server Roles")

    if reasons_dict["ADCS"]:
        explanation_lines.append("- **Active Directory Certification Services (AD CS)**")
        explanation_lines.append("  - Audit policies include certificate issuance and template usage to detect misuse of certificate authority services.")

    if reasons_dict["ADDS"]:
        explanation_lines.append("- **Active Directory Domain Services (AD DS)**")
        explanation_lines.append("  - Enables auditing of Kerberos activity, replication events, and directory object changes to enhance visibility into domain activity.")

    if reasons_dict["AzMan"]:
        explanation_lines.append("- **Authorization Manager (AzMan)**")
        explanation_lines.append("  - Tracks changes to application groups and custom roles for environments using delegated access control via AzMan.")

    if reasons_dict["NPS"]:
        explanation_lines.append("- **Network Policy Server (NPS)**")
        explanation_lines.append("  - Auditing includes RADIUS events, policy evaluations, and access attempts related to NPS configurations.")

    if selected_windows_features:
        explanation_lines.append("#### Windows Features or Functionality")

    if reasons_dict["IPSec"]:
        explanation_lines.append("- **IPSec Logging Enabled**")
        explanation_lines.append("  - Includes auditing of Main Mode, Quick Mode, and Extended Mode negotiations to detect and troubleshoot encrypted network tunnels.")

    if reasons_dict["RPCServer"]:
        explanation_lines.append("- **RPC Server Auditing Enabled**")
        explanation_lines.append("  - Allows detection of abnormal or suspicious remote procedure calls which are often involved in lateral movement or remote service abuse.")

    if selected_detection_frameworks:
        explanation_lines.append("#### Detection Framework")
        
    if reasons_dict["Sigma"]:
        explanation_lines.append("- **SigmaHQ Mapping**")
        explanation_lines.append("  - Sub-categories were selected to ensure compatibility with Sigma Detection rules, improving detection coverage across common TTPs.")

    if reasons_dict["Elastic"]:
        explanation_lines.append("- **Elastic Detection Rules Compatibility**")
        explanation_lines.append("  - Sub-categories were selected to ensure compatibility with Elastic Detection rules, improving detection coverage across common TTPs.")

    if reasons_dict["Splunk"]:
        explanation_lines.append("- **Splunk Security Content Integration**")
        explanation_lines.append("  - Sub-categories were selected to ensure compatibility with Splunk Security Content, improving detection coverage across common TTPs.")

    explanation_lines.append("#### Complexity")
    if reasons_dict["ComplexityHigh"]:
        explanation_lines.append("- **High Complexity Chosen**")
        explanation_lines.append("  - All recommended audit policies were enabled, including those requiring additional configuration like registry edits or SACL configurations.")

    elif reasons_dict["ComplexityMedium"]:
        explanation_lines.append("- **Medium Complexity Chosen**")
        explanation_lines.append("  - Audit settings were chosen to balance coverage and ease of configuration. Some categories requiring deeper system changes were omitted such as \"Registry\" or \"Kernel Object\".")

    elif reasons_dict["ComplexityLow"]:
        explanation_lines.append("- **Low Complexity Chosen**")
        explanation_lines.append("  - Certain categories like **Removable Storage**, **Registry**, or **Kernel Object** were disabled to avoid complex setup.")
        explanation_lines.append("  - Only audit settings that can be easily enabled via `auditpol` without advanced configuration were selected.")

    explanation_lines.append("#### Log Volume")
    if reasons_dict["VolumeVeryHigh"]:
        explanation_lines.append("- **Very High Volume Enabled**")
        explanation_lines.append("  - All relevant audit categories were enabled, maximizing log coverage but generating a large volume of events.")
        explanation_lines.append("  - Suitable for environments with robust log storage and analysis pipelines.")

    elif reasons_dict["VolumeHigh"]:
        explanation_lines.append("- **High Volume Selected**")
        explanation_lines.append("  - Most audit categories are enabled. Only extremely noisy or redundant sub-categories were excluded.")

    elif reasons_dict["VolumeMedium"]:
        explanation_lines.append("- **Medium Volume Selected**")
        explanation_lines.append("  - Balanced selection to retain key audit events while reducing overhead. Verbose and niche audit areas were excluded.")

    elif reasons_dict["VolumeLow"]:
        explanation_lines.append("- **Low Volume Selected**")
        explanation_lines.append("  - Designed for performance-sensitive environments. Only essential audit logs are collected, omitting high-noise sub-categories like **SAM**, **Handle Manipulation**, and **IPSec logs**.")

    if reasons_dict["Mitre"]:
        explanation_lines.append("#### MITRE ATT&CK Mapping")
        explanation_lines.append("- Audit categories were chosen to match detection coverage for the selected MITRE techniques or tactics.")
        explanation_lines.append("- Sub-categories map directly to specific adversary behaviors, aiding in threat detection and investigation.")
        explanation_lines.append("- Visit [MITRE ATT&CK to Event ID Mapping Explorer](/MITRE_To_Event_ID_Mapping).")

    return explanation_lines

def complexity_config(complexity_level, updated_policies_json):
    # 1: Low
    # 2: Medium
    # 3: High

    if volume_level == 0:
        return "ERROR"
    
    if complexity_level == 2:
        updated_policies_json["Object Access"]["File System"] = "N/A"
        updated_policies_json["Object Access"]["Kernel Object"] = "N/A"
        updated_policies_json["Object Access"]["Other Object Access Events"] = "N/A"
        updated_policies_json["Object Access"]["Registry"] = "N/A"
    elif complexity_level == 1:
        updated_policies_json["Object Access"]["Removable Storage"] = "N/A"
    
    return updated_policies_json

def volume_config(volume_level, system_type, selected_roles, selected_windows_features, updated_policies_json):
    # 1: Low
    # 2: Medium
    # 3: High
    # 4: Very High

    if volume_level == 0:
        return "ERROR"
    else:
        # High
        if volume_level == 3:
            updated_policies_json["Object Access"]["Handle Manipulation"] = "N/A"
            if system_type == "Server":
                if "Active Directory Domain Services (AD DS)" in selected_roles:
                    updated_policies_json["Account Logon"]["Kerberos Service Ticket Operations"] = "N/A"
                    updated_policies_json["DS Access"]["Detailed Directory Service Replication"] = "N/A"
                    updated_policies_json["Account Logon"]["Credential Validation"] = "N/A"
        # Medium
        elif volume_level == 3:
            # We should also disable the same thing we did in High as its lower (in the future I will fix this into smaller functions)
            updated_policies_json["Object Access"]["Handle Manipulation"] = "N/A"
            updated_policies_json["Detailed Tracking"]["Token Right Adjusted"] = "N/A"
            updated_policies_json["Object Access"]["Filtering Platform Connection"] = "N/A"
            updated_policies_json["Object Access"]["Filtering Platform Packet Drop"] = "N/A"
            updated_policies_json["Privilege Use"]["Non Sensitive Privilege Use"] = "N/A"
            updated_policies_json["Object Access"]["SAM"] = "N/A"

            if "RPC Server" in selected_windows_features:
                updated_policies_json["Detailed Tracking"]["RPC Events"] = "N/A"
            
            if "IPSec" in selected_windows_features:
                updated_policies_json["Logon/Logoff"]["IPsec Extended Mode"] = "N/A"
                updated_policies_json["Logon/Logoff"]["IPsec Main Mode"] = "N/A"
                updated_policies_json["Logon/Logoff"]["IPsec Quick Mode"] = "N/A"

            if system_type == "Server":
                if "Active Directory Domain Services (AD DS)" in selected_roles:
                    updated_policies_json["Account Logon"]["Kerberos Service Ticket Operations"] = "N/A"
                    updated_policies_json["Account Logon"]["Kerberos Authentication Service"] = "N/A"
                    updated_policies_json["DS Access"]["Directory Service Access"] = "N/A"
                    updated_policies_json["DS Access"]["Directory Service Changes"] = "N/A"
                    updated_policies_json["Account Logon"]["Credential Validation"] = "N/A"
                    updated_policies_json["DS Access"]["Detailed Directory Service Replication"] = "N/A"
                    updated_policies_json["Object Access"]["Detailed File Share"] = "N/A"
                    updated_policies_json["Object Access"]["File Share"] = "N/A"
                if "Network Policy Server (NPS)" in selected_roles:
                    updated_policies_json["Logon/Logoff"]["Network Policy Server"] = "N/A"
        # Low
        else:
            # We should also disable the same thing we did in High & medium as its lower (in the future I will fix this into smaller functions)
            
            updated_policies_json["Detailed Tracking"]["Process Creation"] = "N/A"
            updated_policies_json["Object Access"]["Handle Manipulation"] = "N/A"
            updated_policies_json["Detailed Tracking"]["Token Right Adjusted"] = "N/A"
            updated_policies_json["Object Access"]["Filtering Platform Connection"] = "N/A"
            updated_policies_json["Object Access"]["Filtering Platform Packet Drop"] = "N/A"
            updated_policies_json["Privilege Use"]["Non Sensitive Privilege Use"] = "N/A"
            updated_policies_json["Object Access"]["SAM"] = "N/A"
            updated_policies_json["System"]["Security System Extension"] = "N/A"

            if "RPC Server" in selected_windows_features:
                updated_policies_json["Detailed Tracking"]["RPC Events"] = "N/A"
            
            if "IPSec" in selected_windows_features:
                updated_policies_json["Logon/Logoff"]["IPsec Extended Mode"] = "N/A"
                updated_policies_json["Logon/Logoff"]["IPsec Main Mode"] = "N/A"
                updated_policies_json["Logon/Logoff"]["IPsec Quick Mode"] = "N/A"
                updated_policies_json["System"]["IPsec Driver"] = "N/A"

            if system_type == "Server":
                updated_policies_json["Logon/Logoff"]["Group Membership"] = "N/A"
                updated_policies_json["Logon/Logoff"]["Logon"] = "N/A"
                updated_policies_json["Logon/Logoff"]["Special Logon"] = "N/A"
                updated_policies_json["Logon/Logoff"]["User/Device Claims"] = "N/A"

                if "Active Directory Domain Services (AD DS)" in selected_roles:
                    updated_policies_json["Account Logon"]["Kerberos Service Ticket Operations"] = "N/A"
                    updated_policies_json["Account Logon"]["Kerberos Authentication Service"] = "N/A"
                    updated_policies_json["Account Logon"]["Credential Validation"] = "N/A"
                    updated_policies_json["DS Access"]["Directory Service Access"] = "N/A"
                    updated_policies_json["DS Access"]["Directory Service Changes"] = "N/A"
                    updated_policies_json["DS Access"]["Detailed Directory Service Replication"] = "N/A"
                    updated_policies_json["DS Access"]["Directory Service Replication"] = "N/A" 
                    updated_policies_json["Object Access"]["Detailed File Share"] = "N/A"
                    updated_policies_json["Object Access"]["File Share"] = "N/A"     
                if "Network Policy Server (NPS)" in selected_roles:
                    updated_policies_json["Logon/Logoff"]["Network Policy Server"] = "N/A"
                if "Active Directory Certification Services (AD CS)" in selected_roles:
                    updated_policies_json["Object Access"]["Certification Services"] = "N/A"

    return updated_policies_json

def load_prebuilt_recommendations():
    with open("data/prebuilt_audit_policy_recommendations.json", "r", encoding="utf-8") as f:
        return json.load(f)
    
with open("data/eventid_mitre_mapping_by_technique.json", "r", encoding="utf-8") as f:
    mitre_by_technique = json.load(f)

with open("data/eventid_mitre_mapping_by_tactic.json", "r", encoding="utf-8") as f:
    mitre_by_tactic = json.load(f)


prebuilt_policies = load_prebuilt_recommendations()

with open("data/default_audit_policy_template.json", "r", encoding="utf-8") as f:
    default_policies_json = json.load(f)

with st.sidebar:
    if selected_tab == "Generate Custom Recommendation":
        st.title("🔧 Customize Audit Policy")

        system_type = st.selectbox(
            "Select System Type", 
            ["Server", "Client"], 
            help="Choose whether you are configuring a server or a client system."
        )

        role_placeholder = st.empty()

        if system_type == "Server":
            available_roles = ["Active Directory Certification Services (AD CS)", "Active Directory Domain Services (AD DS)", "Authorization Manager (AzMan)", "Network Policy Server (NPS)"]
            selected_roles = role_placeholder.multiselect(
                "Select Roles/Features", 
                available_roles,
                help="Choose specific server roles/features to tailor audit policies accordingly."
            )
        else:
            selected_roles = []

        selected_windows_features = st.multiselect(
            "Select a Windows Feature / Functionality",
            ["IPSec", "RPC Server"],
            help="Choose specific windows feature or functionality to tailor audit policies accordingly."
        )

        selected_detection_frameworks = st.multiselect(
            "Select Detection Framework(s)",
            ["Elastic Detection Rules", "Splunk Security Content", "SigmaHQ Detection Rules"],
            help="Choose which detection content this policy should align with."
        )

        complexity_level = st.selectbox(
            "Select Complexity Level",
            ["Low", "Medium", "High"],
            help="Controls to what level are you comfortable configuring additional setting to make certain audit sub-categories work. Higher complexity = more difficulty to set up"
        )

        volume_level = st.selectbox(
            "Select Log Volume Preference",
            ["Low", "Medium", "High", "Very High"],
            help="Adjusts the audit settings to balance between coverage and event log size."
        )

        # Helper to prettify tactic labels
        def prettify_tactic(tactic_key: str) -> str:
            return tactic_key.replace("-", " ").title()

        # Build pretty label ↔ key mapping for tactics
        tactic_label_to_key = {
            prettify_tactic(t): t for t in mitre_by_tactic.keys()
        }

        mitre_selection_mode = st.radio(
            "Select by:",
            ["Technique", "Tactic"],
            horizontal=True
        )

        # Technique-based selection
        if mitre_selection_mode == "Technique":
            mitre_technique_options = [
                f"{tid} - {data['technique']}"
                for tid, data in mitre_by_technique.items()
            ]
            selected_mitre_techniques = st.multiselect(
                "Select Techniques",
                mitre_technique_options,
                help="Choose specific MITRE techniques to influence audit policy selection."
            )
            selected_mitre_tactic_labels = []
            selected_mitre_tactics = []

        # Tactic-based selection (with prettified labels)
        else:
            mitre_tactic_options = sorted(tactic_label_to_key.keys())  # Prettified
            selected_mitre_tactic_labels = st.multiselect(
                "Select Tactics",
                mitre_tactic_options,
                help="Choose one or more MITRE tactics to apply related techniques."
            )
            selected_mitre_tactics = [tactic_label_to_key[label] for label in selected_mitre_tactic_labels]
            selected_mitre_techniques = []


        if st.button("⚙️ Generate Recommendation"):
            with st.spinner("Generating recommendations..."):
                updated_policies_json = json.loads(json.dumps(default_policies_json))
                explanation_lines = []

                reasons_dict = {
                    "Client": False,
                    "Server": False,
                    "ADCS": False,
                    "ADDS": False,
                    "AzMan": False,
                    "NPS": False,
                    "IPSec": False,
                    "RPCServer": False,
                    "Sigma": False,
                    "Elastic": False,
                    "Splunk": False,
                    "ComplexityHigh": False,
                    "ComplexityMedium": False,
                    "ComplexityLow": False,
                    "VolumeVeryHigh": False,
                    "VolumeHigh": False,
                    "VolumeMedium": False,
                    "VolumeLow": False,
                    "Mitre": False,
                }

                if system_type == "Server":
                    updated_policies_json["Detailed Tracking"]["Process Creation"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Logon Success"] = "Success, Failure"
                    updated_policies_json["Account Management"]["User Account Change"] = "Success, Failure"
                    reasons_dict["Server"] = True

                    if "Active Directory Domain Services (AD DS)" in selected_roles:
                        updated_policies_json["Account Logon"]["Kerberos Authentication Service"] = "Success, Failure"
                        updated_policies_json["Account Logon"]["Kerberos Service Ticket Operations"] = "Success, Failure"
                        updated_policies_json["DS Access"]["Detailed Directory Service Replication"] = "Success, Failure"
                        updated_policies_json["DS Access"]["Directory Service Access"] = "Success, Failure"
                        updated_policies_json["DS Access"]["Directory Service Changes"] = "Success" # Contains only Success events
                        updated_policies_json["DS Access"]["Directory Service Replication"] = "Success, Failure"
                        reasons_dict["ADDS"] = True

                    if "Active Directory Certification Services (AD CS)" in selected_roles:
                        updated_policies_json["Object Access"]["Certification Services"] = "Success, Failure"
                        reasons_dict["ADCS"] = True
                    
                    if "Authorization Manager (AzMan)" in selected_roles:
                        updated_policies_json["Object Access"]["Application Generated"] = "Success, Failure"
                        updated_policies_json["Account Management"]["Application Group Management"] = "Success, Failure"
                        reasons_dict["AzMan"] = True
                    
                    if "Network Policy Server (NPS)" in selected_roles:
                        updated_policies_json["Logon/Logoff"]["Network Policy Server"] = "Success, Failure"
                        reasons_dict["NPS"] = True

                elif system_type == "Client":
                    updated_policies_json["Detailed Tracking"]["Process Creation"] = "Success, Failure"
                    reasons_dict["Client"] = True

                # Windows Features / Functionalities
                if "IPSec" in selected_windows_features:
                    updated_policies_json["Logon/Logoff"]["IPsec Extended Mode"] = "Success" # Contains Only Success Events
                    updated_policies_json["Logon/Logoff"]["IPsec Main Mode"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["IPsec Quick Mode"] = "Success, Failure"
                    updated_policies_json["System"]["IPsec Driver"] = "Success, Failure"
                    reasons_dict["IPSec"] = True
                
                if "RPC Server"in selected_windows_features:
                    updated_policies_json["Detailed Tracking"]["RPC Events"] = "N/A"
                    reasons_dict["RPCServer"] = True


                # Detection Coverage
                if "SigmaHQ Detection Rules" in selected_detection_frameworks:
                    updated_policies_json["Account Logon"]["Credential Validation"] = "Success, Failure"
                    updated_policies_json["Account Logon"]["Kerberos Authentication Service"] = "Success, Failure"
                    updated_policies_json["Account Logon"]["Kerberos Service Ticket Operations"] = "Success, Failure"
                    updated_policies_json["Account Management"]["Computer Account Management"] = "Success, Failure"
                    updated_policies_json["Account Management"]["Security Group Management"] = "Success" # Contains Only Success Events 
                    updated_policies_json["Account Management"]["User Account Management"] = "Success, Failure"
                    updated_policies_json["Detailed Tracking"]["DPAPI Activity"] = "Success, Failure"
                    updated_policies_json["Detailed Tracking"]["PNP Activity"] = "Success" # Contains Only Success Events
                    updated_policies_json["Detailed Tracking"]["Process Creation"] = "Success" # Contains Only Success Events
                    updated_policies_json["DS Access"]["Directory Service Access"] = "Success, Failure"
                    updated_policies_json["DS Access"]["Directory Service Changes"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Logoff"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Logon"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Other Logon/Logoff Events"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Special Logon"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Certification Services"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Detailed File Share"] = "Success, Failure"
                    updated_policies_json["Object Access"]["File Share"] = "Success, Failure"
                    updated_policies_json["Object Access"]["File System"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Filtering Platform Connection"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Kernel Object"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Other Object Access Events"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Registry"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Removable Storage"] = "Success, Failure"
                    updated_policies_json["Object Access"]["SAM"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Audit Policy Change"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Authentication Policy Change"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Authorization Policy Change"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Filtering Platform Policy Change"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Other Policy Change Events"] = "Success, Failure"
                    updated_policies_json["Privilege Use"]["Sensitive Privilege Use"] = "Success, Failure"
                    updated_policies_json["System"]["Other System Events"] = "Success, Failure"
                    updated_policies_json["System"]["Security State Change"] = "Success, Failure"
                    updated_policies_json["System"]["Security System Extension"] = "Success, Failure"
                    updated_policies_json["System"]["System Integrity"] = "Success, Failure"
                    reasons_dict["Sigma"] = True
                if "Elastic Detection Rules" in selected_detection_frameworks:
                    updated_policies_json["Account Management"]["Security Group Management"] = "Success, Failure"
                    updated_policies_json["Account Management"]["User Account Management"] = "Success, Failure"
                    updated_policies_json["Detailed Tracking"]["Process Creation"] = "Success, Failure"
                    updated_policies_json["Detailed Tracking"]["Token Right Adjusted"] = "Success" # Contains Only Success Events
                    updated_policies_json["DS Access"]["Directory Service Access"] = "Success, Failure"
                    updated_policies_json["DS Access"]["Directory Service Changes"] = "Success" # Contains Only Success Events
                    updated_policies_json["Logon/Logoff"]["Logon"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Special Logon"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Detailed File Share"] = "Success, Failure"
                    updated_policies_json["Object Access"]["File System"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Filtering Platform Connection"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Filtering Platform Packet Drop"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Other Object Access Events"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Audit Policy Change"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Authorization Policy Change"] = "Success, Failure"
                    updated_policies_json["System"]["Other System Events"] = "Success, Failure"
                    updated_policies_json["System"]["Security System Extension"] = "Success, Failure"
                    reasons_dict["Elastic"] = True
                if "Splunk Security Content" in selected_detection_frameworks:
                    updated_policies_json["Account Logon"]["Credential Validation"] = "Success, Failure"
                    updated_policies_json["Account Logon"]["Kerberos Authentication Service"] = "Success, Failure"
                    updated_policies_json["Account Logon"]["Kerberos Service Ticket Operations"] = "Success, Failure"
                    updated_policies_json["Account Management"]["Application Group Management"] = "Success, Failure"
                    updated_policies_json["Account Management"]["Computer Account Management"] = "Success" # Contains Only Success Events
                    updated_policies_json["Account Management"]["Distribution Group Management"] = "Success" # Contains Only Success Events
                    updated_policies_json["Account Management"]["Security Group Management"] = "Success, Failure"
                    updated_policies_json["Account Management"]["User Account Management"] = "Success, Failure"
                    updated_policies_json["Detailed Tracking"]["Process Creation"] = "Success, Failure"
                    updated_policies_json["Detailed Tracking"]["Token Right Adjusted"] = "Success, Failure"
                    updated_policies_json["DS Access"]["Directory Service Access"] = "Success, Failure"
                    updated_policies_json["DS Access"]["Directory Service Changes"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Group Membership"] = "Success" # Contains Only Success Events
                    updated_policies_json["Logon/Logoff"]["Logon"] = "Success, Failure"
                    updated_policies_json["Logon/Logoff"]["Special Logon"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Certification Services"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Detailed File Share"] = "Success, Failure"
                    updated_policies_json["Object Access"]["File Share"] = "Success, Failure"
                    updated_policies_json["Object Access"]["File System"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Other Object Access Events"] = "Success, Failure"
                    updated_policies_json["Object Access"]["Registry"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Audit Policy Change"] = "Success, Failure"
                    updated_policies_json["Policy Change"]["Authorization Policy Change"] = "Success, Failure"
                    reasons_dict["Splunk"] = True

                # MITRE ATT&CK Coverage
                if selected_mitre_techniques or selected_mitre_tactics:
                    
                    reasons_dict['Mitre'] = True
                    
                    # --- Technique-Based Selection ---
                    for label in selected_mitre_techniques:
                        tid = re.match(r"^(T\d{4,5})", label).group(1)
                        data = mitre_by_technique[tid]
                        for mapping in data["mappings"]:
                            category = mapping["audit_category"]
                            subcat = mapping["audit_sub_category"]
                            if category in updated_policies_json and subcat in updated_policies_json[category]:
                                updated_policies_json[category][subcat] = "Success, Failure"

                    # --- Tactic-Based Selection ---
                    for tactic in selected_mitre_tactics:
                        data = mitre_by_tactic[tactic]
                        for mapping in data["mappings"]:
                            category = mapping["audit_category"]
                            subcat = mapping["audit_sub_category"]
                            if category in updated_policies_json and subcat in updated_policies_json[category]:
                                updated_policies_json[category][subcat] = "Success, Failure"

                # Complexity
                if complexity_level == "High":
                    reasons_dict['ComplexityHigh'] = True
                    complexity_level = 3
                elif complexity_level == "Medium":
                    reasons_dict['ComplexityMedium'] = True
                    complexity_level = 2
                elif complexity_level == "Low":
                    reasons_dict['ComplexityLow'] = True
                    complexity_level = 1
                else:
                    complexity_level = 0

                updated_policies_json = complexity_config(complexity_level, updated_policies_json)

                # Log Volume
                if volume_level == "Very High":
                    reasons_dict['VolumeVeryHigh'] = True
                    volume_level = 4 
                elif volume_level == "High":
                    reasons_dict['VolumeHigh'] = True
                    volume_level = 3
                elif volume_level == "Medium":
                    reasons_dict['VolumeMedium'] = True
                    volume_level = 2
                elif volume_level == "Low":
                    reasons_dict['VolumeLow'] = True
                    volume_level = 1
                else:
                    volume_level = 0
                
                updated_policies_json = volume_config(volume_level, system_type, selected_roles, selected_windows_features, updated_policies_json)

                explanation_lines = add_explanation(reasons_dict, explanation_lines, selected_roles, selected_windows_features, selected_detection_frameworks)

                explanation_lines.append("")
                explanation_lines.append("")
                explanation_lines.append("👉 To apply this recommendation, download the generated batch script below.")

                st.session_state.generated_policies = updated_policies_json
                st.session_state.recommendation_explanation = "\n".join(explanation_lines)
                st.success("✅ Recommendations generated successfully!")

    elif selected_tab == "Prebuilt Recommendations":
        st.title("📜 Prebuilt Policy Selection")
        st.markdown("""
            Prebuilt audit policies are pre-configured recommendations based on best practices.  
            Select one from the dropdown to view its recommended settings.
        """)
        selected_profile = st.selectbox("Select a Pre-Built Policy", list(prebuilt_policies.keys()))
        selected_policy_data = prebuilt_policies[selected_profile]

CATEGORY_EMOJIS = {
    "Account Logon": "🔐",
    "Account Management": "👤",
    "Detailed Tracking": "📍",
    "DS Access": "📁",
    "Logon/Logoff": "🔑",
    "Object Access": "🧱",
    "Policy Change": "📜",
    "Privilege Use": "🛡️",
    "System": "🖥️"
}

def render_category_tables(policies):
    for category, subcategories in policies.items():
        emoji = CATEGORY_EMOJIS.get(category, "📂")
        st.subheader(f"{emoji} {category}")
        rows = []
        for subcat, value in subcategories.items():
            if value == "N/A":
                value_html = '<div class="na left-align">N/A</div>'
            elif "Success, Failure" in value:
                value_html = '<div class="both left-align">Success, Failure</div>'
            elif "Success" in value:
                value_html = '<div class="success left-align">Success</div>'
            elif "Failure" in value:
                value_html = '<div class="failure left-align">Failure</div>'
            else:
                value_html = f'<div class="na left-align">{value}</div>'
            rows.append([subcat, value_html])
        category_df = pd.DataFrame(rows, columns=["Sub-Category", "Recommendation"])
        table_html = category_df.to_html(escape=False, index=False).replace("<th>", '<th style="text-align:center;">')
        st.markdown(table_html, unsafe_allow_html=True)

if selected_tab == "Generate Custom Recommendation":
    st.markdown("### Custom Advanced Audit Policy")
    st.markdown("---")

    with st.expander("📘 Reasoning Behind The Recommendation", expanded=False):
        if "recommendation_explanation" in st.session_state:
            col_reason, col_button = st.columns([0.8, 0.2])
            with col_reason:
                st.markdown(st.session_state.recommendation_explanation)
            with col_button:
                batch_lines = ["@echo off", "REM Generated by Eventlog Compendium\n"]
                for category, subcats in st.session_state.generated_policies.items():
                    for subcat, setting in subcats.items():
                        if setting != "N/A":
                            parts = setting.lower().split(", ")
                            success = "enable" if "success" in parts else "disable"
                            failure = "enable" if "failure" in parts else "disable"
                            batch_lines.append(f'auditpol /set /subcategory:"{subcat}" /success:{success} /failure:{failure}')
                batch_script = "\n".join(batch_lines)
                st.download_button(
                    label="💾 Generate Batch Script",
                    data=batch_script,
                    file_name="apply_audit_policy.bat",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("🧠 Nothing here yet! Click **Generate Recommendation** to get a detailed explanation.")

    render_category_tables(st.session_state.generated_policies if "generated_policies" in st.session_state else default_policies_json)

elif selected_tab == "Prebuilt Recommendations":
    st.markdown("### Selected Prebuilt Audit Policy")
    render_category_tables(selected_policy_data)
