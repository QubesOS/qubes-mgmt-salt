
"""
Helper functions for function-like objects.
"""

function_type = type(lambda: True)   # define our own because not def'd in py26


def is_function(obj):
    """ 
    Determines: Is obj a function?
    """
    return isinstance(obj, function_type)


def real_func(flike):
    """
    Given a function-like object (function or staticmethod), return the real function.
    """
    if is_function(flike):
        return flike
    # Not clear this still useful; was for methods < py26
    elif hasattr(flike, 'im_func'):
        return flike.im_func
    elif hasattr(flike, '__func__'):    # method (static or otherwise) >= p26
        return flike.__func__
    elif hasattr(flike, '__get__'):     # static method in py26
        return flike.__get__(True)
    else:
        raise ValueError("doesn't seem to be a function-like object")

    # Introspection: Isn't it fun?! It's valuable...but changing in the underlying
    # data model or implementation => oy vey!


def func_code(flike):
    """
    Given a function like object (function, static method, etc.), return its
    functional code object. Attempts to bridge the gap between different versions'
    introspective namings.
    """

    if hasattr(flike, 'func_code'):    # Python 2.6 or 2.7, most functions
        return flike.func_code
    elif hasattr(flike, '__code__'):   # Python 3
        return flike.__code__
    else:
        raise ValueError("don't know where to find function's code")
