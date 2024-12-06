import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import numpy as np
import webbrowser


# Page configuration
st.set_page_config(
    page_title="NBA Reddit AMA Analysis",
    page_icon="🏀",
    layout="wide",
    # initial_sidebar_state="collapsed"
)


pg = st.navigation([
    st.Page("pages/page1.py", title='AMAs'),
    st.Page("pages/page2.py", title='Organic Tracker', url_path='organic-tracker'),
    st.Page("pages/page3.py", title='Comparative Analysis', url_path='comparative'),
], position='sidebar')

pg.run()