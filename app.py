import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Flight Deal Finder - Maintenance",
    page_icon="✈️",
    layout="centered"
)

# Center content
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title("✈️ Flight Deal Finder")
    
    st.markdown("---")
    
    st.info("""
    ### 🔧 Under Maintenance
    
    We're making exciting improvements to bring you even better flight deals!
    
    **What's coming:**
    - ✨ Cleaner interface
    - 📊 Enhanced filtering options
    - 🚀 Automated daily updates
    
    **Expected return:** Coming soon!
    
    Follow us on Instagram for updates:  
    [@weekendescapeslondon](https://instagram.com/weekendescapeslondon)
    """)
    
    st.markdown("---")
    
    st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y')}")
