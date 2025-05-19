def caesar_encode(text, offset=6):
    result = ''
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shifted = (ord(char) - base + offset) % 26
            result += chr(base + shifted)
        else:
            result += char  # keep spaces and punctuation
    return result

# Example usage
input_text = "J’ai une grande tige verte et un visage doré. Je me tourne pour suivre le soleil dans le ciel."
encoded = caesar_encode(input_text, offset=6)
print(encoded)

