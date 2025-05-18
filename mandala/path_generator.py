import math
import random
import numpy as np

class PathGenerator:
    """Generates paths between challenge points and manages terrain transformations"""
    
    def __init__(self, size, noise_generator=None):
        self.size = size
        self.noise_generator = noise_generator
        
        # Transformation maps for each team
        # Stores which ASCII characters to replace and with what
        self.transformation_maps = {}
        
        # Path data for each team
        # Stores the points along each path segment
        self.paths = {}
        
        # Initialize transformation maps
        self.initialize_transformation_maps()
    
    def initialize_transformation_maps(self):
        """Initialize the character transformation maps for path creation"""
        # Define character transformations for different terrain types
        # Forest terrain transformations
        forest_transforms = {
            "#": ".",  # Dense trees to path
            "%": ",",  # Shrubs to light path
            "&": " ",  # Bushes to clear path
            "@": ".",  # Dense vegetation to path
        }
        
        # Mountain terrain transformations
        mountain_transforms = {
            "^": ".",   # Mountain peak to path
            "*": ",",   # Rocky area to light path
            "+": " ",   # Hills to clear path
            "=": ".",   # Plateau to path
        }
        
        # Water terrain transformations
        water_transforms = {
            "~": ".",   # Waves to path
            "≈": ",",   # Ripples to light path
            "≋": " ",   # Deep water to clear path
            "w": ".",   # Water to path
        }
        
        # Magical terrain transformations
        magic_transforms = {
            "♦": ".",   # Crystal to path
            "♠": ",",   # Dark energy to light path
            "♣": " ",   # Magic bush to clear path
            "★": ".",   # Star power to path
        }
        
        # Assign transformation maps to teams
        self.transformation_maps = {
            0: forest_transforms,    # North team - Forest
            1: mountain_transforms,  # East team - Mountains
            2: water_transforms,     # South team - Water
            3: magic_transforms      # West team - Magic
        }
    
    def generate_path(self, team_idx, start_x, start_y, end_x, end_y, jitter=20):
        """Generate a path between two points with some natural jitter"""
        # Initialize path points
        path_points = []
        
        # Calculate direct path length
        direct_length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        # Number of segments based on length
        num_segments = max(5, int(direct_length / 50))
        
        # Generate intermediate points with jitter
        prev_x, prev_y = start_x, start_y
        path_points.append((prev_x, prev_y))
        
        for i in range(1, num_segments):
            # Calculate position along direct path
            t = i / num_segments
            direct_x = start_x + (end_x - start_x) * t
            direct_y = start_y + (end_y - start_y) * t
            
            # Add random jitter
            jitter_amount = jitter * math.sin(t * math.pi)  # Maximum jitter in middle
            jitter_x = random.uniform(-jitter_amount, jitter_amount)
            jitter_y = random.uniform(-jitter_amount, jitter_amount)
            
            # New point with jitter
            point_x = int(direct_x + jitter_x)
            point_y = int(direct_y + jitter_y)
            
            # Add to path
            path_points.append((point_x, point_y))
            
            # Update previous point
            prev_x, prev_y = point_x, point_y
        
        # Add end point
        path_points.append((end_x, end_y))
        
        # Store the path
        if team_idx not in self.paths:
            self.paths[team_idx] = []
        
        self.paths[team_idx].append(path_points)
        
        return path_points
    
    def get_path_transformation_info(self, team_idx, path_points, radius=5):
        """Get information about the characters to transform along a path"""
        if team_idx not in self.transformation_maps:
            return []
            
        # Get transformation map for this team
        transform_map = self.transformation_maps[team_idx]
        
        # Create a list of transformation instructions
        transformations = []
        
        # For each point in the path
        for x, y in path_points:
            # Define area around the point
            min_x = max(0, x - radius)
            max_x = min(self.size, x + radius)
            min_y = max(0, y - radius)
            max_y = min(self.size, y + radius)
            
            # Add transformation instructions for this area
            transform_info = {
                "area": (min_x, min_y, max_x, max_y),
                "map": transform_map
            }
            transformations.append(transform_info)
        
        return transformations
    
    def get_all_paths_for_team(self, team_idx):
        """Get all path points for a specific team"""
        if team_idx in self.paths:
            return self.paths[team_idx]
        return []