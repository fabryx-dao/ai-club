import pygame

# Colors
BLACK = (0, 0, 0)
GREEN = (50, 255, 50)
AMBER = (255, 176, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)

class UIManager:
    """Manages all UI drawing functionality"""
    
    def __init__(self, screen, mandala_size, info_panel_width, font):
        self.screen = screen
        self.mandala_size = mandala_size
        self.info_panel_width = info_panel_width
        self.font = font
    
    def draw_ui(self, game_phase, current_team, puzzle, cipher, encoded_message, challenge_state, input_text):
        """Draw the appropriate UI based on game phase"""
        # Draw the info panel background
        self.draw_info_panel_background()
        
        # Draw UI based on the current game phase
        if game_phase == "setup":
            self.draw_setup_panel(current_team)
        elif game_phase == "puzzle" and puzzle:
            self.draw_puzzle_panel(puzzle, input_text)
        elif game_phase == "cipher" and cipher:
            self.draw_cipher_panel(encoded_message, input_text)
        elif game_phase == "challenge" and challenge_state:
            self.draw_challenge_panel(challenge_state, input_text)
    
    def draw_info_panel_background(self):
        """Draw the basic info panel background"""
        info_rect = pygame.Rect(self.mandala_size, 0, self.info_panel_width, self.screen.get_height())
        pygame.draw.rect(self.screen, BLACK, info_rect)
        pygame.draw.line(self.screen, GREEN, (self.mandala_size, 0), (self.mandala_size, self.screen.get_height()), 2)
        
        # Draw title
        title_surface = self.font.render(">> ASCII ADVENTURE <<", True, GREEN)
        self.screen.blit(title_surface, (self.mandala_size + 20, 20))
    
    def draw_setup_panel(self, team):
        """Draw the setup/welcome screen"""
        # Draw team info
        team_surface = self.font.render(f"ACTIVE TEAM: {team['name']}", True, AMBER)
        self.screen.blit(team_surface, (self.mandala_size + 20, 60))
        
        progress_surface = self.font.render(f"PROGRESS: LEVEL {team['position']}", True, AMBER)
        self.screen.blit(progress_surface, (self.mandala_size + 20, 90))
        
        # Draw instructions
        instructions = [
            "WELCOME TO THE MANDALA CHALLENGE",
            "",
            "NAVIGATION:",
            "- MOUSE WHEEL: Zoom in/out",
            "- ARROWS/WASD: Pan the view",
            "- NUMBERS 1-4: Switch regions",
            "- CLICK on the mini-map to select region",
            "",
            "GAMEPLAY:",
            "1. CLICK ON A SCROLL TO BEGIN A CHALLENGE",
            "2. SOLVE THE PATTERN PUZZLE",
            "3. DECODE THE CIPHER",
            "4. COMPLETE THE BREATHING CHALLENGE",
            "",
            "REACH THE CENTER TO WIN"
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.font.render(line, True, WHITE)
            self.screen.blit(line_surface, (self.mandala_size + 20, 150 + i*25))
    
    def draw_puzzle_panel(self, puzzle, input_text):
        """Draw the puzzle interface"""
        # Draw phase info
        phase_surface = self.font.render("PHASE: DECODE THE PATTERN", True, AMBER)
        self.screen.blit(phase_surface, (self.mandala_size + 20, 60))
        
        # Draw puzzle title and description
        puzzle_title = self.font.render("== DECODE THE PATTERN ==", True, WHITE)
        self.screen.blit(puzzle_title, (self.mandala_size + 20, 100))
        
        description = self.font.render(puzzle.get_puzzle_description(), True, GREEN)
        self.screen.blit(description, (self.mandala_size + 20, 130))
        
        # Draw input/output table
        self.screen.blit(self.font.render("INPUT", True, AMBER), (self.mandala_size + 50, 170))
        self.screen.blit(self.font.render("OUTPUT", True, AMBER), (self.mandala_size + 200, 170))
        
        for i in range(len(puzzle.input_values) - 1):
            input_val = self.font.render(str(puzzle.input_values[i]), True, WHITE)
            output_val = self.font.render(str(puzzle.output_values[i]), True, WHITE)
            self.screen.blit(input_val, (self.mandala_size + 50, 200 + i * 30))
            self.screen.blit(output_val, (self.mandala_size + 200, 200 + i * 30))
        
        # Draw the test input
        test_input = self.font.render(str(puzzle.test_input) + " = ?", True, GREEN)
        self.screen.blit(test_input, (self.mandala_size + 50, 200 + 4 * 30))
        
        # Draw input box
        pygame.draw.rect(self.screen, GRAY, (self.mandala_size + 20, 350, 300, 40), 2)
        input_surface = self.font.render(input_text, True, WHITE)
        self.screen.blit(input_surface, (self.mandala_size + 30, 360))
        
        # Draw instructions
        instructions = [
            "Find the pattern in the input/output pairs.",
            "What is the rule that transforms each input",
            "into its corresponding output?",
            "",
            "Once you have figured out the pattern,",
            "apply it to the final input and enter",
            "your answer in the box above.",
            "",
            "Press ENTER to submit your answer."
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 410 + i * 25))
    
    def draw_cipher_panel(self, encoded_message, input_text):
        """Draw the cipher interface"""
        # Draw phase info
        phase_surface = self.font.render("PHASE: DECODE THE CIPHER", True, AMBER)
        self.screen.blit(phase_surface, (self.mandala_size + 20, 60))
        
        # Draw cipher title
        cipher_title = self.font.render("== DECODE THE CIPHER ==", True, WHITE)
        self.screen.blit(cipher_title, (self.mandala_size + 20, 100))
        
        # Draw instructions
        instructions = [
            "Use the answer from the previous puzzle",
            "as the key to decode this cipher:",
            "",
            f"{encoded_message}",
            "",
            "Enter the key below:"
        ]
        
        for i, line in enumerate(instructions):
            line_surface = self.font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 140 + i*25))
        
        # Draw input box
        pygame.draw.rect(self.screen, GRAY, (self.mandala_size + 20, 300, 300, 40), 2)
        input_surface = self.font.render(input_text, True, WHITE)
        self.screen.blit(input_surface, (self.mandala_size + 30, 310))
        
        # Draw more instructions
        more_instructions = [
            "Once you've entered the key, press ENTER",
            "to decode the message. The decoded message",
            "will provide instructions for the next challenge."
        ]
        
        for i, line in enumerate(more_instructions):
            line_surface = self.font.render(line, True, GREEN)
            self.screen.blit(line_surface, (self.mandala_size + 20, 360 + i*25))
    
    def draw_challenge_panel(self, challenge_state, input_text):
        """Draw the challenge interface"""
        # Draw phase info
        phase_surface = self.font.render(f"PHASE: {challenge_state['type'].upper()} CHALLENGE", True, AMBER)
        self.screen.blit(phase_surface, (self.mandala_size + 20, 60))
        
        # Draw challenge title
        challenge_title = self.font.render(f"== {challenge_state['type'].upper()} CHALLENGE ==", True, WHITE)
        self.screen.blit(challenge_title, (self.mandala_size + 20, 100))
        
        if challenge_state["phase"] == "setup":
            # Draw decoded message if available
            if challenge_state["decoded_text"]:
                message_surface = self.font.render(f"Message: {challenge_state['decoded_text']}", True, GREEN)
                self.screen.blit(message_surface, (self.mandala_size + 20, 140))
            
            # Draw instructions
            instructions = [
                "Enter the decoded message to begin the challenge:",
                "",
                "When ready, the student will place their finger",
                "on the PPG sensor. A 10-second countdown will",
                "begin, followed by the 60-second challenge."
            ]
            
            for i, line in enumerate(instructions):
                line_surface = self.font.render(line, True, AMBER)
                self.screen.blit(line_surface, (self.mandala_size + 20, 180 + i*25))
            
            # Draw input box
            pygame.draw.rect(self.screen, GRAY, (self.mandala_size + 20, 320, 300, 40), 2)
            input_surface = self.font.render(input_text, True, WHITE)
            self.screen.blit(input_surface, (self.mandala_size + 30, 330))
            
        elif challenge_state["phase"] == "countdown":
            # Draw countdown
            countdown_text = self.font.render(f"PREPARE IN: {challenge_state['timer']} seconds", True, GREEN)
            self.screen.blit(countdown_text, (self.mandala_size + 20, 140))
            
            # Draw instructions
            instructions = [
                "Get ready!",
                "Place your finger on the sensor.",
                f"Challenge begins in {challenge_state['timer']} seconds..."
            ]
            
            for i, line in enumerate(instructions):
                line_surface = self.font.render(line, True, AMBER)
                self.screen.blit(line_surface, (self.mandala_size + 20, 180 + i*25))
            
        elif challenge_state["phase"] == "active":
            # Draw timer
            timer_text = self.font.render(f"TIME: {challenge_state['timer']} seconds", True, GREEN)
            self.screen.blit(timer_text, (self.mandala_size + 20, 140))
            
            # Draw score
            score_text = self.font.render(f"SCORE: {int(challenge_state['score'])}", True, GREEN)
            self.screen.blit(score_text, (self.mandala_size + 20, 170))
            
            # Draw challenge-specific visualization
            if challenge_state["type"] == "fire":
                self.draw_fire_challenge(challenge_state)
            elif challenge_state["type"] == "wave":
                self.draw_wave_challenge(challenge_state)
            elif challenge_state["type"] == "lightning":
                self.draw_lightning_challenge(challenge_state)
                
        elif challenge_state["phase"] == "complete":
            # Draw completion message
            complete_text = self.font.render("CHALLENGE COMPLETE!", True, GREEN)
            self.screen.blit(complete_text, (self.mandala_size + 20, 140))
            
            # Draw final score
            score_text = self.font.render(f"FINAL SCORE: {int(challenge_state['score'])}", True, GREEN)
            self.screen.blit(score_text, (self.mandala_size + 20, 170))
            
            # Draw success/failure message
            if challenge_state["score"] >= 70:
                result_text = self.font.render("SUCCESS! You may advance.", True, AMBER)
            else:
                result_text = self.font.render("Try again to improve your score.", True, AMBER)
            self.screen.blit(result_text, (self.mandala_size + 20, 200))
    
    def draw_fire_challenge(self, challenge_state):
        """Draw the fire challenge visualization"""
        # Draw breathing guide
        y_pos = 220
        width = self.info_panel_width - 40
        height = 100
        
        # Draw fire animation based on score
        flame_height = int(height * (challenge_state["score"] / 100))
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
            line_surface = self.font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 340 + i*25))
    
    def draw_wave_challenge(self, challenge_state):
        """Draw the wave challenge visualization"""
        # Draw breathing guide
        y_pos = 220
        width = self.info_panel_width - 40
        height = 100
        
        # Draw wave animation
        wave_points = []
        for x in range(width):
            # Create a wave effect
            import time
            import math
            t = time.time()
            x_norm = x / width
            y_value = math.sin(x_norm * 10 + t) * 20
            
            # Invert based on score (high score = low wave)
            y_adjust = height * (1 - challenge_state["score"] / 100) 
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
            line_surface = self.font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 340 + i*25))
    
    def draw_lightning_challenge(self, challenge_state):
        """Draw the lightning challenge visualization"""
        # Draw breathing guide
        y_pos = 220
        width = self.info_panel_width - 40
        height = 100
        
        # Draw lightning animation
        import time
        import math
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
        score_width = int(width * challenge_state["score"] / 100)
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
            line_surface = self.font.render(line, True, AMBER)
            self.screen.blit(line_surface, (self.mandala_size + 20, 340 + i*25))