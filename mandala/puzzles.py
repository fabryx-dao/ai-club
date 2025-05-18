import random

class IfThenElsePattern:
    """Generate and verify if/then/else pattern puzzles"""
    
    def __init__(self, level=0):
        self.level = level
        self.pattern_type = self.generate_pattern_type()
        self.input_values = []
        self.output_values = []
        self.test_input = None
        self.correct_output = None
        self.generate_puzzle()
    
    def generate_pattern_type(self):
        """Determine the type of pattern based on level"""
        patterns = [
            # Level 0 patterns (simple)
            [
                {"op": "add", "value": lambda: random.randint(1, 10)},
                {"op": "subtract", "value": lambda: random.randint(1, 10)},
                {"op": "multiply", "value": lambda: random.randint(2, 5)},
            ],
            # Level 1 patterns (medium)
            [
                {"op": "conditional", "threshold": lambda: random.randint(5, 15), 
                 "if_true": lambda: random.randint(1, 10), 
                 "if_false": lambda: random.randint(-10, -1)},
                {"op": "modulo", "value": lambda: random.randint(2, 5)},
                {"op": "power", "value": lambda: random.randint(2, 3)},
            ],
            # Level 2 patterns (complex)
            [
                {"op": "multi_condition", 
                 "conditions": [
                     {"threshold": lambda: random.randint(10, 20), "result": lambda: random.randint(1, 10)},
                     {"threshold": lambda: random.randint(0, 9), "result": lambda: random.randint(11, 20)},
                     {"default": lambda: random.randint(21, 30)}
                 ]},
                {"op": "digit_sum"},
                {"op": "complex_function"},
            ]
        ]
        
        # Select a random pattern from the appropriate level
        level_patterns = patterns[min(self.level, len(patterns)-1)]
        return random.choice(level_patterns)
    
    def generate_puzzle(self):
        """Generate input/output pairs based on the selected pattern"""
        # Generate 5 input values (with the last one being the test)
        if self.pattern_type["op"] == "add":
            value = self.pattern_type["value"]()
            self.input_values = [random.randint(1, 30) for _ in range(5)]
            self.output_values = [x + value for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = self.test_input + value
        
        elif self.pattern_type["op"] == "subtract":
            value = self.pattern_type["value"]()
            self.input_values = [random.randint(value+1, 30) for _ in range(5)]
            self.output_values = [x - value for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = self.test_input - value
            
        elif self.pattern_type["op"] == "multiply":
            value = self.pattern_type["value"]()
            self.input_values = [random.randint(1, 20) for _ in range(5)]
            self.output_values = [x * value for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = self.test_input * value
            
        elif self.pattern_type["op"] == "conditional":
            threshold = self.pattern_type["threshold"]()
            if_true = self.pattern_type["if_true"]()
            if_false = self.pattern_type["if_false"]()
            
            self.input_values = [random.randint(1, 30) for _ in range(5)]
            self.output_values = [if_true if x >= threshold else if_false for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = if_true if self.test_input >= threshold else if_false
            
        elif self.pattern_type["op"] == "modulo":
            value = self.pattern_type["value"]()
            self.input_values = [random.randint(1, 30) for _ in range(5)]
            self.output_values = [x % value for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = self.test_input % value
            
        elif self.pattern_type["op"] == "power":
            value = self.pattern_type["value"]()
            self.input_values = [random.randint(1, 10) for _ in range(5)]
            self.output_values = [x ** value for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = self.test_input ** value
            
        elif self.pattern_type["op"] == "multi_condition":
            conditions = self.pattern_type["conditions"]
            thresholds = [cond["threshold"]() if "threshold" in cond else None for cond in conditions[:-1]]
            results = [cond["result"]() if "result" in cond else cond["default"]() for cond in conditions]
            
            self.input_values = [random.randint(1, 30) for _ in range(5)]
            
            # Apply the conditions to generate outputs
            self.output_values = []
            for x in self.input_values[:-1]:
                result_idx = len(thresholds)  # Default to last condition
                for i, threshold in enumerate(thresholds):
                    if x <= threshold:
                        result_idx = i
                        break
                self.output_values.append(results[result_idx])
            
            # Calculate the correct output for the test input
            self.test_input = self.input_values[-1]
            result_idx = len(thresholds)  # Default to last condition
            for i, threshold in enumerate(thresholds):
                if self.test_input <= threshold:
                    result_idx = i
                    break
            self.correct_output = results[result_idx]
            
        elif self.pattern_type["op"] == "digit_sum":
            self.input_values = [random.randint(10, 999) for _ in range(5)]
            self.output_values = [sum(int(digit) for digit in str(x)) for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = sum(int(digit) for digit in str(self.test_input))
            
        elif self.pattern_type["op"] == "complex_function":
            # Example: output = (input % 3) * 2 + (1 if input > 15 else -1)
            self.input_values = [random.randint(1, 30) for _ in range(5)]
            self.output_values = [(x % 3) * 2 + (1 if x > 15 else -1) for x in self.input_values[:-1]]
            self.test_input = self.input_values[-1]
            self.correct_output = (self.test_input % 3) * 2 + (1 if self.test_input > 15 else -1)
    
    def get_puzzle_description(self):
        """Get a description of the pattern for display"""
        if self.pattern_type["op"] == "add":
            return f"The pattern adds a constant value to each input."
        elif self.pattern_type["op"] == "subtract":
            return f"The pattern subtracts a constant value from each input."
        elif self.pattern_type["op"] == "multiply":
            return f"The pattern multiplies each input by a constant value."
        elif self.pattern_type["op"] == "conditional":
            return f"The pattern uses an if/then/else logic based on a threshold."
        elif self.pattern_type["op"] == "modulo":
            return f"The pattern uses the remainder after division (modulo)."
        elif self.pattern_type["op"] == "power":
            return f"The pattern raises each input to a power."
        elif self.pattern_type["op"] == "multi_condition":
            return f"The pattern uses multiple conditions with different thresholds."
        elif self.pattern_type["op"] == "digit_sum":
            return f"The pattern sums the individual digits of each input."
        elif self.pattern_type["op"] == "complex_function":
            return f"The pattern applies a complex formula to each input."
        return "Decode the pattern hidden in the input/output pairs."
    
    def verify_answer(self, answer):
        """Check if the provided answer matches the correct output"""
        try:
            return int(answer) == self.correct_output
        except ValueError:
            return False