"""
High-Performance Sieve of Eratosthenes Implementation

This module provides a production-grade, memory-optimized implementation of the 
Sieve of Eratosthenes algorithm to compute prime numbers up to a given integer `n`.
It utilizes a half-sieve (skipping even numbers) backed by a C-contiguous `bytearray` 
and slice assignments for maximum computational efficiency.
"""

import math
import sys
import time
from typing import Any, Generator, List, Union, Iterator
import pytest

# Maximum safe memory threshold for the sieve array (2 GB or half of sys.maxsize)
_MAX_SIEVE_BYTES = min(2 * 1024 * 1024 * 1024, sys.maxsize // 2)


def _validate_and_cast(n: Any) -> int:
    """
    Validates and casts the input to a strict integer.
    
    Args:
        n: The input value to validate.
        
    Returns:
        The validated integer value.
        
    Raises:
        TypeError: If the input is a boolean, float, string, None, or an object 
                   lacking the __index__ protocol.
    """
    if isinstance(n, bool):
        raise TypeError("Boolean values are not valid integers for this operation.")
    if isinstance(n, int):
        return n
    if hasattr(n, '__index__'):
        return n.__index__()
    raise TypeError(f"Expected an integer or an object implementing __index__, got {type(n).__name__}.")


def _check_memory_limit(half_n: int) -> None:
    """
    Checks if the requested sieve size exceeds the safe memory threshold.
    
    Args:
        half_n: The size of the half-sieve array (representing odd numbers).
        
    Raises:
        MemoryError: If the required memory exceeds the predefined safe limit.
    """
    if half_n > _MAX_SIEVE_BYTES:
        raise MemoryError(
            f"Requested sieve size ({half_n} bytes) exceeds the safe memory "
            f"threshold of {_MAX_SIEVE_BYTES} bytes. Reduce 'n' to prevent OOM."
        )


def _prime_generator(n: int) -> Generator[int, None, None]:
    """
    Core sieving algorithm that lazily yields prime numbers up to `n`.
    
    Implements the "skip evens" optimization, handling 2 as a special case 
    and sieving only odd numbers. Uses `bytearray` with slice assignment 
    for O(n log log n) time complexity and minimal memory overhead.
    
    Args:
        n: The upper bound (inclusive) for finding primes. Must be a validated integer.
        
    Yields:
        Prime numbers in the range [2, n].
    """
    if n < 2:
        return
        
    yield 2
    
    if n == 2:
        return

    # Calculate the number of odd integers >= 3 up to n.
    # Mapping: index i represents the number 2*i + 3.
    half_n = (n - 1) // 2
    if half_n <= 0:
        return
        
    _check_memory_limit(half_n)
    
    # 1 indicates prime, 0 indicates composite.
    sieve = bytearray(b'\x01') * half_n
    
    limit = math.isqrt(n)
    
    # Outer loop only needs to check primes up to sqrt(n).
    # p = 2*i + 3 <= limit  =>  i <= (limit - 3) // 2
    max_i = (limit - 3) // 2
    
    for i in range(max_i + 1):
        if sieve[i]:
            p = 2 * i + 3
            # Start marking at p^2. 
            # Index for p^2 is (p^2 - 3) // 2 = 2*i^2 + 6*i + 3
            start = 2 * i * i + 6 * i + 3
            step = p  # Step by p in index space (equivalent to 2p in number space)
            
            if start < half_n:
                length = len(range(start, half_n, step))
                # Slice assignment with bytes is the fastest way to zero out memory in Python
                sieve[start::step] = bytes(length)
                
    # Yield the remaining primes lazily
    for i in range(half_n):
        if sieve[i]:
            yield 2 * i + 3


def sieve_of_eratosthenes(n: Any, materialize: bool = False) -> Union[Generator[int, None, None], List[int]]:
    """
    Public API to compute all prime numbers up to `n` using the Sieve of Eratosthenes.
    
    Args:
        n: The upper bound (inclusive) for the prime search. Must be an integer 
           (or an object implementing `__index__`). Booleans, floats, and strings 
           are strictly rejected.
        materialize: If True, returns a fully materialized list of primes. If False 
                     (default), returns a memory-efficient generator.
                     
    Returns:
        A generator yielding primes, or a list of primes if `materialize=True`.
        
    Raises:
        TypeError: If `n` is not a valid integer type.
        MemoryError: If `n` is large enough that the sieve array would exceed 2GB.
    """
    validated_n = _validate_and_cast(n)
    gen = _prime_generator(validated_n)
    
    if materialize:
        return list(gen)
    return gen


# ==============================================================================
# UNIT TESTS (pytest)
# ==============================================================================

class TestSieveValidation:
    """Tests for strict input validation and type checking."""

    def test_valid_integers(self):
        assert sieve_of_eratosthenes(10, materialize=True) == [2, 3, 5, 7]
        assert sieve_of_eratosthenes(2, materialize=True) == [2]
        assert sieve_of_eratosthenes(0, materialize=True) == []
        assert sieve_of_eratosthenes(-100, materialize=True) == []

    def test_reject_booleans(self):
        with pytest.raises(TypeError, match="Boolean values"):
            sieve_of_eratosthenes(True)
        with pytest.raises(TypeError, match="Boolean values"):
            sieve_of_eratosthenes(False)

    def test_reject_invalid_types(self):
        with pytest.raises(TypeError):
            sieve_of_eratosthenes(3.14)
        with pytest.raises(TypeError):
            sieve_of_eratosthenes("10")
        with pytest.raises(TypeError):
            sieve_of_eratosthenes(None)
        with pytest.raises(TypeError):
            sieve_of_eratosthenes([10])

    def test_accept_indexable_custom_types(self):
        class CustomInt:
            def __init__(self, val):
                self.val = val
            def __index__(self):
                return self.val
                
        assert sieve_of_eratosthenes(CustomInt(10), materialize=True) == [2, 3, 5, 7]

    def test_reject_non_indexable_custom_types(self):
        class BadCustomType:
            def __int__(self):
                return 10  # __int__ is not __index__
                
        with pytest.raises(TypeError):
            sieve_of_eratosthenes(BadCustomType())


class TestSieveAlgorithm:
    """Tests for mathematical correctness and boundary conditions."""

    def test_standard_cases(self):
        assert sieve_of_eratosthenes(100, materialize=True) == [
            2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 
            53, 59, 61, 67, 71, 73, 79, 83, 89, 97
        ]

    def test_boundary_n_equals_2(self):
        assert sieve_of_eratosthenes(2, materialize=True) == [2]

    def test_boundary_n_equals_3(self):
        assert sieve_of_eratosthenes(3, materialize=True) == [2, 3]

    def test_boundary_n_equals_1(self):
        assert sieve_of_eratosthenes(1, materialize=True) == []

    def test_generator_consumption(self):
        gen = sieve_of_eratosthenes(10)
        assert next(gen) == 2
        assert next(gen) == 3
        assert next(gen) == 5
        assert next(gen) == 7
        with pytest.raises(StopIteration):
            next(gen)


class TestSievePerformanceAndMemory:
    """Tests for performance constraints and memory safety."""

    def test_performance_10_million(self):
        """Ensures n=10^7 executes well under standard time limits."""
        start_time = time.perf_counter()
        # We materialize to force full evaluation of the generator
        primes = sieve_of_eratosthenes(10_000_000, materialize=True)
        elapsed = time.perf_counter() - start_time
        
        # 10^7 should take < 1.5 seconds on any modern CPU with this optimized sieve
        assert elapsed < 2.0, f"Performance regression: took {elapsed:.2f}s"
        assert len(primes) == 664579  # Known prime counting function value for 10^7

    def test_memory_limit_enforcement(self):
        """Ensures a MemoryError is raised for astronomically large n."""
        # n = 10^11 would require ~50GB of RAM for the half-sieve
        with pytest.raises(MemoryError, match="exceeds the safe memory threshold"):
            # We don't materialize, but the generator initialization checks memory
            gen = sieve_of_eratosthenes(100_000_000_000)
            next(gen)  # Force generator execution


if __name__ == "__main__":
    # Execute pytest when the script is run directly
    pytest.main([__file__, "-v", "--tb=short"])