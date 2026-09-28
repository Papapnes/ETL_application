class DatabaseError(RuntimeError):
    """Safe operational error: never include a driver exception or connection URI."""
