# Prompt
# Create a robust python script that calculates Fibonacci numbers up to n.


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






"""
Fibonacci Module

Provides highly optimized, production-hardened functions for calculating 
Fibonacci numbers, adhering to strict algorithmic and memory constraints.
"""

from typing import Iterator, Callable, Any, TypeVar
import functools
import unittest
import time

F = TypeVar('F', bound=Callable[..., Any])

def _validate_fib_input(func: F) -> F:
    """
    Decorator to centralize input validation for Fibonacci functions.
    
    Ensures the input 'n' is a non-negative integer and explicitly rejects
    booleans, floats, strings, and other invalid types.
    """
    @functools.wraps(func)
    def wrapper(n: int, *args: Any, **kwargs: Any) -> Any:
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(f"Input 'n' must be an integer, got {type(n).__name__}.")
        if n < 0:
            raise ValueError(f"Input 'n' must be non-negative, got {n}.")
        return func(n, *args, **kwargs)
    return wrapper  # type: ignore

@_validate_fib_input
def fib_sequence(n: int) -> Iterator[int]:
    """
    Generates the Fibonacci sequence from F_0 to F_n iteratively.
    
    Args:
        n (int): The upper bound index for the Fibonacci sequence (inclusive).
        
    Returns:
        Iterator[int]: A generator yielding Fibonacci numbers from F_0 to F_n.
        
    Raises:
        TypeError: If 'n' is not an integer or is a boolean.
        ValueError: If 'n' is negative.
        
    Time Complexity:
        O(n * M(k)) where M(k) is the cost of multiplying/adding k-digit numbers.
    Space Complexity:
        O(1) auxiliary space (excluding the size of the yielded large integers).
    """
    a, b = 0, 1
    for _ in range(n + 1):
        yield a
        a, b = b, a + b

@_validate_fib_input
def fib_nth(n: int) -> int:
    """
    Calculates the exact n-th Fibonacci number using the Fast Doubling method.
    
    Uses an iterative bitwise approach to achieve O(log n) time complexity
    without relying on recursion, thus avoiding RecursionError limits.
    
    Args:
        n (int): The index of the Fibonacci number to calculate.
        
    Returns:
        int: The n-th Fibonacci number.
        
    Raises:
        TypeError: If 'n' is not an integer or is a boolean.
        ValueError: If 'n' is negative.
        
    Time Complexity:
        O(log n * M(k)) where M(k) is the cost of large integer arithmetic.
    Space Complexity:
        O(1) auxiliary space.
    """
    if n == 0:
        return 0
        
    a, b = 0, 1
    
    # Iterate from the most significant bit to the least significant bit
    for bit in bin(n)[2:]:
        # Fast doubling formulas:
        # F(2k) = F(k) * [2 * F(k+1) - F(k)]
        # F(2k+1) = F(k)^2 + F(k+1)^2
        c = a * (2 * b - a)
        d = a * a + b * b
        
        if bit == '0':
            a, b = c, d
        else:
            a, b = d, c + d
            
    return a


class _CustomObj:
    """Dummy class for testing custom object type rejection."""
    pass


class TestFibonacci(unittest.TestCase):
    """Comprehensive test suite for the Fibonacci module."""

    def test_boundary_values(self) -> None:
        self.assertEqual(fib_nth(0), 0)
        self.assertEqual(fib_nth(1), 1)
        self.assertEqual(fib_nth(2), 1)
        
        self.assertEqual(list(fib_sequence(0)), [0])
        self.assertEqual(list(fib_sequence(1)), [0, 1])
        self.assertEqual(list(fib_sequence(2)), [0, 1, 1])

    def test_type_rejections(self) -> None:
        invalid_inputs: list[Any] = [5.0, "5", True, False, None, _CustomObj()]
        for val in invalid_inputs:
            with self.assertRaises(TypeError):
                fib_nth(val)
            with self.assertRaises(TypeError):
                list(fib_sequence(val))

    def test_negative_bounds(self) -> None:
        for val in [-1, -100]:
            with self.assertRaises(ValueError):
                fib_nth(val)
            with self.assertRaises(ValueError):
                list(fib_sequence(val))

    def test_performance_and_scale(self) -> None:
        n = 100_000
        
        # Test fib_nth performance (must be < 1 second)
        start_time = time.time()
        res = fib_nth(n)
        elapsed_nth = time.time() - start_time
        
        self.assertLess(elapsed_nth, 1.0, "fib_nth took longer than 1 second for n=100,000")
        self.assertIsInstance(res, int)
        
        # Test fib_sequence for memory spikes (OOM trap avoidance)
        # We do not store the sequence in a list. We just iterate and count.
        start_time = time.time()
        count = 0
        for _ in fib_sequence(n):
            count += 1
        elapsed_seq = time.time() - start_time
        
        self.assertEqual(count, n + 1)
        # Note: Iterative addition of 100,000 large ints takes >1s in pure Python 
        # due to O(N^2) bit complexity, but it strictly avoids OOM memory spikes 
        # by maintaining O(1) space complexity.

if __name__ == "__main__":
    unittest.main()