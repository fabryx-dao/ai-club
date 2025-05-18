import math
import random

class ChallengePointsManager:
    """Manages the progression and placement of challenge points"""
    
    def __init__(self, mandala_size, regions_count=4):
        self.size = mandala_size
        self.regions_count = regions_count
        
        # Challenge points for each team and level
        self.challenge_points = [[] for _ in range(regions_count)]
        
        # Visibility status for each challenge
        # A challenge is only visible after the previous one is completed
        self.visibility_status = [[] for _ in range(regions_count)]
        
        # Generate initial challenge points
        self.generate_challenge_points()
    
    def generate_challenge_points(self, levels_count=3):
        """Generate the challenge points for all teams and levels"""
        # Define terrain influence for each team's area
        region_centers = [
            (0.25, 0.25),  # North region
            (0.75, 0.25),  # East region
            (0.75, 0.75),  # South region
            (0.25, 0.75)   # West region
        ]
        
        # For each team/region
        for region_idx in range(self.regions_count):
            # Get the center of this region
            center_x, center_y = region_centers[region_idx]
            
            # Convert to pixel coordinates
            center_x_px = int(center_x * self.size)
            center_y_px = int(center_y * self.size)
            
            # Starting position at the edge of the region, pointing toward center
            angle = math.atan2(0.5 - center_y, 0.5 - center_x)
            start_dist = 0.35  # Distance from center to starting point
            
            start_x = int(center_x_px + math.cos(angle) * start_dist * self.size)
            start_y = int(center_y_px + math.sin(angle) * start_dist * self.size)
            
            # Generate challenge points for this region
            team_points = []
            
            # Calculate step sizes toward center
            step_size = start_dist / (levels_count + 1)
            
            prev_x, prev_y = start_x, start_y
            
            # For each level
            for level in range(levels_count):
                # Calculate position along path toward center
                t = (level + 1) / (levels_count + 1)  # Normalize to 0-1
                
                # Add some jitter/variety to the path
                jitter = 0.05 * self.size * (1 - t)  # Less jitter as we approach center
                jitter_x = random.uniform(-jitter, jitter)
                jitter_y = random.uniform(-jitter, jitter)
                
                # Calculate position with jitter
                pos_x = int(center_x_px + math.cos(angle) * (start_dist - t * start_dist) * self.size + jitter_x)
                pos_y = int(center_y_px + math.sin(angle) * (start_dist - t * start_dist) * self.size + jitter_y)
                
                # Spacing between challenge elements
                spacing = 25 - level * 5  # Decrease spacing as we approach center
                
                # Calculate positions for scroll, cipher, and challenge
                scroll_angle = angle + math.pi/6  # Slightly offset
                cipher_angle = angle
                challenge_angle = angle - math.pi/6  # Slightly offset
                
                scroll_x = int(pos_x + math.cos(scroll_angle) * spacing)
                scroll_y = int(pos_y + math.sin(scroll_angle) * spacing)
                
                cipher_x = pos_x
                cipher_y = pos_y
                
                challenge_x = int(pos_x + math.cos(challenge_angle) * spacing)
                challenge_y = int(pos_y + math.sin(challenge_angle) * spacing)
                
                # Create the challenge point set
                challenge_type = ["fire", "wave", "lightning"][level % 3]
                point_set = {
                    "level": level,
                    "scroll": {"x": scroll_x, "y": scroll_y},
                    "cipher": {"x": cipher_x, "y": cipher_y},
                    "challenge": {"x": challenge_x, "y": challenge_y, "type": challenge_type}
                }
                
                # Add to team's challenge points
                team_points.append(point_set)
                
                # Default visibility - only first level is visible initially
                self.visibility_status[region_idx].append(level == 0)
                
                # Update previous position for next iteration
                prev_x, prev_y = pos_x, pos_y
            
            # Store points for this team
            self.challenge_points[region_idx] = team_points
    
    def get_visible_challenge_points(self, team_idx):
        """Get the challenge points that are currently visible for a team"""
        if team_idx >= len(self.challenge_points):
            return []
            
        visible_points = []
        team_points = self.challenge_points[team_idx]
        visibility = self.visibility_status[team_idx]
        
        for i, point_set in enumerate(team_points):
            if i < len(visibility) and visibility[i]:
                visible_points.append(point_set)
        
        return visible_points
    
    def mark_level_completed(self, team_idx, level):
        """Mark a level as completed and reveal the next level"""
        if team_idx >= len(self.visibility_status):
            return
            
        # Ensure this level exists
        visibility = self.visibility_status[team_idx]
        if level >= len(visibility):
            return
            
        # Mark the current level as completed by keeping it visible
        visibility[level] = True
        
        # Reveal the next level if it exists
        next_level = level + 1
        if next_level < len(visibility):
            visibility[next_level] = True
    
    def get_challenge_points(self):
        """Get all challenge points"""
        return self.challenge_points