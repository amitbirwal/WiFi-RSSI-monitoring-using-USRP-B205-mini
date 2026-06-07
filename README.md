Real-Time USRP WiFi RSSI & Spectrum Analyzer
This Python script interfaces with an Ettus USRP B200 Software Defined Radio (SDR) using the uhd library to capture, analyze, and visualize live RF signals in the 2.4 GHz WiFi band (configured by default for 2.437 GHz / Channel 6).

🚀 Key Features
Live IQ Data Acquisition: Streams raw IQ samples in real time from the USRP using a 20 MHz sampling rate.

RSSI Tracking & Logging: Computes continuous Received Signal Strength Indicator (RSSI) power levels, outputs them to the console, and logs timestamps and raw values to rssi_log.csv.

Signal Post-Processing: Filters out measurement outliers and applies a moving average window to generate a smoothed RSSI trend.

FFT Spectrum Analysis: Performs a Fast Fourier Transform (FFT) on the raw signal to compute and display a normalized power spectrum over the frequency offset.

Headless Automated Plotting: Utilizes Matplotlib’s safe Agg backend to generate and save individual diagnostic charts (wifi_spectrum.png, rssi_smooth.png, etc.) as well as a combined 2x2 subplot matrix (all_plots.png).

Statistical Reporting: Calculates and saves key metrics (Average, Median, Min/Max percentiles, and Standard Deviation) directly to a results.txt summary file upon a clean Ctrl+C exit.
