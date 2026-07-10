from __future__ import annotations

import random
import statistics


def generate_dataset(size: int = 1000, seed: int = 42, min_val: int = 1, max_val: int = 100) -> tuple[int, ...]:
    """
    Factory function to generate a reproducible dataset of random integers.
    Returns an immutable tuple to prevent accidental mutation.
    """
    random.seed(seed)
    return tuple(random.randint(min_val, max_val) for _ in range(size))


# The generated dataset immediately cast to an immutable tuple at the module level
DATASET: tuple[int, ...] = generate_dataset()


def validate_dataset(data: tuple[int, ...]) -> None:
    """
    Performs strict runtime type validation and negative bounds checking.
    Fails fast with TypeError or ValueError if constraints are violated.
    """
    for item in data:
        # Strict type check: must be exactly int, not a subclass like bool
        if type(item) is not int:
            raise TypeError(
                f"Type validation failed: encountered {type(item).__name__}, expected strictly 'int'."
            )
        # Negative bounds check
        if item < 0:
            raise ValueError(
                f"Negative bounds check failed: encountered {item}, expected non-negative integer (>= 0)."
            )


def analyze_dataset(data: tuple[int, ...]) -> dict[str, float | list[int]]:
    """
    Encapsulates statistical calculations. Accepts an immutable dataset 
    and returns a structured dictionary of results.
    """
    # Validate before performing any calculations
    validate_dataset(data)
    
    # Mean: O(N) time complexity
    mean_val: float = sum(data) / len(data)
    
    # Median: O(N log N) via standard library sorting overhead
    median_val: float = statistics.median(data)
    
    # Mode: multimode used to correctly identify all modes and avoid traps
    mode_val: list[int] = statistics.multimode(data)
    
    # Standard Deviation: Sample standard deviation (Bessel's correction applied)
    stdev_val: float = statistics.stdev(data)
    
    return {
        "mean": mean_val,
        "median": median_val,
        "mode": mode_val,
        "standard_deviation": stdev_val
    }


def present_results(results: dict[str, float | list[int]]) -> None:
    """
    Encapsulates output formatting. Prints results in a clean, aligned, 
    human-readable format.
    """
    print("=" * 45)
    print("       STATISTICAL ANALYSIS RESULTS")
    print("=" * 45)
    
    print(f"Mean:               {results['mean']:.4f}")
    print(f"Median:             {results['median']:.4f}")
    
    # Format mode as a comma-separated list
    modes = results['mode']
    mode_str = ", ".join(str(m) for m in modes)
    print(f"Mode(s):            {mode_str}")
    
    print(f"Standard Deviation: {results['standard_deviation']:.4f}")
    print("=" * 45)


if __name__ == "__main__":
    # Execute analysis on the module-level immutable dataset
    analysis_results = analyze_dataset(DATASET)
    present_results(analysis_results)