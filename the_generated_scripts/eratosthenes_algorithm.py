import math
import time
from typing import List

def generate_primes(n: int) -> List[int]:
    """
    Generates all prime numbers up to a given integer `n` using a highly 
    optimized Sieve of Eratosthenes algorithm.

    This implementation utilizes Base-2 wheel factorization to halve memory 
    and execution time, CPython slice assignments to push iteration to C-level, 
    and a bytearray for memory-efficient storage.

    Args:
        n (int): The upper bound (inclusive) for finding prime numbers.

    Returns:
        List[int]: A list of all prime numbers less than or equal to `n`.

    Raises:
        TypeError: If `n` is not strictly an integer (e.g., bool, float, str).
        ValueError: If `n` is negative.

    Complexity:
        Time: O(n log log n)
        Space: O(n) - Specifically, ~0.5 bytes per integer up to n due to 
                Base-2 wheel factorization and bytearray, drastically reducing 
                memory compared to naive list[bool] implementations.
    """
    # Strict type validation: reject bool (subclass of int), float, str, etc.
    if type(n) is not int:
        raise TypeError(f"Expected 'int' for parameter 'n', got '{type(n).__name__}'.")
    
    # Negative bounds checking
    if n < 0:
        raise ValueError(f"Parameter 'n' must be non-negative, got {n}.")
        
    # Handle edge cases where n < 2 gracefully
    if n < 2:
        return []
        
    # Base-2 wheel factorization: only store odd numbers >= 3.
    # Index `i` represents the number `2*i + 3`.
    # The maximum index required is calculated to cover up to `n`.
    size = (n - 1) // 2
    
    # Memory-efficient data structure: bytearray initialized to 1 (True/Prime)
    sieve = bytearray(b'\x01' * size)
    
    # Square root boundary for the outer loop
    limit = math.isqrt(n)
    
    # Iterate over indices `i` such that the represented prime `p = 2*i + 3 <= limit`
    for i in range((limit - 1) // 2):
        if sieve[i]:
            p = 2 * i + 3
            
            # Start marking composites from p^2
            # The index for p^2 is (p^2 - 3) // 2
            start = (p * p - 3) // 2
            step = p
            
            # Guard against index out of bounds on p^2
            if start < size:
                # Mathematical slice length calculation to avoid len() overhead
                length = (size - start + step - 1) // step
                
                # CPython slice assignment to push iteration to C-level
                # bytearray(length) creates a zero-filled sequence (0 = Composite)
                sieve[start::step] = bytearray(length)
                
    # Collect primes: 2 is the only even prime
    primes = [2]
    
    # Extract remaining primes from the sieve using list comprehension for speed
    primes.extend([2 * i + 3 for i, is_prime in enumerate(sieve) if is_prime])
    
    return primes


if __name__ == "__main__":
    print("=" * 60)
    print(" SIEVE OF ERATOSTHENES - OPTIMIZED IMPLEMENTATION TESTS")
    print("=" * 60)
    
    # 1. Standard & Edge Cases
    print("\n--- Standard & Edge Cases ---")
    test_cases = [0, 1, 2, 3, 10, 100]
    for tc in test_cases:
        result = generate_primes(tc)
        print(f"n = {tc:3d} -> {result}")
        
    # 2. Exception Cases
    print("\n--- Exception Cases ---")
    exception_cases = [
        (True, TypeError),
        (10.5, TypeError),
        ("100", TypeError),
        (-5, ValueError)
    ]
    
    for val, expected_exc in exception_cases:
        try:
            generate_primes(val)
            print(f"FAIL: n = {val!r} did not raise {expected_exc.__name__}")
        except expected_exc as e:
            print(f"PASS: n = {val!r} correctly raised {expected_exc.__name__}: {e}")
        except Exception as e:
            print(f"FAIL: n = {val!r} raised {type(e).__name__} instead of {expected_exc.__name__}: {e}")

    # 3. Performance Benchmark
    print("\n--- Performance Benchmark ---")
    N_BENCH = 10_000_000
    print(f"Benchmarking generate_primes(n={N_BENCH:,})...")
    print("*(This utilizes CPython slice assignments and Base-2 wheel factorization)*")
    
    start_time = time.perf_counter()
    primes = generate_primes(N_BENCH)
    end_time = time.perf_counter()
    
    elapsed = end_time - start_time
    print(f"\nResults:")
    print(f" - Found {len(primes):,} primes in {elapsed:.4f} seconds.")
    print(f" - First 10 primes: {primes[:10]}")
    print(f" - Last 10 primes:  {primes[-10:]}")
    print("=" * 60)