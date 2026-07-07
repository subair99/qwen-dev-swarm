import random
import math
import statistics
from typing import List, Sequence


def generate_dataset(seed: int = 42, size: int = 1000, min_val: int = 1, max_val: int = 10000) -> List[int]:
    """
    Deterministically generates a list of random integers.

    This function resolves the paradox of a "hardcoded" random list by using a 
    fixed seed, ensuring the output is perfectly reproducible and functionally 
    immutable across runs without bloating the source code with literal integers.

    Args:
        seed (int): The random seed for reproducibility. Defaults to 42.
        size (int): The number of integers to generate. Defaults to 1000.
        min_val (int): The minimum possible integer value. Defaults to 1.
        max_val (int): The maximum possible integer value. Defaults to 10000.

    Returns:
        List[int]: A list of deterministically generated integers.
        
    Time Complexity:
        O(N) where N is the size of the dataset.
    """
    random.seed(seed)
    return [random.randint(min_val, max_val) for _ in range(size)]


def validate_non_negative(data: Sequence[int]) -> None:
    """
    Validates that all integers in the dataset are strictly non-negative.

    Args:
        data (Sequence[int]): The dataset to validate.

    Raises:
        TypeError: If an element is not an integer.
        ValueError: If a negative integer is found, detailing the index and value.
        
    Time Complexity:
        O(N) where N is the length of the dataset.
    """
    for index, value in enumerate(data):
        if not isinstance(value, int):
            raise TypeError(f"Type violation at index {index}: expected int, got {type(value).__name__}.")
        if value < 0:
            raise ValueError(
                f"Negative bound violated at index {index}: value is {value}. "
                "All values must be >= 0."
            )


def calculate_mean(data: Sequence[int]) -> float:
    """
    Calculates the arithmetic mean of the dataset.

    Uses math.fsum to ensure high precision and avoid floating-point 
    catastrophic cancellation during the summation phase.

    Args:
        data (Sequence[int]): The dataset.

    Returns:
        float: The arithmetic mean.

    Raises:
        statistics.StatisticsError: If the dataset is empty.
        
    Time Complexity:
        O(N) where N is the length of the dataset.
    """
    if not data:
        raise statistics.StatisticsError("calculate_mean requires at least one data point.")
    return math.fsum(data) / len(data)


def calculate_median(data: Sequence[int]) -> float:
    """
    Calculates the median of the dataset.

    Args:
        data (Sequence[int]): The dataset.

    Returns:
        float: The median value.

    Raises:
        statistics.StatisticsError: If the dataset is empty.
        
    Time Complexity:
        O(N log N) due to the Timsort algorithm used in Python's sorted().
    """
    if not data:
        raise statistics.StatisticsError("calculate_median requires at least one data point.")
    
    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2
    
    if n % 2 == 0:
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2.0
    return float(sorted_data[mid])


def calculate_modes(data: Sequence[int]) -> List[int]:
    """
    Identifies all modes (most frequent values) in the dataset.

    Args:
        data (Sequence[int]): The dataset.

    Returns:
        List[int]: A list of all modal values.

    Raises:
        statistics.StatisticsError: If the dataset is empty.
        
    Time Complexity:
        O(N) where N is the length of the dataset.
    """
    if not data:
        raise statistics.StatisticsError("calculate_modes requires at least one data point.")
    return statistics.multimode(data)


def calculate_sample_std_dev(data: Sequence[int]) -> float:
    """
    Calculates the sample standard deviation using Welford's online algorithm.

    This approach applies Bessel's correction (dividing by N-1) and operates 
    in O(N) time while minimizing floating-point catastrophic cancellation 
    compared to naive two-pass or sum-of-squares methods.

    Args:
        data (Sequence[int]): The dataset.

    Returns:
        float: The sample standard deviation.

    Raises:
        statistics.StatisticsError: If the dataset has fewer than two data points.
        
    Time Complexity:
        O(N) where N is the length of the dataset.
    """
    n = 0
    mean = 0.0
    m2 = 0.0
    
    for x in data:
        n += 1
        delta = x - mean
        mean += delta / n
        delta2 = x - mean
        m2 += delta * delta2
        
    if n < 2:
        raise statistics.StatisticsError("Sample standard deviation requires at least two data points.")
        
    variance = m2 / (n - 1)  # Bessel's correction
    return math.sqrt(variance)


def display_results(mean: float, median: float, modes: List[int], std_dev: float) -> None:
    """
    Formats and prints the statistical results to the console.

    Args:
        mean (float): The calculated mean.
        median (float): The calculated median.
        modes (List[int]): The calculated modes.
        std_dev (float): The calculated sample standard deviation.
    """
    print("-" * 45)
    print("         STATISTICAL ANALYSIS RESULTS        ")
    print("-" * 45)
    print(f"{'Mean:':<25} {mean:>15.4f}")
    print(f"{'Median:':<25} {median:>15.4f}")
    
    modes_str = ", ".join(str(m) for m in modes)
    # Adjust alignment dynamically if the modes string is exceptionally long
    print(f"{'Mode(s):':<25} {modes_str:>15}")
    
    print(f"{'Sample Std Dev:':<25} {std_dev:>15.4f}")
    print("-" * 45)


def main() -> None:
    """
    Main execution entry point.
    
    Orchestrates data generation, validation, statistical computation, 
    and result display. Ensures strict separation of concerns and 
    handles edge-case exceptions gracefully.
    """
    # 1. Generate Data
    dataset = generate_dataset(seed=42, size=1000, min_val=1, max_val=10000)
    
    # 2. Validate Data
    # We intentionally do not catch ValueError here. If a negative bound is 
    # violated, the script must immediately halt and raise the exception 
    # to the interpreter as per strict structural guardrails.
    validate_non_negative(dataset)

    # 3. Compute Statistics
    try:
        mean_val = calculate_mean(dataset)
        median_val = calculate_median(dataset)
        modes_val = calculate_modes(dataset)
        std_dev_val = calculate_sample_std_dev(dataset)
    except statistics.StatisticsError as e:
        print(f"Statistical Computation Error: {e}")
        return

    # 4. Display Results
    display_results(mean_val, median_val, modes_val, std_dev_val)


if __name__ == '__main__':
    main()