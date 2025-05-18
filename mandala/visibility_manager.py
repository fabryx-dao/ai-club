import pygame
import numpy as np
import math

class VisibilityManager:
    """Manages the visibility of the map, implementing fog of war and progressive reveal"""
    
    def __init__(self, size, regions_count=4):
        self.size = size
        self.regions_count = regions_count
        
        # Initialize visibility masks (one per team/region)
        # 0 = hidden, 1 = visible
        self.visibility_masks = []
        for _ in range(regions_count):
            self.visibility_masks.append(np.zeros((size, size)))
        
        # Create surfaces for rendering visibility
        self.visibility_surfaces = []
        for _ in range(regions_count):
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            surface.fill((0, 0, 0, 200))  # Semi-transparent black
            self.visibility_surfaces.append(surface)
        
        # Initialize starting visibility at team gates
        self.initialize_visibility()
    
    def initialize_visibility(self):
        """Set initial visibility at team starting points"""
        # Starting visibility radius
        start_radius = self.size // 10
        
        # For each team, reveal area around their starting gate
        for team_idx in range(self.regions_count):
            # Calculate gate position based on team
            angle = team_idx * math.pi / 2
            gate_x = int(self.size/2 + math.cos(angle) * self.size * 0.4)
            gate_y = int(self.size/2 + math.sin(angle) * self.size * 0.4)
            
            # Reveal circular area around gate
            self.reveal_area(team_idx, gate_x, gate_y, start_radius)
    
    def reveal_area(self, team_idx, center_x, center_y, radius, feather=10):
        """Reveal a circular area for a given team"""
        if team_idx >= len(self.visibility_masks):
            return
            
        # Get mask for this team
        mask = self.visibility_masks[team_idx]
        
        # Calculate bounds for the circle
        min_x = max(0, center_x - radius - feather)
        max_x = min(self.size, center_x + radius + feather)
        min_y = max(0, center_y - radius - feather)
        max_y = min(self.size, center_y + radius + feather)
        
        # Update each pixel in the bounded area
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                # Calculate distance from center
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # If within hard radius, fully visible
                if dist <= radius:
                    mask[y, x] = 1
                # If within feathered edge, partially visible
                elif dist <= radius + feather:
                    # Calculate opacity based on distance
                    opacity = 1 - (dist - radius) / feather
                    mask[y, x] = max(mask[y, x], opacity)
    
    def reveal_path(self, team_idx, start_x, start_y, end_x, end_y, width=10):
        """Reveal a path between two points"""
        if team_idx >= len(self.visibility_masks):
            return
            
        # Calculate path length and direction
        path_length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        if path_length == 0:
            return
            
        # Normalize direction vector
        dir_x = (end_x - start_x) / path_length
        dir_y = (end_y - start_y) / path_length
        
        # Reveal points along the path
        steps = int(path_length)
        for step in range(steps + 1):
            # Calculate position along path
            t = step / steps
            pos_x = int(start_x + dir_x * path_length * t)
            pos_y = int(start_y + dir_y * path_length * t)
            
            # Reveal area at this position
            self.reveal_area(team_idx, pos_x, pos_y, width)
    
    def update_visibility_surface(self, team_idx):
        """Update the visibility surface for rendering"""
        if team_idx >= len(self.visibility_surfaces):
            return
            
        # Get mask and surface for this team
        mask = self.visibility_masks[team_idx]
        surface = self.visibility_surfaces[team_idx]
        
        # Reset surface
        surface.fill((0, 0, 0, 200))
        
        # Update surface based on mask
        for y in range(self.size):
            for x in range(self.size):
                # Skip fully visible pixels
                if mask[y, x] >= 0.99:
                    # Make pixel transparent
                    surface.set_at((x, y), (0, 0, 0, 0))
                elif mask[y, x] > 0:
                    # Partially visible - adjust alpha
                    alpha = int(200 * (1 - mask[y, x]))
                    surface.set_at((x, y), (0, 0, 0, alpha))
    
    def reveal_next_challenge(self, team_idx, challenge_points, current_level):
        """Reveal the area around the next challenge"""
        if current_level >= len(challenge_points) or team_idx >= len(self.visibility_masks):
            return
            
        # Get the next challenge points
        next_level = current_level
        next_points = challenge_points[team_idx][next_level]
        
        # Get previous challenge points (if they exist)
        prev_points = None
        if current_level > 0:
            prev_points = challenge_points[team_idx][current_level - 1]
        
        # Reveal area around each element
        for element_type in ["scroll", "cipher", "challenge"]:
            point = next_points[element_type]
            screen_x, screen_y = point["x"], point["y"]
            
            # Reveal larger area around the new challenge elements
            self.reveal_area(team_idx, screen_x, screen_y, 40)
            
            # Create path from previous challenge if it exists
            if prev_points:
                prev_point = prev_points["challenge"]
                prev_x, prev_y = prev_point["x"], prev_point["y"]
                
                # Reveal path from previous challenge to next scroll
                if element_type == "scroll":
                    self.reveal_path(team_idx, prev_x, prev_y, screen_x, screen_y, 15)
        
        # Update the visibility surface
        self.update_visibility_surface(team_idx)
    
    def get_visibility_surface(self, team_idx):
        """Get the visibility surface for a specific team"""
        if team_idx < len(self.visibility_surfaces):
            return self.visibility_surfaces[team_idx]
        return None