import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import font as tkfont
from matplotlib.figure import Figure

class PPGMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("PPG Monitor")
        self.root.geometry("800x600")
        self.root.configure(bg='black')  # Set root background to black
        
        # Create Monaco-like font (fallback to monospace if Monaco isn't available)
        self.monaco_font = tkfont.Font(family="Monaco", size=9)
        self.monaco_font_bold = tkfont.Font(family="Monaco", size=9, weight="bold")
        
        # Try to set Monaco font, fall back to system monospace fonts if unavailable
        available_fonts = tkfont.families()
        if "Monaco" not in available_fonts:
            if "Consolas" in available_fonts:
                self.monaco_font = tkfont.Font(family="Consolas", size=9)
                self.monaco_font_bold = tkfont.Font(family="Consolas", size=9, weight="bold")
            elif "Menlo" in available_fonts:
                self.monaco_font = tkfont.Font(family="Menlo", size=9)
                self.monaco_font_bold = tkfont.Font(family="Menlo", size=9, weight="bold")
            elif "Courier" in available_fonts:
                self.monaco_font = tkfont.Font(family="Courier", size=9)
                self.monaco_font_bold = tkfont.Font(family="Courier", size=9, weight="bold")
        
        # Serial configuration
        self.port = '/dev/cu.usbmodem101'
        self.baud_rate = 9600
        self.ser = None
        self.connected = False
        
        # Data storage - 40 seconds at 10Hz = 400 samples
        self.max_duration = 40  # Maximum recording time in seconds
        self.window_size = 400  # Maximum number of data points to store
        self.ppg_values = []    # No need for deque since we're capping at 40 seconds
        self.timestamps = []    # Actual timestamps
        
        # Setup the main UI
        self.setup_ui()
        
        # Recording state
        self.recording_start_time = None
        self.recording_complete = False
        
        # Try to connect to Arduino
        self.connect_arduino()
        
        # Start update loop using Tkinter's after method
        self.update_interval = 100  # 100ms = 10 updates per second
        self.update_plot()
        
    def setup_ui(self):
        # Create frame for the plot with black background
        self.plot_frame = tk.Frame(self.root, bg='black')
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure with black background
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor='black', edgecolor='white')
        self.ax = self.fig.add_subplot(111, facecolor='black')
        
        # Style the plot
        self.ax.tick_params(colors='white', which='both')  # White tick marks
        self.ax.spines['bottom'].set_color('white')  # White axes
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
        # White labels with small font
        self.ax.set_xlabel('Time (seconds)', color='white', fontsize=9)
        self.ax.set_ylabel('PPG Value', color='white', fontsize=9)
        self.ax.set_title('PPG Signal Recording (40 seconds)', color='white', fontsize=10)
        
        # White grid lines, slightly transparent
        self.ax.grid(True, color='white', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # White tick labels
        for label in self.ax.get_xticklabels():
            label.set_color('white')
            label.set_fontsize(8)
        for label in self.ax.get_yticklabels():
            label.set_color('white')
            label.set_fontsize(8)
        
        # Create the canvas on the frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Setup the plot
        self.line, = self.ax.plot([], [], color='#FF5555', linewidth=1.5)  # Bright red line
        self.ax.set_xlim(0, self.max_duration)  # Fixed 40 second window
        self.ax.set_ylim(0, 1023)  # Arduino analog range (0-1023)
        
        # Bottom control frame with black background
        self.control_frame = tk.Frame(self.root, bg='black')
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Style for buttons
        button_style = {
            'bg': 'white',
            'fg': 'black',
            'activebackground': '#EEEEEE',
            'activeforeground': 'black',
            'font': self.monaco_font,
            'relief': tk.FLAT,
            'borderwidth': 1,
            'padx': 10,
            'pady': 5
        }
        
        # Status label with white text on black background
        self.status_label = tk.Label(
            self.control_frame, 
            text="Status: Disconnected", 
            fg="white", 
            bg="black",
            font=self.monaco_font
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Add reset button with modern styling
        self.reset_button = tk.Button(
            self.control_frame, 
            text="Reset Recording",
            command=self.reset_recording,
            **button_style
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        # Reconnect button with modern styling
        self.connect_button = tk.Button(
            self.control_frame, 
            text="Reconnect",
            command=self.connect_arduino,
            **button_style
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # Recording info label with white text on black background
        self.recording_label = tk.Label(
            self.control_frame, 
            text="Waiting to start recording...",
            fg="white", 
            bg="black",
            font=self.monaco_font
        )
        self.recording_label.pack(side=tk.RIGHT, padx=5)
    
    def reset_recording(self):
        # Reset all recording data and state
        self.ppg_values = []
        self.timestamps = []
        self.recording_start_time = None
        self.recording_complete = False
        self.recording_label.config(text="Waiting to start recording...")
        self.line.set_data([], [])
        self.canvas.draw_idle()
        print("Recording reset - ready to start a new 40-second recording")
    
    def connect_arduino(self):
        try:
            # Close existing connection if any
            if self.ser and self.ser.is_open:
                self.ser.close()
                
            # Open new connection
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for connection to stabilize
            self.ser.reset_input_buffer()
            self.connected = True
            self.status_label.config(text=f"Status: Connected to {self.port}", fg="#00FF00")  # Bright green for success
            print(f"Connected to Arduino on {self.port}")
        except Exception as e:
            self.connected = False
            self.status_label.config(text=f"Status: Error - {str(e)}", fg="#FF5555")  # Bright red for error
            print(f"Error connecting to Arduino: {str(e)}")
    
    def read_ppg_data(self):
        if not self.connected or not self.ser or not self.ser.is_open:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()
                try:
                    value = int(line)
                    # Print the value to stdout with timestamp
                    timestamp = time.strftime("%H:%M:%S", time.localtime())
                    print(f"{timestamp} - PPG value: {value}")
                    return value
                except ValueError:
                    return None
        except Exception as e:
            # Handle potential errors
            self.connected = False
            self.status_label.config(text="Status: Connection lost", fg="#FF5555")  # Bright red for error
            print(f"Connection error: {str(e)}")
        
        return None
    
    def update_plot(self):
        # If recording is complete, don't update
        if self.recording_complete:
            self.root.after(self.update_interval, self.update_plot)
            return
        
        # Read new data
        value = self.read_ppg_data()
        
        # If we have a valid reading
        if value is not None:
            current_time = time.time()
            
            # Initialize recording start time if this is the first data point
            if self.recording_start_time is None:
                self.recording_start_time = current_time
                print("Recording started - capturing 40 seconds of PPG data")
                self.recording_label.config(text="Recording in progress: 0.0 seconds")
            
            # Calculate elapsed time since recording started
            elapsed = current_time - self.recording_start_time
            
            # Only add data if we're within the 40-second window
            if elapsed <= self.max_duration:
                self.timestamps.append(elapsed)
                self.ppg_values.append(value)
                
                # Update recording progress
                self.recording_label.config(text=f"Recording in progress: {elapsed:.1f} seconds")
            else:
                # Mark recording as complete once we reach 40 seconds
                if not self.recording_complete:
                    self.recording_complete = True
                    print(f"Recording complete - captured {len(self.ppg_values)} data points over 40 seconds")
                    self.recording_label.config(text="Recording complete! Press 'Reset Recording' to start again")
        
        # Update the plot
        if len(self.timestamps) > 0:
            self.line.set_data(self.timestamps, self.ppg_values)
            
            # Auto-adjust y-axis if we have real data
            if len(self.ppg_values) > 1:
                min_val = max(0, min(self.ppg_values) - 50)
                max_val = min(1023, max(self.ppg_values) + 50)
                self.ax.set_ylim(min_val, max_val)
            
            # Redraw the canvas
            self.canvas.draw_idle()
        
        # Schedule the next update
        self.root.after(self.update_interval, self.update_plot)
    
    def on_close(self):
        # Clean up resources
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PPGMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    print("Starting PPG Monitor - will record first 40 seconds of signal")
    root.mainloop()