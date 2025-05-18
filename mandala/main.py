import pygame
import sys
import numpy as np
import math
import serial
from PIL import Image, ImageGrab
import time
import os
from collections import deque

# Game configuration
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MANDALA_SIZE = WINDOW_HEIGHT  # 1:1 aspect ratio
INFO_PANEL_WIDTH = WINDOW_WIDTH - MANDALA_SIZE
FPS = 30

# ASCII characters for density mapping (from dark to light)
ASCII_CHARS = ' .\'`^",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'

# Colors (retro terminal feel)
BLACK = (0, 0, 0)
GREEN = (50, 255, 50)
AMBER = (255, 176, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)

# PPG configuration
PORT = '/dev/tty.usbmodem101'  # Will be configurable
BAUD = 9600
SAMPLING_RATE = 100  # Hz
MAX_BUFFER_SIZE = 500

class MandalaGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("ASCII Mandala Adventure")
        self.clock = pygame.time.Clock()
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
        
        # PPG data
        self.ppg_buffer = deque([0]*MAX_BUFFER_SIZE, maxlen=MAX_BUFFER_SIZE)
        self.filtered_buffer = deque([0]*MAX_BUFFER_SIZE, maxlen=MAX_BUFFER_SIZE)
        self.serial_connection = None
        
        # Generate the mandala
        self.mandala_surface = self.generate_ascii_mandala()
        
        # Setup clickable regions
        self.clickable_regions = []
        self.setup_clickable_regions()
        
    def setup_serial(self, port=PORT):
        """Setup the serial connection to Arduino"""
        try:
            self.serial_connection = serial.Serial(port, BAUD, timeout=1)
            print(f"Connected to Arduino on {port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
    
    def generate_ascii_mandala(self):
        """Generate the ASCII art mandala with four paths"""
        surface = pygame.Surface((MANDALA_SIZE, MANDALA_SIZE))
        surface.fill(BLACK)
        
        # ASCII character size
        char_width, char_height = self.terminal_font.size("X")
        cols = MANDALA_SIZE // char_width
        rows = MANDALA_SIZE // char_height
        
        center_x, center_y = cols // 2, rows // 2
        max_radius = min(center_x, center_y) - 2
        
        # Create the mandala pattern
        for y in range(rows):
            for x in range(cols):
                # Calculate position relative to center
                dx = x - center_x
                dx2 = 2 * dx / cols
                dy = y - center_y
                dy2 = 2 * dy / rows
                
                # Calculate distance from center (normalized)
                distance = math.sqrt(dx2*dx2 + dy2*dy2)
                
                # Calculate angle from center
                angle = math.atan2(dy, dx)
                
                # Path logic - create 4 spiral paths from cardinal directions
                angle_norm = (angle + math.pi) / (2 * math.pi)  # 0 to 1
                cardinal_path = int(angle_norm * 4)  # 0, 1, 2, 3 for N, E, S, W
                
                # Create spiral effect
                spiral = (distance * 15 + angle * 5) % 1.0
                
                # Combine various effects for the final pattern
                pos1 = 0.5 + 0.5 * math.sin(distance * 20 - spiral * 2 * math.pi)
                pos2 = 0.5 + 0.5 * math.sin(angle * 8)
                pos3 = 0.5 + 0.5 * math.sin(distance * 15)
                
                # Combine into final pattern
                value = (pos1 + pos2 + pos3) / 3
                
                # Create gates at cardinal directions
                is_gate = False
                gate_width = 0.1
                
                # North gate
                if distance > 0.8 and distance < 0.9 and abs(angle_norm - 0.0) < gate_width:
                    is_gate = True
                # East gate
                elif distance > 0.8 and distance < 0.9 and abs(angle_norm - 0.25) < gate_width:
                    is_gate = True
                # South gate
                elif distance > 0.8 and distance < 0.9 and abs(angle_norm - 0.5) < gate_width:
                    is_gate = True
                # West gate
                elif distance > 0.8 and distance < 0.9 and abs(angle_norm - 0.75) < gate_width:
                    is_gate = True
                
                # Center area
                if distance < 0.1:
                    char_index = len(ASCII_CHARS) - 1  # Brightest
                    color = AMBER
                # Gates
                elif is_gate:
                    char_index = len(ASCII_CHARS) - 10
                    color = WHITE
                # Normal mandala pattern
                else:
                    char_index = int(value * (len(ASCII_CHARS) - 1))
                    
                    # Color based on which cardinal path this belongs to
                    if cardinal_path == 0:  # North
                        color = (200, 255, 200)  # Light green
                    elif cardinal_path == 1:  # East
                        color = (255, 200, 150)  # Light orange
                    elif cardinal_path == 2:  # South
                        color = (200, 200, 255)  # Light blue
                    else:  # West
                        color = (255, 200, 255)  # Light purple
                
                # Draw the character
                char = ASCII_CHARS[char_index]
                char_surface = self.terminal_font.render(char, True, color)
                surface.blit(char_surface, (x * char_width, y * char_height))
        
        return surface
    
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
                scroll_x = MANDALA_SIZE/2 + math.cos(scroll_angle) * (distance * MANDALA_SIZE/2)
                scroll_y = MANDALA_SIZE/2 + math.sin(scroll_angle) * (distance * MANDALA_SIZE/2)
                
                # Cipher position
                cipher_angle = angle_start + 0.2 + (0.2 * level)
                cipher_x = MANDALA_SIZE/2 + math.cos(cipher_angle) * (distance * MANDALA_SIZE/2)
                cipher_y = MANDALA_SIZE/2 + math.sin(cipher_angle) * (distance * MANDALA_SIZE/2)
                
                # Challenge position
                challenge_angle = angle_start + 0.3 + (0.2 * level)
                challenge_x = MANDALA_SIZE/2 + math.cos(challenge_angle) * (distance * MANDALA_SIZE/2)
                challenge_y = MANDALA_SIZE/2 + math.sin(challenge_angle) * (distance * MANDALA_SIZE/2)
                
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
    
    def draw_mandala(self):
        """Draw the mandala on the screen"""
        self.screen.blit(self.mandala_surface, (0, 0))
        
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
        """Draw the information panel on the right side"""
        info_rect = pygame.Rect(MANDALA_SIZE, 0, INFO_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, info_rect)
        pygame.draw.line(self.screen, GREEN, (MANDALA_SIZE, 0), (MANDALA_SIZE, WINDOW_HEIGHT), 2)
        
        # Draw title
        title_surface = self.terminal_font.render(">> ASCII ADVENTURE <<", True, GREEN)
        self.screen.blit(title_surface, (MANDALA_SIZE + 20, 20))
        
        # Draw current team info
        team_surface = self.terminal_font.render(f"ACTIVE TEAM: {self.teams[self.current_team]['name']}", True, AMBER)
        self.screen.blit(team_surface, (MANDALA_SIZE + 20, 60))
        
        # Draw game phase info
        phase_surface = self.terminal_font.render(f"PHASE: {self.game_phase.upper()}", True, AMBER)
        self.screen.blit(phase_surface, (MANDALA_SIZE + 20, 90))
        
        # Draw instructions based on game phase
        if self.game_phase == "setup":
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
                self.screen.blit(line_surface, (MANDALA_SIZE + 20, 150 + i*30))
    
    def print_screen(self):
        """Take a screenshot and print it"""
        # Logic to capture screen and send to printer will go here
        print("Printing screen...")
        pygame.image.save(self.screen, "mandala_print.png")
    
    def handle_click(self, pos):
        """Handle mouse clicks"""
        x, y = pos
        
        # Check if click is in mandala area
        if x < MANDALA_SIZE:
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
        
        if region["type"] == "scroll":
            self.game_phase = "puzzle"
            self.display_puzzle(region["team"], region["level"])
        elif region["type"] == "cipher":
            self.game_phase = "cipher"
            self.display_cipher(region["team"], region["level"])
        elif region["type"] == "challenge":
            self.game_phase = "challenge"
            self.display_challenge(region["team"], region["level"], region["challenge_type"])
    
    def display_puzzle(self, team, level):
        """Display puzzle in the info panel"""
        # This would generate and display if/then/else pattern data
        print(f"Displaying puzzle for team {team}, level {level}")
        # This functionality will be implemented in the next phase
    
    def display_cipher(self, team, level):
        """Display cipher in the info panel"""
        print(f"Displaying cipher for team {team}, level {level}")
        # This functionality will be implemented in the next phase
    
    def display_challenge(self, team, level, challenge_type):
        """Display challenge in the info panel"""
        print(f"Displaying {challenge_type} challenge for team {team}, level {level}")
        # This functionality will be implemented in the next phase
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:  # P key for Print
                        self.print_screen()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_click(event.pos)
            
            # Clear the screen
            self.screen.fill(BLACK)
            
            # Draw the game elements
            self.draw_mandala()
            self.draw_info_panel()
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = MandalaGame()
    game.run()