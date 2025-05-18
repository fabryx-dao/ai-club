import pygame
import math
import time
from mandala import MandalaGenerator
from puzzles import IfThenElsePattern
from ciphers import CipherEncoder
from ppg_processor import PPGProcessor

# Colors
BLACK = (0, 0, 0)
GREEN = (50, 255, 50)
AMBER = (255, 176, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)

class GameManager:
    """Manages the overall game state and components"""
    
    def __init__(self, screen, mandala_size, info_panel_width):
        self.screen = screen
        self.mandala_size = mandala_size
        self.info_panel_width = info_panel_width
        
        # Initialize fonts
        self.font = pygame.font.Font('freesansbold.ttf', 14)
        self.terminal_font = pygame.font.SysFont('courier', 16)
        
        # Game state
        self.teams = [
            {"name": "North", "position": 0, "path": []},
            {"name": "East", "position": 0, "path": []},
            {"name": "South", "position": 0, "path": []},
            {"name": "West", "position": 0, "path": []}
        ]
        self.current_team = 0
        self.game_phase = "setup"  # setup, puzzle, cipher, challenge
        self.current_level = 0
        
        # Create components
        self.mandala = MandalaGenerator(mandala_size)
        self.ppg_processor = PPGProcessor()
        
        # Puzzle and cipher components
        self.current_puzzle = None
        self.current_cipher = None
        self.encoded_message = ""
        
        # Challenge state
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
        
        # Input handling
        self.input_text = ""
        self.input_active = False
        
        # Generate clickable regions
        self.clickable_regions = []
        self.setup_clickable_regions()
    
    def setup_clickable_regions(self):
        """Setup clickable regions on the mandala"""
        # Define the regions where items will be placed on paths
        
        # For each team path, create scroll, cipher, and challenge icons
        for team_idx in range(4):
            angle_start = team_idx * math.pi / 2  # 0, π/2, π, 3π/2
            
            # Calculate positions along the path
            for level in range(3):  # 3 levels of challenges
                # Calculate distance from center (farther to closer)
                distance = 0.7 - (level * 0.2)
                
                # Scroll position
                scroll_angle = angle_start + 0.1 + (0.2 * level)
                scroll_x = self.mandala_size/2 + math.cos(scroll_angle) * (distance * self.mandala_size/2)
                scroll_y = self.mandala_size/2 + math.sin(scroll_angle) * (distance * self.mandala_size/2)
                
                # Cipher position
                cipher_angle = angle_start + 0.2 + (0.2 * level)
                cipher_x = self.mandala_size/2 + math.cos(cipher_angle) * (distance * self.mandala_size/2)
                cipher_y = self.mandala_size/2 + math.sin(cipher_angle) * (distance * self.mandala_size/2)
                
                # Challenge position
                challenge_angle = angle_start + 0.3 + (0.2 * level)
                challenge_x = self.mandala_size/2 + math.cos(challenge_angle) * (distance * self.mandala_size/2)
                challenge_y = self.mandala_size/2 + math.sin(challenge_angle) * (distance * self.mandala_size/2)
                
                # Add to clickable regions with a radius of 20 pixels
                self.clickable_regions.append({
                    "type": "scroll",
                    "team": team_idx,
                    "level": level,
                    "x": scroll_x,
                    "y": scroll_y,
                    "radius": 20
                })
                
                self.clickable_regions.append({
                    "type": "cipher",
                    "team": team_idx,
                    "level": level,
                    "x": cipher_x,
                    "y": cipher_y,
                    "radius": 20
                })
                
                icon_type = ["fire", "wave", "lightning"][level]
                self.clickable_regions.append({
                    "type": "challenge",
                    "challenge_type": icon_type,
                    "team": team_idx,
                    "level": level,
                    "x": challenge_x,
                    "y": challenge_y,
                    "radius": 20
                })
    
    def handle_click(self, pos):
        """Handle mouse clicks"""
        x, y = pos
        
        # Check if click is in mandala area
        if x < self.mandala_size:
            # Check if click hits any clickable region
            for region in self.clickable_regions:
                # Calculate distance from click to region center
                distance = math.sqrt((x - region["x"])**2 + (y - region["y"])**2)
                
                if distance <= region["radius"]:
                    print(f"Clicked on {region['type']} for team {region['team']}, level {region['level']}")
                    self.handle_region_click(region)
                    return
    
    def handle_region_click(self, region):
        """Handle click on a specific region"""
        # Set current team to the one that owns this region
        self.current_team = region["team"]
        self.current_level = region["level"]
        
        if region["type"] == "scroll":
            self.display_puzzle(region["team"], region["level"])
        elif region["type"] == "cipher":
            self.display_cipher(region["team"], region["level"])
        elif region["type"] == "challenge":
            self.display_challenge(region["team"], region["level"], region["challenge_type"])
    
    def display_puzzle(self, team, level):
        """Display puzzle in the info panel"""
        self.current_puzzle = IfThenElsePattern(level)
        self.game_phase = "puzzle"
        self.input_active = True
        self.input_text = ""
        self.print_screen()
    
    def display_cipher(self, team, level):
        """Display cipher in the info panel"""
        if self.current_puzzle and self.current_puzzle.correct_output:
            self.current_cipher = CipherEncoder(level)
            key = str(self.current_puzzle.correct_output)
            challenge_type = ["fire", "wave", "lightning"][level]
            message = self.current_cipher.get_challenge_instructions(challenge_type)
            self.encoded_message = self.current_cipher.encode(message, key)
            self.game_phase = "cipher"
            self.input_active = True
            self.input_text = ""
            self.print_screen()
    
    def display_challenge(self, team, level, challenge_type):
        """Display challenge in the info panel"""
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
        self.game_phase = "challenge"
        self.input_active = True
        self.input_text = ""
    
    def start_challenge(self):
        """Start the biofeedback challenge with countdown"""
        self.challenge_state["phase"] = "countdown"
        self.challenge_state["timer"] = 10  # 10 second countdown
        self.challenge_state["start_time"] = time.time()
        self.ppg_processor.reset_metrics()
    
    def handle_input(self, event):
        """Handle text input events"""
        if not self.input_active:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.process_input()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
    
    def process_input(self):
        """Process the current input text"""
        if self.game_phase == "puzzle":
            if self.current_puzzle and self.current_puzzle.verify_answer(self.input_text):
                print("Puzzle solved correctly!")
                # Move to cipher phase
                self.display_cipher(self.current_team, self.current_level)
            else:
                print("Incorrect answer, try again.")
                
        elif self.game_phase == "cipher":
            if self.current_cipher and self.input_text.isdigit():
                decoded = self.current_cipher.decode(self.encoded_message, self.input_text)
                self.challenge_state["decoded_text"] = decoded
                print(f"Decoded message: {decoded}")
                self.game_phase = "challenge"
                self.challenge_state["phase"] = "setup"
                
        elif self.game_phase == "challenge" and self.challenge_state["phase"] == "setup":
            self.challenge_state["decoded_text"] = self.input_text
            self.start_challenge()
            
        self.input_text = ""
    
    def update(self):
        """Update game state each frame"""
        # Update PPG data and challenge state
        if self.game_phase == "challenge" and self.challenge_state["active"]:
            self.update_challenge()
    
    def update_challenge(self):
        """Update the challenge state"""
        if not self.challenge_state["active"]:
            return
            
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
                # Update team progress
                self.teams[self.current_team]["position"] = self.current_level + 1
    
    def draw(self):
        """Draw all game elements to the screen"""
        # Clear the screen
        self.screen.fill(BLACK)
        
        # Draw the mandala
        self.draw_mandala()
        
        # Draw the information panel
        self.draw_info_panel()
    
    def draw_mandala(self):
        """Draw the mandala and clickable icons"""
        # Draw the mandala background
        self.screen.blit(self.mandala.surface, (0, 0))
        
        # Draw clickable icons on top of the mandala
        for region in self.clickable_regions:
            # Different icons for different types
            if region["type"] == "scroll":
                color = WHITE
                icon = "📜"
            elif region["type"] == "cipher":
                color = GREEN
                icon = "🔣"
            elif region["type"] == "challenge":
                if region["challenge_type"] == "fire":
                    color = (255, 100, 50)  # Orange-red
                    icon = "🔥"
                elif region["challenge_type"] == "wave":
                    color = (50, 100, 255)  # Blue
                    icon = "🌊"
                else:  # Lightning
                    color = (230, 230, 50)  # Yellow
                    icon = "⚡"
            
            # Draw the icon
            icon_surface = self.font.render(icon, True, color)
            self.screen.blit(icon_surface, (region["x"] - 10, region["y"] - 10))
    
    def draw_info_panel(self):
        """Draw the information panel with current game state"""
        info_rect = pygame.Rect(self.mandala_size, 0, self.info_panel_width, self.screen.get_height())
        pygame.draw.rect(self.screen, BLACK, info_rect)
        pygame.draw.line(self.screen, GREEN, (self.mandala_size, 0), (self.mandala_size, self.screen.get_height()), 2)
        
        # Draw title
        title_surface = self.terminal_font.render(">> ASCII ADVENTURE <<", True, GREEN)
        self.screen.blit(title_surface, (self.mandala_size + 20, 20))
        
        # Draw current team info
        team_surface = self.terminal_font.render(f"ACTIVE TEAM: {self.teams[self.current_team]['name']}", True, AMBER)
        self.screen.blit(team_surface, (self.mandala_size + 20, 60))
        
        # Draw game phase info
        phase_surface = self.terminal_font.render(f"PHASE: {self.game_phase.upper()}", True, AMBER)
        self.screen.blit(phase_surface, (self.mandala_size + 20, 90))
        
        # Draw content based on game phase
        if self.game_phase == "setup":
            self.draw_setup_panel()
            
        elif self.game_phase == "puzzle" and self.current_puzzle:
            self.draw_puzzle_panel()
            
        elif self.game_phase == "cipher" and self.current_cipher:
            self.draw_cipher_panel()
            
        elif self.game_phase == "challenge" and self.challenge_state["active"]:
            self.draw_challenge_panel()
    
    def draw_setup_panel(self):
        """Draw the setup/welcome screen"""
        instructions = [
            "WELCOME TO THE MANDALA CHALLENGE",
            "",
            "1. CLICK ON A SCROLL TO BEGIN",
            "2. SOLVE THE PUZZLE",
            "3. DECODE THE CIPHER",
            "4. COMPLETE THE CHALLENGE",
            "",
            "REACH THE CENTER TO WIN"
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.terminal_font.render(line, True, WHITE)
            self.screen.blit(line_surface, (self.mandala_size + 20, 150 + i*30))
    
    def draw_puzzle_panel(self):
        """Draw the puzzle interface"""
        puzzle_title = self.terminal_font.render("== DECODE THE PATTERN ==", True, WHITE)
        self.screen.blit(puzzle_title, (self.mandala_size + 20, 130))
        
        description = self.terminal_font.render(self.current_puzzle.get_puzzle_description(), True, GREEN)
        self.screen.blit(description, (self.mandala_size + 20, 160))
        
        # Draw input/output table
        self.screen.blit(self.terminal_font.render("INPUT", True, AMBER), (self.mandala_size + 50, 200))
        self.screen.blit(self.terminal_font.render("OUTPUT", True, AMBER), (self.mandala_size + 200, 200))
        
        for i in range(len(self.current_puzzle.input_values) - 1):
            input_val = self.terminal_font.render(str(self.current_puzzle.input_values[i]), True, WHITE)
            output_val = self.terminal_font.render(str(self.current_puzzle.output_values[i]), True, WHITE)
            self.screen.blit(input_val, (self.mandala_size + 50, 230 + i * 30))
            self.screen.blit(output_val, (self.mandala_size + 200, 230 + i * 30))
        
        # Draw the test input
        test_input = self.terminal_font.render(str(self.current_puzzle.test_input) + " = ?", True, GREEN)
        self.screen.blit(test_input, (self.mandala_size + 50, 230 + 4 * 30))
        
        # Draw input box
        pygame.draw.rect(self.screen, GRAY, (self.mandala_size + 20, 400, 300, 40), 2)
        input_surface = self.terminal_font.render(self.input_text, True, WHITE)
        self.screen.blit(input_surface, (self.mandala_size + 30, 410))
        
        # Draw instructions
        instructions = [
            "Find the pattern in the input/output pairs.",
            "What is the rule that transforms each input",
            "into its corresponding output?",
            "",
            "Once you have figured out the pattern,",
            "apply it to the final input and enter",
            "your answer in the box above."
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.terminal_font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 460 + i * 30))
    
    def draw_cipher_panel(self):
        """Draw the cipher interface"""
        cipher_title = self.terminal_font.render("== DECODE THE CIPHER ==", True, WHITE)
        self.screen.blit(cipher_title, (self.mandala_size + 20, 130))
        
        # Draw instructions
        instructions = [
            "Use the answer from the previous puzzle",
            "as the key to decode this cipher:",
            "",
            f"{self.encoded_message}",
            "",
            "Enter the key below:"
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.terminal_font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 170 + i*30))
        
        # Draw input box
        pygame.draw.rect(self.screen, GRAY, (self.mandala_size + 20, 350, 300, 40), 2)
        input_surface = self.terminal_font.render(self.input_text, True, WHITE)
        self.screen.blit(input_surface, (self.mandala_size + 30, 360))
    
    def draw_challenge_panel(self):
        """Draw the challenge interface"""
        challenge_title = self.terminal_font.render(f"== {self.challenge_state['type'].upper()} CHALLENGE ==", True, WHITE)
        self.screen.blit(challenge_title, (self.mandala_size + 20, 130))
        
        if self.challenge_state["phase"] == "setup":
            # Draw decoded message if available
            if self.challenge_state["decoded_text"]:
                message_surface = self.terminal_font.render(f"Message: {self.challenge_state['decoded_text']}", True, GREEN)
                self.screen.blit(message_surface, (self.mandala_size + 20, 170))
            
            # Draw instructions
            instructions = [
                "Enter the decoded message to begin the challenge:",
                "",
                "When ready, the student will place their finger",
                "on the PPG sensor. A 10-second countdown will",
                "begin, followed by the 60-second challenge."
            ]
            
            for i, line in enumerate(instructions):
                line_surface = self.terminal_font.render(line, True, AMBER)
                self.screen.blit(line_surface, (self.mandala_size + 20, 200 + i*30))
            
            # Draw input box
            pygame.draw.rect(self.screen, GRAY, (self.mandala_size + 20, 350, 300, 40), 2)
            input_surface = self.terminal_font.render(self.input_text, True, WHITE)
            self.screen.blit(input_surface, (self.mandala_size + 30, 360))
            
        elif self.challenge_state["phase"] == "countdown":
            countdown_text = self.terminal_font.render(f"PREPARE IN: {self.challenge_state['timer']}", True, GREEN)
            self.screen.blit(countdown_text, (self.mandala_size + 20, 170))
            
            # Draw instructions
            instructions = [
                "Get ready!",
                "Place your finger on the sensor.",
                f"Challenge begins in {self.challenge_state['timer']} seconds..."
            ]
            
            for i, line in enumerate(instructions):
                line_surface = self.terminal_font.render(line, True, AMBER)
                self.screen.blit(line_surface, (self.mandala_size + 20, 200 + i*30))
            
        elif self.challenge_state["phase"] == "active":
            # Draw timer
            timer_text = self.terminal_font.render(f"TIME: {self.challenge_state['timer']} seconds", True, GREEN)
            self.screen.blit(timer_text, (self.mandala_size + 20, 170))
            
            # Draw score
            score_text = self.terminal_font.render(f"SCORE: {int(self.challenge_state['score'])}", True, GREEN)
            self.screen.blit(score_text, (self.mandala_size + 20, 200))
            
            # Draw visual feedback based on challenge type
            if self.challenge_state["type"] == "fire":
                self.draw_fire_challenge()
            elif self.challenge_state["type"] == "wave":
                self.draw_wave_challenge()
            elif self.challenge_state["type"] == "lightning":
                self.draw_lightning_challenge()
                
        elif self.challenge_state["phase"] == "complete":
            # Draw completion message
            complete_text = self.terminal_font.render("CHALLENGE COMPLETE!", True, GREEN)
            self.screen.blit(complete_text, (self.mandala_size + 20, 170))
            
            # Draw final score
            score_text = self.terminal_font.render(f"FINAL SCORE: {int(self.challenge_state['score'])}", True, GREEN)
            self.screen.blit(score_text, (self.mandala_size + 20, 200))
            
            # Draw success/failure message
            if self.challenge_state["score"] >= 70:
                result_text = self.terminal_font.render("SUCCESS! You may advance.", True, AMBER)
            else:
                result_text = self.terminal_font.render("Try again to improve your score.", True, AMBER)
            self.screen.blit(result_text, (self.mandala_size + 20, 230))
    
    def draw_fire_challenge(self):
        """Draw the fire challenge visualization"""
        # Draw breathing guide
        y_pos = 250
        width = self.info_panel_width - 40
        height = 100
        
        # Draw fire animation based on score
        flame_height = int(height * (self.challenge_state["score"] / 100))
        pygame.draw.rect(self.screen, (255, 100, 50), (self.mandala_size + 20, y_pos + height - flame_height, width, flame_height))
        
        # Draw target line
        target_y = y_pos + height - int(height * 0.7)  # 70% target
        pygame.draw.line(self.screen, WHITE, (self.mandala_size + 20, target_y), (self.mandala_size + 20 + width, target_y), 2)
        
        # Draw instructions
        instructions = [
            "BREATHE RAPIDLY TO IGNITE THE FIRE",
            "Try to reach the white line with your flame!",
            "",
            "Breathe in through your nose and out through your mouth",
            "as quickly and forcefully as possible."
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.terminal_font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 370 + i*30))
    
    def draw_wave_challenge(self):
        """Draw the wave challenge visualization"""
        # Draw breathing guide
        y_pos = 250
        width = self.info_panel_width - 40
        height = 100
        
        # Draw wave animation
        wave_points = []
        for x in range(width):
            # Create a wave effect
            t = time.time()
            x_norm = x / width
            y_value = math.sin(x_norm * 10 + t) * 20
            
            # Invert based on score (high score = low wave)
            y_adjust = height * (1 - self.challenge_state["score"] / 100) 
            wave_points.append((self.mandala_size + 20 + x, y_pos + height/2 + y_value - y_adjust))
        
        # Draw the wave
        if len(wave_points) > 1:
            pygame.draw.lines(self.screen, (50, 100, 255), False, wave_points, 2)
        
        # Draw target line
        target_y = y_pos + height - int(height * 0.7)  # 70% target
        pygame.draw.line(self.screen, WHITE, (self.mandala_size + 20, target_y), (self.mandala_size + 20 + width, target_y), 2)
        
        # Draw instructions
        instructions = [
            "RIDE THE WAVE DOWN",
            "Exhale fully and hold your breath",
            "",
            "Try to make the wave drop below the white line",
            "by staying calm during your breath hold."
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.terminal_font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 370 + i*30))
    
    def draw_lightning_challenge(self):
        """Draw the lightning challenge visualization"""
        # Draw breathing guide
        y_pos = 250
        width = self.info_panel_width - 40
        height = 100
        
        # Draw lightning animation
        t = time.time()
        for i in range(5):
            # Create jagged lightning effect
            points = [(self.mandala_size + width/2, y_pos)]
            
            segments = 10
            for s in range(segments):
                prev_x, prev_y = points[-1]
                
                # Calculate new point with random zigzag
                new_y = prev_y + height / segments
                zigzag = math.sin(t * 5 + s) * 30
                new_x = prev_x + zigzag
                
                points.append((new_x, new_y))
            
            # Draw lightning
            if len(points) > 1:
                color_intensity = int(128 + 127 * math.sin(t * 10 + i))
                color = (color_intensity, color_intensity, 50)
                pygame.draw.lines(self.screen, color, False, points, 2)
        
        # Draw target area
        target_height = int(height * 0.3)
        pygame.draw.rect(self.screen, (50, 50, 50), (self.mandala_size + 20, y_pos + height - target_height, width, target_height))
        
        # Draw score indicator
        score_width = int(width * self.challenge_state["score"] / 100)
        pygame.draw.rect(self.screen, (230, 230, 50), (self.mandala_size + 20, y_pos + height - 10, score_width, 10))
        
        # Draw instructions
        instructions = [
            "MASTER THE INNER ALCHEMIST",
            "Complete the full breath cycle:",
            "30 rapid breaths → exhale hold → inhale squeeze",
            "",
            "Try to fill the progress bar at the bottom!"
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.terminal_font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 370 + i*30))
    
    def print_screen(self):
        """Take a screenshot and print it"""
        print("Printing screen...")
        pygame.image.save(self.screen, "mandala_print.png")