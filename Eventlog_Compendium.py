import streamlit as st
import os
import base64
from sidebar import show_sidebar
from PIL import Image

st.set_page_config(
    page_title="Eventlog Compendium",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=Image.open("images/EventLog-Compendium.ico"),
)

show_sidebar()

custom_css = """
    <style>
        body {
            background-color: #10252F;
            color: white;
            font-family: Arial, sans-serif;
        }
        .title-container {
            text-align: center;
            margin-top: -30px;
        }
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 10px;
        }
        .content-container {
            text-align: center;
            padding-top: 20px;
        }
        .footer {
            position: relative;  /* Fixed issue: Footer now stays at the bottom without overlapping */
            left: 0;
            bottom: 0;
            width: 100%;
            text-align: center;
            padding: 10px;
            margin-top: 50px; /* Ensures it stays below content */
        }
        .btn {
            background-color: #0078D4;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
            margin-top: 20px;
        }
        .btn:hover {
            background-color: #005A9E;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.markdown("<div class='title-container'><h1><center>Eventlog Compendium</center></h1></div>", unsafe_allow_html=True)

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = "./images/EventLog-Compendium.png"

if os.path.exists(logo_path):
    img_base64 = encode_image(logo_path)
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 10px;">
            <img src="data:image/png;base64,{img_base64}" width="580">
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <div class='content-container'>
        <h3><center>Centralized Windows Event Log Reference</center></h3>
        <p>
            The Eventlog Compendium is the go-to resource for understanding Windows Event Logs. 
        </p>
        <p>
            Whether you're investigating incidents, configuring audit policies, or developing security content this tool provides in-depth details and for each event.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

with col1:
    pass

with col3:
    pass

footer = """
<div class="footer">
    Developed with ❤
    <br>
    <a href="https://twitter.com/nas_bench/">Nasreddine Bencherchali</a>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
