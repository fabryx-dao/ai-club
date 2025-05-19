#!/usr/bin/env python3
"""
Arduino Manager Module

This module handles all communication with the Arduino,
including serial connection, data reading, and signal processing.
"""

import serial
import time
import threading
import random
from collections import deque

class ArduinoManager:
    """Handles communication with Arduino and signal processing"""
    
    def __init__(self, port, baud_rate=9600, debug=False, use_fake_data=False):
        """Initialize the Arduino manager
        
        Args:
            port (str): Serial port for the Arduino
            baud_rate (int): Baud rate for serial communication
            debug (bool): Enable debug output
            use_fake_data (bool): Use fake PPG data instead of real Arduino data
        """
        self.port = port
        self.baud_rate = baud_rate
        self.debug = debug
        self.use_fake_data = use_fake_data
        
        self.ser = None
        self.connected = False
        self.running = False
        self.read_thread = None
        
        # Data buffers - increased to hold full game duration (40s at ~10Hz = 400 points, with margin)
        self.data_buffer = deque(maxlen=5000)  # Store up to 5000 data points
        self.timestamps = deque(maxlen=5000)   # Corresponding timestamps
        
        # Callback function to notify when new data is available
        self.data_callback = None
        
        # Connection status callback
        self.connection_callback = None
        
        # Fake data generation parameters
        self.fake_data_base = 575  # Base value for fake data
        self.fake_data_game_mode = None  # Will store the game mode for fake data generation
        self.fake_data_calibration_end = 10.0  # Time at which calibration ends
        self.fake_data_game_end = 40.0  # Time at which the fire game ends
        self.fake_data_wave_transition = 40.0  # Time at which wave game transitions
        self.fake_data_wave_end = 70.0  # Time at which the wave game ends
        
        # No automatic connection at init - will be called from main
    
    def connect(self, start_reading=False):
        """Attempt to connect to the Arduino or set up fake data
        
        Args:
            start_reading (bool): Whether to start reading data after connecting
            
        Returns:
            bool: Whether connection was successful
        """
        # If using fake data, no need for actual connection
        if self.use_fake_data:
            self.connected = True
            
            if self.debug:
                print("Fake data mode active - no Arduino connection needed")
            
            # Notify via callback if provided, but make it look like normal connection
            if self.connection_callback:
                status_msg = "Connected"
                if start_reading:
                    status_msg += " & Reading"
                self.connection_callback(True, status_msg, self.running)
            
            # Only start reading if explicitly requested
            if start_reading and not self.running:
                self.start_reading()
            
            return True
            
        # Use actual Arduino connection
        try:
            # Close existing connection if any
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.running = False
                
                if self.read_thread and self.read_thread.is_alive():
                    self.read_thread.join(timeout=1.0)
            
            # Open new connection
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for connection to stabilize
            self.ser.reset_input_buffer()
            self.connected = True
            
            if self.debug:
                print(f"Connected to Arduino on {self.port}")
            
            # Notify via callback if provided
            if self.connection_callback:
                # Simplified status message focusing on connection state
                status_msg = "Connected"
                if start_reading:
                    status_msg += " & Reading"
                self.connection_callback(True, status_msg, self.running)
            
            # Only start reading if explicitly requested
            if start_reading and not self.running:
                self.start_reading()
            
            return True
            
        except Exception as e:
            self.connected = False
            self.ser = None
            self.running = False
            
            if self.debug:
                print(f"Error connecting to Arduino: {str(e)}")
            
            # Notify via callback if provided
            if self.connection_callback:
                self.connection_callback(False, f"Disconnected: {str(e)}", False)
            
            return False
    
    def register_data_callback(self, callback):
        """Register a callback function for new data
        
        Args:
            callback (function): Function to call when new data is received.
                                Will be called with (timestamp, value) parameters.
        """
        self.data_callback = callback
    
    def register_connection_callback(self, callback):
        """Register a callback function for connection status updates
        
        Args:
            callback (function): Function to call when connection status changes.
                                Will be called with (connected, message, reading) parameters.
        """
        self.connection_callback = callback
    
    def start_reading(self):
        """Start the data reading thread"""
        # Special handling for fake data mode
        if self.use_fake_data:
            if not self.connected:
                # Ensure connected state is set for fake data mode
                self.connected = True
                
            # Only clear data if we're restarting reading after a stop
            if not self.running:
                self.clear_data()
            
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop)
            self.read_thread.daemon = True  # Thread will exit when main program exits
            self.read_thread.start()
            
            if self.debug:
                print("Started fake data generation thread")
            
            # Notify about reading status change (hide the fact it's fake data)
            if self.connection_callback:
                self.connection_callback(True, "Connected & Reading", True)
            
            return True
        
        # Original behavior for real Arduino connection
        if not self.connected or self.ser is None or not self.ser.is_open:
            if self.debug:
                print("Cannot start reading - not connected")
            self.connected = False  # Make sure state is consistent
            self.running = False
            
            # Notify via callback if provided
            if self.connection_callback:
                self.connection_callback(False, "No valid connection", False)
                
            return False
        
        # Only clear data if we're restarting reading after a stop
        if not self.running:
            self.clear_data()
        
        self.running = True
        self.read_thread = threading.Thread(target=self._read_loop)
        self.read_thread.daemon = True  # Thread will exit when main program exits
        self.read_thread.start()
        
        if self.debug:
            print("Started Arduino reading thread")
        
        # Notify about reading status change
        if self.connection_callback:
            self.connection_callback(True, "Connected & Reading", True)
        
        return True
    
    def stop_reading(self):
        """Stop the data reading thread"""
        if not self.running:
            return  # Nothing to do if not running
            
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)  # Wait up to 1 second for thread to end
        
        if self.debug:
            print("Stopped Arduino reading thread")
        
        # Notify that we stopped reading but are still connected
        if self.connection_callback and self.connected:
            self.connection_callback(True, "Connected", False)
    
    def _generate_fake_data(self, current_time):
        """Generate fake PPG data that's guaranteed to succeed in the game
        
        Args:
            current_time (float): Current time in seconds
            
        Returns:
            int: Fake PPG value that will lead to game success
        """
        # Base value with random oscillation
        value = self.fake_data_base + random.randint(-10, 10)
        
        # During calibration phase (0-10s), just return oscillating values
        if current_time <= self.fake_data_calibration_end:
            return value
            
        # Determine game mode from elapsed time if not already known
        if self.fake_data_game_mode is None:
            # If time goes beyond 40s, we must be in wave mode
            if current_time > self.fake_data_game_end:
                self.fake_data_game_mode = 'wave'
            # We'll assume fire mode until we see evidence of wave mode
            else:
                self.fake_data_game_mode = 'fire'
        
        # For fire game (10-40s), gradually increase signal to end above target
        if self.fake_data_game_mode == 'fire':
            # Calculate how far we are in the game (0.0 to 1.0)
            game_progress = (current_time - self.fake_data_calibration_end) / (self.fake_data_game_end - self.fake_data_calibration_end)
            game_progress = max(0.0, min(1.0, game_progress))  # Clamp to 0-1 range
            
            # Add gradually increasing trend (ensure we end up comfortably above target)
            trend_value = 60 * game_progress  # Will add up to +60 at the end
            return int(value + trend_value)
            
        # For wave game (10-70s)
        elif self.fake_data_game_mode == 'wave':
            # First phase (10-40s) - go up
            if current_time <= self.fake_data_wave_transition:
                # Calculate progress in first phase (0.0 to 1.0)
                phase_progress = (current_time - self.fake_data_calibration_end) / (self.fake_data_wave_transition - self.fake_data_calibration_end)
                phase_progress = max(0.0, min(1.0, phase_progress))  # Clamp to 0-1 range
                
                # Add gradually increasing trend
                trend_value = 60 * phase_progress  # Will add up to +60 at transition
                return int(value + trend_value)
                
            # Second phase (40-70s) - go down
            else:
                # Calculate progress in second phase (0.0 to 1.0)
                phase_progress = (current_time - self.fake_data_wave_transition) / (self.fake_data_wave_end - self.fake_data_wave_transition)
                phase_progress = max(0.0, min(1.0, phase_progress))  # Clamp to 0-1 range
                
                # Start from peak and gradually decrease to below baseline
                peak_value = 60  # Peak value added at the transition point
                trend_value = peak_value - (peak_value + 20) * phase_progress  # Will go from +60 to -20
                return int(value + trend_value)
        
        # Fallback - just return the oscillating base value
        return value

    def _read_loop(self):
        """Main loop for reading data from Arduino or generating fake data (runs in separate thread)"""
        start_time = time.time()  # Reference time for timestamps
        
        # If using fake data, run a separate loop that generates data
        if self.use_fake_data:
            # Reset game mode detection on each new data stream
            self.fake_data_game_mode = None
            
            # Loop for generating fake data at regular intervals
            while self.running and self.connected:
                try:
                    current_time = time.time() - start_time  # Time since start
                    
                    # Generate fake data
                    value = self._generate_fake_data(current_time)
                    
                    # Store the value
                    self.data_buffer.append(value)
                    self.timestamps.append(current_time)
                    
                    # Debug output (don't expose that it's fake data unless debug is on)
                    if self.debug:
                        timestamp = time.strftime("%H:%M:%S", time.localtime())
                        print(f"{timestamp} - PPG value: {value} (fake)")
                    
                    # Notify via callback if provided
                    if self.data_callback:
                        self.data_callback(current_time, value)
                    
                    # Sleep to simulate 10Hz data rate (same as Arduino)
                    time.sleep(0.1)
                    
                except Exception as e:
                    # Handle errors
                    if self.debug:
                        print(f"Error generating fake data: {str(e)}")
                    
                    # Small sleep to avoid tight loop on error
                    time.sleep(0.1)
            
            # When we exit the loop, make sure running is set to False
            self.running = False
            
            if self.debug:
                print("Exiting fake data generation loop")
            
            return
        
        # Original Arduino read loop
        while self.running and self.connected and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    # Read a line from serial
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    try:
                        # Convert to int and store
                        value = int(line)
                        current_time = time.time() - start_time  # Time since start
                        
                        # Store the value
                        self.data_buffer.append(value)
                        self.timestamps.append(current_time)
                        
                        # Debug output
                        if self.debug:
                            timestamp = time.strftime("%H:%M:%S", time.localtime())
                            print(f"{timestamp} - PPG value: {value}")
                        
                        # Notify via callback if provided
                        if self.data_callback:
                            self.data_callback(current_time, value)
                            
                    except ValueError:
                        # Skip invalid values
                        if self.debug:
                            print(f"Invalid data received: {line}")
                
                # Small sleep to avoid tight loop
                time.sleep(0.01)
                
            except Exception as e:
                # Handle connection errors
                self.connected = False
                
                if self.debug:
                    print(f"Connection error in read loop: {str(e)}")
                
                # Notify via callback if provided
                if self.connection_callback:
                    self.connection_callback(False, f"Connection lost: {str(e)}", False)
                
                # Exit the loop
                break
                
        # When we exit the loop, make sure running is set to False
        self.running = False
        
        if self.debug:
            print("Exiting Arduino read loop")
    
    def get_recent_data(self, max_points=None, time_range=None):
        """Get recent data points, optionally limited by count or time range
        
        Args:
            max_points (int, optional): Maximum number of points to return
            time_range (float, optional): Time range in seconds from the latest point
        
        Returns:
            tuple: (timestamps_list, values_list)
        """
        if not self.data_buffer:
            return [], []
        
        if time_range is not None and self.timestamps:
            # Get data within time range from the latest reading
            latest_time = self.timestamps[-1]
            cutoff_time = latest_time - time_range
            
            # Find points within the time range
            valid_indices = [i for i, t in enumerate(self.timestamps) if t >= cutoff_time]
            
            timestamps = [self.timestamps[i] for i in valid_indices]
            values = [self.data_buffer[i] for i in valid_indices]
        else:
            # Use all available data
            timestamps = list(self.timestamps)
            values = list(self.data_buffer)
        
        # Limit by max_points if specified
        if max_points is not None and max_points > 0 and len(timestamps) > max_points:
            start_idx = len(timestamps) - max_points
            timestamps = timestamps[start_idx:]
            values = values[start_idx:]
        
        return timestamps, values
    
    def clear_data(self):
        """Clear all stored data"""
        self.data_buffer.clear()
        self.timestamps.clear()
        
        if self.debug:
            print("Cleared all data buffers")
    
    def cleanup(self):
        """Clean up resources before exit"""
        self.stop_reading()
        
        if self.ser and self.ser.is_open:
            self.ser.close()
            
            if self.debug:
                print("Serial connection closed")