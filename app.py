"""
Air Quality Dashboard - Main Streamlit Application

This is the main application file for the UCI Air Quality Dataset dashboard.
Students will work in teams to enhance this dashboard through Git collaboration.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from analysis import (load_data, clean_data, get_data_summary, calculate_air_quality_metrics,
                      filter_by_date_range, calculate_pollutant_metrics, POLLUTANTS)
from visualize import (plot_co_over_time, plot_temperature_vs_humidity,
                      plot_pollutant_distribution, plot_correlation_heatmap,
                      plot_nox_vs_sensor, create_summary_metrics_display,
                      plot_pollutant_over_time, plot_pollutant_vs_sensor)

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
    
    # ------------------------------------------------------------------
    # Sidebar filters: pollutant type and date range
    # ------------------------------------------------------------------
    st.sidebar.header("Filters")

    # Pollutant selector - drives the KPI card, data preview, and all charts
    selected_pollutant = st.sidebar.selectbox(
        "Pollutant type",
        options=list(POLLUTANTS.keys()),
        format_func=lambda col: POLLUTANTS[col]['label'],
    )
    pollutant_info = POLLUTANTS[selected_pollutant]
    unit = pollutant_info['unit']
    sensor = pollutant_info['sensor']

    # Date range picker - limited to the dates available in the dataset
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # While the user is picking, date_input returns only the start date;
    # in that case treat the range as a single day.
    if isinstance(date_range, (list, tuple)):
        start_date = date_range[0]
        end_date = date_range[1] if len(date_range) > 1 else date_range[0]
    else:
        start_date = end_date = date_range

    # Apply the date filter once; every section below uses filtered_df
    filtered_df = filter_by_date_range(df, start_date, end_date)

    # Show the user how much data the current filters keep
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Showing **{len(filtered_df):,}** of {df['Date'].notna().sum():,} hourly records  \n"
        f"{start_date:%d %b %Y} → {end_date:%d %b %Y}"
    )

    # Stop early if the filters leave nothing to show
    if filtered_df.empty:
        st.warning("No data available for the selected date range. Please adjust the filters.")
        return

    # Warn when the selected pollutant has no valid readings in the range
    # (e.g. NMHC(GT) is only recorded during the first weeks of the dataset)
    if filtered_df[selected_pollutant].dropna().empty:
        st.warning(f"No valid {selected_pollutant} readings in the selected date range. "
                   "Pollutant-specific charts will be empty.")
    # ------------------------------------------------------------------
    # End sidebar filters
    # ------------------------------------------------------------------

    # Key Metrics - KPI Boxes
    st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)

    # Calculate metrics on the filtered data (reacts to the date range)
    metrics = calculate_air_quality_metrics(filtered_df)
    display_metrics = create_summary_metrics_display(metrics)

    # Replace the fixed CO card with a card for the selected pollutant
    # (reacts to the pollutant filter)
    display_metrics.pop('CO Concentration', None)
    pollutant_metrics = calculate_pollutant_metrics(filtered_df, selected_pollutant)
    if pollutant_metrics:
        pollutant_card = {
            'Average': f"{pollutant_metrics['mean']:.2f} {unit}",
            'Maximum': f"{pollutant_metrics['max']:.2f} {unit}",
            'Minimum': f"{pollutant_metrics['min']:.2f} {unit}",
        }
    else:
        pollutant_card = {'Average': "N/A", 'Maximum': "N/A", 'Minimum': "N/A"}
    display_metrics = {pollutant_info['label']: pollutant_card, **display_metrics}

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
    # Show the filtered rows, focused on the selected pollutant, its sensor and weather columns
    preview_cols = list(dict.fromkeys(['Date', 'Time', selected_pollutant, sensor, 'T', 'RH', 'AH']))
    st.dataframe(filtered_df[preview_cols].head(10), use_container_width=True)

    # Visualizations
    st.markdown('<h2 class="section-header">Data Visualizations</h2>', unsafe_allow_html=True)

    # Base charts as required
    col1, col2 = st.columns(2)

    with col1:
        # Time series of the selected pollutant over the selected dates
        st.subheader(f"{selected_pollutant} Concentration Over Time")
        pollutant_time_plot = plot_pollutant_over_time(filtered_df, selected_pollutant, unit)
        if pollutant_time_plot:
            st.pyplot(pollutant_time_plot)
        else:
            st.warning(f"No {selected_pollutant} data available for plotting")

    with col2:
        # Temperature vs humidity, points coloured by the selected pollutant
        st.subheader("Temperature vs Absolute Humidity")
        temp_humidity_plot = plot_temperature_vs_humidity(
            filtered_df,
            title=f"Temperature vs Absolute Humidity (coloured by {selected_pollutant})",
            color_by=selected_pollutant,
        )
        if temp_humidity_plot:
            st.pyplot(temp_humidity_plot)
        else:
            st.warning("No temperature/humidity data available for plotting")

    # Additional visualizations
    col3, col4 = st.columns(2)

    with col3:
        # Distribution of the selected pollutant
        st.subheader(f"{selected_pollutant} Distribution")
        dist_plot = plot_pollutant_distribution(filtered_df, selected_pollutant)
        if dist_plot:
            st.pyplot(dist_plot)
        else:
            st.warning(f"No {selected_pollutant} data available for plotting")

    with col4:
        # Selected pollutant vs its matching sensor
        st.subheader(f"{selected_pollutant} vs Sensor Value")
        sensor_plot = plot_pollutant_vs_sensor(filtered_df, selected_pollutant, sensor, unit)
        if sensor_plot:
            st.pyplot(sensor_plot)
        else:
            st.warning(f"No {selected_pollutant} / {sensor} data available for plotting")

    # Correlation heatmap on the filtered data, with the selected pollutant outlined
    st.subheader("Correlation Heatmap")
    corr_plot = plot_correlation_heatmap(filtered_df, highlight=selected_pollutant)
    if corr_plot:
        st.pyplot(corr_plot)

    # Free matplotlib memory - figures are recreated on every filter change
    plt.close('all')

if __name__ == "__main__":
    main()
