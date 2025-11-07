# -*- coding: utf-8 -*-
"""
Created on Thu Nov  6 16:21:24 2025

@author: Alessandro
apavan@ogs.it
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pyproj import CRS, Transformer
import simplekml
import sys
from matplotlib import cm

# --- File Configuration ---
FILE_NAME = '170314_100443_M02.txt'
KML_FILE_NAME = FILE_NAME[:-3] + 'kml'
SEP_CHARACTER = ';'

# Define the column names
column_names = ['Time', 'Latitude', 'Longitude', 'CO2', 'Temperature', 'Humidity']

# ====================================================================
# AUXILIARY DATA PREPARATION FUNCTIONS (UNCHANGED LOGIC)
# ====================================================================

def convert_ddmmss_to_dd(coord):
    """Converts coordinates from DDMM.SSSS to Decimal Degrees (DD.XXXX)."""
    degrees = int(coord // 100)
    decimal_minutes = coord % 100
    return degrees + decimal_minutes / 60

def format_time_string(time_value):
    """Formats the HHMMSS value into an HH:MM:SS string."""
    time_str = str(int(time_value)).zfill(6)
    return f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"

def calculate_relative_seconds(row, start_time):
    """Calculates the seconds elapsed since the start of the measurement."""
    current_time_str = str(int(row['Time'])).zfill(6)
    current_time = datetime.strptime(current_time_str, '%H%M%S')
    difference = current_time - start_time
    return difference.total_seconds()


def load_and_prepare_data(file_name):
    """Loads the file, cleans the data, and converts it to UTM."""
    print(f"Attempting to read file: {file_name}")

    try:
        df = pd.read_csv(
            file_name,
            sep=SEP_CHARACTER,
            header=None,
            names=column_names,
            skipinitialspace=True
        )
    except FileNotFoundError:
        print(f"ERROR: File '{file_name}' not found. Script will terminate.")
        sys.exit(1)
    except pd.errors.ParserError as e:
        print(f"Data parsing ERROR: Check the separator (';') or file structure. Details: {e}")
        sys.exit(1)

    # --- 1. Lat/Lon Conversion ---
    df['Latitude_DD'] = df['Latitude'].apply(convert_ddmmss_to_dd)
    df['Longitude_DD'] = df['Longitude'].apply(convert_ddmmss_to_dd)

    # --- 2. UTM Conversion ---
    crs_latlon = CRS.from_epsg(4326)
    mean_lon = df['Longitude_DD'].mean()
    utm_zone = int((mean_lon + 180) / 6) + 1
    crs_utm = CRS.from_epsg(f'326{utm_zone}')

    transformer = Transformer.from_crs(crs_latlon, crs_utm, always_xy=True)
    easting, northing = transformer.transform(df['Longitude_DD'].values, df['Latitude_DD'].values)

    df['Easting_m'] = easting
    df['Northing_m'] = northing
    df['UTM_Zone'] = utm_zone

    # --- 3. Time Preparation ---
    df['Time_HHMMSS'] = df['Time'].apply(format_time_string)

    start_time_str = str(int(df['Time'].iloc[0])).zfill(6)
    start_time = datetime.strptime(start_time_str, '%H%M%S')

    df['Relative_Seconds'] = df.apply(lambda row: calculate_relative_seconds(row, start_time), axis=1)

    return df

# ====================================================================
# VISUALIZATION FUNCTIONS (MATPLOTLIB)
# ====================================================================

def draw_plots(df):

    print("Generating Matplotlib plots with 3 Y-axes and CO2-colored (G-Y-R) trajectory...")

    # Ensure data is treated as numeric
    df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
    df['Humidity'] = pd.to_numeric(df['Humidity'], errors='coerce')
    df['CO2'] = pd.to_numeric(df['CO2'], errors='coerce')

    # --- 1. CO2, Temperature, and Humidity vs. Time (Three Y-Axes Plot) ---

    fig, ax1 = plt.subplots(figsize=(12, 6))

    n_points = len(df)
    step = max(1, n_points // 15)

    # == 1a. Primary Y-Axis (Left): CO2 ==
    color_co2_plot = 'tab:blue'
    ax1.set_xlabel('Time of Day (HH:MM:SS)')
    ax1.set_ylabel('CO2 (ppm)', color=color_co2_plot)
    line_co2, = ax1.plot(df.index, df['CO2'], marker='o', linestyle='-', color=color_co2_plot, label='CO2 (ppm)')
    ax1.tick_params(axis='y', labelcolor=color_co2_plot)
    ax1.grid(True)

    # == 1b. Secondary Y-Axis (Right 1): Temperature ==
    ax2 = ax1.twinx()
    color_temp = 'tab:red'
    line_temp, = ax2.plot(df.index, df['Temperature'], marker='x', linestyle='--', color=color_temp, label='Temperature (°C)')
    ax2.set_ylabel('Temperature (°C)', color=color_temp)
    ax2.tick_params(axis='y', labelcolor=color_temp)

    # == 1c. Tertiary Y-Axis (Right 2): Humidity ==
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))

    color_hum = 'tab:green'
    line_hum, = ax3.plot(df.index, df['Humidity'], marker='^', linestyle=':', color=color_hum, label='Humidity (%)')
    ax3.set_ylabel('Humidity (%)', color=color_hum)
    ax3.tick_params(axis='y', labelcolor=color_hum)

    ax2.spines['right'].set_color(color_temp)
    ax3.spines['right'].set_color(color_hum)

    plt.title('CO2, Temperature, and Humidity vs. Time of Day (3 Y-Axes)')

    lines = [line_co2, line_temp, line_hum]
    ax1.legend(lines, [line.get_label() for line in lines], loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3)

    ax1.set_xticks(df.index[::step])
    ax1.set_xticklabels(df['Time_HHMMSS'][::step], rotation=45, ha='right')

    fig.tight_layout()

    # --- 2. Instrument Trajectory (UTM Easting vs. Northing with CO2 color-coded G-Y-R) ---
    plt.figure(figsize=(8, 8))

    # == Color Mapping Preparation for the Plot ==
    min_co2 = df['CO2'].min()
    max_co2 = df['CO2'].max()

    # Use the 'RdYlGn_r' colormap for Green (low) -> Yellow (medium) -> Red (high)
    # '_r' means "reverse", so Red-Yellow-Green becomes Green-Yellow-Red
    cmap_for_plot = 'RdYlGn_r'

    # == Actual Trajectory Plot ==
    scatter = plt.scatter(df['Easting_m'], df['Northing_m'],
                          c=df['CO2'], # Pass the CO2 values
                          cmap=cmap_for_plot,  # Green-Yellow-Red Colormap
                          norm=plt.Normalize(vmin=min_co2, vmax=max_co2),
                          marker='o', s=50, edgecolors='black', linewidth=0.5)

    # Add the colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('CO2 Concentration (ppm)')

    utm_zone = df['UTM_Zone'].iloc[0]
    plt.title(f'Instrument Trajectory (UTM Zone {utm_zone}N) - CO2 Colored (G-Y-R)')

    plt.xlabel('Easting (X - meters)')
    plt.ylabel('Northing (Y - meters)')

    # Start/End Markers
    plt.plot(df['Easting_m'].iloc[0], df['Northing_m'].iloc[0], marker='^', markersize=10, color='blue', label='Start')
    plt.plot(df['Easting_m'].iloc[-1], df['Northing_m'].iloc[-1], marker='s', markersize=10, color='purple', label='End')
    plt.legend(loc='upper right')

    plt.axis('equal')
    plt.grid(True)
    plt.tight_layout()

    plt.show()

# ====================================================================
# DYNAMIC KML GENERATION FUNCTION (CORRECTED)
# ====================================================================

def generate_kml_trajectory(df, kml_file_name):
    """Generates a KML file with the trajectory and points colored based on CO2 (Green/Yellow/Red)."""

    kml = simplekml.Kml(name="CO2 Sensor Measurement")

    # --- 1. Color Mapping Preparation ---
    min_co2 = df['CO2'].min()
    max_co2 = df['CO2'].max()

    # MODIFICATION: Use of the 'RdYlGn_r' color map (Red-Yellow-Green, reversed)
    # The reversal ('_r') ensures Green (low value) is at the start and Red (high value) at the end.
    try:
        # Will attempt to use the 'RdYlGn_r' map for maximum Green/Red contrast
        cmap = cm.get_cmap('RdYlGn_r')
    except AttributeError:
        # Fallback for newer Matplotlib versions
        cmap = cm.get_cmap('RdYlGn_r')

    def get_kml_color(co2_value):
        """Converts a CO2 value into a simplekml color object."""
        # Normalization: 0 for min_co2, 1 for max_co2
        normalized_value = (co2_value - min_co2) / (max_co2 - min_co2)

        # Gets the RGBA color from the map
        rgba = cmap(normalized_value)
        r, g, b, a = [int(c * 255) for c in rgba]

        # Returns the simplekml color object
        return simplekml.Color.rgb(r, g, b, a)

    # 2. Create the Line representing the trajectory
    trajectory_coords = [
        (row['Longitude_DD'], row['Latitude_DD'], 0)
        for index, row in df.iterrows()
    ]

    linestring = kml.newlinestring(name="Trajectory")
    linestring.coords = trajectory_coords
    linestring.altitudemode = simplekml.AltitudeMode.clamptoground
    linestring.extrude = 1
    linestring.style.linestyle.width = 3
    linestring.style.linestyle.color = simplekml.Color.white

    # 3. Add a Placemark for each point with dynamic color
    points_folder = kml.newfolder(name="CO2 Measurement Points")

    for index, row in df.iterrows():
        co2_val = row['CO2']
        kml_color_obj = get_kml_color(co2_val)

        pnt = points_folder.newpoint(name=f"CO2: {co2_val} ppm")
        pnt.coords = [(row['Longitude_DD'], row['Latitude_DD'], 0)]
        pnt.altitudemode = simplekml.AltitudeMode.clamptoground

        # Define the dynamic style: Round pin and CO2 color
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
        pnt.style.iconstyle.color = kml_color_obj # Direct assignment of the color object
        pnt.style.iconstyle.scale = 1.0

        # Detailed Description
        description = f"""
        Time: {row['Time_HHMMSS']}<br>
        Lat/Lon (Dec): {row['Latitude_DD']:.5f}, {row['Longitude_DD']:.5f}<br>
        ---<br>
        CO2: {co2_val} ppm<br>
        Temperature: {row['Temperature']} °C<br>
        Humidity: {row['Humidity']} %
        """
        pnt.description = description

    # 4. Save the KML file
    kml.save(kml_file_name)
    print(f"\nColored KML file successfully generated: {kml_file_name}")

# ====================================================================
# MAIN PROGRAM EXECUTION
# ====================================================================

if __name__ == "__main__":

    data_df = load_and_prepare_data(FILE_NAME)

    if data_df is not None:
        print(f"Reading complete. Found {len(data_df)} data points.")

        # 1. Generate the plots
        draw_plots(data_df)

        # 2. Generate the dynamic KML file
        generate_kml_trajectory(data_df, KML_FILE_NAME)