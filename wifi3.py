import uhd
import numpy as np
import time
import csv
import signal

# ----------------------------
# SAFE BACKEND
# ----------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ----------------------------
# SAFE EXIT FLAG
# ----------------------------
running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)

# ----------------------------
# USRP CONFIGURATION
# ----------------------------
usrp = uhd.usrp.MultiUSRP("type=b200")

sample_rate = 20e6
center_freq = 2.437e9
#center_freq = 2.45e9
gain = 45

usrp.set_rx_rate(sample_rate)
usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq))
usrp.set_rx_gain(gain)
usrp.set_rx_antenna("RX2")

print("USRP configured")
print("Running... Press Ctrl+C to stop")

# ----------------------------
# STREAM SETUP
# ----------------------------
st_args = uhd.usrp.StreamArgs("fc32", "sc16")
rx_streamer = usrp.get_rx_stream(st_args)

buffer_size = 4096
recv_buffer = np.zeros((1, buffer_size), dtype=np.complex64)

metadata = uhd.types.RXMetadata()

stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
stream_cmd.stream_now = True
rx_streamer.issue_stream_cmd(stream_cmd)

# ----------------------------
# DATA STORAGE
# ----------------------------
time_data = []
rssi_data = []

start_time = time.time()

# ----------------------------
# MEASUREMENT LOOP
# ----------------------------
while running:
    samples = rx_streamer.recv(recv_buffer, metadata)
    data = recv_buffer[0]

    power = np.mean(np.abs(data)**2)
    power = np.clip(power, 1e-12, 1)

    rssi = 10 * np.log10(power)

    current_time = time.time() - start_time

    time_data.append(current_time)
    rssi_data.append(rssi)

    print("Time: %.2fs | RSSI: %.2f dB" % (current_time, rssi))

# ----------------------------
# CLEAN EXIT
# ----------------------------
print("\nStopping safely... generating plots")

stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
rx_streamer.issue_stream_cmd(stream_cmd)

time_data = np.array(time_data)
rssi_data = np.array(rssi_data)

# ----------------------------
# REMOVE OUTLIERS
# ----------------------------
rssi_clean = rssi_data[(rssi_data < -10) & (rssi_data > -120)]

# ----------------------------
# SAVE CSV
# ----------------------------
with open("rssi_log.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Time (s)", "RSSI (dB)"])
    for t, r in zip(time_data, rssi_data):
        writer.writerow([t, r])

# ----------------------------
# SMOOTHING
# ----------------------------
window = 50
rssi_smooth = np.convolve(rssi_clean, np.ones(window)/window, mode='valid')

# ----------------------------
# SPECTRUM
# ----------------------------
fft_data = np.fft.fftshift(np.fft.fft(data))
freq_axis = np.linspace(-sample_rate/2, sample_rate/2, len(fft_data)) / 1e6
spectrum = 20 * np.log10(np.abs(fft_data) / np.max(np.abs(fft_data)) + 1e-12)

# =========================================================
# 📊 COMBINED SUBPLOTS
# =========================================================
fig, axs = plt.subplots(2, 2, figsize=(12, 8))

axs[0, 0].plot(time_data, rssi_data)
axs[0, 0].set(title="RSSI vs Time", xlabel="Time (s)", ylabel="RSSI (dB)")
axs[0, 0].grid()

axs[0, 1].hist(rssi_clean, bins=30)
axs[0, 1].set(title="RSSI Distribution", xlabel="RSSI (dB)", ylabel="Frequency")
axs[0, 1].grid()

axs[1, 0].plot(rssi_clean, alpha=0.3, label="Raw")
axs[1, 0].plot(rssi_smooth, label="Smoothed")
axs[1, 0].set(title="Smoothed RSSI", xlabel="Samples", ylabel="RSSI (dB)")
axs[1, 0].legend()
axs[1, 0].grid()

axs[1, 1].plot(freq_axis, spectrum)
axs[1, 1].set(title="WiFi Spectrum", xlabel="Frequency Offset (MHz)", ylabel="Normalized Power (dB)")
axs[1, 1].grid()

plt.tight_layout()
plt.savefig("all_plots.png", dpi=300)

# =========================================================
# 📊 SEPARATE INDIVIDUAL PLOTS (NEW)
# =========================================================

# 1. RSSI vs Time
plt.figure()
plt.plot(time_data, rssi_data)
plt.title("RSSI vs Time")
plt.xlabel("Time (seconds)")
plt.ylabel("RSSI (dB)")
plt.grid()
plt.savefig("rssi_vs_time.png", dpi=300)

# 2. Histogram
plt.figure()
plt.hist(rssi_clean, bins=30)
plt.title("RSSI Distribution")
plt.xlabel("RSSI (dB)")
plt.ylabel("Frequency")
plt.grid()
plt.savefig("rssi_histogram.png", dpi=300)

# 3. Smoothed RSSI
plt.figure()
plt.plot(rssi_clean, alpha=0.3, label="Raw")
plt.plot(rssi_smooth, label="Smoothed")
plt.title("Smoothed RSSI")
plt.xlabel("Samples")
plt.ylabel("RSSI (dB)")
plt.legend()
plt.grid()
plt.savefig("rssi_smooth.png", dpi=300)

# 4. Spectrum
plt.figure()
plt.plot(freq_axis, spectrum)
plt.title("WiFi Spectrum (Normalized)")
plt.xlabel("Frequency Offset (MHz)")
plt.ylabel("Normalized Power (dB)")
plt.grid()
plt.savefig("wifi_spectrum.png", dpi=300)

# =========================================================
# 📊 METRICS
# =========================================================
avg_rssi = np.mean(rssi_clean)
median_rssi = np.median(rssi_clean)
max_rssi = np.percentile(rssi_clean, 99)
min_rssi = np.percentile(rssi_clean, 1)
std_rssi = np.std(rssi_clean)

print("\n--- FINAL RESULTS ---")
print("Average RSSI:", avg_rssi)
print("Median RSSI:", median_rssi)
print("Max RSSI:", max_rssi)
print("Min RSSI:", min_rssi)
print("Std Dev:", std_rssi)

# ----------------------------
# SAVE RESULTS
# ----------------------------
with open("results.txt", "w") as f:
    f.write("WiFi RSSI Measurement Results\n")
    f.write("=============================\n\n")
    f.write(f"Average RSSI: {avg_rssi:.2f} dB\n")
    f.write(f"Median RSSI: {median_rssi:.2f} dB\n")
    f.write(f"Max RSSI (99th percentile): {max_rssi:.2f} dB\n")
    f.write(f"Min RSSI (1st percentile): {min_rssi:.2f} dB\n")
    f.write(f"Standard Deviation: {std_rssi:.2f} dB\n")
    f.write(f"Total Samples: {len(rssi_clean)}\n")

print("\n✅ All plots + results saved successfully!")