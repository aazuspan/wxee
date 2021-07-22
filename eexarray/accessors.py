from typing import Any, Callable, Type


class Accessor:
    """Object for implementing class accessors."""

    def __init__(self, name: str, accessor: Any):
        self.name = name
        self.accessor = accessor

    def __get__(self, obj: Any, cls: Type) -> Any:
        return self.accessor(obj)


def eex_accessor(cls: Type) -> Callable:
    """Create an accessor through the eex namespace to a given class.

    Parameters
    ----------
    cls : class
        The class to set the accessor to.

    Returns
    -------
    function
        The accessor function to to the class.
    """

    def decorator(accessor: Any) -> Any:
        setattr(cls, "eex", Accessor("eex", accessor))
        return accessor

    return decorator
