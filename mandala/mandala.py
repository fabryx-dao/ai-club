import pygame
import math
import numpy as np
import random
from opensimplex import OpenSimplex

# ASCII characters for elevation mapping (from lowest to highest)
TERRAIN_CHARS = ' .:;~=+*#%@'

# ASCII characters for water features
WATER_CHARS = '.~≈≋'

# ASCII characters for landmarks and special features
LANDMARK_CHARS = '⚑⚐◊♦♠♣♥♦⚓✧✦★☽☾⌂⍟'

# Colors
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
GRAY = (80, 80, 80)
GREEN = (50, 255, 50)
AMBER = (255, 176, 0)
WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
CYAN = (0, 200, 200)
DARK_GREEN = (0, 100, 50)
LIGHT_GREEN = (150, 255, 150)
ORANGE = (255, 150, 50)
PURPLE = (200, 100, 255)

class MandalaGenerator:
    """Generates a terrain-based ASCII art mandala with mini-map"""
    
    def __init__(self, size):
        self.size = size
        self.surface = pygame.Surface((size, size))
        self.font = pygame.font.SysFont('courier', 14)
        self.mini_map_size = size // 5  # Mini-map will be 1/5 the size
        self.mini_map = pygame.Surface((self.mini_map_size, self.mini_map_size))
        
        # Initialize noise generators for terrain
        self.noise_gen = OpenSimplex(seed=random.randint(1, 10000))
        self.feature_noise = OpenSimplex(seed=random.randint(1, 10000))
        
        # Current view parameters
        self.current_region = 0  # 0, 1, 2, 3 for the four cardinal regions
        self.zoom_level = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        
        # Cache for character surfaces (for better performance)
        self.char_cache = {}
        
        # Regions for the four cardinal areas
        self.regions = [
            {"name": "North", "center_x": 0.25, "center_y": 0.25, "color_bias": LIGHT_GREEN},
            {"name": "East", "center_x": 0.75, "center_y": 0.25, "color_bias": ORANGE},
            {"name": "South", "center_x": 0.75, "center_y": 0.75, "color_bias": CYAN},
            {"name": "West", "center_x": 0.25, "center_y": 0.75, "color_bias": PURPLE}
        ]
        
        # Location of the three challenge points for each region
        self.challenge_points = []
        for region_idx in range(4):
            points = []
            region = self.regions[region_idx]
            center_x, center_y = region["center_x"], region["center_y"]
            
            # Create path from outside toward center
            path_length = 0.3
            angle_offset = region_idx * math.pi / 2
            
            for i in range(3):
                # Calculate position along path toward center
                distance = 0.4 - (i * path_length / 3)
                angle = angle_offset + (i * 0.2)
                
                x = 0.5 + math.cos(angle) * distance
                y = 0.5 + math.sin(angle) * distance
                
                # Store positions for scroll, cipher, and challenge
                scroll_x = x - 0.03 + (i * 0.01)
                scroll_y = y - 0.03 + (i * 0.01)
                
                cipher_x = x
                cipher_y = y
                
                challenge_x = x + 0.03 - (i * 0.01)
                challenge_y = y + 0.03 - (i * 0.01)
                
                # Add to challenge points with all three elements
                challenge_type = ["fire", "wave", "lightning"][i]
                points.append({
                    "level": i,
                    "scroll": {"x": scroll_x, "y": scroll_y},
                    "cipher": {"x": cipher_x, "y": cipher_y},
                    "challenge": {"x": challenge_x, "y": challenge_y, "type": challenge_type}
                })
            
            self.challenge_points.append(points)
        
        # Generate the terrain and mini-map
        self.generate_terrain()
        self.generate_mini_map()
    
    def get_elevation(self, x, y, scale=5.0):
        """Get terrain elevation at a point using noise"""
        # Use multiple layers of noise at different scales for more interesting terrain
        value = 0
        value += self.noise_gen.noise2(x * scale, y * scale) * 0.5
        value += self.noise_gen.noise2(x * scale * 2, y * scale * 2) * 0.25
        value += self.noise_gen.noise2(x * scale * 4, y * scale * 4) * 0.125
        
        # Normalize to 0-1 range
        value = (value + 1) * 0.5
        
        # Create central mountain peak
        center_dist = math.sqrt((x - 0.5)**2 + (y - 0.5)**2)
        center_value = max(0, 1 - center_dist * 2)
        
        # Blend the noise with the central peak
        value = value * 0.6 + center_value * 0.4
        
        return value
    
    def get_feature(self, x, y, scale=8.0):
        """Get terrain feature type at a point"""
        # Use different noise generator for features
        value = self.feature_noise.noise2(x * scale, y * scale)
        
        # Normalize to 0-1 range
        value = (value + 1) * 0.5
        
        return value
    
    def get_region_influence(self, x, y):
        """Calculate influence from each region based on distance"""
        influences = []
        for region in self.regions:
            center_x, center_y = region["center_x"], region["center_y"]
            dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            influence = max(0, 1 - dist * 3)  # Influence decreases with distance
            influences.append((influence, region["color_bias"]))
        
        return influences
    
    def get_terrain_char_and_color(self, x, y):
        """Get the character and color for terrain at a given point"""
        # Get the elevation at this point
        elevation = self.get_elevation(x, y)
        feature = self.get_feature(x, y)
        
        # Calculate region influences
        influences = self.get_region_influence(x, y)
        
        # Determine base character from elevation
        if elevation < 0.3:  # Water
            water_idx = min(len(WATER_CHARS) - 1, int(elevation * 10))
            char = WATER_CHARS[water_idx]
            
            # Color gradient from dark blue to cyan for water
            blue_factor = elevation / 0.3
            base_color = (
                int(50 + 150 * blue_factor),
                int(100 + 100 * blue_factor),
                255
            )
        else:  # Land
            # Normalize elevation to land range (0.3-1.0 -> 0.0-1.0)
            land_elevation = (elevation - 0.3) / 0.7
            char_idx = min(len(TERRAIN_CHARS) - 1, int(land_elevation * len(TERRAIN_CHARS)))
            char = TERRAIN_CHARS[char_idx]
            
            # Base color based on elevation
            if land_elevation < 0.2:  # Low lands
                base_color = (100, 180, 100)  # Light green
            elif land_elevation < 0.5:  # Medium elevation
                base_color = (110, 140, 80)  # Medium green
            elif land_elevation < 0.8:  # High elevation
                base_color = (140, 120, 60)  # Brown
            else:  # Mountain peaks
                base_color = (200, 200, 200)  # Gray/white
        
        # Modify color based on region influences
        final_color = list(base_color)
        total_influence = 0
        
        for influence, color in influences:
            if influence > 0:
                total_influence += influence
                for i in range(3):
                    final_color[i] += int(color[i] * influence)
        
        # Normalize color
        if total_influence > 0:
            for i in range(3):
                final_color[i] = int(final_color[i] / (1 + total_influence))
                final_color[i] = min(255, max(0, final_color[i]))
        
        # Special landmarks or features
        if 0.3 < elevation < 0.9 and feature > 0.93:
            # Special feature (5% chance)
            char = random.choice(LANDMARK_CHARS)
            
            # Make it glow a bit
            for i in range(3):
                final_color[i] = min(255, final_color[i] + 50)
        
        return char, tuple(final_color)
    
    def generate_terrain(self):
        """Generate the ASCII art terrain"""
        self.surface.fill(BLACK)
        
        # ASCII character size
        char_width, char_height = self.font.size("X")
        cols = self.size // char_width
        rows = self.size // char_height
        
        # Create the terrain pattern
        for y in range(rows):
            for x in range(cols):
                # Skip the mini-map area in the top right
                if x >= cols - self.mini_map_size // char_width and y < self.mini_map_size // char_height:
                    continue
                
                # Calculate normalized position with zoom and offset
                zoom_factor = 1.0 / self.zoom_level
                region = self.regions[self.current_region]
                
                norm_x = region["center_x"] + (x / cols - 0.5) * zoom_factor + self.view_offset_x
                norm_y = region["center_y"] + (y / rows - 0.5) * zoom_factor + self.view_offset_y
                
                # Get character and color for this position
                char, color = self.get_terrain_char_and_color(norm_x, norm_y)
                
                # Render the character efficiently (using cache for better performance)
                cache_key = f"{char}_{color}"
                if cache_key not in self.char_cache:
                    self.char_cache[cache_key] = self.font.render(char, True, color)
                    
                char_surface = self.char_cache[cache_key]
                self.surface.blit(char_surface, (x * char_width, y * char_height))
    
    def generate_mini_map(self):
        """Generate the mini-map in the top right corner"""
        self.mini_map.fill(DARK_GRAY)
        
        # Mini-map resolution
        map_size = self.mini_map_size
        pixels_per_point = max(1, map_size // 50)  # Ensure at least 1 pixel per point
        
        # Draw simplified terrain
        for y in range(0, map_size, pixels_per_point):
            for x in range(0, map_size, pixels_per_point):
                # Calculate normalized position for the entire world
                norm_x = x / map_size
                norm_y = y / map_size
                
                # Get elevation and color
                elevation = self.get_elevation(norm_x, norm_y)
                
                # Simplified color based on elevation
                if elevation < 0.3:  # Water
                    color = BLUE
                elif elevation < 0.5:  # Lowlands
                    color = DARK_GREEN
                elif elevation < 0.8:  # Highlands
                    color = GRAY
                else:  # Mountains
                    color = WHITE
                
                # Draw the pixel on the mini-map
                pygame.draw.rect(self.mini_map, color, 
                                (x, y, pixels_per_point, pixels_per_point))
        
        # Draw region borders
        for region_idx, region in enumerate(self.regions):
            center_x = int(region["center_x"] * map_size)
            center_y = int(region["center_y"] * map_size)
            
            # Draw region indicator
            region_color = region["color_bias"]
            pygame.draw.circle(self.mini_map, region_color, (center_x, center_y), 3)
            
            # Highlight current region
            if region_idx == self.current_region:
                pygame.draw.rect(self.mini_map, GREEN, 
                                (center_x - 10, center_y - 10, 20, 20), 1)
        
        # Blit mini-map to main surface
        self.surface.blit(self.mini_map, (self.size - self.mini_map_size, 0))
        
        # Draw border around mini-map
        pygame.draw.rect(self.surface, GREEN, 
                        (self.size - self.mini_map_size, 0, self.mini_map_size, self.mini_map_size), 1)
    
    def set_region(self, region_idx):
        """Set the current region to view"""
        if 0 <= region_idx < 4:
            self.current_region = region_idx
            self.view_offset_x = 0
            self.view_offset_y = 0
            self.zoom_level = 1.0
            self.generate_terrain()
            self.generate_mini_map()
    
    def handle_minimap_click(self, pos):
        """Handle click on mini-map"""
        x, y = pos
        
        # Check if click is in mini-map area
        mini_map_x = x - (self.size - self.mini_map_size)
        mini_map_y = y
        
        if 0 <= mini_map_x < self.mini_map_size and 0 <= mini_map_y < self.mini_map_size:
            # Convert click to normalized coordinates
            norm_x = mini_map_x / self.mini_map_size
            norm_y = mini_map_y / self.mini_map_size
            
            # Find closest region
            closest_idx = 0
            closest_dist = float('inf')
            
            for i, region in enumerate(self.regions):
                dist = math.sqrt((norm_x - region["center_x"])**2 + (norm_y - region["center_y"])**2)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_idx = i
            
            # Set the new region
            self.set_region(closest_idx)
            return True
            
        return False
    
    def get_clickable_points(self):
        """Get all clickable points in the current view"""
        clickable = []
        
        # Only include points from the current region
        region_points = self.challenge_points[self.current_region]
        
        for point_set in region_points:
            level = point_set["level"]
            
            # Add scroll point
            norm_x = point_set["scroll"]["x"]
            norm_y = point_set["scroll"]["y"]
            screen_x, screen_y = self.get_screen_pos(norm_x, norm_y)
            
            if screen_x is not None:
                clickable.append({
                    "type": "scroll",
                    "team": self.current_region,
                    "level": level,
                    "x": screen_x,
                    "y": screen_y,
                    "radius": 15
                })
            
            # Add cipher point
            norm_x = point_set["cipher"]["x"]
            norm_y = point_set["cipher"]["y"]
            screen_x, screen_y = self.get_screen_pos(norm_x, norm_y)
            
            if screen_x is not None:
                clickable.append({
                    "type": "cipher",
                    "team": self.current_region,
                    "level": level,
                    "x": screen_x,
                    "y": screen_y,
                    "radius": 15
                })
            
            # Add challenge point
            norm_x = point_set["challenge"]["x"]
            norm_y = point_set["challenge"]["y"]
            screen_x, screen_y = self.get_screen_pos(norm_x, norm_y)
            
            if screen_x is not None:
                clickable.append({
                    "type": "challenge",
                    "challenge_type": point_set["challenge"]["type"],
                    "team": self.current_region,
                    "level": level,
                    "x": screen_x,
                    "y": screen_y,
                    "radius": 15
                })
        
        return clickable
    
    def get_screen_pos(self, norm_x, norm_y):
        """Convert normalized world position to screen position"""
        # Calculate the visible region
        region = self.regions[self.current_region]
        view_center_x = region["center_x"] + self.view_offset_x
        view_center_y = region["center_y"] + self.view_offset_y
        view_width = 1.0 / self.zoom_level
        view_height = 1.0 / self.zoom_level
        
        # Check if the point is in the visible region
        if (abs(norm_x - view_center_x) > view_width / 2 or 
            abs(norm_y - view_center_y) > view_height / 2):
            return None, None
        
        # Calculate screen position
        char_width, char_height = self.font.size("X")
        cols = self.size // char_width
        rows = self.size // char_height
        
        # Adjust for mini-map region
        mini_map_cols = self.mini_map_size // char_width
        mini_map_rows = self.mini_map_size // char_height
        
        # Convert from normalized to screen coordinates
        screen_x = int((norm_x - (view_center_x - view_width / 2)) / view_width * cols)
        screen_y = int((norm_y - (view_center_y - view_height / 2)) / view_height * rows)
        
        # Check if the point is in the mini-map area
        if screen_x >= cols - mini_map_cols and screen_y < mini_map_rows:
            return None, None
        
        return screen_x * char_width, screen_y * char_height
    
    def zoom(self, factor):
        """Zoom in or out"""
        new_zoom = self.zoom_level * factor
        # Limit zoom range
        if 0.5 <= new_zoom <= 5.0:
            self.zoom_level = new_zoom
            self.generate_terrain()
            self.generate_mini_map()
    
    def pan(self, dx, dy):
        """Pan the view"""
        # Adjust by zoom level to make panning consistent at different zooms
        self.view_offset_x += dx / self.zoom_level
        self.view_offset_y += dy / self.zoom_level
        
        # Limit panning to prevent getting too far from the region
        region = self.regions[self.current_region]
        max_offset = 0.3 / self.zoom_level
        
        self.view_offset_x = max(-max_offset, min(max_offset, self.view_offset_x))
        self.view_offset_y = max(-max_offset, min(max_offset, self.view_offset_y))
        
        self.generate_terrain()
        self.generate_mini_map()