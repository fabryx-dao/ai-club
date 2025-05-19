# PPG Biofeedback Game

A Python application for creating biofeedback games using a PPG (Photoplethysmography) sensor connected to an Arduino.

## Overview

This application receives PPG sensor data from an Arduino and visualizes it in real-time. It includes a simple biofeedback game where users try to maintain their signal above a gradually increasing target level.

## Hardware Requirements

- Arduino (any model)
- PPG sensor (3-pin)
- USB cable to connect Arduino to computer

## Arduino Setup

Upload the following sketch to your Arduino:

```cpp
const int pulsePin = A0; // Analog input pin connected to the sensor
int signalValue = 0;     // Variable to store the sensor value

void setup() {
  Serial.begin(9600);    // Initialize serial communication
}

void loop() {
  signalValue = analogRead(pulsePin); // Read the analog value
  Serial.println(signalValue);        // Print the value to the Serial Monitor
  delay(10);                          // Short delay for stability
}
```

## Software Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Run the application with:

```bash
python main.py
```

Optional command-line arguments:

- `--port PORT`: Specify the Arduino serial port (default: `/dev/cu.usbmodem101`)
- `--baud RATE`: Specify the baud rate (default: `9600`)
- `--debug`: Enable debug output

Example:

```bash
python main.py --port COM3 --debug
```

## Project Structure

- `main.py`: Entry point and configuration
- `arduino_manager.py`: Arduino serial communication and data processing
- `game_logic.py`: Game mechanics and scoring
- `ui_manager.py`: UI rendering and user interactions

## Game Instructions

1. Connect the PPG sensor to your finger
2. Click "Start Challenge" to begin
3. The first 10 seconds are used for calibration (first 3 seconds are ignored)
4. After calibration, try to keep your signal (white line) above the yellow target line
5. Stay out of the red zone for a better score!

## Extending the Game

This project is designed to be modular and extensible. You can create new game modes by extending the `GameManager` class in `game_logic.py`.

## License

MIT License