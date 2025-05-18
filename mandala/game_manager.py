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
from visibility_manager import VisibilityManager
from path_generator import PathGenerator
from challenge_points_manager import ChallengePointsManager

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
        
        # Initialize visibility and path systems
        self.visibility_manager = VisibilityManager(mandala_size)
        self.path_generator = PathGenerator(mandala_size, self.mandala.noise_gen)
        self.challenge_points_manager = ChallengePointsManager(mandala_size)
        
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
        
        # Reveal initial areas on the map
        self.initialize_visibility()
    
    def initialize_visibility(self):
        """Initialize visibility for starting areas"""
        for team_idx in range(4):
            # Reveal the first challenge for each team
            points = self.challenge_points_manager.get_challenge_points()[team_idx]
            if points:  # Make sure there are points
                first_point = points[0]
                
                # Reveal area around first scroll
                scroll_x = first_point["scroll"]["x"]
                scroll_y = first_point["scroll"]["y"]
                self.visibility_manager.reveal_area(team_idx, scroll_x, scroll_y, 30)
                
                # Update the visibility surface
                self.visibility_manager.update_visibility_surface(team_idx)
    
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
            # Get visible challenge points for the current team
            visible_points = self.challenge_points_manager.get_visible_challenge_points(self.current_team)
            clickable_regions = self.get_clickable_regions_from_points(visible_points)
            
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
    
    def get_clickable_regions_from_points(self, points):
        """Convert challenge points to clickable regions"""
        clickable_regions = []
        
        for point_set in points:
            level = point_set["level"]
            
            # Add scroll point
            scroll_x = point_set["scroll"]["x"]
            scroll_y = point_set["scroll"]["y"]
            
            # Convert to screen coordinates
            screen_x, screen_y = self.mandala.get_screen_pos(scroll_x / self.mandala_size, 
                                                            scroll_y / self.mandala_size)
            
            if screen_x is not None:
                clickable_regions.append({
                    "type": "scroll",
                    "team": self.current_team,
                    "level": level,
                    "x": screen_x,
                    "y": screen_y,
                    "radius": 15
                })
            
            # Add cipher point if scroll for this level is completed
            if f"{level}-scroll" in self.teams[self.current_team]["completed_challenges"]:
                cipher_x = point_set["cipher"]["x"]
                cipher_y = point_set["cipher"]["y"]
                
                screen_x, screen_y = self.mandala.get_screen_pos(cipher_x / self.mandala_size, 
                                                                cipher_y / self.mandala_size)
                
                if screen_x is not None:
                    clickable_regions.append({
                        "type": "cipher",
                        "team": self.current_team,
                        "level": level,
                        "x": screen_x,
                        "y": screen_y,
                        "radius": 15
                    })
            
            # Add challenge point if cipher for this level is completed
            if f"{level}-cipher" in self.teams[self.current_team]["completed_challenges"]:
                challenge_x = point_set["challenge"]["x"]
                challenge_y = point_set["challenge"]["y"]
                
                screen_x, screen_y = self.mandala.get_screen_pos(challenge_x / self.mandala_size, 
                                                                challenge_y / self.mandala_size)
                
                if screen_x is not None:
                    clickable_regions.append({
                        "type": "challenge",
                        "challenge_type": point_set["challenge"]["type"],
                        "team": self.current_team,
                        "level": level,
                        "x": screen_x,
                        "y": screen_y,
                        "radius": 15
                    })
        
        return clickable_regions
    
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
                self.input_text = self.input_handler.get_input_text()
    
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
            challenge_type = ["fire", "wave", "lightning"][level % 3]
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
                
                # Reveal the cipher on the map
                self.reveal_next_element("cipher")
                
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
                
                # Reveal the challenge on the map
                self.reveal_next_element("challenge")
                
                # Move to challenge phase
                self.game_phase = "challenge"
                
        elif self.game_phase == "challenge" and self.challenge_manager.is_in_setup_phase():
            self.challenge_manager.set_decoded_text(input_text)
            self.challenge_manager.start_challenge()
            
        self.input_handler.clear_input()
        self.input_text = ""
    
    def reveal_next_element(self, element_type):
        """Reveal the next element on the map after completing a challenge"""
        team_idx = self.current_team
        level = self.current_level
        
        # Get the challenge points for this team
        all_points = self.challenge_points_manager.get_challenge_points()
        if team_idx >= len(all_points) or level >= len(all_points[team_idx]):
            return
            
        # Get the point set for this level
        point_set = all_points[team_idx][level]
        
        # Determine which element to reveal
        source_element = "scroll"
        if element_type == "challenge":
            source_element = "cipher"
        
        # Get positions
        source_x = point_set[source_element]["x"]
        source_y = point_set[source_element]["y"]
        
        target_x = point_set[element_type]["x"]
        target_y = point_set[element_type]["y"]
        
        # Reveal path between source and target
        path_points = self.path_generator.generate_path(
            team_idx, source_x, source_y, target_x, target_y
        )
        
        # Get transformation info for this path
        transformations = self.path_generator.get_path_transformation_info(
            team_idx, path_points
        )
        
        # Apply transformations to create a visible path
        self.mandala.apply_path_transformations(transformations)
        
        # Reveal area around the target element
        self.visibility_manager.reveal_area(team_idx, target_x, target_y, 30)
        
        # If this was the challenge completion, check if we should reveal the next level
        if element_type == "challenge":
            # Mark level as completed
            self.challenge_points_manager.mark_level_completed(team_idx, level)
            
            # Update team progress
            team_data = self.teams[team_idx]
            team_data["position"] = max(team_data["position"], level + 1)
            
            # Reveal next level if it exists
            next_level = level + 1
            all_points = self.challenge_points_manager.get_challenge_points()
            if team_idx < len(all_points) and next_level < len(all_points[team_idx]):
                next_point_set = all_points[team_idx][next_level]
                
                # Reveal path to the next scroll
                next_scroll_x = next_point_set["scroll"]["x"]
                next_scroll_y = next_point_set["scroll"]["y"]
                
                # Create path to next scroll
                path_points = self.path_generator.generate_path(
                    team_idx, target_x, target_y, next_scroll_x, next_scroll_y, jitter=30
                )
                
                # Get transformation info for this path
                transformations = self.path_generator.get_path_transformation_info(
                    team_idx, path_points, radius=7
                )
                
                # Apply transformations
                self.mandala.apply_path_transformations(transformations)
                
                # Reveal area around the next scroll
                self.visibility_manager.reveal_area(team_idx, next_scroll_x, next_scroll_y, 40)
        
        # Update visibility surface
        self.visibility_manager.update_visibility_surface(team_idx)
    
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
                
                # Reveal path to next challenge or center
                self.reveal_next_element("challenge")
                
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
        
        # Apply visibility fog of war
        visibility_surface = self.visibility_manager.get_visibility_surface(self.current_team)
        if visibility_surface:
            self.screen.blit(visibility_surface, (0, 0))
        
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
        # Get visible challenge points for the current team
        visible_points = self.challenge_points_manager.get_visible_challenge_points(self.current_team)
        clickable_regions = self.get_clickable_regions_from_points(visible_points)
        
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