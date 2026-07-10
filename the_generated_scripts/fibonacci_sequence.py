"""
Production-hardened Fibonacci sequence generator and utilities.

This module provides highly optimized, iterative generators for Fibonacci sequences,
alongside an O(log n) Fast Doubling utility for retrieving specific terms.
"""

import time
import tracemalloc
from typing import Any, Generator

import pytest


def _validate_non_negative_int(value: Any, param_name: str) -> None:
    """
    Centralized validation helper for Fibonacci input parameters.
    
    Enforces strict type checking (explicitly rejecting booleans) and 
    non-negative bounds to prevent type-coercion vulnerabilities and 
    mathematically undefined behavior in standard sequences.
    
    Args:
        value: The input value to validate.
        param_name: The name of the parameter (for precise error messaging).
        
    Raises:
        TypeError: If the value is a boolean, float, string, or complex number.
        ValueError: If the value is a negative integer.
    """
    # CRITICAL TRAP: In Python, bool is a subclass of int. 
    # We must explicitly reject booleans before checking for int.
    if type(value) is bool:
        raise TypeError(f"'{param_name}' must be an integer, got bool.")
    if not isinstance(value, int):
        raise TypeError(f"'{param_name}' must be an integer, got {type(value).__name__}.")
    if value < 0:
        raise ValueError(f"'{param_name}' must be a non-negative integer, got {value}.")


def fibonacci_terms(num_terms: int) -> Generator[int, None, None]:
    """
    Generates the first `num_terms` of the Fibonacci sequence.
    
    Uses an iterative generator pattern to ensure O(1) auxiliary space complexity,
    preventing Out-Of-Memory (OOM) crashes for exceptionally large `num_terms`.
    
    Args:
        num_terms: The exact number of Fibonacci terms to generate.
        
    Yields:
        int: The next Fibonacci number in the sequence.
        
    Raises:
        TypeError: If `num_terms` is not an integer (including booleans).
        ValueError: If `num_terms` is negative.
        
    Complexity:
        Time: O(n) where n is `num_terms`.
        Space: O(1) auxiliary space.
    """
    _validate_non_negative_int(num_terms, "num_terms")
    a, b = 0, 1
    for _ in range(num_terms):
        yield a
        a, b = b, a + b


def fibonacci_up_to_value(max_value: int) -> Generator[int, None, None]:
    """
    Generates Fibonacci numbers up to a maximum value (inclusive).
    
    Resolves the ambiguity of "up to n" by explicitly bounding the sequence
    by the maximum numerical value rather than the number of terms.
    
    Args:
        max_value: The maximum inclusive value for the generated Fibonacci numbers.
        
    Yields:
        int: The next Fibonacci number less than or equal to `max_value`.
        
    Raises:
        TypeError: If `max_value` is not an integer (including booleans).
        ValueError: If `max_value` is negative.
        
    Complexity:
        Time: O(log(max_value)) since Fibonacci numbers grow exponentially.
        Space: O(1) auxiliary space.
    """
    _validate_non_negative_int(max_value, "max_value")
    a, b = 0, 1
    while a <= max_value:
        yield a
        a, b = b, a + b


def fibonacci_nth(n: int) -> int:
    """
    Calculates the n-th Fibonacci number using the iterative Fast Doubling method.
    
    Avoids recursion entirely while achieving O(log n) time complexity by 
    processing the binary representation of `n` from most to least significant bit.
    
    Args:
        n: The 0-based index of the Fibonacci number to retrieve.
        
    Returns:
        int: The n-th Fibonacci number.
        
    Raises:
        TypeError: If `n` is not an integer (including booleans).
        ValueError: If `n` is negative.
        
    Complexity:
        Time: O(log n) arithmetic operations (though arbitrary-precision 
              multiplication makes actual bit-complexity slightly higher).
        Space: O(1) auxiliary space (excluding the memory footprint of the 
               resulting massive integer).
    """
    _validate_non_negative_int(n, "n")
    if n == 0:
        return 0
        
    a, b = 0, 1
    # Iterate through the binary representation of n, skipping the '0b' prefix
    for bit in bin(n)[2:]:
        # Fast doubling formulas:
        # F(2k) = F(k) * [2*F(k+1) - F(k)]
        # F(2k+1) = F(k)^2 + F(k+1)^2
        c = a * ((b << 1) - a)
        d = a * a + b * b
        
        if bit == '1':
            a, b = d, c + d
        else:
            a, b = c, d
            
    return a


