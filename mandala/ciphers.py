import random

class CipherEncoder:
    """Encode and decode messages for the cipher puzzles"""
    
    def __init__(self, level=0):
        self.level = level
        self.cipher_type = self.select_cipher_type()
        
    def select_cipher_type(self):
        """Select a cipher type based on level"""
        ciphers = [
            # Level 0 ciphers (simple)
            ["caesar", "reverse", "atbash"],
            # Level 1 ciphers (medium)
            ["vigenere", "railfence", "columnar"],
            # Level 2 ciphers (complex)
            ["playfair", "adfgvx", "bifid"]
        ]
        
        level_ciphers = ciphers[min(self.level, len(ciphers)-1)]
        return random.choice(level_ciphers)
    
    def encode(self, message, key):
        """Encode a message using the selected cipher"""
        message = message.upper()
        
        if self.cipher_type == "caesar":
            # Simple shift cipher
            try:
                shift = int(key) % 26
            except ValueError:
                shift = sum(ord(c) for c in key) % 26
                
            result = ""
            for char in message:
                if char.isalpha():
                    ascii_offset = ord('A')
                    shifted = (ord(char) - ascii_offset + shift) % 26 + ascii_offset
                    result += chr(shifted)
                else:
                    result += char
            return result
            
        elif self.cipher_type == "reverse":
            # Simply reverse the message
            return message[::-1]
            
        elif self.cipher_type == "atbash":
            # Substitute each letter with its opposite
            result = ""
            for char in message:
                if char.isalpha():
                    ascii_offset = ord('A')
                    reversed_char = 25 - (ord(char) - ascii_offset) + ascii_offset
                    result += chr(reversed_char)
                else:
                    result += char
            return result
            
        # For levels beyond 0, use more complex ciphers    
        elif self.cipher_type == "vigenere":
            # Implement a simple vigenere cipher
            key_repeated = key * (len(message) // len(key) + 1)
            key_repeated = key_repeated[:len(message)]
            
            result = ""
            for i, char in enumerate(message):
                if char.isalpha():
                    # Convert key character to shift value
                    try:
                        shift = int(key_repeated[i]) % 26
                    except ValueError:
                        shift = (ord(key_repeated[i].upper()) - ord('A')) % 26
                        
                    ascii_offset = ord('A')
                    shifted = (ord(char) - ascii_offset + shift) % 26 + ascii_offset
                    result += chr(shifted)
                else:
                    result += char
            return result
        
        # Default fallback for unimplemented ciphers
        return message
    
    def decode(self, encoded_message, key):
        """Decode a message using the selected cipher"""
        encoded_message = encoded_message.upper()
        
        if self.cipher_type == "caesar":
            try:
                shift = int(key) % 26
            except ValueError:
                shift = sum(ord(c) for c in key) % 26
                
            result = ""
            for char in encoded_message:
                if char.isalpha():
                    ascii_offset = ord('A')
                    shifted = (ord(char) - ascii_offset - shift) % 26 + ascii_offset
                    result += chr(shifted)
                else:
                    result += char
            return result
            
        elif self.cipher_type == "reverse":
            return encoded_message[::-1]
            
        elif self.cipher_type == "atbash":
            # Same algorithm for encode and decode
            return self.encode(encoded_message, key)
            
        elif self.cipher_type == "vigenere":
            key_repeated = key * (len(encoded_message) // len(key) + 1)
            key_repeated = key_repeated[:len(encoded_message)]
            
            result = ""
            for i, char in enumerate(encoded_message):
                if char.isalpha():
                    # Convert key character to shift value
                    try:
                        shift = int(key_repeated[i]) % 26
                    except ValueError:
                        shift = (ord(key_repeated[i].upper()) - ord('A')) % 26
                        
                    ascii_offset = ord('A')
                    shifted = (ord(char) - ascii_offset - shift) % 26 + ascii_offset
                    result += chr(shifted)
                else:
                    result += char
            return result
            
        # Default fallback
        return encoded_message
    
    def get_challenge_instructions(self, challenge_type):
        """Get poetic instructions for each challenge type"""
        if challenge_type == "fire":
            instructions = [
                "IGNITE THE FIRE WITHIN YOUR CHEST",
                "BREATHE RAPIDLY LIKE BELLOWS TO A FLAME",
                "FEEL THE HEAT RISE WITH EACH BREATH",
                "THIRTY BREATHS OF FIRE TO AWAKEN",
                "THEN RETURN TO CALM LIKE EMBERS"
            ]
        elif challenge_type == "wave":
            instructions = [
                "RIDE THE WAVE OF YOUR BREATH",
                "FIRST STOKE THE FIRE WITH TWENTY BREATHS",
                "THEN EXHALE COMPLETELY AND HOLD",
                "SURRENDER TO THE CALM OF THE OCEAN DEPTHS",
                "FINALLY RETURN WITH ONE DEEP BREATH"
            ]
        elif challenge_type == "lightning":
            instructions = [
                "BECOME THE ALCHEMIST OF BREATH",
                "THIRTY BREATHS TO CHARGE THE STORM",
                "RELEASE AND HOLD IN PERFECT STILLNESS",
                "INHALE DEEPLY AND SQUEEZE YOUR BODY",
                "MASTER BOTH CHAOS AND CALM"
            ]
        else:  # tree pose
            instructions = [
                "STAND TALL LIKE THE MIGHTY OAK",
                "ONE FOOT PLANTED FIRMLY ON EARTH",
                "THE OTHER RESTING AGAINST YOUR THIGH",
                "ARMS STRETCHED SKYWARD LIKE BRANCHES",
                "FIND STILLNESS AND BALANCE FOR SIXTY BEATS"
            ]
        
        return random.choice(instructions)