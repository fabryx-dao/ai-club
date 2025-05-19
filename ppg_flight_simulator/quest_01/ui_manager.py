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
        
        # Enable debug
        self.debug = True
        
        # Configure background color
        self.root.configure(bg='black')
        
        # Set up Monaco-like font
        self.setup_fonts()
        
        # UI state
        self.current_screen = 'intro'  # Start with intro screen
        
        # Create the frames for different screens
        self.intro_frame = tk.Frame(self.root, bg='black')
        self.game_frame = tk.Frame(self.root, bg='black')
        
        # Initialize matplotlib elements
        self.fig = None
        self.ax = None
        self.canvas = None
        self.line = None
        
        # Visualization elements
        self.baseline_line = None
        self.ramp_line = None
        self.ramp_fill = None
        self.wave_fill = None  # New blue fill for wave down phase
        
        # Setup intro screen first
        self.setup_intro_ui()
        
        # Then setup game UI
        self.setup_game_ui()
        
        # Show intro screen initially
        self.show_intro_screen()
        
        # Register callbacks
        self.register_callbacks()
        
        # Start the UI update loop
        self.update_interval = 100  # 100ms = 10 updates per second
        # Only schedule updates when in game mode
        if self.current_screen == 'game':
            self.schedule_update()
            
        if self.debug:
            print("UI Manager initialized successfully")
    
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
    
    def setup_intro_ui(self):
        """Set up the intro screen with game selection buttons"""
        # Title label
        title_label = tk.Label(
            self.intro_frame,
            text="Biofeedback Game",
            fg="white",
            bg="black",
            font=self.font_title
        )
        title_label.pack(pady=50)
        
        # Button style
        button_style = {
            'bg': 'white',
            'fg': 'black',
            'activebackground': '#EEEEEE',
            'activeforeground': 'black',
            'font': self.font_normal,
            'relief': tk.FLAT,
            'borderwidth': 1,
            'padx': 20,
            'pady': 10,
            'width': 15
        }
        
        # Buttons frame
        buttons_frame = tk.Frame(self.intro_frame, bg='black')
        buttons_frame.pack(pady=20)
        
        # Fire game button
        self.fire_button = tk.Button(
            buttons_frame,
            text="Fire",
            command=lambda: self.start_game_mode('fire'),
            **button_style
        )
        self.fire_button.pack(side=tk.LEFT, padx=20)
        
        # Wave game button
        self.wave_button = tk.Button(
            buttons_frame,
            text="Wave",
            command=lambda: self.start_game_mode('wave'),
            **button_style
        )
        self.wave_button.pack(side=tk.LEFT, padx=20)
    
    def setup_game_ui(self):
        """Set up the game screen with plot and controls"""
        # Main frame for the plot
        self.plot_frame = tk.Frame(self.game_frame, bg='black')
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
        self.control_frame = tk.Frame(self.game_frame, bg='black')
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
        
        # Action button (Start/Stop/Clear)
        self.action_button = tk.Button(
            self.control_frame, 
            text="Start",
            command=self.handle_action_button,
            **button_style
        )
        self.action_button.pack(side=tk.LEFT, padx=5)
        
        # Quit button to return to menu
        self.quit_button = tk.Button(
            self.control_frame,
            text="Quit",
            command=self.handle_quit_button,
            **button_style
        )
        self.quit_button.pack(side=tk.RIGHT, padx=5)
        
        # Add pass/fail indicator (initially hidden)
        self.pass_fail_label = tk.Label(
            self.control_frame,
            text="",
            fg="black",
            bg="black",
            font=("Arial", 24, "bold")  # Larger font for visibility
        )
        self.pass_fail_label.pack(side=tk.RIGHT, padx=15)
    
    def show_intro_screen(self):
        """Show the intro/selection screen, hide the game screen"""
        try:
            # First, ensure we stop data reading if it's running
            if self.arduino_manager.running:
                self.arduino_manager.stop_reading()
            
            # Force reset the game state
            self.game_manager.reset_game()
            
            # Clear visualization completely
            if hasattr(self, 'ax') and self.ax is not None:
                self.clear_visualization()
            
            # Clear any data in the Arduino manager
            self.arduino_manager.clear_data()
            
            # Reset the action button to Start
            if hasattr(self, 'action_button'):
                self.action_button.config(text="Start")
            
            # Hide game frame, show intro frame
            self.game_frame.pack_forget()
            self.intro_frame.pack(fill=tk.BOTH, expand=True)
            
            # Update current screen
            self.current_screen = 'intro'
            
            # Cancel any scheduled updates
            if hasattr(self, '_update_id'):
                self.root.after_cancel(self._update_id)
                
            if self.debug:
                print("Successfully switched to intro screen")
        except Exception as e:
            if self.debug:
                print(f"Error returning to intro screen: {e}")
    
    def start_game_mode(self, mode):
        """Start a specific game mode (fire or wave)
        
        Args:
            mode (str): Game mode to start
        """
        # Set the game mode
        if mode == 'fire':
            self.game_manager.set_game_mode(self.game_manager.MODE_FIRE)
        else:
            self.game_manager.set_game_mode(self.game_manager.MODE_WAVE)
        
        # Debug print
        if self.debug:
            print(f"Starting game mode: {mode}, duration: {self.game_manager.max_duration}s")
            
        try:
            # Make sure any ongoing updates are cancelled
            if hasattr(self, '_update_id'):
                try:
                    self.root.after_cancel(self._update_id)
                except:
                    pass
            
            # Reset game state 
            self.game_manager.reset_game()
            
            # Clear any data in Arduino manager
            self.arduino_manager.clear_data()
            
            # Make sure Arduino is not reading
            if self.arduino_manager.running:
                self.arduino_manager.stop_reading()
                
            # Completely recreate the plot if needed
            if self.fig is None or self.ax is None:
                if self.debug:
                    print("Creating new matplotlib figure")
                self.fig = Figure(figsize=(16, 9), dpi=100, facecolor='black', edgecolor='black')
                self.ax = self.fig.add_subplot(111, facecolor='black')
                
                if hasattr(self, 'canvas') and self.canvas is not None:
                    self.canvas.get_tk_widget().destroy()
                
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                # Clear the plot completely
                self.ax.clear()
            
            # Reset the plot style
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
            
            # Create vertical line at 10s
            self.ax.axvline(x=10, color='gray', linestyle='-', linewidth=0.5)
            
            # For Wave mode, add a second vertical line at 40s
            if mode == 'wave':
                self.ax.axvline(x=40, color='gray', linestyle='-', linewidth=0.5)
            
            # Set x ticks and labels to reflect the appropriate duration
            max_duration = self.game_manager.max_duration
            self.ax.set_xlim(0, max_duration)
            self.ax.set_xticks(range(0, int(max_duration) + 1, 10))
            
            for label in self.ax.get_xticklabels():
                label.set_color('white')
                label.set_fontsize(8)
            
            # PPG signal line (white)
            self.line, = self.ax.plot([], [], color='white', linewidth=1.5)
            
            # Set y-axis limits
            self.ax.set_ylim(0, 1023)  # Arduino analog range (0-1023)
            
            # Reset visualization elements
            self.baseline_line = None
            self.ramp_line = None
            self.ramp_fill = None
            self.wave_fill = None
            
            # Force draw the canvas
            self.canvas.draw()
            
            # Hide intro frame, show game frame
            self.intro_frame.pack_forget()
            self.game_frame.pack(fill=tk.BOTH, expand=True)
            
            # Update current screen
            self.current_screen = 'game'
            
            # Reset action button
            self.action_button.config(text="Start")
            
            # Start the UI update loop
            self.schedule_update()
            
        except Exception as e:
            # Print any errors that occur during setup
            print(f"Error setting up game mode: {e}")
            # If there's an error, try to return to the intro screen
            try:
                self.handle_quit_button()
            except:
                pass
    
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
                
            # Make one final update to the pass/fail indicator to freeze it at the final state
            # The indicator will stay as-is until the user clears the game
            self.update_pass_fail_indicator(data)
    
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
            
            # Reset the pass/fail indicator
            if hasattr(self, 'pass_fail_label'):
                self.pass_fail_label.config(text="", fg="black")
            
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
        game_mode = data.get('game_mode')
        
        # Calculate ramp end value
        ramp_end_value = baseline + ramp_delta
        
        if game_mode == self.game_manager.MODE_FIRE:
            # Fire mode - simple red fill from 10s to 40s
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
                
            # Make sure wave fill is not visible
            if self.wave_fill is not None:
                self.wave_fill.set_visible(False)
                
        elif game_mode == self.game_manager.MODE_WAVE:
            # Wave mode - red fill from 10s to 40s, then blue fill from 40s to 70s
            wave_transition = self.game_manager.wave_transition_time
            
            # Red fill for first phase (breathe up) - bottom half is colored
            red_vertices = [
                (challenge_start, self.ax.get_ylim()[0]),  # Bottom left
                (challenge_start, baseline),               # Top left
                (wave_transition, ramp_end_value),         # Top right
                (wave_transition, self.ax.get_ylim()[0])   # Bottom right
            ]
            
            if self.ramp_fill is None:
                self.ramp_fill = self.ax.add_patch(Polygon(red_vertices, closed=True, facecolor='red', alpha=0.3))
            else:
                self.ramp_fill.set_xy(red_vertices)
                self.ramp_fill.set_visible(True)
            
            # Blue fill for second phase (breathe down) - top half is colored
            # The ramp should be symmetrically reflected around the wave_transition point (40s)
            # First phase goes from baseline to ramp_end_value over 30 seconds
            # Second phase should go from ramp_end_value back to baseline over 30 seconds
            
            # Calculate upper bound for plot
            upper_bound = self.ax.get_ylim()[1]
            
            blue_vertices = [
                (wave_transition, ramp_end_value),         # Bottom left
                (wave_transition, upper_bound),            # Top left
                (max_duration, upper_bound),               # Top right
                (max_duration, baseline),                  # Bottom right
            ]
            
            if self.wave_fill is None:
                self.wave_fill = self.ax.add_patch(Polygon(blue_vertices, closed=True, facecolor='blue', alpha=0.3))
            else:
                self.wave_fill.set_xy(blue_vertices)
                self.wave_fill.set_visible(True)
        
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
        
        # For Wave mode, add a second vertical line at 40s
        if self.game_manager.game_mode == self.game_manager.MODE_WAVE:
            self.ax.axvline(x=40, color='gray', linestyle='-', linewidth=0.5)
        
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
        self.wave_fill = None
        
        # Reset axis limits to default
        self.ax.set_xlim(0, self.game_manager.max_duration)
        self.ax.set_ylim(0, 1023)  # Arduino analog range (0-1023)
        
        # Any pass/fail feedback is automatically cleared when we call ax.clear()
        
        # Force redraw immediately
        self.canvas.draw()
        
        if self.debug:
            print("Visualization cleared")
    
    def update_plot(self):
        """Update the plot with latest data"""
        # Only update if we're in game mode and have a connection
        if self.current_screen != 'game' or not self.arduino_manager.connected:
            # Schedule next update and return
            self.schedule_update()
            return
            
        try:
            # Get all data (don't limit by time_range to ensure we keep all points)
            timestamps, values = self.arduino_manager.get_recent_data()
            
            if timestamps and values and hasattr(self, 'line') and self.line is not None:
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
                    
                    # Set x-axis limits
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
                    
                    # Update visualization based on game mode
                    if self.game_manager.state != self.game_manager.STATE_IDLE:
                        self.update_visualization(game_data)
                        
                        # Only update pass/fail indicator if we're in the challenge state
                        # and calibration is complete (so we have a baseline to compare against)
                        if self.game_manager.state == self.game_manager.STATE_CHALLENGE:
                            # Update the pass/fail indicator in real-time
                            self.update_pass_fail_indicator(game_data)
                
                # Redraw the canvas
                self.canvas.draw_idle()
        except Exception as e:
            if self.debug:
                print(f"Error updating plot: {e}")
        
        # Schedule next update
        self.schedule_update()
    
    def update_pass_fail_indicator(self, data):
        """Update the pass/fail indicator in the footer
        
        Args:
            data (dict): Game state data with current values
        """
        try:
            # Get the necessary data for evaluation
            current_value = data.get('current_value')
            target = data.get('target')
            game_mode = data.get('game_mode')
            
            # Skip if we don't have enough data
            if current_value is None or target is None or game_mode is None:
                return
            
            # Determine if the user is currently passing or failing
            passed = False
            
            # IMPORTANT: The pass/fail test needs to match the visual representation
            # In Fire mode: red area is below the target line, so pass if above target
            # In Wave mode: blue area is above the target line, so pass if below target
            
            if game_mode == self.game_manager.MODE_FIRE:
                # Fire mode: pass if signal is ABOVE target (not in red area)
                passed = current_value >= target
            else:
                # Wave mode: pass if signal is BELOW target (not in blue area)
                passed = current_value <= target
            
            # Set the symbol and color based on pass/fail
            symbol = "✓" if passed else "✗"
            color = "#00FF00" if passed else "#FF0000"  # Bright green or red
            
            # Update or create the indicator label
            if hasattr(self, 'pass_fail_label') and self.pass_fail_label:
                self.pass_fail_label.config(text=symbol, fg=color)
            else:
                # Create the label if it doesn't exist
                self.pass_fail_label = tk.Label(
                    self.control_frame,
                    text=symbol,
                    fg=color,
                    bg="black",
                    font=("Arial", 24, "bold")  # Larger font for visibility
                )
                self.pass_fail_label.pack(side=tk.RIGHT, padx=15)
            
        except Exception as e:
            print(f"Error updating pass/fail indicator: {e}")
    
    # This method is no longer used but kept for reference
    def show_pass_fail_feedback(self, data):
        """Display pass/fail feedback at the end of the game (no longer used)"""
        # This method is replaced by update_pass_fail_indicator
        pass
    
    def handle_quit_button(self):
        """Handle quit button press, properly cleaning up based on current state"""
        if self.debug:
            print("Quit button pressed - returning to menu")
            
        # Stop reading data if it's running
        if self.arduino_manager.running:
            self.arduino_manager.stop_reading()
            
        # Reset game state
        self.game_manager.reset_game()
        
        # Clear any data in Arduino manager
        self.arduino_manager.clear_data()
            
        # Cancel any ongoing updates
        if hasattr(self, '_update_id'):
            try:
                self.root.after_cancel(self._update_id)
            except:
                pass
        
        # Update UI state for next game
        if hasattr(self, 'action_button'):
            self.action_button.config(text="Start")
        
        # Reset pass/fail indicator
        if hasattr(self, 'pass_fail_label'):
            self.pass_fail_label.config(text="", fg="black")
            
        # Reset visualization elements
        self.baseline_line = None
        self.ramp_line = None
        self.ramp_fill = None
        self.wave_fill = None
                
        # Clear out existing frames
        self.game_frame.pack_forget()
        
        # Show intro frame
        self.intro_frame.pack(fill=tk.BOTH, expand=True)
        
        # Update current screen
        self.current_screen = 'intro'
        
        if self.debug:
            print("Successfully returned to intro screen")
    
    def schedule_update(self):
        """Schedule the next UI update"""
        self._update_id = self.root.after(self.update_interval, self.update_plot)