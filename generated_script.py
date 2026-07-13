from typing import Iterator

def _validate_n(n: int) -> None:
    """Validates the input parameter for Fibonacci calculations.

    Args:
        n: The target index for the Fibonacci sequence.

    Raises:
        TypeError: If 'n' is not strictly an integer (rejects bools, floats, etc.).
        ValueError: If 'n' is a negative integer.
    """
    if type(n) is not int:
        raise TypeError(f"Input 'n' must be strictly an integer, received {type(n).__name__}.")
    if n < 0:
        raise ValueError(f"Input 'n' must be a non-negative integer, received {n}.")


def _fibonacci_core() -> Iterator[int]:
    """Infinite generator yielding the Fibonacci sequence.

    Encapsulates the core state-transition logic to adhere to the DRY principle.
    Operates in O(1) auxiliary space.

    Yields:
        int: The next number in the Fibonacci sequence.
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def fibonacci_sequence(n: int) -> Iterator[int]:
    """Generates the Fibonacci sequence from F(0) up to F(n).

    Utilizes a generator pattern to compute values on-the-fly, preventing
    memory exhaustion (OOM) for large values of 'n'.

    Args:
        n: The maximum index of the Fibonacci sequence to generate.

    Returns:
        Iterator[int]: A generator yielding Fibonacci numbers up to F(n).

    Raises:
        TypeError: If 'n' is not strictly an integer.
        ValueError: If 'n' is negative.
    """
    _validate_n(n)
    gen = _fibonacci_core()
    for _ in range(n + 1):
        yield next(gen)


def fibonacci_nth(n: int) -> int:
    """Calculates the exact n-th Fibonacci number.

    Consumes the core generator to maintain O(n) time complexity and 
    O(1) auxiliary space complexity without storing the entire sequence.

    Args:
        n: The index of the desired Fibonacci number.

    Returns:
        int: The n-th Fibonacci number.

    Raises:
        TypeError: If 'n' is not strictly an integer.
        ValueError: If 'n' is negative.
    """
    _validate_n(n)
    gen = _fibonacci_core()
    result = 0
    for _ in range(n + 1):
        result = next(gen)
    return result


if __name__ == "__main__":
    DEFAULT_N = 50
    
    print("=" * 60)
    print("PRODUCTION FIBONACCI SEQUENCE GENERATOR")
    print("=" * 60)
    
    # 1. First 10 Numbers
    print("\n[1] First 10 Fibonacci Numbers (F0 to F9):")
    first_10 = list(fibonacci_sequence(9))
    print(", ".join(str(x) for x in first_10))
    
    # 2. Full Sequence up to DEFAULT_N
    print(f"\n[2] Full Sequence up to F({DEFAULT_N}):")
    full_seq = list(fibonacci_sequence(DEFAULT_N))
    # Format cleanly in rows of 5 for readability
    for i in range(0, len(full_seq), 5):
        chunk = full_seq[i:i+5]
        indices = [f"F({i+j})" for j in range(len(chunk))]
        print(" | ".join(f"{idx:>5}: {val}" for idx, val in zip(indices, chunk)))
        
    # 3. Exact Nth Value
    print(f"\n[3] Exact Value of F({DEFAULT_N}):")
    nth_val = fibonacci_nth(DEFAULT_N)
    print(f"F({DEFAULT_N}) = {nth_val}")
    
    print("=" * 60)