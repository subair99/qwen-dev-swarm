"""
Fibonacci Module

A production-hardened, highly optimized Python module for calculating 
Fibonacci numbers, adhering to enterprise-grade software engineering standards.
"""

import argparse
import functools
import sys
from typing import Any, Callable, Iterator, Tuple


def _validate_fibonacci_input(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to enforce strict type and bounds checking for Fibonacci inputs.
    
    Validates that the input 'n' is strictly an integer (rejecting booleans, 
    floats, strings, and None) and is non-negative.
    """
    @functools.wraps(func)
    def wrapper(n: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(
                f"Input 'n' must be an integer, got {type(n).__name__}."
            )
        if n < 0:
            raise ValueError(
                f"Input 'n' must be non-negative, got {n}."
            )
        return func(n, *args, **kwargs)
    return wrapper


@_validate_fibonacci_input
def fibonacci_sequence(n: int) -> Iterator[int]:
    """
    Generates the Fibonacci sequence up to the n-th index.
    
    Uses a generator pattern to ensure O(1) auxiliary space complexity.
    
    Args:
        n: The number of Fibonacci numbers to generate (from F(0) to F(n)).
        
    Returns:
        An iterator yielding the Fibonacci sequence.
        
    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is negative.
        
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    a, b = 0, 1
    for _ in range(n + 1):
        yield a
        a, b = b, a + b


@_validate_fibonacci_input
def fibonacci_nth(n: int) -> int:
    """
    Calculates the n-th Fibonacci number using the Fast Doubling algorithm.
    
    Args:
        n: The index of the Fibonacci number to calculate.
        
    Returns:
        The n-th Fibonacci number.
        
    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is negative.
        
    Time Complexity: O(log n)
    Space Complexity: O(log n) due to recursion stack
    """
    def _fast_doubling(k: int) -> Tuple[int, int]:
        if k == 0:
            return (0, 1)
        
        a, b = _fast_doubling(k >> 1)
        
        # c = F(2k), d = F(2k+1)
        c = a * (b * 2 - a)
        d = a * a + b * b
        
        if k & 1:
            return (d, c + d)
        return (c, d)

    if n == 0:
        return 0
        
    return _fast_doubling(n)[0]


def main() -> None:
    """
    CLI entry point for the Fibonacci module.
    """
    parser = argparse.ArgumentParser(
        description="Calculate Fibonacci numbers or stream the sequence."
    )
    parser.add_argument(
        "n",
        type=int,
        nargs="?",
        default=10,
        help="The index n for Fibonacci calculation (default: 10).",
    )
    parser.add_argument(
        "-s",
        "--sequence",
        action="store_true",
        help="Print the sequence up to n instead of the n-th number.",
    )
    
    args = parser.parse_args()
    
    try:
        if args.sequence:
            for num in fibonacci_sequence(args.n):
                print(num)
        else:
            print(fibonacci_nth(args.n))
    except KeyboardInterrupt:
        print("\nStreaming interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except (TypeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()