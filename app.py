"""
Air Quality Dashboard - Main Streamlit Application

This is the main application file for the UCI Air Quality Dataset dashboard.
Students will work in teams to enhance this dashboard through Git collaboration.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from analysis import load_data, clean_data, get_data_summary, calculate_air_quality_metrics
from visualize import (plot_co_over_time, plot_temperature_vs_humidity, 
                      plot_pollutant_distribution, plot_correlation_heatmap,
                      plot_nox_vs_sensor, create_summary_metrics_display)

# Configure the page
st.set_page_config(
    page_title="Air Quality Dashboard",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2E8B57;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #2E8B57;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">Air Quality Dashboard</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Welcome to the Air Quality Analysis Dashboard!** 
    
    This dashboard analyzes air quality data from an Italian city monitoring station. 
    The dataset includes various air pollutants and weather variables collected over time.
    """)
    
    # Load and cache data
    @st.cache_data
    def load_and_clean_data():
        """Load and clean the air quality data."""
        raw_data = load_data("data/AirQualityUCI.csv")
        if raw_data is not None:
            return clean_data(raw_data)
        return None
    
    # Load data
    with st.spinner("Loading air quality data..."):
        df = load_and_clean_data()
    
    if df is None:
        st.error("Could not load the air quality dataset. Please check if 'data/AirQualityUCI.csv' exists.")
        return
    
    # Key Metrics - KPI Boxes
    st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)
    
    # Calculate metrics
    metrics = calculate_air_quality_metrics(df)
    display_metrics = create_summary_metrics_display(metrics)
    
    if display_metrics:
        # Display metrics in cards
        cols = st.columns(len(display_metrics))
        
        for i, (metric_name, metric_values) in enumerate(display_metrics.items()):
            with cols[i]:
                st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
                st.subheader(metric_name)
                for key, value in metric_values.items():
                    st.metric(key, value)
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Data preview table
    st.markdown('<h2 class="section-header">Data Preview</h2>', unsafe_allow_html=True)
    st.sidebar.header("Table controls")

    # Filter and sort options
    sort_column = st.sidebar.selectbox("Sort by", df.columns.tolist())
    sort_order = st.sidebar.selectbox(
        "Sort order", ["Ascending", "Descending"]
    )

    height = st.sidebar.slider("Table height", 200, 1000, 400, 50)

    table_data = df.copy()

    # Filter by pollutant concentration range
    pollutant = st.sidebar.selectbox(
        "Filter by pollutant",
        ["CO(GT)", "C6H6(GT)", "NOx(GT)", "NO2(GT)"]
    )

    # Filter the table based on pollutant concentration range
    values = pd.to_numeric(table_data[pollutant], errors="coerce")
    valid_values = values.dropna()

    if not valid_values.empty:
        minimum = float(valid_values.min())
        maximum = float(valid_values.max())

        if minimum < maximum:
            lower, upper = st.sidebar.slider(
                f"{pollutant} concentration range",
                min_value=minimum,
                max_value=maximum,
                value=(minimum, maximum)
            )

            table_data = table_data.loc[values.between(lower, upper)]

    # Sort the table based on user selection
    table_data = table_data.sort_values(
        sort_column,
        ascending=(sort_order == "Ascending"),
        na_position="last"
    )

    # Display the filtered and sorted table
    st.caption(f"Showing {len(table_data):,} of {len(df):,} readings")
    st.dataframe(table_data, use_container_width=True, height=height)
    
    # Visualizations
    st.markdown('<h2 class="section-header">Data Visualizations</h2>', unsafe_allow_html=True)
    
    # Base charts as required
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CO Concentration Over Time")
        co_plot = plot_co_over_time(df)
        if co_plot:
            st.pyplot(co_plot)
        else:
            st.warning("No CO data available for plotting")
    
    with col2:
        st.subheader("Temperature vs Absolute Humidity")
        temp_humidity_plot = plot_temperature_vs_humidity(df)
        if temp_humidity_plot:
            st.pyplot(temp_humidity_plot)
        else:
            st.warning("No temperature/humidity data available for plotting")
    
    # Additional visualizations
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("CO Distribution")
        co_dist_plot = plot_pollutant_distribution(df, 'CO(GT)')
        if co_dist_plot:
            st.pyplot(co_dist_plot)
    
    with col4:
        st.subheader("NOx(GT) vs Sensor Value")
        nox_plot = plot_nox_vs_sensor(df)
        if nox_plot:
            st.pyplot(nox_plot)
        else:
            st.warning("No NOx data available for plotting")
    
    # Correlation heatmap
    st.subheader("Correlation Heatmap")
    corr_plot = plot_correlation_heatmap(df)
    if corr_plot:
        st.pyplot(corr_plot)

if __name__ == "__main__":
    main()
