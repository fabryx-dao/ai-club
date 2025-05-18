import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# === CONFIGURATION ===
PORT = '/dev/tty.usbmodem101'  # <- Change this to match your Arduino port
BAUD_RATE = 9600
MAX_POINTS = 500  # Number of points to display in plot window

# === SETUP ===
ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
buffer = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

fig, ax = plt.subplots()
line, = ax.plot(buffer)
ax.set_ylim(400, 800)  # Adjust based on your signal range
ax.set_title("Live PPG Signal")
ax.set_xlabel("Time")
ax.set_ylabel("PPG Value")

def update(frame):
    global buffer
    try:
        line_bytes = ser.readline()
        line_str = line_bytes.decode('utf-8').strip()
        if line_str.isdigit():
            val = int(line_str)
            if 400 <= val <= 800:
                buffer.append(val)
                line.set_ydata(buffer)
    except:
        pass
    return line,

ani = animation.FuncAnimation(fig, update, interval=10)
plt.show()

