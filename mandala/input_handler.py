import pygame

class InputHandler:
    """Handles text input and processing"""
    
    def __init__(self):
        self.input_text = ""
    
    def handle_input(self, event, is_active, current_text=None):
        """Handle text input events"""
        if not is_active:
            return
        
        if current_text is not None:
            self.input_text = current_text
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Return key event will be processed elsewhere
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                # Add the character if it's printable
                if event.unicode.isprintable():
                    self.input_text += event.unicode
    
    def get_input_text(self):
        """Get the current input text"""
        return self.input_text
    
    def clear_input(self):
        """Clear the input text"""
        self.input_text = ""