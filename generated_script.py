"""
Production-hardened Fibonacci sequence module.

This module provides highly optimized, memory-efficient functions to calculate
Fibonacci numbers up to a given index `n`. It strictly enforces type safety,
bounds checking, and utilizes an O(1) auxiliary space generator for lazy evaluation.
"""

from typing import Iterator


def _validate_n(n: int) -> None:
    """Validates the input parameter `n` for Fibonacci calculations.

    Args:
        n: The target index/term count for the Fibonacci sequence.

    Raises:
        TypeError: If `n` is not strictly an integer (e.g., float, bool, string).
        ValueError: If `n` is a negative integer.
    """
    # Strict type checking: `type(n) is not int` correctly rejects booleans 
    # (which are a subclass of int) as well as floats and strings.
    if type(n) is not int:
        raise TypeError(
            f"Input 'n' must be strictly an integer, got {type(n).__name__}."
        )
    
    # Mathematical bounds checking: Fibonacci indices cannot be negative 
    # in this standard sequence implementation.
    if n < 0:
        raise ValueError(
            f"Input 'n' must be non-negative, got {n}. Negative indices are "
            "mathematically invalid for this implementation."
        )


def fibonacci_generator(n: int) -> Iterator[int]:
    """Generates Fibonacci numbers up to the n-th index lazily.

    This function utilizes an iterative approach to yield Fibonacci numbers
    one at a time. It operates in O(n) time complexity and strictly O(1) 
    auxiliary space complexity, making it safe for extremely large values of `n` 
    without risking memory exhaustion.

    Args:
        n: The maximum index of the Fibonacci sequence to generate (inclusive).
           For example, n=5 yields F_0 through F_5.

    Yields:
        int: The next Fibonacci number in the sequence, starting from F_0 = 0.

    Raises:
        TypeError: If `n` is not strictly an integer.
        ValueError: If `n` is negative.
    """
    _validate_n(n)
    
    # F_0 = 0, F_1 = 1
    a, b = 0, 1
    
    # Iterate n + 1 times to include both the 0th and n-th indices.
    for _ in range(n + 1):
        yield a
        
        # O(1) auxiliary space rationale: We only maintain the two most recent 
        # state variables (a and b) in memory. We do not store the historical 
        # sequence, preventing O(n) memory scaling.
        a, b = b, a + b


def fibonacci_list(n: int) -> list[int]:
    """Calculates and returns the Fibonacci sequence up to the n-th index eagerly.

    This function consumes the lazy `fibonacci_generator` to build and return 
    a complete list in memory. Adheres to DRY principles by delegating the 
    core mathematical logic to the generator.

    Args:
        n: The maximum index of the Fibonacci sequence to generate (inclusive).

    Returns:
        list[int]: A list containing the Fibonacci numbers from F_0 to F_n.

    Raises:
        TypeError: If `n` is not strictly an integer.
        ValueError: If `n` is negative.
    """
    # Consume the generator to construct the eager list.
    return list(fibonacci_generator(n))


if __name__ == "__main__":
    # Hardcoded default for sandbox execution demonstration
    DEFAULT_N = 50

    print("=" * 60)
    print("FIBONACCI MODULE DEMONSTRATION")
    print("=" * 60)

    # 1. Demonstrate Eager Evaluation (List)
    print(f"\n[1] Eager Evaluation (List) for n={DEFAULT_N}")
    print("-" * 40)
    fib_list = fibonacci_list(DEFAULT_N)
    print(f"Total terms generated: {len(fib_list)}")
    print(f"First 5 terms: {fib_list[:5]}")
    print(f"Last term (F_{DEFAULT_N}): {fib_list[-1]}")

    # 2. Demonstrate Lazy Evaluation (Generator)
    print(f"\n[2] Lazy Evaluation (Generator) for n=10")
    print("-" * 40)
    fib_gen = fibonacci_generator(10)
    print(f"Generator object created: {fib_gen}")
    print("Yielding terms manually via next():")
    for i in range(5):
        print(f"  F_{i} = {next(fib_gen)}")
    print("Consuming the rest of the generator into a list:")
    print(f"  Remaining terms: {list(fib_gen)}")

    # 3. Demonstrate Edge Cases
    print("\n[3] Edge Cases (n=0 and n=1)")
    print("-" * 40)
    print(f"Fibonacci list for n=0: {fibonacci_list(0)}")
    print(f"Fibonacci list for n=1: {fibonacci_list(1)}")

    # 4. Demonstrate Error Handling
    print("\n[4] Error Handling Demonstrations")
    print("-" * 40)
    
    # Test TypeError with a float
    try:
        fibonacci_generator(10.5)
    except TypeError as e:
        print(f"Caught TypeError (float): {e}")

    # Test TypeError with a boolean
    try:
        fibonacci_list(True)
    except TypeError as e:
        print(f"Caught TypeError (bool): {e}")

    # Test ValueError with a negative integer
    try:
        fibonacci_generator(-5)
    except ValueError as e:
        print(f"Caught ValueError (negative): {e}")
        
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)