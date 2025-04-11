import streamlit as st
import os
from PIL import Image
from urllib.parse import unquote
from sidebar import show_sidebar

st.set_page_config(
    page_title="Audit Policy Documentation",
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

st.title("📚 Audit Policy Documentation")
st.info("🚧 This feature is a work in progress. The data has not yet been fully mapped, stay tuned")

BASE_DIR = "Advanced-Audit-Policy"
GENERAL_DOCS_DIR = "docs"

@st.cache_data
def get_available_categories():
    if os.path.exists(BASE_DIR):
        return sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))])
    return []

@st.cache_data
def get_subcategories(category):
    category_path = os.path.join(BASE_DIR, category)
    if os.path.exists(category_path):
        return sorted([d for d in os.listdir(category_path) if os.path.isdir(os.path.join(category_path, d))])
    return []

def load_markdown_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "⚠️ Documentation not found."

query_params = st.query_params
param_category = unquote(query_params.get("category", "")) if query_params.get("category") else None
param_subcategory = unquote(query_params.get("sub_category", "")) if query_params.get("sub_category") else None

tabs = st.tabs(["Audit Policy Docs", "General Documentation"])

with tabs[0]:
    categories = get_available_categories()

    category_lookup = {c.lower(): c for c in categories}
    param_category_normalized = param_category.lower() if param_category else None
    selected_category = category_lookup.get(param_category_normalized, None)

    if selected_category:
        category_index = categories.index(selected_category)
    else:
        selected_category = categories[0] if categories else ""
        category_index = 0

    selected_category = st.selectbox(
        "Select a Category:",
        categories,
        index=category_index,
        format_func=lambda x: x.replace("_", " "),
        help="Select a main category. If no sub-category is chosen, the main category documentation will be displayed."
    )

    subcategories = get_subcategories(selected_category)
    subcategory_lookup = {s.lower(): s for s in subcategories}
    param_subcategory_normalized = param_subcategory.lower() if param_subcategory else None
    selected_subcategory = subcategory_lookup.get(param_subcategory_normalized, None)

    if selected_subcategory:
        subcategory_index = subcategories.index(selected_subcategory) + 1
    else:
        subcategory_index = 0
        selected_subcategory = None

    selected_subcategory = st.selectbox(
        "Select a Sub-Category (Optional):",
        ["None"] + subcategories,
        index=subcategory_index,
        format_func=lambda x: x.replace("_", " ") if x != "None" else x,
        help="Selecting a sub-category will load its specific documentation. Otherwise, the main category documentation will be shown."
    )

    if selected_subcategory == "None":
        selected_subcategory = None

    if selected_subcategory:
        markdown_file = os.path.join(BASE_DIR, selected_category, selected_subcategory, f"{selected_subcategory}.md")
    else:
        markdown_file = os.path.join(BASE_DIR, selected_category, f"{selected_category}.md")

    markdown_content = load_markdown_file(markdown_file)
    st.markdown(markdown_content, unsafe_allow_html=True)

with tabs[1]:

    general_docs = [
        {
            "title": "Internal Advanced Audit Policy IDs",
            "description": "Map raw audit policy IDs to their human-readable names, straight from the Windows kernel.",
            "file": os.path.join(GENERAL_DOCS_DIR, "Internal-Advanced-Audit-Policy-IDs.md")
        }
    ]

    # Slightly smaller left column
    col1, col2 = st.columns([0.7, 2.3])

    with col1:
        for doc in general_docs:
            read_key = f"read_{doc['title'].replace(' ', '_')}"
            st.markdown(f"##### {doc['title']}")
            st.markdown(f"<small style='color: #ccc'>{doc['description']}</small>", unsafe_allow_html=True)
            if st.button("📖 Read More", key=read_key):
                st.session_state.selected_general_doc = doc["file"]
            st.markdown("---")

    with col2:
        selected_file = st.session_state.get("selected_general_doc")
        if selected_file:
            if os.path.exists(selected_file):
                with open(selected_file, "r", encoding="utf-8") as f:
                    st.markdown(f.read(), unsafe_allow_html=True)
            else:
                st.warning("Selected documentation file not found.")
        else:
            st.info("Select a document from the left to view its content here.")
