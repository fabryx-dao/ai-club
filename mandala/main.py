import pygame
import sys
from game_manager import GameManager

# Initialize pygame
pygame.init()

# Game configuration
WINDOW_WIDTH = 1680
WINDOW_HEIGHT = 990
MANDALA_SIZE = WINDOW_HEIGHT  # 1:1 aspect ratio
INFO_PANEL_WIDTH = WINDOW_WIDTH - MANDALA_SIZE
FPS = 30

def main():
    """Main entry point for the game"""
    # Create the game window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("ASCII Mandala Adventure")
    clock = pygame.time.Clock()
    
    # Create game manager
    game = GameManager(screen, MANDALA_SIZE, INFO_PANEL_WIDTH)
    
    # Main game loop
    running = True
    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # P key for Print
                    game.print_screen()
                elif event.key == pygame.K_RETURN and game.input_active:
                    game.process_input()
                else:
                    game.handle_input(event)
            elif event.type in [pygame.MOUSEWHEEL, pygame.MOUSEBUTTONDOWN]:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                    game.handle_click(event.pos)
                else:
                    game.handle_input(event)
        
        # Update game state
        game.update()
        
        # Draw everything
        game.draw()
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()