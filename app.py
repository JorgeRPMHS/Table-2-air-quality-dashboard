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
                      plot_pollutant_over_time, plot_pollutant_vs_sensor,
                      plot_pollutants_grid)

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

    # Pollutant selector - drives the KPI cards, data table, and all charts.
    # The first option, ALL_POLLUTANTS, shows every pollutant at once.
    ALL_POLLUTANTS = "All pollutants"
    selected_pollutant = st.sidebar.selectbox(
        "Pollutant type",
        options=[ALL_POLLUTANTS] + list(POLLUTANTS.keys()),
        format_func=lambda col: col if col == ALL_POLLUTANTS else POLLUTANTS[col]['label'],
    )
    show_all = selected_pollutant == ALL_POLLUTANTS

    # The list of pollutant columns in play: all of them, or just the selected one
    active_pollutants = list(POLLUTANTS.keys()) if show_all else [selected_pollutant]
    if not show_all:
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
    st.sidebar.caption(
        f"Showing **{len(filtered_df):,}** of {df['Date'].notna().sum():,} hourly records  \n"
        f"{start_date:%d %b %Y} → {end_date:%d %b %Y}"
    )

    # Stop early if the filters leave nothing to show
    if filtered_df.empty:
        st.warning("No data available for the selected date range. Please adjust the filters.")
        return

    # Warn about pollutants with no valid readings in the range
    # (e.g. NMHC(GT) is only recorded during the first weeks of the dataset)
    empty_pollutants = [p for p in active_pollutants if filtered_df[p].dropna().empty]
    if empty_pollutants:
        st.warning(f"No valid {', '.join(empty_pollutants)} readings in the selected date range. "
                   "Related charts will be empty.")
    # ------------------------------------------------------------------
    # End sidebar filters
    # ------------------------------------------------------------------

    # Key Metrics - KPI Boxes
    st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)

    # Calculate metrics on the filtered data (reacts to the date range)
    metrics = calculate_air_quality_metrics(filtered_df)
    display_metrics = create_summary_metrics_display(metrics)

    # Replace the fixed CO card with one card per active pollutant
    # (reacts to the pollutant filter)
    display_metrics.pop('CO Concentration', None)
    pollutant_cards = {}
    for p in active_pollutants:
        p_unit = POLLUTANTS[p]['unit']
        p_metrics = calculate_pollutant_metrics(filtered_df, p)
        if p_metrics:
            pollutant_cards[POLLUTANTS[p]['label']] = {
                'Average': f"{p_metrics['mean']:.2f} {p_unit}",
                'Maximum': f"{p_metrics['max']:.2f} {p_unit}",
                'Minimum': f"{p_metrics['min']:.2f} {p_unit}",
            }
        else:
            pollutant_cards[POLLUTANTS[p]['label']] = {'Average': "N/A", 'Maximum': "N/A", 'Minimum': "N/A"}

    # With "All pollutants", show the pollutant cards on their own row and the
    # weather cards on a second row so the columns don't get too narrow
    if show_all:
        card_rows = [pollutant_cards, display_metrics]
    else:
        card_rows = [{**pollutant_cards, **display_metrics}]

    for card_row in card_rows:
        if not card_row:
            continue
        # Display metrics in cards
        cols = st.columns(len(card_row))

        for i, (metric_name, metric_values) in enumerate(card_row.items()):
            with cols[i]:
                st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
                st.subheader(metric_name)
                for key, value in metric_values.items():
                    st.metric(key, value)
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Data table: one interactive table that combines the sidebar filters
    # (pollutant type, date range) with the Table controls (sort, height,
    # concentration range)
    # ------------------------------------------------------------------
    st.markdown('<h2 class="section-header">Data Table</h2>', unsafe_allow_html=True)

    # Columns follow the pollutant filter: the selected pollutant and its sensor,
    # or every pollutant when "All pollutants" is chosen, plus weather columns
    if show_all:
        table_cols = ['Date', 'Time'] + active_pollutants + ['T', 'RH', 'AH']
    else:
        table_cols = ['Date', 'Time', selected_pollutant, sensor, 'T', 'RH', 'AH']
    table_cols = list(dict.fromkeys(table_cols))

    # Rows follow the date range filter
    table_data = filtered_df[table_cols].copy()

    st.sidebar.header("Table controls")

    # Sort options - limited to the columns shown in the table
    sort_column = st.sidebar.selectbox("Sort by", table_cols)
    sort_order = st.sidebar.selectbox(
        "Sort order", ["Ascending", "Descending"]
    )

    height = st.sidebar.slider("Table height", 200, 1000, 400, 50)

    # Concentration range filter - applies to the selected pollutant; with
    # "All pollutants" the user picks which pollutant the range applies to
    if show_all:
        range_pollutant = st.sidebar.selectbox("Filter by pollutant", active_pollutants)
    else:
        range_pollutant = selected_pollutant

    values = pd.to_numeric(table_data[range_pollutant], errors="coerce")
    valid_values = values.dropna()

    if not valid_values.empty:
        minimum = float(valid_values.min())
        maximum = float(valid_values.max())

        if minimum < maximum:
            lower, upper = st.sidebar.slider(
                f"{range_pollutant} concentration range",
                min_value=minimum,
                max_value=maximum,
                value=(minimum, maximum)
            )

            # Only filter when the range is narrowed, so rows with a missing
            # reading for this pollutant are not hidden by default
            if (lower, upper) != (minimum, maximum):
                table_data = table_data.loc[values.between(lower, upper)]

    # Sort the table based on user selection
    table_data = table_data.sort_values(
        sort_column,
        ascending=(sort_order == "Ascending"),
        na_position="last"
    )

    # Display the filtered and sorted table
    st.caption(f"Showing {len(table_data):,} of {len(filtered_df):,} readings in the selected date range")
    st.dataframe(table_data, use_container_width=True, height=height)
    # ------------------------------------------------------------------
    # End data table
    # ------------------------------------------------------------------

    # Visualizations
    st.markdown('<h2 class="section-header">Data Visualizations</h2>', unsafe_allow_html=True)

    if show_all:
        # "All pollutants": full-width grids with one small chart per pollutant,
        # since the pollutants are measured on very different scales
        st.subheader("Pollutant Concentrations Over Time")
        st.pyplot(plot_pollutants_grid(filtered_df, POLLUTANTS, kind='time'))

        col1, col2 = st.columns(2)
        with col1:
            # Temperature vs humidity, coloured by temperature (no single pollutant selected)
            st.subheader("Temperature vs Absolute Humidity")
            temp_humidity_plot = plot_temperature_vs_humidity(filtered_df)
            if temp_humidity_plot:
                st.pyplot(temp_humidity_plot)
            else:
                st.warning("No temperature/humidity data available for plotting")
        with col2:
            # Correlation heatmap on the filtered data
            st.subheader("Correlation Heatmap")
            corr_plot = plot_correlation_heatmap(filtered_df)
            if corr_plot:
                st.pyplot(corr_plot)

        st.subheader("Pollutant Distributions")
        st.pyplot(plot_pollutants_grid(filtered_df, POLLUTANTS, kind='hist'))

        st.subheader("Pollutants vs Sensor Values")
        st.pyplot(plot_pollutants_grid(filtered_df, POLLUTANTS, kind='sensor'))

    else:
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
