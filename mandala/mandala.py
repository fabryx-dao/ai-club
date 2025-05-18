import math

# Define the size of the grid
width, height = 80, 40
center_x, center_y = width // 2, height // 2

# Define characters for different intensity levels
chars = " .:-=+*#%@"

# Function to map a value to a character
def get_char(value):
    index = int(value * (len(chars) - 1))
    return chars[index]

# Generate the ASCII mandala
for y in range(height):
    for x in range(width):
        # Convert grid coordinates to Cartesian coordinates
        dx = x - center_x
        dy = y - center_y
        distance = math.hypot(dx, dy)

        # Calculate angle and normalize it
        angle = math.atan2(dy, dx)
        angle = (angle + math.pi) / (2 * math.pi)  # Normalize between 0 and 1

        # Create radial and circular patterns
        radial = 0.5 + 0.5 * math.sin(10 * angle + distance / 2)
        circular = 0.5 + 0.5 * math.sin(distance / 2)

        # Combine patterns
        value = (radial + circular) / 2

        # Print the corresponding character
        print(get_char(value), end='')
    print()
