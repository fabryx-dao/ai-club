import pygame
import math
import numpy as np

# ASCII characters for density mapping (from dark to light)
ASCII_CHARS = ' .\'`^",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'

# Colors
BLACK = (0, 0, 0)
GREEN = (50, 255, 50)
AMBER = (255, 176, 0)
WHITE = (255, 255, 255)

class MandalaGenerator:
    """Generates an ASCII art mandala"""
    
    def __init__(self, size):
        self.size = size
        self.surface = pygame.Surface((size, size))
        self.font = pygame.font.SysFont('courier', 16)
        
        # Generate the mandala
        self.generate_ascii_mandala()
    
    def generate_ascii_mandala(self):
        """Generate the ASCII art mandala with four paths"""
        self.surface.fill(BLACK)
        
        # ASCII character size
        char_width, char_height = self.font.size("X")
        cols = self.size // char_width
        rows = self.size // char_height
        
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
                char_surface = self.font.render(char, True, color)
                self.surface.blit(char_surface, (x * char_width, y * char_height))