import pygame
import math
import time
from mandala import MandalaGenerator
from puzzles import IfThenElsePattern
from ciphers import CipherEncoder
from ppg_processor import PPGProcessor
from ui_manager import UIManager
from challenge_manager import ChallengeManager
from input_handler import InputHandler

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
            {"name": "North", "position": 0, "path": [], "completed_challenges": []},
            {"name": "East", "position": 0, "path": [], "completed_challenges": []},
            {"name": "South", "position": 0, "path": [], "completed_challenges": []},
            {"name": "West", "position": 0, "path": [], "completed_challenges": []}
        ]
        self.current_team = 0
        self.game_phase = "setup"  # setup, puzzle, cipher, challenge
        self.current_level = 0
        
        # Create components
        self.mandala = MandalaGenerator(mandala_size)
        self.ppg_processor = PPGProcessor()
        
        # Specialized managers
        self.ui_manager = UIManager(self.screen, mandala_size, info_panel_width, self.terminal_font)
        self.challenge_manager = ChallengeManager(self.ppg_processor)
        self.input_handler = InputHandler()
        
        # Active content
        self.current_puzzle = None
        self.current_cipher = None
        self.encoded_message = ""
        
        # Input state
        self.input_text = ""
        self.input_active = False
    
    def handle_click(self, pos):
        """Handle mouse clicks"""
        x, y = pos
        
        # First check if click is on mini-map
        if x < self.mandala_size and self.mandala.handle_minimap_click(pos):
            # Mini-map was clicked and handled
            self.current_team = self.mandala.current_region
            return
        
        # Check if click is in mandala area
        if x < self.mandala_size:
            # Get clickable points from mandala
            clickable_regions = self.mandala.get_clickable_points()
            
            # Check if click hits any clickable region
            for region in clickable_regions:
                # Calculate distance from click to region center
                distance = math.sqrt((x - region["x"])**2 + (y - region["y"])**2)
                
                if distance <= region["radius"]:
                    print(f"Clicked on {region['type']} for team {region['team']}, level {region['level']}")
                    self.handle_region_click(region)
                    return
            
            # If no clickable region was hit, check for navigation
            if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                # Shift+Click to pan
                self.mandala.pan((pos[0] - self.mandala_size / 2) / 100, 
                               (pos[1] - self.mandala_size / 2) / 100)
    
    def handle_region_click(self, region):
        """Handle click on a specific region"""
        # Set current team to the one that owns this region
        self.current_team = region["team"]
        self.current_level = region["level"]
        
        # Check if this challenge is already completed
        team_data = self.teams[self.current_team]
        challenge_key = f"{region['level']}-{region['type']}"
        
        if challenge_key in team_data["completed_challenges"]:
            print(f"This challenge has already been completed!")
            return
        
        if region["type"] == "scroll":
            self.display_puzzle(region["team"], region["level"])
        elif region["type"] == "cipher":
            self.display_cipher(region["team"], region["level"])
        elif region["type"] == "challenge":
            self.display_challenge(region["team"], region["level"], region["challenge_type"])
    
    def handle_input(self, event):
        """Process input events"""
        # Handle zoom with mousewheel
        if event.type == pygame.MOUSEWHEEL:
            scroll_y = event.y
            if scroll_y > 0:
                self.mandala.zoom(1.1)  # Zoom in
            elif scroll_y < 0:
                self.mandala.zoom(0.9)  # Zoom out
        
        # Handle keyboard navigation
        elif event.type == pygame.KEYDOWN:
            # WASD or Arrow keys for panning
            if event.key in [pygame.K_w, pygame.K_UP]:
                self.mandala.pan(0, -0.05)
            elif event.key in [pygame.K_s, pygame.K_DOWN]:
                self.mandala.pan(0, 0.05)
            elif event.key in [pygame.K_a, pygame.K_LEFT]:
                self.mandala.pan(-0.05, 0)
            elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                self.mandala.pan(0.05, 0)
            # Number keys to switch regions
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                region = event.key - pygame.K_1
                self.mandala.set_region(region)
                self.current_team = region
            else:
                # Process text input
                self.input_handler.handle_input(event, self.input_active, self.input_text)
    
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
        self.challenge_manager.setup_challenge(challenge_type, team, level)
        self.game_phase = "challenge"
        self.input_active = True
        self.input_text = ""
    
    def process_input(self):
        """Process text input"""
        input_text = self.input_handler.get_input_text()
        
        if self.game_phase == "puzzle":
            if self.current_puzzle and self.current_puzzle.verify_answer(input_text):
                print("Puzzle solved correctly!")
                # Mark as completed
                team_data = self.teams[self.current_team]
                team_data["completed_challenges"].append(f"{self.current_level}-scroll")
                # Move to cipher phase
                self.display_cipher(self.current_team, self.current_level)
            else:
                print("Incorrect answer, try again.")
                
        elif self.game_phase == "cipher":
            if self.current_cipher and input_text.isdigit():
                decoded = self.current_cipher.decode(self.encoded_message, input_text)
                self.challenge_manager.set_decoded_text(decoded)
                print(f"Decoded message: {decoded}")
                # Mark as completed
                team_data = self.teams[self.current_team]
                team_data["completed_challenges"].append(f"{self.current_level}-cipher")
                # Move to challenge phase
                self.game_phase = "challenge"
                
        elif self.game_phase == "challenge" and self.challenge_manager.is_in_setup_phase():
            self.challenge_manager.set_decoded_text(input_text)
            self.challenge_manager.start_challenge()
            
        self.input_handler.clear_input()
        self.input_text = ""
    
    def update(self):
        """Update game state each frame"""
        # Update challenge if active
        if self.game_phase == "challenge":
            result = self.challenge_manager.update()
            
            # Check if challenge completed
            if result == "completed":
                # Mark challenge as completed
                team_data = self.teams[self.current_team]
                challenge_type = self.challenge_manager.get_challenge_type()
                team_data["completed_challenges"].append(f"{self.current_level}-challenge")
                
                # Update team progress
                team_data["position"] = max(team_data["position"], self.current_level + 1)
                
                # Reset game phase
                self.game_phase = "setup"
    
    def draw(self):
        """Draw all game elements to the screen"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Draw the mandala with terrain
        self.screen.blit(self.mandala.surface, (0, 0))
        
        # Draw clickable elements on the mandala
        self.draw_clickable_elements()
        
        # Draw UI appropriate for the current game phase
        self.ui_manager.draw_ui(
            self.game_phase,
            self.teams[self.current_team],
            self.current_puzzle,
            self.current_cipher,
            self.encoded_message,
            self.challenge_manager.get_challenge_state(),
            self.input_handler.get_input_text()
        )

    def draw_clickable_elements(self):
        """Draw the clickable elements (scroll, cipher, challenge icons) on the mandala"""
        # Get clickable points from mandala
        clickable_regions = self.mandala.get_clickable_points()
        
        # Get completed challenges for the current team
        completed_challenges = self.teams[self.current_team]["completed_challenges"]
        
        # Draw each clickable region
        for region in clickable_regions:
            # Check if this challenge has been completed
            challenge_key = f"{region['level']}-{region['type']}"
            is_completed = challenge_key in completed_challenges
            
            # Different icons and colors for different types
            if region["type"] == "scroll":
                color = (200, 200, 200) if not is_completed else (100, 255, 100)  # White or green
                icon = "📜"
            elif region["type"] == "cipher":
                color = (50, 255, 50) if not is_completed else (100, 255, 100)  # Green
                icon = "🔣"
            elif region["type"] == "challenge":
                if region["challenge_type"] == "fire":
                    color = (255, 100, 50) if not is_completed else (100, 255, 100)  # Orange-red
                    icon = "🔥"
                elif region["challenge_type"] == "wave":
                    color = (50, 100, 255) if not is_completed else (100, 255, 100)  # Blue
                    icon = "🌊"
                else:  # Lightning
                    color = (230, 230, 50) if not is_completed else (100, 255, 100)  # Yellow
                    icon = "⚡"
            
            # Draw the icon
            icon_surface = self.font.render(icon, True, color)
            self.screen.blit(icon_surface, (region["x"] - 10, region["y"] - 10))
    
    def print_screen(self):
        """Take a screenshot and print it"""
        print("Printing screen...")
        pygame.image.save(self.screen, "mandala_print.png")