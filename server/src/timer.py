import time
from functools import partial, wraps


def timeit(fn=None, *, print_fn=print, name=None):
    if fn is None:
        return partial(timeit, name=name)
    name = fn.__name__

    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        res = fn(*args, **kwargs)
        duration = time.time() - start
        print_fn(f"Running {name} took {duration:.3f} (s)")
        return res

    return wrapper
