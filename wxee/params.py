import difflib
from enum import Enum
from typing import Any, Dict, Union


class ParamEnum(Enum):
    """An abstract class for automatically handling function parameters"""

    @classmethod
    def _options(cls) -> Dict[str, Any]:
        return {option.name: option.value for option in cls}

    @classmethod
    def _get_closest_option(cls, name: str) -> Union[str, None]:
        match = difflib.get_close_matches(
            word=name, possibilities=cls._options().keys(), n=1
        )
        return match[0] if match else None

    @classmethod
    def get_option(cls, name: str) -> Any:
        try:
            return cls._options()[name]
        except KeyError:
            error_msg = (
                f"Option must be in {sorted(cls._options().keys())}, not '{name}'."
            )

            closest = cls._get_closest_option(name)
            hint = f" Did you mean '{closest}'?" if closest else ""

            raise ValueError(error_msg + hint)
