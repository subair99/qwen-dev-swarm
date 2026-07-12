from typing import Generator


def _fibonacci_generator() -> Generator[int, None, None]:
    """Generates an infinite sequence of Fibonacci numbers.

    Utilizes an iterative state-transition approach to ensure O(1) auxiliary
    space and avoid Python's recursion depth limits.

    Yields:
        int: The next Fibonacci number in the sequence, starting from F(0).
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def _validate_n(n: int) -> None:
    """Validates the input parameter `n` for Fibonacci calculations.

    Ensures `n` is strictly an integer (explicitly rejecting booleans, floats,
    strings, and None) and is non-negative.

    Args:
        n: The target index or count for the Fibonacci sequence.

    Raises:
        TypeError: If `n` is not strictly an integer.
        ValueError: If `n` is less than zero.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"Expected 'n' to be an integer, got {type(n).__name__}.")
    if n < 0:
        raise ValueError(f"Expected 'n' to be non-negative, got {n}.")


def get_fibonacci(n: int) -> int:
    """Returns the n-th Fibonacci number (0-indexed).

    Calculates the Fibonacci number at index `n` using an O(n) iterative
    approach with O(1) auxiliary space. Leverages the core generator to
    maintain DRY principles.

    Args:
        n: The 0-based index of the desired Fibonacci number.

    Returns:
        int: The n-th Fibonacci number.

    Raises:
        TypeError: If `n` is not strictly an integer.
        ValueError: If `n` is less than zero.
    """
    _validate_n(n)
    gen = _fibonacci_generator()
    for _ in range(n):
        next(gen)
    return next(gen)


def generate_fibonacci_sequence(n: int) -> Generator[int, None, None]:
    """Yields the first n Fibonacci numbers.

    Generates a lazy sequence of `n` Fibonacci numbers starting from F(0).
    Maintains an O(1) memory footprint regardless of the size of `n`,
    preventing memory exhaustion for large values.

    Args:
        n: The total count of Fibonacci numbers to yield.

    Yields:
        int: The next Fibonacci number in the sequence, up to `n` items.

    Raises:
        TypeError: If `n` is not strictly an integer.
        ValueError: If `n` is less than zero.
    """
    _validate_n(n)
    gen = _fibonacci_generator()
    for _ in range(n):
        yield next(gen)


def main() -> None:
    """Hardcoded execution block for sandbox demonstration."""
    n = 50
    
    print(f"--- Fibonacci Demonstration (n={n}) ---")
    
    nth_fib = get_fibonacci(n)
    print(f"F({n}) = {nth_fib}")
    
    print(f"\nFirst {n} Fibonacci numbers:")
    seq = list(generate_fibonacci_sequence(n))
    print(seq)
    
    print("\n--- Edge Cases ---")
    print(f"F(0) = {get_fibonacci(0)}")
    print(f"F(1) = {get_fibonacci(1)}")
    print(f"Sequence(0) = {list(generate_fibonacci_sequence(0))}")
    print(f"Sequence(1) = {list(generate_fibonacci_sequence(1))}")
    print(f"Sequence(2) = {list(generate_fibonacci_sequence(2))}")
    
    print("\n--- Error Handling ---")
    test_cases = [-1, 5.5, "10", True, None]
    for invalid_n in test_cases:
        try:
            get_fibonacci(invalid_n)
        except (TypeError, ValueError) as e:
            print(f"Input {repr(invalid_n):<6} raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()