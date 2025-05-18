import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import butter, lfilter
from collections import deque

# === CONFIG ===
PORT = '/dev/tty.usbmodem101'  # <- Replace with your port
BAUD = 9600
SAMPLING_RATE = 100  # Hz (from Arduino's delay(10))
MAX_POINTS = 500

# === FILTER ===
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return butter(order, [low, high], btype='band')

def bandpass_filter(data, lowcut=0.5, highcut=4.0, fs=SAMPLING_RATE, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    return lfilter(b, a, data)

# === SETUP ===
ser = serial.Serial(PORT, BAUD, timeout=1)
raw_buffer = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
filt_buffer = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

fig, ax = plt.subplots()
raw_line, = ax.plot([], [], label="Raw")
filt_line, = ax.plot([], [], label="Filtered")
ax.set_ylim(500, 650)
ax.set_title("PPG Signal (Bandpass Filtered)")
ax.set_xlabel("Time")
ax.set_ylabel("PPG Value")
ax.legend()

def update(frame):
    try:
        line_bytes = ser.readline()
        line_str = line_bytes.decode('utf-8').strip()
        if line_str.isdigit():
            val = int(line_str)
            if 400 <= val <= 800:
                raw_buffer.append(val)

                # Apply bandpass filter to the entire buffer
                raw_array = np.array(raw_buffer)
                filtered = bandpass_filter(raw_array)

                filt_buffer.clear()
                filt_buffer.extend(filtered)

                raw_line.set_data(range(len(raw_buffer)), raw_buffer)
                filt_line.set_data(range(len(filt_buffer)), filt_buffer)
    except Exception as e:
        print("Error:", e)

    ax.set_xlim(0, MAX_POINTS)
    return raw_line, filt_line

ani = animation.FuncAnimation(fig, update, interval=10)
plt.show()

