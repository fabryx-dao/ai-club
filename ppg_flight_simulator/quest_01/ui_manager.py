#!/usr/bin/env python3
"""
UI Manager Module

This module handles the UI components, rendering, and user interactions
for the PPG Biofeedback Game.
"""

import tkinter as tk
from tkinter import font as tkfont
import matplotlib
matplotlib.use('TkAgg')  # Set the backend before importing pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Polygon

class UIManager:
    """Manages the UI components and rendering"""
    
    def __init__(self, root, arduino_manager, game_manager, debug=False):
        """Initialize the UI Manager
        
        Args:
            root (tk.Tk): Root Tkinter window
            arduino_manager (ArduinoManager): Arduino manager instance
            game_manager (GameManager): Game logic manager instance
            debug (bool): Enable debug output
        """
        self.root = root
        self.arduino_manager = arduino_manager
        self.game_manager = game_manager
        self.debug = debug
        
        # Configure background color
        self.root.configure(bg='black')
        
        # Set up Monaco-like font
        self.setup_fonts()
        
        # Create UI components
        self.setup_ui()
        
        # Register callbacks
        self.register_callbacks()
        
        # Initialize plot with empty data
        if hasattr(self, 'line'):
            self.line.set_data([], [])
            self.canvas.draw_idle()
        
        # Visualization elements
        self.baseline_line = None
        self.ramp_line = None
        self.ramp_fill = None
        
        # Start the UI update loop
        self.update_interval = 100  # 100ms = 10 updates per second
        self.schedule_update()
    
    def setup_fonts(self):
        """Set up fonts for the application"""
        # Try to create Monaco font, with fallbacks to system monospace fonts
        available_fonts = tkfont.families()
        
        if "Monaco" in available_fonts:
            base_font = "Monaco"
        elif "Consolas" in available_fonts:
            base_font = "Consolas"
        elif "Menlo" in available_fonts:
            base_font = "Menlo"
        elif "Courier" in available_fonts:
            base_font = "Courier"
        else:
            base_font = "TkFixedFont"  # Default monospace font
        
        # Create font instances
        self.font_normal = tkfont.Font(family=base_font, size=9)
        self.font_bold = tkfont.Font(family=base_font, size=9, weight="bold")
        self.font_title = tkfont.Font(family=base_font, size=10, weight="bold")
    
    def setup_ui(self):
        """Set up UI components"""
        # Main frame for the plot
        self.plot_frame = tk.Frame(self.root, bg='black')
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure with black background (larger size for bigger window)
        self.fig = Figure(figsize=(16, 9), dpi=100, facecolor='black', edgecolor='black')
        self.ax = self.fig.add_subplot(111, facecolor='black')
        
        # Style the plot - ultra minimalist approach
        self.ax.tick_params(colors='white', which='both')  # White tick marks
        
        # Hide all spines (borders) except the bottom one
        for position in ['top', 'right', 'left']:
            self.ax.spines[position].set_visible(False)
        
        # Keep only bottom spine (x-axis) and make it white
        self.ax.spines['bottom'].set_color('white')
        
        # Only show x-axis label, no title, no y-axis label
        self.ax.set_xlabel('seconds', color='white', fontsize=9)
        self.ax.set_ylabel('')
        self.ax.set_title('')
        
        # Hide y-axis completely
        self.ax.yaxis.set_visible(False)
        
        # Only show x-axis grid lines
        self.ax.grid(True, axis='x', color='white', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Set x ticks every 10 seconds
        self.ax.set_xticks(range(0, int(self.game_manager.max_duration) + 1, 10))
        
        # Add vertical line at 10s (calibration end)
        self.ax.axvline(x=10, color='gray', linestyle='-', linewidth=0.5)
        
        # White tick labels for x-axis only
        for label in self.ax.get_xticklabels():
            label.set_color('white')
            label.set_fontsize(8)
        
        # PPG signal line (white)
        self.line, = self.ax.plot([], [], color='white', linewidth=1.5)
        
        # Set up axis limits
        self.ax.set_xlim(0, self.game_manager.max_duration)
        self.ax.set_ylim(0, 1023)  # Arduino analog range (0-1023)
        
        # Create the canvas on the frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Bottom control frame with black background
        self.control_frame = tk.Frame(self.root, bg='black')
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Button style
        button_style = {
            'bg': 'white',
            'fg': 'black',
            'activebackground': '#EEEEEE',
            'activeforeground': 'black',
            'font': self.font_normal,
            'relief': tk.FLAT,
            'borderwidth': 1,
            'padx': 10,
            'pady': 5
        }
        
        # Single multi-function button (Start/Stop/Clear)
        self.action_button = tk.Button(
            self.control_frame, 
            text="Start",
            command=self.handle_action_button,
            **button_style
        )
        self.action_button.pack(side=tk.LEFT, padx=5)
    
    def register_callbacks(self):
        """Register callbacks for Arduino and game events"""
        # Register Arduino connection callback
        self.arduino_manager.register_connection_callback(self.on_connection_change)
        
        # Register Arduino data callback
        self.arduino_manager.register_data_callback(self.on_new_data)
        
        # Register game state callback
        self.game_manager.register_state_callback(self.on_game_state_change)
    
    def on_connection_change(self, connected, message, reading=None):
        """Callback for Arduino connection status changes
        
        Args:
            connected (bool): Whether the Arduino is connected
            message (str): Status message
            reading (bool): Whether the Arduino is actively reading data
        """
        # We no longer use a status label, so this method is simplified
        if self.debug:
            print(f"Connection status: {message} (Connected: {connected}, Reading: {reading})")
    
    def on_new_data(self, timestamp, value):
        """Callback for new data from Arduino
        
        Args:
            timestamp (float): Time value
            value (int): PPG signal value
        """
        # Forward to game manager for processing
        if self.game_manager.state != self.game_manager.STATE_IDLE:
            self.game_manager.process_data_point(timestamp, value)
    
    def on_game_state_change(self, state, data):
        """Callback for game state changes
        
        Args:
            state (str): New game state
            data (dict): Game state data
        """
        if state == self.game_manager.STATE_IDLE:
            # Button state is managed by handle_action_button, don't change it here
            # No labels to update
            pass
        
        elif state == self.game_manager.STATE_CALIBRATING:
            # Button should be in Stop state during calibration
            if self.action_button.cget('text') != "Stop":
                self.action_button.config(text="Stop")
            
            # Make sure we're reading data
            if not self.arduino_manager.running and self.arduino_manager.connected:
                self.arduino_manager.start_reading()
        
        elif state == self.game_manager.STATE_CHALLENGE:
            # Ensure visualization elements are created
            self.update_visualization(data)
            
            # Button should be in Stop state during challenge
            if self.action_button.cget('text') != "Stop":
                self.action_button.config(text="Stop")
            
            # Make sure we're still reading data
            if not self.arduino_manager.running and self.arduino_manager.connected:
                self.arduino_manager.start_reading()
        
        elif state == self.game_manager.STATE_COMPLETE:
            # After completion, go to Clear stage
            self.action_button.config(text="Clear")
            
            # Leave connection intact but stop reading data when game is complete
            if self.arduino_manager.running:
                self.arduino_manager.stop_reading()
    
    def handle_action_button(self):
        """Multi-function button handler (Start/Stop/Clear)"""
        current_state = self.game_manager.state
        current_button_text = self.action_button.cget('text')
        
        # Automatically handle connection if needed (except for Clear which doesn't need connection)
        if current_button_text != "Clear" and not self.arduino_manager.connected:
            # Try to connect silently, don't start reading yet
            success = self.arduino_manager.connect(start_reading=False)
            
            if not success and current_button_text == "Start":
                # Just return if connection fails - no status message
                if self.debug:
                    print("Failed to connect to Arduino")
                return
        
        # Logic based on button's current state
        if current_button_text == "Start":
            # Start a new game
            self.clear_visualization()
            self.arduino_manager.clear_data()
            
            # Start reading data from Arduino - this must happen before game start
            success = self.arduino_manager.start_reading()
            if not success:
                # Just return on error - no status message
                if self.debug:
                    print("Failed to start reading from Arduino")
                return
                
            # Start the game logic
            self.game_manager.start_game()
            self.action_button.config(text="Stop")
            
        elif current_button_text == "Stop":
            # Stop the current game
            self.arduino_manager.stop_reading()
            
            # Keep the visualization but stop the game
            self.game_manager.reset_game()
            
            # Change button to clear mode
            self.action_button.config(text="Clear")
            
        elif current_button_text == "Clear":
            # Force a complete reset of the plot
            self.clear_visualization()
            
            # Also clear the data buffer in Arduino manager
            self.arduino_manager.clear_data()
            
            # Force a redraw with empty data
            self.line.set_data([], [])
            self.canvas.draw()  # Use draw() instead of draw_idle() for immediate effect
            
            # Change button back to start
            self.action_button.config(text="Start")
    
    def update_visualization(self, data):
        """Update the visualization elements based on game data
        
        Args:
            data (dict): Game state data
        """
        # Only add visualization elements if we have baseline data
        baseline = data.get('baseline')
        if baseline is None:
            return
            
        # Get challenge parameters
        challenge_start = self.game_manager.challenge_start_time
        max_duration = self.game_manager.max_duration
        ramp_delta = self.game_manager.ramp_delta
        
        # Calculate ramp end value (we'll need this even though we don't show the line)
        ramp_end_value = baseline + ramp_delta
        
        # Create or update the red fill under the ramp - the only visualization element
        vertices = [
            (challenge_start, self.ax.get_ylim()[0]),  # Bottom left
            (challenge_start, baseline),               # Top left
            (max_duration, ramp_end_value),            # Top right
            (max_duration, self.ax.get_ylim()[0])      # Bottom right
        ]
        
        if self.ramp_fill is None:
            self.ramp_fill = self.ax.add_patch(Polygon(vertices, closed=True, facecolor='red', alpha=0.3))
        else:
            self.ramp_fill.set_xy(vertices)
            
        # We no longer create baseline_line or ramp_line
        self.baseline_line = None
        self.ramp_line = None
    
    def clear_visualization(self):
        """Clear all visualization elements"""
        # Clear the entire Matplotlib figure
        self.ax.clear()
        
        # Reset the look and feel of the plot - ultra minimalist
        self.ax.set_facecolor('black')
        self.ax.tick_params(colors='white', which='both')
        
        # Hide all spines (borders) except the bottom one
        for position in ['top', 'right', 'left']:
            self.ax.spines[position].set_visible(False)
        
        # Keep only bottom spine (x-axis) and make it white
        self.ax.spines['bottom'].set_color('white')
            
        # Only show x-axis label, no title, no y-axis label
        self.ax.set_xlabel('seconds', color='white', fontsize=9)
        self.ax.set_ylabel('')
        self.ax.set_title('')
        
        # Hide y-axis completely
        self.ax.yaxis.set_visible(False)
        
        # Only show x-axis grid lines
        self.ax.grid(True, axis='x', color='white', alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Set x ticks every 10 seconds
        self.ax.set_xticks(range(0, int(self.game_manager.max_duration) + 1, 10))
        
        # Add vertical line at 10s (calibration end)
        self.ax.axvline(x=10, color='gray', linestyle='-', linewidth=0.5)
        
        # White tick labels for x-axis only
        for label in self.ax.get_xticklabels():
            label.set_color('white')
            label.set_fontsize(8)
        
        # Reset signal line
        self.line, = self.ax.plot([], [], color='white', linewidth=1.5)
        
        # Remove other elements
        self.baseline_line = None
        self.ramp_line = None
        self.ramp_fill = None
        
        # Reset axis limits to default
        self.ax.set_xlim(0, self.game_manager.max_duration)
        self.ax.set_ylim(0, 1023)  # Arduino analog range (0-1023)
        
        # Force redraw immediately
        self.canvas.draw()
    
    def update_plot(self):
        """Update the plot with latest data"""
        # Only update if we have a connection and are in an active game state
        if not self.arduino_manager.connected:
            # Schedule next update and return
            self.schedule_update()
            return
            
        # Get all data (don't limit by time_range to ensure we keep all points)
        timestamps, values = self.arduino_manager.get_recent_data()
        
        if timestamps and values:
            # Update the signal line
            self.line.set_data(timestamps, values)
            
            # Adjust x-axis to show full game duration or all data points
            if timestamps:
                # Ensure the x-axis shows all data
                min_time = min(timestamps)
                max_time = max(timestamps)
                
                # Add small margin
                margin = (max_time - min_time) * 0.05 if max_time > min_time else 1.0
                
                # Ensure x-axis is at least game.max_duration wide
                if max_time - min_time < self.game_manager.max_duration:
                    max_time = min_time + self.game_manager.max_duration
                
                self.ax.set_xlim(min_time - margin, max_time + margin)
            
            # Auto-adjust y-axis if we have real data
            if len(values) > 1:
                min_val = max(0, min(values) - 50)
                max_val = min(1023, max(values) + 50)
                
                # If we have a baseline, make sure it's visible
                game_data = self.game_manager.get_game_state()
                baseline = game_data.get('baseline')
                
                if baseline is not None:
                    ramp_delta = self.game_manager.ramp_delta
                    max_val = max(max_val, baseline + ramp_delta + 20)
                    
                self.ax.set_ylim(min_val, max_val)
                
                # Update fill if y-axis changed and ramp_fill exists
                if self.ramp_fill is not None:
                    self.update_visualization(game_data)
            
            # Redraw the canvas
            self.canvas.draw_idle()
        
        # Schedule next update
        self.schedule_update()
    
    def schedule_update(self):
        """Schedule the next UI update"""
        self.root.after(self.update_interval, self.update_plot)