# ==========================================
# Pytest Test Suite
# ==========================================

def test_fibonacci_terms_first_20():
    """Verifies the correctness of the first 20 Fibonacci terms."""
    expected = [
        0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 
        55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181
    ]
    assert list(fibonacci_terms(20)) == expected

def test_fibonacci_terms_edge_cases():
    """Verifies edge cases for n=0, n=1, and n=2."""
    assert list(fibonacci_terms(0)) == []
    assert list(fibonacci_terms(1)) == [0]
    assert list(fibonacci_terms(2)) == [0, 1]

def test_fibonacci_up_to_value_correctness():
    """Verifies sequence generation bounded by max_value."""
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    assert list(fibonacci_up_to_value(100)) == expected
    assert list(fibonacci_up_to_value(0)) == [0]
    assert list(fibonacci_up_to_value(1)) == [0, 1, 1]

def test_fibonacci_nth_correctness():
    """Verifies the Fast Doubling implementation against known values."""
    assert fibonacci_nth(0) == 0
    assert fibonacci_nth(1) == 1
    assert fibonacci_nth(2) == 1
    assert fibonacci_nth(10) == 55
    assert fibonacci_nth(20) == 6765
    assert fibonacci_nth(100) == 354224848179261915075

@pytest.mark.parametrize("func, param_name", [
    (fibonacci_terms, "num_terms"),
    (fibonacci_up_to_value, "max_value"),
    (fibonacci_nth, "n"),
])
class TestInputValidation:
    """Centralized validation tests for all public functions."""

    def test_rejects_booleans(self, func, param_name):
        with pytest.raises(TypeError, match=f"'{param_name}' must be an integer, got bool."):
            func(True)
        with pytest.raises(TypeError, match=f"'{param_name}' must be an integer, got bool."):
            func(False)

    def test_rejects_floats(self, func, param_name):
        with pytest.raises(TypeError, match=f"'{param_name}' must be an integer, got float."):
            func(10.5)

    def test_rejects_strings(self, func, param_name):
        with pytest.raises(TypeError, match=f"'{param_name}' must be an integer, got str."):
            func("10")

    def test_rejects_complex(self, func, param_name):
        with pytest.raises(TypeError, match=f"'{param_name}' must be an integer, got complex."):
            func(1 + 2j)

    def test_rejects_negatives(self, func, param_name):
        with pytest.raises(ValueError, match=f"'{param_name}' must be a non-negative integer, got -5."):
            func(-5)

def test_memory_profiling_1_million_terms():
    """
    Proves that generating 1,000,000 terms does not consume proportional RAM.
    Iterates through the generator without storing it in a list.
    """
    tracemalloc.start()
    
    gen = fibonacci_terms(1_000_000)
    # Consume the generator entirely
    for _ in gen:
        pass
        
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # The 1,000,000th Fibonacci number has ~208,987 digits, taking roughly ~100KB in memory.
    # The generator overhead and loop variables should keep peak memory well under 10MB.
    # A naive list implementation would consume hundreds of megabytes or trigger an OOM crash.
    assert peak < 10 * 1024 * 1024, f"Peak memory {peak / (1024*1024):.2f} MB exceeded 10 MB limit."

def test_execution_time_benchmark_fast_doubling():
    """
    Benchmarks the O(log n) Fast Doubling method for n = 100,000.
    Ensures the iterative loop is not bottlenecked by hidden overhead.
    """
    n = 100_000
    start = time.perf_counter()
    result = fibonacci_nth(n)
    end = time.perf_counter()
    
    elapsed = end - start
    # 100,000th Fibonacci number has ~20,898 digits. 
    # Fast doubling should compute this in a fraction of a second in pure Python.
    assert elapsed < 1.0, f"Execution took {elapsed:.4f}s, expected < 1.0s."
    assert result > 0


if __name__ == "__main__":
    # Run pytest programmatically when the script is executed directly
    pytest.main(["-v", "--tb=short", __file__])