# Prompt
# Create a robust python script that calculates Fibonacci numbers up to n.


"""
Fibonacci Module
High-performance, production-hardened mathematical algorithms for Fibonacci sequences.
"""

import functools
from typing import Iterator


class ComputationLimitExceededError(ValueError):
    """Raised when a computation exceeds defined safety limits to prevent CPU/Memory exhaustion."""
    pass


def _validate_fib_input(n: int, max_limit: int | None = None, override_limit: bool = False) -> None:
    """
    Validates input parameters for Fibonacci functions.
    
    Enforces strict type checking (rejecting booleans and other types),
    non-negative bounds, and computational safety limits.
    
    Args:
        n: The Fibonacci index to validate.
        max_limit: The maximum allowed value for n. If None, no limit is enforced.
        override_limit: If True, bypasses the max_limit check.
        
    Raises:
        TypeError: If n is not strictly an integer (e.g., bool, float, str).
        ValueError: If n is negative.
        ComputationLimitExceededError: If n exceeds max_limit and override_limit is False.
    """
    if type(n) is not int:
        raise TypeError(f"Input 'n' must be strictly an integer, got {type(n).__name__}.")
    if n < 0:
        raise ValueError(f"Input 'n' must be non-negative, got {n}.")
    if max_limit is not None and not override_limit and n > max_limit:
        raise ComputationLimitExceededError(
            f"n={n} exceeds max_limit={max_limit}. "
            "Set override_limit=True to bypass this safeguard."
        )


def fib_sequence_generator(n: int, max_limit: int = 1000000) -> Iterator[int]:
    """
    Yields Fibonacci numbers from F(0) to F(n) using an iterative generator.
    
    This ensures O(1) auxiliary space complexity, preventing Out-Of-Memory (OOM) 
    crashes when n is large.
    
    Args:
        n: The upper bound index for the Fibonacci sequence.
        max_limit: Safety limit to prevent excessive CPU usage. Defaults to 1,000,000.
        
    Yields:
        The next Fibonacci number in the sequence.
        
    Raises:
        TypeError: If n is not strictly an integer.
        ValueError: If n is negative.
        ComputationLimitExceededError: If n exceeds max_limit.
    """
    _validate_fib_input(n, max_limit=max_limit)
    a, b = 0, 1
    for _ in range(n + 1):
        yield a
        a, b = b, a + b


def fib_sequence_list(n: int, max_limit: int = 100000, override_limit: bool = False) -> list[int]:
    """
    Returns the Fibonacci sequence from F(0) to F(n) as a list.
    
    Enforces a strict upper bound to protect heap memory from exhaustion.
    
    Args:
        n: The upper bound index for the Fibonacci sequence.
        max_limit: Safety limit to prevent memory exhaustion. Defaults to 100,000.
        override_limit: If True, allows n to exceed max_limit.
        
    Returns:
        A list of Fibonacci numbers from F(0) to F(n).
        
    Raises:
        TypeError: If n is not strictly an integer.
        ValueError: If n is negative.
        ComputationLimitExceededError: If n exceeds max_limit and override_limit is False.
    """
    _validate_fib_input(n, max_limit=max_limit, override_limit=override_limit)
    res = []
    a, b = 0, 1
    for _ in range(n + 1):
        res.append(a)
        a, b = b, a + b
    return res


def fib_nth(n: int) -> int:
    """
    Returns exactly the n-th Fibonacci number using the iterative Fast Doubling algorithm.
    
    Achieves O(log n) time complexity and O(1) space complexity, avoiding the 
    recursion depth limits and stack memory constraints of naive recursive approaches.
    
    Args:
        n: The index of the Fibonacci number to calculate.
        
    Returns:
        The n-th Fibonacci number.
        
    Raises:
        TypeError: If n is not strictly an integer.
        ValueError: If n is negative.
    """
    _validate_fib_input(n)
    if n == 0:
        return 0
    
    # Iterative Fast Doubling
    bits = bin(n)[2:]
    a, b = 0, 1  # F(0), F(1)
    
    for bit in bits:
        # c = F(2k), d = F(2k+1)
        c = a * (2 * b - a)
        d = a * a + b * b
        if bit == '1':
            a, b = d, c + d
        else:
            a, b = c, d
            
    return a


# ==============================================================================
# TEST SUITE
# Guarded with try...except ImportError to prevent ModuleNotFoundError in 
# production environments lacking the pytest dependency.
# ==============================================================================
try:
    import pytest
    from collections.abc import Iterator as AbcIterator

    class TestFibonacciHappyPaths:
        def test_fib_nth(self):
            assert fib_nth(0) == 0
            assert fib_nth(1) == 1
            assert fib_nth(2) == 1
            assert fib_nth(10) == 55
            assert fib_nth(50) == 12586269025

        def test_fib_sequence_list(self):
            assert fib_sequence_list(0) == [0]
            assert fib_sequence_list(1) == [0, 1]
            assert fib_sequence_list(2) == [0, 1, 1]
            assert fib_sequence_list(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

        def test_fib_sequence_generator(self):
            assert list(fib_sequence_generator(10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    class TestFibonacciEdgeCases:
        def test_zero_yield(self):
            assert list(fib_sequence_generator(0)) == [0]
            
        def test_exact_boundary_limit(self):
            # Should not raise
            fib_sequence_list(10, max_limit=10)
            # Should raise
            with pytest.raises(ComputationLimitExceededError):
                fib_sequence_list(11, max_limit=10)

    class TestFibonacciTypeRejection:
        @pytest.mark.parametrize("invalid_input", [True, False, 3.14, "10", None, []])
        def test_type_rejection(self, invalid_input):
            with pytest.raises(TypeError):
                fib_nth(invalid_input)
            with pytest.raises(TypeError):
                fib_sequence_list(invalid_input)
            with pytest.raises(TypeError):
                list(fib_sequence_generator(invalid_input))

    class TestFibonacciBoundsRejection:
        @pytest.mark.parametrize("negative_input", [-1, -100])
        def test_bounds_rejection(self, negative_input):
            with pytest.raises(ValueError):
                fib_nth(negative_input)
            with pytest.raises(ValueError):
                fib_sequence_list(negative_input)
            with pytest.raises(ValueError):
                list(fib_sequence_generator(negative_input))

    class TestFibonacciLimitGuards:
        def test_limit_exceeded(self):
            with pytest.raises(ComputationLimitExceededError):
                fib_sequence_list(100001)  # Default limit is 100000
                
        def test_limit_override(self):
            # Should not raise
            res = fib_sequence_list(100001, override_limit=True)
            assert len(res) == 100002
            
        def test_generator_limit(self):
            with pytest.raises(ComputationLimitExceededError):
                list(fib_sequence_generator(1000001))  # Default limit 1000000

    class TestFibonacciGeneratorVerification:
        def test_is_iterator(self):
            gen = fib_sequence_generator(10)
            assert isinstance(gen, AbcIterator)
            
        def test_memory_lazy_evaluation(self):
            # Verifies it doesn't crash or OOM on a large limit override
            gen = fib_sequence_generator(1000000)
            assert next(gen) == 0
            assert next(gen) == 1

    if __name__ == "__main__":
        pytest.main([__file__, "-v"])

except ImportError:
    if __name__ == "__main__":
        print("pytest is not installed. Skipping test execution.")