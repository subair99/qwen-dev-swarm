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