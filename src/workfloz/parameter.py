from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import get_type_hints
from typing import TypeVar

# TODO: change validators to be compatible with pydatic, Flask or Django


class Undefined:
    def __str__(self) -> str:
        return "<UNDEFINED>"


UND = Undefined()  # A sentinel object representing an undefined value.

UND_TYPE = type("UND_TYPE", (), {})  # A sentinel object representing an undefined type.

T = TypeVar("T")
Validator = Callable[["Parameter", Any], None]


class Parameter:
    """Validated and documented attributes.

    Args:
        default: The default value for this Parameter. It will be
            returned on a call to `__get__` if no other value has been
            set. The default value will NOT be validated.
        doc: The description for this parameter.
        validators: A list of validators to be run when the value is
            set. The `dtype_validator` will be added automatically,
            other validators can be added through this argument.
            Custom validators are very easy to implement. See below
            for examples.

    Attributes:
        _default_: The default value for this Parameter. It will be
            returned on a call to `__get__` if no other value has been
            set.
        _doc_: The description for this parameter.
        _validators_: A list of validators to be run when the value is
            set.
        _owner_: The class that owns this descriptor through one of its
            attributes.
        _name_: The name of the attribute on the owner class.
    """

    def __init__(
        self,
        default: Any = UND,
        doc: str = "",
        validators: list[Validator] | None = None,
    ) -> None:
        self._default_ = default
        self._doc_ = doc
        self._validators_: list[Validator] = [dtype_validator]
        if validators is None:
            validators = []
        if not isinstance(validators, list):
            validators = [validators]
        self._validators_.extend(validators)

    def __set_name__(self, owner: type[T], name: str) -> None:
        self._name_ = name
        self._owner_ = owner
        self._dtype_ = get_type_hints(owner).get(name, UND_TYPE)

    def __get__(self, instance: T, owner: type[T]) -> Parameter | Any:
        """
        Returns:
            The descriptor object itself when called on the class.
            The `_default_` value if no other value has been set.
            The value that was set otherwise.
        """
        if not instance:
            return self
        ret = vars(instance).get(self._name_, self._default_)
        return ret

    def __set__(self, instance: T, value: Any) -> None:
        for validator in self._validators_:
            validator(self, value)
        vars(instance)[self._name_] = value


def dtype_validator(parameter: Parameter, value: Any) -> None:
    """Check if the value corresponds to the given annotation.

    Raises:
        TypeError: If the value does not correspond to the type
            annotation. If no type hint was defined for the Parameter,
            any value will pass validation.
    """
    if parameter._dtype_ is not UND_TYPE and not isinstance(value, parameter._dtype_):
        raise TypeError(
            f"Parameter '{parameter._name_}' on class '{parameter._owner_.__name__}' "
            f"should be of type {parameter._dtype_}. "
            f"'{value}' given (type '{type(value)}'.)"
        )


@dataclass
class NumberValidator:
    """Validate a numerical parameter.

    Args:
        min_value: The lower bound for this parameter value.
        max_value: The upper bound for this parameter value.

    Raises:
        ValueError: If the value is not between `min_value` and
            `max_value`.
    """

    min_value: int | float = -float("inf")
    max_value: int | float = float("inf")

    def __call__(self, parameter: Parameter, value: Any) -> None:
        if not self.min_value <= value <= self.max_value:
            raise ValueError(
                f"Parameter '{parameter._name_}' on "
                f"'{parameter._owner_.__name__}' should be between "
                f"'{self.min_value}' and '{self.max_value}'. "
                f"'{value}' given."
            )


@dataclass
class StringValidator:
    """Validate a string.

    Args:
        min_len: The minimal number of characters in the string.
        max_len: The maximal number of characters in the string.

    Raises:
        ValueError: If the length of the string is not between
            `min_len` and `max_len`.
    """

    min_len: int = 0
    max_len: int = float("inf")  # type: ignore[assignment]

    def __call__(self, parameter: Parameter, value: Any) -> None:
        if not self.min_len <= len(value) <= self.max_len:
            raise ValueError(
                f"Parameter '{parameter._name_}' on '{parameter._owner_.__name__}' "
                f"should be between '{self.min_len}' and '{self.max_len}' "
                f"characters long. '{value}' given ('{len(value)}' characters)."
            )
