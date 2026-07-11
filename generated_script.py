"""
Fibonacci Sequence Module

Provides highly optimized, memory-efficient generation of Fibonacci numbers.
Standardizes on generating `n` terms (1-indexed count, 0-indexed mathematical values).
"""

from typing import Iterator, List


def _validate_input(n: int) -> None:
    """
    Validates the input parameter `n` for Fibonacci generation.
    
    Args:
        n (int): The number of terms to generate.
        
    Raises:
        TypeError: If `n` is not strictly an integer (e.g., float, string, bool).
        ValueError: If `n` is negative.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"Parameter 'n' must be strictly an integer, got {type(n).__name__}.")
    if n < 0:
        raise ValueError(f"Parameter 'n' must be non-negative (n >= 0), got {n}.")


def fibonacci_generator(n: int) -> Iterator[int]:
    """
    Generates the Fibonacci sequence up to `n` terms using an iterative generator.
    
    This function standardizes on yielding exactly `n` terms. 
    - For n=0, it yields nothing (empty sequence).
    - For n=1, it yields [0].
    - For n=2, it yields [0, 1], and so on.
    
    Args:
        n (int): The number of Fibonacci terms to generate. Must be >= 0.
        
    Yields:
        int: The next Fibonacci number in the sequence.
        
    Raises:
        TypeError: If `n` is not an integer.
        ValueError: If `n` is negative.
        
    Complexity:
        Time: O(n) - Iterates exactly n times.
        Space: O(1) - Auxiliary space is constant due to the generator pattern.
    """
    _validate_input(n)
    
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


def get_fibonacci_sequence(n: int) -> List[int]:
    """
    Retrieves the Fibonacci sequence up to `n` terms as a list.
    
    This is a convenience wrapper around `fibonacci_generator` for cases 
    where the entire sequence is required in memory at once.
    
    Args:
        n (int): The number of Fibonacci terms to generate. Must be >= 0.
        
    Returns:
        List[int]: A list containing the first `n` Fibonacci numbers.
        
    Raises:
        TypeError: If `n` is not an integer.
        ValueError: If `n` is negative.
        
    Complexity:
        Time: O(n)
        Space: O(n) - Stores all n terms in a list.
    """
    return list(fibonacci_generator(n))


if __name__ == "__main__":
    DEFAULT_N = 50
    
    print(f"--- Fibonacci Sequence (First {DEFAULT_N} terms) ---")
    
    # Consuming the generator and formatting output cleanly
    sequence = get_fibonacci_sequence(DEFAULT_N)
    
    # Print as a comma-separated string to avoid overwhelming the standard output buffer
    print(", ".join(str(num) for num in sequence))
    
    print("\n--- Edge Case Demonstrations ---")
    print(f"n = 0 (Yields nothing): {get_fibonacci_sequence(0)}")
    print(f"n = 1 (Yields first term): {get_fibonacci_sequence(1)}")
    print(f"n = 2 (Yields first two terms): {get_fibonacci_sequence(2)}")
    
    print("\n--- Exception Handling Demonstrations ---")
    
    try:
        get_fibonacci_sequence(-5)
    except ValueError as e:
        print(f"ValueError caught: {e}")
        
    try:
        get_fibonacci_sequence(10.5)
    except TypeError as e:
        print(f"TypeError caught: {e}")
        
    try:
        get_fibonacci_sequence(True)
    except TypeError as e:
        print(f"TypeError caught: {e}")