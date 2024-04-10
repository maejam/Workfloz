import pytest

from workfloz.parameter import dtype_validator
from workfloz.parameter import NumberValidator
from workfloz.parameter import Parameter
from workfloz.parameter import StringValidator
from workfloz.parameter import UND
from workfloz.parameter import UND_TYPE


def test_Undefined_str():
    assert str(UND) == "<UNDEFINED>"


@pytest.fixture
def Default():
    class Owner:
        a = Parameter()

    return Owner


def test_default_get(Default):
    d = Default()
    assert d.a is UND


@pytest.mark.parametrize("value", [42, "test", None, object(), UND])
def test_default_set(Default, value):
    d = Default()
    d.a = value
    assert d.a == value


def test_default_dtype(Default):
    assert Default.a._dtype_ is UND_TYPE


@pytest.mark.parametrize(
    "default, other",
    [
        (5, "test"),
        ("test", 6.7),
        (None, object()),
        (0, None),
    ],
)
def test_get_set(default, other):
    class Owner:
        a = Parameter(default=default)

    o = Owner()

    assert o.a == default
    o.a = other
    assert o.a == other


@pytest.mark.parametrize(
    "argument, attribute",
    [
        (None, [dtype_validator]),
        (NumberValidator, [dtype_validator, NumberValidator]),
        (
            [NumberValidator, StringValidator],
            [dtype_validator, NumberValidator, StringValidator],
        ),
    ],
)
def test_validators_list(argument, attribute):
    class Owner:
        a = Parameter(validators=argument)

    assert Owner.a._validators_ == attribute


@pytest.mark.parametrize(
    "default, hint, other",
    [
        (5, str, "test"),
        ("test", float, 6.7),
        (5, dict, {"arg1": 1, "arg2": 2}),
    ],
)
def test_dtype_validator(default, hint, other):
    class Owner:
        a: hint = Parameter(default=default)

    o = Owner()

    assert o.a == default
    o.a = other
    assert o.a == other


@pytest.mark.parametrize(
    "default, hint, other",
    [
        (5, str, None),
        ("test", float, "test"),
        (5, dict, [1, 2]),
    ],
)
def test_dtype_validator_raises(default, hint, other):
    class Owner:
        a: hint = Parameter(default=default)

    o = Owner()

    assert o.a == default
    with pytest.raises(TypeError, match="should be of type"):
        o.a = other


@pytest.mark.parametrize(
    "default, other, min_value, max_value",
    [
        (5, 42, 6, 43),
        ("test", -42, -43, 0),
        (None, 0, 0, 0),
        ([1, 2, 3], 4.2, 4.0, 5.0),
    ],
)
def test_NumberValidator(default, other, min_value, max_value):
    class Owner:
        a = Parameter(
            default=default,
            validators=[NumberValidator(min_value=min_value, max_value=max_value)],
        )

    o = Owner()

    assert o.a == default
    o.a = other
    assert o.a == other


@pytest.mark.parametrize(
    "default, other, min_value, max_value",
    [
        (5, 42, 6, 40),
        ("test", -42, -40, 0),
        (None, 1, 0, 0),
        ([1, 2, 3], 4.2, 4.3, 5.0),
    ],
)
def test_NumberValidator_raises(default, other, min_value, max_value):
    class Owner:
        a = Parameter(
            default=default,
            validators=[NumberValidator(min_value=min_value, max_value=max_value)],
        )

    o = Owner()

    assert o.a == default
    with pytest.raises(ValueError, match="should be between"):
        o.a = other


@pytest.mark.parametrize(
    "default, other, min_len, max_len",
    [
        (5, "42", 2, 43),
        ("test", "test", -43, 5),
        (None, "e", 1, 1),
        ([1, 2, 3], "hjhjhjhjhjhjhjh", 0.6, 15.2),
    ],
)
def test_StringValidator(default, other, min_len, max_len):
    class Owner:
        a = Parameter(
            default=default,
            validators=[StringValidator(min_len=min_len, max_len=max_len)],
        )

    o = Owner()

    assert o.a == default
    o.a = other
    assert o.a == other


@pytest.mark.parametrize(
    "default, other, min_len, max_len",
    [
        (5, "42", 3, 43),
        ("test", "test", -43, -2),
        (None, "e", 2, 3),
        ([1, 2, 3], "hjhjhjhjhjhjhjh", 0.6, 14.9),
    ],
)
def test_StringValidator_raises(default, other, min_len, max_len):
    class Owner:
        a = Parameter(
            default=default,
            validators=[StringValidator(min_len=min_len, max_len=max_len)],
        )

    o = Owner()

    assert o.a == default
    with pytest.raises(ValueError, match="should be between"):
        o.a = other
