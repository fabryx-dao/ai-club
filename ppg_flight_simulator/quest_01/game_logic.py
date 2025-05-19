#!/usr/bin/env python3
"""
Game Logic Module

This module handles the game mechanics, challenge logic, and scoring
for the PPG Biofeedback Game.
"""

class GameManager:
    """Manages game states, challenges, and scoring"""
    
    # Game states
    STATE_IDLE = 'idle'                # Not started
    STATE_CALIBRATING = 'calibrating'  # First phase (0-10s)
    STATE_CHALLENGE = 'challenge'      # Main phase (fire: 10-40s, wave: 10-70s)
    STATE_COMPLETE = 'complete'        # Finished
    
    # Game modes
    MODE_FIRE = 'fire'     # Original game (40s total, breathe up)
    MODE_WAVE = 'wave'     # Extended game (70s total, breathe up then down)
    
    def __init__(self, debug=False):
        """Initialize the Game Manager
        
        Args:
            debug (bool): Enable debug output
        """
        self.debug = debug
        
        # Default to fire game
        self.game_mode = self.MODE_FIRE
        
        # Game configuration - common for both modes
        self.calibration_start_time = 3.0    # Start collecting baseline at 3s
        self.calibration_end_time = 10.0     # End baseline calculation at 10s
        self.challenge_start_time = 10.0     # Start the challenge phase
        self.ramp_delta = 50.0               # Increase/decrease in target over challenge
        
        # Fire (default) game configuration
        self.fire_max_duration = 40.0        # Total fire game duration
        
        # Wave game configuration
        self.wave_max_duration = 70.0        # Total wave game duration
        self.wave_transition_time = 40.0     # When to switch from up to down
        
        # Current max duration depends on mode
        self.max_duration = self.fire_max_duration
        
        # Game state
        self.state = self.STATE_IDLE
        self.start_time = None
        self.current_time = 0.0
        
        # Signal processing
        self.baseline_value = None
        self.calibration_values = []
        self.current_value = None
        
        # Performance metrics
        self.score = 0
        self.time_in_target = 0.0
        self.time_below_target = 0.0
        self.max_consecutive_target = 0.0
        self.current_consecutive_target = 0.0
        
        # Callback for state changes
        self.state_callback = None
    
    def set_game_mode(self, mode):
        """Set the game mode (fire or wave)
        
        Args:
            mode (str): Game mode (MODE_FIRE or MODE_WAVE)
        """
        if mode == self.MODE_FIRE:
            self.game_mode = self.MODE_FIRE
            self.max_duration = self.fire_max_duration
        elif mode == self.MODE_WAVE:
            self.game_mode = self.MODE_WAVE
            self.max_duration = self.wave_max_duration
        
        if self.debug:
            print(f"Game mode set to {mode}, duration: {self.max_duration}s")
        
    def register_state_callback(self, callback):
        """Register a callback for game state changes
        
        Args:
            callback (function): Function to call when game state changes.
                                Will be called with (state, data) parameters.
        """
        self.state_callback = callback
    
    def start_game(self):
        """Start a new game"""
        self.state = self.STATE_CALIBRATING
        self.start_time = None  # Will be set when first data point arrives
        self.current_time = 0.0
        
        # Reset metrics
        self.baseline_value = None
        self.calibration_values = []
        self.current_value = None
        self.score = 0
        self.time_in_target = 0.0
        self.time_below_target = 0.0
        self.max_consecutive_target = 0.0
        self.current_consecutive_target = 0.0
        
        if self.debug:
            print("Game started - in calibration phase")
        
        # Notify state change
        if self.state_callback:
            self.state_callback(self.state, {"time": 0.0})
        
        return True
    
    def reset_game(self):
        """Reset the game to idle state"""
        self.state = self.STATE_IDLE
        
        # Reset all game metrics
        self.start_time = None
        self.current_time = 0.0
        self.baseline_value = None
        self.calibration_values = []
        self.current_value = None
        self.score = 0
        self.time_in_target = 0.0
        self.time_below_target = 0.0
        self.max_consecutive_target = 0.0
        self.current_consecutive_target = 0.0
        
        if self.debug:
            print("Game reset to idle state")
        
        # Notify state change
        if self.state_callback:
            self.state_callback(self.state, {})
        
        return True
    
    def process_data_point(self, time_value, signal_value):
        """Process a new data point from the sensor
        
        Args:
            time_value (float): Time in seconds
            signal_value (float): PPG signal value
            
        Returns:
            dict: Updated game state information
        """
        # Initialize start time if this is the first point
        if self.start_time is None:
            self.start_time = time_value
            if self.debug:
                print(f"First data point received, setting start time to {time_value}")
        
        # Calculate elapsed time since game start
        self.current_time = time_value - self.start_time
        self.current_value = signal_value
        
        # Process based on current state
        if self.state == self.STATE_IDLE:
            # No processing in idle state
            return {}
            
        elif self.state == self.STATE_CALIBRATING:
            # Collect calibration data (between 3-10 seconds)
            if self.calibration_start_time <= self.current_time <= self.calibration_end_time:
                self.calibration_values.append(signal_value)
                
                if self.debug and len(self.calibration_values) % 10 == 0:
                    print(f"Collected {len(self.calibration_values)} calibration points")
            
            # Check if we've reached the end of calibration
            if self.current_time >= self.calibration_end_time:
                self._complete_calibration()
                
                # Transition to challenge state
                self.state = self.STATE_CHALLENGE
                
                if self.debug:
                    print(f"Calibration complete, baseline: {self.baseline_value:.1f}")
                    print("Starting challenge phase")
                
                # Notify state change
                if self.state_callback:
                    self.state_callback(self.state, self.get_game_state())
            
            return self.get_game_state()
            
        elif self.state == self.STATE_CHALLENGE:
            # Calculate target value at current time
            target_value = self._calculate_target(self.current_time)
            
            # Score the current point
            is_above_target = signal_value >= target_value
            time_delta = 0.1  # Assuming 10Hz update rate
            
            if is_above_target:
                self.time_in_target += time_delta
                self.current_consecutive_target += time_delta
                self.score += 1
            else:
                self.time_below_target += time_delta
                # Reset consecutive counter if below target
                if self.current_consecutive_target > self.max_consecutive_target:
                    self.max_consecutive_target = self.current_consecutive_target
                self.current_consecutive_target = 0.0
            
            # Check if game is complete
            if self.current_time >= self.max_duration:
                self.state = self.STATE_COMPLETE
                
                # Final update to max consecutive
                if self.current_consecutive_target > self.max_consecutive_target:
                    self.max_consecutive_target = self.current_consecutive_target
                
                if self.debug:
                    print("Challenge complete!")
                    print(f"Final score: {self.score}")
                    print(f"Time in target: {self.time_in_target:.1f} seconds")
                    print(f"Max consecutive: {self.max_consecutive_target:.1f} seconds")
                
                # Notify state change
                if self.state_callback:
                    self.state_callback(self.state, self.get_game_state())
            
            return self.get_game_state()
            
        elif self.state == self.STATE_COMPLETE:
            # No processing in complete state
            return self.get_game_state()
    
    def _complete_calibration(self):
        """Calculate baseline from collected calibration values"""
        if self.calibration_values:
            self.baseline_value = sum(self.calibration_values) / len(self.calibration_values)
        else:
            # Default baseline if no values collected
            self.baseline_value = 500.0  # Middle of Arduino analog range
            
            if self.debug:
                print("Warning: No calibration values collected, using default baseline")
    
    def _calculate_target(self, time_value):
        """Calculate the target value at a specific time
        
        Args:
            time_value (float): Time in seconds
            
        Returns:
            float: Target PPG value at the given time
        """
        if time_value < self.challenge_start_time:
            return self.baseline_value
        
        if self.game_mode == self.MODE_FIRE:
            # Fire game - single ramp up
            challenge_duration = self.fire_max_duration - self.challenge_start_time
            position = min(1.0, (time_value - self.challenge_start_time) / challenge_duration)
            
            # Calculate target value using linear interpolation (ramp up)
            target = self.baseline_value + (position * self.ramp_delta)
            return target
            
        elif self.game_mode == self.MODE_WAVE:
            # Wave game - ramp up, then ramp down
            if time_value < self.wave_transition_time:
                # First phase - ramp up (10s to 40s)
                phase_duration = self.wave_transition_time - self.challenge_start_time
                position = min(1.0, (time_value - self.challenge_start_time) / phase_duration)
                
                # Calculate target value using linear interpolation (ramp up)
                target = self.baseline_value + (position * self.ramp_delta)
                return target
            else:
                # Second phase - ramp down (40s to 70s)
                phase_duration = self.wave_max_duration - self.wave_transition_time
                position = min(1.0, (time_value - self.wave_transition_time) / phase_duration)
                
                # Start from the peak and ramp down
                peak_value = self.baseline_value + self.ramp_delta
                target = peak_value - (position * self.ramp_delta)
                return target
        
        # Default fallback
        return self.baseline_value
    
    def get_game_state(self):
        """Get the current game state as a dictionary
        
        Returns:
            dict: Current game state information
        """
        state_info = {
            'state': self.state,
            'time': self.current_time,
            'baseline': self.baseline_value,
            'current_value': self.current_value,
            'target': self._calculate_target(self.current_time) if self.baseline_value is not None else None,
            'score': self.score,
            'time_in_target': self.time_in_target,
            'time_below_target': self.time_below_target,
            'max_consecutive_target': self.max_consecutive_target,
            'challenge_start_time': self.challenge_start_time,
            'max_duration': self.max_duration,
            'game_mode': self.game_mode
        }
        
        # Add wave-specific information if in wave mode
        if self.game_mode == self.MODE_WAVE:
            state_info['wave_transition_time'] = self.wave_transition_time
            
            # Add phase info (whether we're in the up or down phase)
            if self.current_time < self.wave_transition_time:
                state_info['wave_phase'] = 'up'
            else:
                state_info['wave_phase'] = 'down'
        
        return state_info
    
    def get_final_results(self):
        """Get the final game results
        
        Returns:
            dict: Game results and performance metrics
        """
        if self.state != self.STATE_COMPLETE:
            return None
        
        # Calculate percentage of time in target
        total_challenge_time = self.max_duration - self.challenge_start_time
        percent_in_target = (self.time_in_target / total_challenge_time) * 100 if total_challenge_time > 0 else 0
        
        return {
            'score': self.score,
            'time_in_target': self.time_in_target,
            'time_below_target': self.time_below_target,
            'percent_in_target': percent_in_target,
            'max_consecutive_target': self.max_consecutive_target,
            'baseline': self.baseline_value
        }