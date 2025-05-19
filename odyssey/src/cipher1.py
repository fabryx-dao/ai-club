def encode_with_offset(text, offset):
    text = text.lower()
    output = []
    for char in text:
        if char.isalpha():
            value = ord(char) - ord('a') + 1
            output.append(str(value + offset))
            output.append(' ')
        elif char == ' ':
            output.append('    ')  # four spaces
        elif char == '.':
            output.append('\n')  # newline
        # ignore other characters
    return ' '.join(output)

# Example usage
input_text = "J’ai de grandes oreilles et une longue trompe. J’adore les cacahuètes et je suis le plus grand animal sur terre. Qui suis-je ?"
offset = 0
result = encode_with_offset(input_text, offset)
print(result)

