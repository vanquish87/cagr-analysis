import time


# Define your decorator function
def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        finish_time = time.perf_counter()
        print(f"Finished in {int(finish_time - start_time)} seconds.")
        return result

    return wrapper
