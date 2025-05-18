import time

class ChallengeManager:
    """Manages the biofeedback challenges"""
    
    def __init__(self, ppg_processor):
        self.ppg_processor = ppg_processor
        
        # Initialize challenge state
        self.challenge_state = {
            "active": False,
            "type": None,
            "team": 0,
            "level": 0,
            "phase": "setup",  # setup, countdown, active, complete
            "timer": 0,
            "score": 0,
            "start_time": 0,
            "decoded_text": ""
        }
    
    def setup_challenge(self, challenge_type, team, level):
        """Initialize a new challenge"""
        self.challenge_state = {
            "active": True,
            "type": challenge_type,
            "team": team,
            "level": level,
            "phase": "setup",
            "timer": 0,
            "score": 0,
            "start_time": 0,
            "decoded_text": ""
        }
    
    def set_decoded_text(self, text):
        """Set the decoded text for the challenge"""
        self.challenge_state["decoded_text"] = text
    
    def start_challenge(self):
        """Start the countdown for the challenge"""
        self.challenge_state["phase"] = "countdown"
        self.challenge_state["timer"] = 10  # 10 second countdown
        self.challenge_state["start_time"] = time.time()
        self.ppg_processor.reset_metrics()
    
    def is_in_setup_phase(self):
        """Check if the challenge is in setup phase"""
        return self.challenge_state["phase"] == "setup"
    
    def get_challenge_state(self):
        """Get the current challenge state"""
        return self.challenge_state
    
    def get_challenge_type(self):
        """Get the type of the current challenge"""
        return self.challenge_state["type"]
    
    def update(self):
        """Update the challenge state. Returns 'completed' if challenge is done."""
        if not self.challenge_state["active"]:
            return None
            
        current_time = time.time()
        
        if self.challenge_state["phase"] == "countdown":
            elapsed = current_time - self.challenge_state["start_time"]
            self.challenge_state["timer"] = max(0, 10 - int(elapsed))
            
            if self.challenge_state["timer"] <= 0:
                self.challenge_state["phase"] = "active"
                self.challenge_state["timer"] = 60  # 60 second challenge
                self.challenge_state["start_time"] = current_time
                
        elif self.challenge_state["phase"] == "active":
            elapsed = current_time - self.challenge_state["start_time"]
            self.challenge_state["timer"] = max(0, 60 - int(elapsed))
            
            # Read PPG data
            self.ppg_processor.read_ppg_data()
            
            # Evaluate performance based on challenge type
            if self.challenge_state["type"] == "fire":
                result = self.ppg_processor.evaluate_fire_challenge()
                self.challenge_state["score"] = result["normalized_score"]
                
            elif self.challenge_state["type"] == "wave":
                result = self.ppg_processor.evaluate_wave_challenge()
                self.challenge_state["score"] = result["normalized_score"]
                
            elif self.challenge_state["type"] == "lightning":
                result = self.ppg_processor.evaluate_lightning_challenge()
                self.challenge_state["score"] = result["normalized_score"]
            
            # Check if challenge is complete
            if self.challenge_state["timer"] <= 0:
                self.challenge_state["phase"] = "complete"
                return "completed"
        
        return None