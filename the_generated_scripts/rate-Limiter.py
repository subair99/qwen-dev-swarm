# Prompt
"""

Create a high-throughput multi-threaded Rate-Limiter Decorator Engine named rate_limiter.
Requirements:
1. Accept parameters: max_calls (int), window_size (float), and on_limit (str strategy: 'raise', 'block', or 'drop').
2. Algorithmic Foundation: Implement a stateful Token Bucket rate-limiting algorithm tracking float tokens and a last_refill_time timestamp using time.monotonic().
3. CRITICAL - CONCURRENCY SYNC & ANTI-THUNDERING HERD CONSTRAINTS:
   - To eliminate thread-interleaving race conditions and thundering herd performance degradation, do not use raw tracking arrays with detached time.sleep() statements.
   - Use a thread-safe synchronization condition layer (threading.Condition()) to control the execution queue.
   - For the 'block' strategy, compute the precise missing token duration mathematically: wait_duration = (1.0 - tokens) / refill_rate.
   - Leverage cv.wait(timeout) inside a deterministic while-loop to natively suspend and queue out-of-token threads at the OS kernel level, ensuring immediate state re-evaluation upon wake-up.
4. Exception Handling: Raise a custom RateLimitExceeded exception when the 'raise' strategy triggers.
5. Defensive Execution: Include comprehensive runtime type-checking (handling boolean type exclusions cleanly) and guarantee that the wrapped function executes completely outside the lock boundary to maximize thread throughput.

"""


import time
import threading
import functools

class RateLimitExceeded(Exception):
    """Custom exception raised when the rate limit is exceeded under the 'raise' strategy."""
    pass

def rate_limiter(max_calls, window_size, on_limit='raise'):
    if isinstance(max_calls, bool) or not isinstance(max_calls, int):
        raise TypeError("max_calls must be an integer.")
    if max_calls <= 0:
        raise ValueError("max_calls must be strictly positive.")
        
    if isinstance(window_size, bool) or not isinstance(window_size, (int, float)):
        raise TypeError("window_size must be a numeric type (int or float).")
    if window_size <= 0:
        raise ValueError("window_size must be strictly positive.")
        
    if not isinstance(on_limit, str) or on_limit not in ('raise', 'block', 'drop'):
        raise ValueError("on_limit must be one of: 'raise', 'block', 'drop'.")

    capacity = float(max_calls)
    refill_rate = capacity / float(window_size)
    tokens = capacity
    last_refill_time = time.monotonic()
    cv = threading.Condition()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal tokens, last_refill_time
            
            while True:
                action = None
                with cv:
                    current_time = time.monotonic()
                    elapsed = current_time - last_refill_time
                    
                    if elapsed > 0:
                        tokens = min(capacity, tokens + (elapsed * refill_rate))
                        last_refill_time = current_time
                        
                    if tokens >= 1.0:
                        tokens -= 1.0
                        action = 'execute'
                    else:
                        if on_limit == 'raise':
                            action = 'raise'
                        elif on_limit == 'drop':
                            action = 'drop'
                        elif on_limit == 'block':
                            wait_duration = (1.0 - tokens) / refill_rate
                            cv.wait(timeout=wait_duration)
                            continue
                            
                if action == 'execute':
                    return func(*args, **kwargs)
                elif action == 'raise':
                    raise RateLimitExceeded("Rate limit exceeded.")
                elif action == 'drop':
                    return None
                    
        return wrapper
    return decorator