import time
import math
import random
import numpy as np
from collections import deque

# Try importing serial - make it optional for development
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    print("PySerial not installed. Arduino functionality will be disabled.")
    print("Install with: pip install pyserial")
    SERIAL_AVAILABLE = False

class PPGProcessor:
    """Process PPG data from Arduino for biofeedback challenges"""
    
    def __init__(self, sampling_rate=100):
        self.sampling_rate = sampling_rate
        self.buffer_size = 10 * sampling_rate  # 10 seconds of data
        self.data_buffer = deque(maxlen=self.buffer_size)
        self.hr_buffer = deque(maxlen=30)  # Store recent heart rate estimates
        self.baseline_hr = 70  # Default baseline HR
        self.max_hr = 0  # Maximum HR during challenge
        self.serial_connection = None
    
    def setup_serial(self, port, baud=9600):
        """Setup serial connection to Arduino"""
        if not SERIAL_AVAILABLE:
            return False
            
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=1)
            return True
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
    
    def read_ppg_data(self):
        """Read data from Arduino if available"""
        if not self.serial_connection:
            # Generate synthetic data for testing
            return self.generate_synthetic_data()
            
        try:
            if self.serial_connection.in_waiting:
                line = self.serial_connection.readline().decode('utf-8').strip()
                # Parse PPG value from Arduino output
                if line.startswith("PPG:"):
                    parts = line.split("|")
                    if len(parts) > 0:
                        ppg_str = parts[0].replace("PPG:", "").strip()
                        try:
                            ppg_value = int(ppg_str)
                            self.data_buffer.append(ppg_value)
                            return ppg_value
                        except ValueError:
                            pass
        except Exception as e:
            print(f"Error reading from Arduino: {e}")
            
        return None
    
    def generate_synthetic_data(self):
        """Generate synthetic PPG data for testing"""
        # Simulate a PPG signal with heartbeats
        t = time.time()
        heart_rate = 60 + 20 * math.sin(t / 10)  # HR varies between 40-80 BPM
        period = 60 / heart_rate
        
        # Create a synthetic pulse
        phase = (t % period) / period
        pulse = math.sin(phase * 2 * math.pi)
        
        # Add some noise
        noise = random.uniform(-0.1, 0.1)
        
        # Scale to typical PPG range (400-800 from Arduino example)
        ppg_value = int(600 + 100 * pulse + 50 * noise)
        
        self.data_buffer.append(ppg_value)
        return ppg_value
    
    def calculate_heart_rate(self):
        """Calculate heart rate from PPG data using peak detection"""
        if len(self.data_buffer) < self.sampling_rate * 3:
            return 70  # Default HR if not enough data
            
        # Simple peak detection algorithm
        # (In a real implementation, you'd use a more robust algorithm)
        last_3s = list(self.data_buffer)[-self.sampling_rate * 3:]
        peaks = 0
        threshold = np.mean(last_3s) + 0.3 * np.std(last_3s)
        
        for i in range(1, len(last_3s) - 1):
            if last_3s[i] > threshold and last_3s[i] > last_3s[i-1] and last_3s[i] > last_3s[i+1]:
                peaks += 1
                
        hr = peaks * 20  # peaks in 3s → beats per minute
        
        # Apply smoothing
        self.hr_buffer.append(hr)
        return np.mean(self.hr_buffer)
    
    def get_hr_change_rate(self, window_size=10):
        """Calculate rate of change of heart rate"""
        if len(self.hr_buffer) < window_size:
            return 0
            
        recent_hrs = list(self.hr_buffer)[-window_size:]
        if len(recent_hrs) < 2:
            return 0
            
        # Calculate linear regression slope
        x = np.arange(len(recent_hrs))
        slope, _ = np.polyfit(x, recent_hrs, 1)
        
        return slope
    
    def reset_metrics(self):
        """Reset metrics for a new challenge"""
        self.max_hr = 0
        self.baseline_hr = self.calculate_heart_rate()
    
    def evaluate_fire_challenge(self):
        """Evaluate performance on the fire breathing challenge"""
        current_hr = self.calculate_heart_rate()
        
        # Update maximum heart rate
        if current_hr > self.max_hr:
            self.max_hr = current_hr
            
        # Calculate score (difference between max and baseline)
        ignition_score = self.max_hr - self.baseline_hr
        
        # Normalize score to 0-100 range
        normalized_score = min(100, max(0, ignition_score * 5))
        
        return {
            "current_hr": current_hr,
            "max_hr": self.max_hr,
            "baseline_hr": self.baseline_hr,
            "ignition_score": ignition_score,
            "normalized_score": normalized_score
        }
    
    def evaluate_wave_challenge(self):
        """Evaluate performance on the wave breathing challenge"""
        current_hr = self.calculate_heart_rate()
        slope = self.get_hr_change_rate()
        
        # Negative slope is good (HR decreasing during hold)
        wave_score = -slope
        
        # Normalize score to 0-100 range
        normalized_score = min(100, max(0, wave_score * 10 + 50))
        
        return {
            "current_hr": current_hr,
            "hr_slope": slope,
            "wave_score": wave_score,
            "normalized_score": normalized_score
        }
    
    def evaluate_lightning_challenge(self):
        """Evaluate performance on the lightning breathing challenge"""
        current_hr = self.calculate_heart_rate()
        
        # Calculate heart rate variability (simple method)
        if len(self.hr_buffer) > 5:
            recent_hrs = list(self.hr_buffer)[-5:]
            hrv = np.std(recent_hrs)
        else:
            hrv = 0
            
        # Calculate score based on HRV and overall pattern
        alchemist_score = hrv
        
        # Normalize score to 0-100 range
        normalized_score = min(100, max(0, alchemist_score * 10))
        
        return {
            "current_hr": current_hr,
            "hrv": hrv,
            "alchemist_score": alchemist_score,
            "normalized_score": normalized_score
        }