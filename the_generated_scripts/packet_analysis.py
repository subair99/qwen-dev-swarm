# Prompt
# Create a network Packet Analysis Script: A utility utilizing standard socket or telemetry libraries to monitor local host connection states, filter payload strings, and format a readable system metric log.


import sys
from typing import List

def fibonacci_sequence(n: int, by_value: bool = False) -> List[int]:
    """
    Calculates Fibonacci numbers based on the specified limit.
    
    Args:
        n (int): The limit for the Fibonacci sequence.
                 If by_value is False, n represents the number of terms to generate.
                 If by_value is True, n represents the maximum value (inclusive) of the terms.
        by_value (bool): Flag to determine if 'n' is the term count or max value.
        
    Returns:
        List[int]: A list of Fibonacci numbers.
        
    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is negative.
    """
    if not isinstance(n, int):
        raise TypeError(f"Expected integer for 'n', got {type(n).__name__}")
    if n < 0:
        raise ValueError("'n' must be a non-negative integer")
        
    if by_value:
        sequence = []
        a, b = 0, 1
        while a <= n:
            sequence.append(a)
            a, b = b, a + b
        return sequence
    else:
        if n == 0:
            return []
        sequence = [0]
        if n == 1:
            return sequence
        sequence.append(1)
        a, b = 0, 1
        for _ in range(2, n):
            a, b = b, a + b
            sequence.append(b)
        return sequence

if __name__ == "__main__":
    try:
        terms_count = 15
        max_value = 1000
        
        print(f"First {terms_count} Fibonacci numbers:")
        print(fibonacci_sequence(terms_count))
        
        print(f"\nFibonacci numbers up to the value {max_value}:")
        print(fibonacci_sequence(max_value, by_value=True))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)





import sys
from typing import List

def generate_fibonacci_sequence(term_count: int) -> List[int]:
    """
    Calculates the Fibonacci sequence up to the specified number of terms.
    
    Args:
        term_count (int): The exact number of Fibonacci terms to generate.
        
    Returns:
        List[int]: A list containing the generated Fibonacci sequence.
    """
    if type(term_count) is not int:
        raise TypeError(f"Expected an integer for term_count, got {type(term_count).__name__}.")
        
    if term_count < 0:
        raise ValueError(f"term_count must be a non-negative integer, got {term_count}.")
        
    if term_count == 0:
        return []
        
    sequence = [0]
    if term_count == 1:
        return sequence
        
    sequence.append(1)
    for current_index in range(2, term_count):
        next_fibonacci_value = sequence[current_index - 1] + sequence[current_index - 2]
        sequence.append(next_fibonacci_value)
        
    return sequence

if __name__ == "__main__":
    try:
        target_terms = 15
        fibonacci_result = generate_fibonacci_sequence(target_terms)
        print(f"Fibonacci sequence for {target_terms} terms: {fibonacci_result}")
    except (TypeError, ValueError) as error:
        print(f"Error generating Fibonacci sequence: {error}", file=sys.stderr)
        sys.exit(1)