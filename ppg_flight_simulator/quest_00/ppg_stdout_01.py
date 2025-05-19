import serial
import time

# Configuration
port = '/dev/cu.usbmodem101'  # Your Arduino port
baud_rate = 9600              # Make sure this matches your Arduino's baud rate
sample_interval = 0.1         # 100ms between readings

def read_ppg_data():
    try:
        # Open serial connection to Arduino
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"Connected to Arduino on {port}")
        
        # Give the serial connection time to initialize
        time.sleep(2)
        
        # Main loop to read and print data
        while True:
            # Check if data is available to read
            if ser.in_waiting > 0:
                # Read a line from the serial port
                line = ser.readline().decode('utf-8').strip()
                
                # Print the PPG value with timestamp
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                print(f"{timestamp} - PPG value: {line}")
            
            # Wait for the specified interval
            time.sleep(sample_interval)
            
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        # Make sure to close the serial connection
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed")

if __name__ == "__main__":
    read_ppg_data()