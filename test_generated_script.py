import pytest
from unittest.mock import patch

# Note: Adjust the import module name if your implementation file is named differently (e.g., fib.py)
from fibonacci import (
    _validate_n,
    _infinite_fibonacci,
    fibonacci_up_to_index,
    fibonacci_up_to_value,
    get_fibonacci_list
)

# ==========================================
# Tests for _validate_n
# ==========================================

@pytest.mark.parametrize("invalid_input", [
    True, False,       # bools are subclass of int, but strictly rejected
    5.0, 0.0,          # floats
    "10", "0",         # strings
    None,              # NoneType
    [5], (5,), {5}     # collections
])
def test_validate_n_type_error(invalid_input):
    """Verifies that non-strict integer types raise TypeError."""
    with pytest.raises(TypeError, match="Input must be strictly of type 'int'"):
        _validate_n(invalid_input)

@pytest.mark.parametrize("negative_input", [-1, -100, -9999])
def test_validate_n_value_error(negative_input):
    """Verifies that negative integers raise ValueError."""
    with pytest.raises(ValueError, match="Input must be a non-negative integer"):
        _validate_n(negative_input)

@pytest.mark.parametrize("valid_input", [0, 1, 10, 1000, 999999])
def test_validate_n_valid(valid_input):
    """Verifies that valid non-negative integers pass validation without exceptions."""
    _validate_n(valid_input)


# ==========================================
# Tests for _infinite_fibonacci
# ==========================================

def test_infinite_fibonacci_sequence():
    """Verifies the core generator yields the correct mathematical sequence."""
    gen = _infinite_fibonacci()
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    result = [next(gen) for _ in range(10)]
    assert result == expected


# ==========================================
# Tests for fibonacci_up_to_index
# ==========================================

@pytest.mark.parametrize("n, expected", [
    (0, [0]),
    (1, [0, 1]),
    (2, [0, 1, 1]),
    (5, [0, 1, 1, 2, 3, 5]),
    (7, [0, 1, 1, 2, 3, 5, 8, 13]),
    (14, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377])
])
def test_fibonacci_up_to_index_valid(n, expected):
    """Verifies correct sequence generation up to the n-th zero-based index."""
    assert list(fibonacci_up_to_index(n)) == expected

def test_fibonacci_up_to_index_type_error():
    """Verifies TypeError propagation for invalid types."""
    with pytest.raises(TypeError):
        list(fibonacci_up_to_index(5.0))

def test_fibonacci_up_to_index_value_error():
    """Verifies ValueError propagation for negative bounds."""
    with pytest.raises(ValueError):
        list(fibonacci_up_to_index(-1))


# ==========================================
# Tests for fibonacci_up_to_value
# ==========================================

@pytest.mark.parametrize("n, expected", [
    (0, [0]),
    (1, [0, 1]),             # Skips the duplicate '1'
    (2, [0, 1, 2]),
    (5, [0, 1, 2, 3, 5]),
    (7, [0, 1, 2, 3, 5]),    # Stops at 5 since 8 > 7
    (8, [0, 1, 2, 3, 5, 8]),
    (10, [0, 1, 2, 3, 5, 8]),
    (13, [0, 1, 2, 3, 5, 8, 13]),
    (20, [0, 1, 2, 3, 5, 8, 13]) # Stops at 13 since 21 > 20
])
def test_fibonacci_up_to_value_valid(n, expected):
    """Verifies correct unique sequence generation up to a maximum value boundary."""
    assert list(fibonacci_up_to_value(n)) == expected

def test_fibonacci_up_to_value_type_error():
    """Verifies TypeError propagation for invalid types."""
    with pytest.raises(TypeError):
        list(fibonacci_up_to_value("10"))

def test_fibonacci_up_to_value_value_error():
    """Verifies ValueError propagation for negative bounds."""
    with pytest.raises(ValueError):
        list(fibonacci_up_to_value(-5))


# ==========================================
# Tests for get_fibonacci_list
# ==========================================

@pytest.mark.parametrize("n, expected", [
    (0, [0]),
    (7, [0, 1, 1, 2, 3, 5, 8, 13]),
    (14, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377])
])
def test_get_fibonacci_list_valid(n, expected):
    """Verifies the utility wrapper correctly consumes the generator into a list."""
    assert get_fibonacci_list(n) == expected

@pytest.mark.parametrize("n", [100_001, 1_000_000, 999_999_999])
def test_get_fibonacci_list_memory_guardrail_exceeded(n):
    """Verifies that values exceeding the safe memory threshold raise ValueError."""
    with pytest.raises(ValueError, match="n > 100,000 is restricted"):
        get_fibonacci_list(n)

def test_get_fibonacci_list_boundary_allowed():
    """
    Verifies that n=100,000 bypasses the memory guardrail.
    We mock the underlying generator to prevent actual computation of 100,000 large integers 
    which would unnecessarily consume CPU/time during test execution.
    """
    module_name = get_fibonacci_list.__module__
    with patch(f'{module_name}.fibonacci_up_to_index', return_value=iter([0, 1])):
        result = get_fibonacci_list(100_000)
        assert result == [0, 1]

def test_get_fibonacci_list_type_error():
    """Verifies TypeError propagation for invalid types."""
    with pytest.raises(TypeError):
        get_fibonacci_list(True)

def test_get_fibonacci_list_value_error():
    """Verifies ValueError propagation for negative bounds."""
    with pytest.raises(ValueError):
        get_fibonacci_list(-10)