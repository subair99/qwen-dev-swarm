from typing import List

def fibonacci_up_to_value(n: int) -> List[int]:
    """
    Calculates Fibonacci numbers where the value is less than or equal to n.
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        return []
    
    sequence = []
    a, b = 0, 1
    while a <= n:
        sequence.append(a)
        a, b = b, a + b
    return sequence

def fibonacci_n_terms(n: int) -> List[int]:
    """
    Calculates the first n Fibonacci numbers.
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n <= 0:
        return []
    
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

if __name__ == "__main__":
    target_value = 100
    print(f"Fibonacci numbers up to the value {target_value}:")
    print(fibonacci_up_to_value(target_value))
    
    target_terms = 15
    print(f"\nFirst {target_terms} Fibonacci numbers:")
    print(fibonacci_n_terms(target_terms))