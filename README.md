This Python script is a specialized tool designed to process, visualize, and map environmental sensor data collected by mobile CO2 detection units at the ECCSEL NatLab Latera laboratory.
It takes raw measurement data (a text file containing time, location, CO2, Temperature, and Humidity readings) and generates essential analytical outputs:

Matplotlib Plots
Generates two plots for in-depth analysis of the survey:
A three-Y-axis time series plot showing CO2, Temperature, and Humidity trends over time.
A map of the instrument's trajectory (UTM coordinates) where each data point is vividly color-coded based on the CO2 concentration (Green for low, Red for high), clearly highlighting CO2 anomalies or hotspots within the measurement area.

Google Earth KML File
Creates a dynamic KML file, enabling 3D visualization of the measurement track in Google Earth. Each point along the trajectory is a placemark containing detailed sensor readings, and the placemarks are color-coded according to the measured CO2 value, offering a powerful tool for spatial analysis of the CO2 emissions at the Latera site.
