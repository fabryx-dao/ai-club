#!/usr/bin/env python3
"""
Arduino Manager Module

This module handles all communication with the Arduino,
including serial connection, data reading, and signal processing.
"""

import serial
import time
import threading
from collections import deque

class ArduinoManager:
    """Handles communication with Arduino and signal processing"""
    
    def __init__(self, port, baud_rate=9600, debug=False):
        """Initialize the Arduino manager
        
        Args:
            port (str): Serial port for the Arduino
            baud_rate (int): Baud rate for serial communication
            debug (bool): Enable debug output
        """
        self.port = port
        self.baud_rate = baud_rate
        self.debug = debug
        
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
        
        # No automatic connection at init - will be called from main
    
    def connect(self, start_reading=False):
        """Attempt to connect to the Arduino
        
        Args:
            start_reading (bool): Whether to start reading data after connecting
            
        Returns:
            bool: Whether connection was successful
        """
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
    
    def _read_loop(self):
        """Main loop for reading data from Arduino (runs in separate thread)"""
        start_time = time.time()  # Reference time for timestamps
        
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