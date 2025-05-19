#!/usr/bin/env python3
"""
PPG Biofeedback Game - Main Entry Point

This file serves as the entry point for the PPG Biofeedback game application.
It handles configuration and initializes the core components.
"""

import tkinter as tk
import argparse
import os
import sys
from ui_manager import UIManager
from arduino_manager import ArduinoManager
from game_logic import GameManager

# Configuration constants
DEFAULT_PORT = '/dev/cu.usbmodem101'  # Default Arduino port
DEFAULT_BAUD_RATE = 9600              # Default baud rate
APP_TITLE = 'PPG Biofeedback Game'    # Application title
APP_SIZE = '1680x990'                 # Larger window size

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='PPG Biofeedback Game')
    parser.add_argument('--port', type=str, default=DEFAULT_PORT,
                        help=f'Arduino serial port (default: {DEFAULT_PORT})')
    parser.add_argument('--baud', type=int, default=DEFAULT_BAUD_RATE,
                        help=f'Serial baud rate (default: {DEFAULT_BAUD_RATE})')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (more verbose output)')
    return parser.parse_args()

def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure debug mode if requested
    debug_mode = args.debug
    if debug_mode:
        print("Debug mode enabled")
        print(f"Using port: {args.port}")
        print(f"Using baud rate: {args.baud}")
    
    # Create the root Tkinter window
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(APP_SIZE)
    root.configure(bg='black')
    
    # Initialize Arduino Manager and try to connect at startup
    # but DO NOT start reading data until explicitly requested
    arduino_manager = ArduinoManager(
        port=args.port,
        baud_rate=args.baud,
        debug=debug_mode
    )
    
    # Try to connect immediately, but don't start reading data yet
    connection_success = arduino_manager.connect(start_reading=False)
    if connection_success:
        if debug_mode:
            print("Successfully connected to Arduino (not reading data yet)")
    elif debug_mode:
        print(f"Failed to connect to Arduino on port {args.port}. Use --port to specify a different port.")
    
    # Initialize Game Manager (game logic)
    game_manager = GameManager(
        debug=debug_mode
    )
    
    # Initialize UI Manager
    ui_manager = UIManager(
        root=root,
        arduino_manager=arduino_manager,
        game_manager=game_manager,
        debug=debug_mode
    )
    
    # Set up closing handler
    def on_closing():
        if debug_mode:
            print("Application closing")
        arduino_manager.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the application
    print(f"Starting {APP_TITLE}")
    root.mainloop()

if __name__ == "__main__":
    main()