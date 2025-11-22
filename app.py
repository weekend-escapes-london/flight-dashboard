"""
Streamlit App - Azure Blob Storage Version
Reads from Azure Blob Storage using st.secrets
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import StringIO
from azure.storage.blob import BlobServiceClient
import math

# Azure configuration
CONTAINER_NAME = 'flight-data'

# Page config
st.set_page_config(
    page_title="Flight Deal Finder",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Flight Deal Finder from London")
st.markdown("*Find the cheapest flights to European destinations*")

# Helper functions
@st.cache_resource
def get_blob_service_client():
    """Create Azure Blob Service Client using Streamlit secrets"""
    try:
        connection_string = st.secrets["AZURE_STORAGE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        return blob_service_client
    except KeyError:
        st.error("⚠️ App configuration error. Please contact the administrator.")
        return None
    except Exception as e:
        st.error("❌ Unable to connect. Please try again later.")
        return None


@st.cache_data(ttl=1800)
def load_flight_data():
    """Load latest flight data from Azure Blob Storage"""
    try:
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            return None
        
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME,
            blob='latest_flights.csv'
        )
        
        download_stream = blob_client.download_blob()
        csv_content = download_stream.readall().decode('utf-8')
        
        df = pd.read_csv(StringIO(csv_content))
        return df
    
    except Exception as e:
        st.error("Error loading flight data. Please try again.")
        return None


@st.cache_data(ttl=1800)
def load_metadata():
    """Load metadata from Azure Blob Storage"""
    try:
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            return None
        
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME,
            blob='metadata.json'
        )
        
        download_stream = blob_client.download_blob()
        json_content = download_stream.readall().decode('utf-8')
        
        return json.loads(json_content)
    
    except Exception as e:
        st.error("Error loading metadata. Please try again.")
        return None


@st.cache_data(ttl=3600)
def get_history_files():
    """Get list of historical CSV files from Azure"""
    try:
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            return []
        
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        
        history_blobs = []
        for blob in container_client.list_blobs(name_starts_with='history/'):
            if blob.name.endswith('.csv'):
                history_blobs.append({
                    'name': blob.name,
                    'last_modified': blob.last_modified
                })
        
        history_blobs.sort(key=lambda x: x['last_modified'], reverse=True)
        return history_blobs
    
    except Exception as e:
        st.error("Error loading history. Please try again.")
        return []

@st.cache_data(ttl=3600)
def load_history_file(blob_name):
    """Load a specific historical CSV file from Azure"""
    try:
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            return None
        
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME,
            blob=blob_name
        )
        
        download_stream = blob_client.download_blob()
        csv_content = download_stream.readall().decode('utf-8')
        
        return pd.read_csv(StringIO(csv_content))
    
    except Exception as e:
        st.error("Error loading historical data. Please try again.")
        return None


# Load data
df = load_flight_data()
metadata = load_metadata()

# Check if data exists
if df is None:
    st.error("❌ Unable to load flight data!")
    st.info("""
    **Possible issues:**
    - Data is being updated, please try again shortly
    - Connection issue, please refresh the page
    """)
    st.stop()

# Show last update info
if metadata:
    last_updated = datetime.fromisoformat(metadata['last_updated'])
    time_diff = datetime.now() - last_updated
    hours_ago = int(time_diff.total_seconds() / 3600)
    minutes_ago = int((time_diff.total_seconds() % 3600) / 60)
    
    if hours_ago > 0:
        time_str = f"{hours_ago}h {minutes_ago}m ago"
    else:
        time_str = f"{minutes_ago}m ago"
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.success(f"✅ Data last updated: {last_updated.strftime('%B %d, %Y at %I:%M %p')} ({time_str})")
    with col2:
        if st.button("🔄 Refresh Data", help="Check for latest data"):
            st.cache_data.clear()
            st.rerun()
    with col3:
        departure_date = metadata.get('departure_date', 'N/A')
        st.info(f"📅 Searching for: {departure_date}")

# Summary statistics
st.markdown("### 📊 Summary Statistics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Flights", len(df))
with col2:
    st.metric("Cheapest Flight", f"£{df['Price (numeric)'].min():.2f}")
with col3:
    st.metric("Average Price", f"£{df['Price (numeric)'].mean():.2f}")
with col4:
    if metadata:
        st.metric("Destinations", metadata['destinations_searched'])
    else:
        st.metric("Destinations", df['Destination City'].nunique())

# Sidebar filters
st.sidebar.header("🎛️ Filters")

# Price filter - RANGE SLIDER
min_price_value = 0
max_price_value = math.ceil(df['Price (numeric)'].max())

price_range = st.sidebar.slider(
    "Price Range (£)",
    min_value=min_price_value,
    max_value=max_price_value,
    value=(min_price_value, max_price_value),
    help="Drag handles to set min and max price"
)

min_price, max_price = price_range

# Destination filter
all_destinations = sorted(df['Destination City'].unique())
selected_destinations = st.sidebar.multiselect(
    "Destinations",
    options=all_destinations,
    default=[]
)

# Airline filter
all_airlines = sorted(df['Airline'].unique())
selected_airlines = st.sidebar.multiselect(
    "Airlines",
    options=all_airlines,
    default=[]
)

# Direct flights only
direct_only = st.sidebar.checkbox("Direct flights only")

# Apply filters
filtered_df = df[(df['Price (numeric)'] >= min_price) & (df['Price (numeric)'] <= max_price)]

if selected_destinations:
    filtered_df = filtered_df[filtered_df['Destination City'].isin(selected_destinations)]

if selected_airlines:
    filtered_df = filtered_df[filtered_df['Airline'].isin(selected_airlines)]

if direct_only:
    filtered_df = filtered_df[filtered_df['Stops'] == 0]

# Display results - Current data
st.markdown(f"### 🏆 Current Best Deals ({len(filtered_df)} flights)")

# Add timestamp for clarity
if metadata:
    last_updated = datetime.fromisoformat(metadata['last_updated'])
    st.caption(f"📊 Showing latest data from {last_updated.strftime('%b %d at %I:%M %p')} • Use filters above to refine results")

if len(filtered_df) == 0:
    st.warning("No flights match your filters. Try adjusting the criteria.")
else:
    # Select columns to display
    display_columns = [
        'Destination City',
        'Price',
        'Airline',
        'Flight Number',
        'Aircraft',
        'Departure Airport',
        'Destination Airport',
        'Departure Time',
        'Arrival Time',
        'Duration',
        'Stops'
    ]
    
    # Display table
    st.dataframe(
        filtered_df[display_columns],
        width='stretch',
        hide_index=True,
        column_config={
            'Price': st.column_config.TextColumn('Price', width="small"),
            'Duration': st.column_config.TextColumn('Duration', width="small"),
            'Stops': st.column_config.NumberColumn('Stops', width="small")
        }
    )
    
    # Expandable detailed view
    with st.expander("📋 View All Columns"):
        st.dataframe(filtered_df, width='stretch', hide_index=True)
    
    # Download button
    csv_data = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_data,
        file_name=f"flight_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Sidebar - Historical data (COLLAPSIBLE)
st.sidebar.markdown("---")

# Initialize selection variable
selected_display = 'Current'
filename_mapping = {}

with st.sidebar.expander("📂 Historical Data", expanded=False):
    history_files = get_history_files()
    if history_files and len(history_files) > 1:
        older_files = history_files[1:]
        st.info(f"Found {len(older_files)} older price checks")
        
        def format_history_name(blob_info):
            filename = blob_info['name'].replace('history/', '').replace('.csv', '')
            try:
                timestamp_str = filename.replace('flights_', '').replace('.csv', '')
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d_%H%M%S')
                return dt.strftime('%b %d, %Y at %I:%M %p')
            except:
                return filename
        
        display_options = ['Current'] + [format_history_name(f) for f in older_files[:10]]
        filename_mapping = {format_history_name(f): f['name'] for f in older_files[:10]}
        
        selected_display = st.selectbox(
            "Compare with past prices:",
            options=display_options,
            index=0,
            key='history_select'
        )
    else:
        st.info("No older price data yet")

# Display historical data in MAIN AREA (outside sidebar)
if selected_display != 'Current' and filename_mapping:
    actual_blob_name = filename_mapping[selected_display]
    df_history = load_history_file(actual_blob_name)
    
    if df_history is not None:
    
        # Show in main area with clear separation
        st.markdown("---")
        st.markdown(f"### 📂 Past Prices: {selected_display}")
        st.warning("⚠️ These are older prices - they may have changed since then.")
        st.caption(f"Showing first 20 flights from this date")
        st.dataframe(df_history.head(20), width='stretch', hide_index=True)

# Sidebar - Info (COLLAPSIBLE)
with st.sidebar.expander("ℹ️ About", expanded=False):
    st.info("""
**Flight Deal Finder**

The best flight deals from London to European destinations, updated daily.

📸 **Follow [@weekendescapeslondon](https://instagram.com/weekendescapeslondon)**

We post the best finds from this site — so you never miss a great deal!
""")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption("Flight Deal Finder | Data refreshed daily")