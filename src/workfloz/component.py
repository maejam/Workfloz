from __future__ import annotations

import functools
import inspect
from collections import OrderedDict
from collections.abc import Callable
from typing import Any
from typing import ParamSpec

from workfloz.cluster import getcluster
from workfloz.entity import Entity
from workfloz.entity import ExecutableMixin
from workfloz.entity import NamedMixin
from workfloz.exceptions import WorkflowCompilationError
from workfloz.exceptions import WorkflowExecutionError
from workfloz.parameter import UND


class Component(ExecutableMixin, Entity):
    """Entities at the base of the hierarchy in a workflow.

    When a component is instantiated inside a cluster, it will be
    registered as a member of this cluster.

    Args:
        name: The name for this component.
    """

    def __init__(self, name: str | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        cluster = getcluster()
        if cluster:
            cluster._entities_.append(self)


P = ParamSpec("P")


class Action(Entity):
    """Wrapper around functions and class bound-methods.

    Actions allow us to treat functions as full-blown mutable objects.
    Among other things, this let us postpone function calls and
    overload operators between function objects.

    Args:
        func: The function to wrap.
        instance: The related instance in the case of a bound-method.
            See `ActionContainer`.

    Attributes:
        _func_: The function from the `ActionContainer` class to wrap around.
        _instance_: The instance of `ActionContainer`.
    """

    def __init__(
        self,
        name: str | None = None,
        *,
        func: Callable[P, Any],
        instance: ActionContainer | None = None,
    ) -> None:
        super().__init__(name)
        self._func_: Callable[P, Any] | functools.partial[Any] = (
            functools.partial(func, instance) if instance else func
        )
        self._instance_ = instance

    def __str__(self) -> str:
        ret = super().__str__()
        args = self._bind_args(include_und=True).arguments
        ret += f"({', '.join('='.join([str(k), str(v)]) for k, v in args.items())})"
        return ret

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> _ActionCall:
        """Postpone the call to the wrapped function.

        When calling an Action, an `_ActionCall` object will be
        produced. This object will encapsulate the arguments set on
        the `_instance_` and the `_func_` default values when the call
        was made, updated with the arguments passed to the call itself.
        As a `Component`, the `_ActionCall` object will be registered
        by the active `Cluster`, if any, and will be able to be run
        with the right set of arguments later.
        """
        # Args passed to __call__.
        sig = inspect.signature(self._func_)
        boundcall = sig.bind_partial(*args, **kwargs)
        # Validate with descriptors.
        if self._instance_:
            instancedict = vars(self._instance_).copy()
            for key, value in boundcall.arguments.items():
                setattr(self._instance_, key, value)
            self._instance_.__dict__ = instancedict
        # Combine with args on ActionContainer and func default values.
        bound = self._bind_args(include_und=True)
        bound.arguments.update(boundcall.arguments)
        return _ActionCall(self, bound)

    def _execute(self, *args: P.args, **kwargs: P.kwargs) -> Any:
        return self._func_(*args, **kwargs)

    def _bind_args(self, include_und: bool = False) -> inspect.BoundArguments:
        """Bind arguments to the wrapped function signature.

        The arguments to bind will first be looked-up on the
        `_instance_`. Then the default values from the function
        definition will be applied.

        Returns:
            The mapping of arguments to the function’s signature.
        """
        sig = inspect.signature(self._func_)
        # Compute ActionContainer attributes.
        kwargs = {
            key: getattr(self._instance_, key)
            for key in dir(self._instance_)
            if key in sig.parameters and getattr(self._instance_, key) is not UND
        }
        # Apply kwargs and default values.
        bound = sig.bind_partial(**kwargs)
        bound.apply_defaults()
        # Apply UND.
        if include_und:
            kwargs = {}
            for key in sig.parameters:
                kwargs[key] = bound.arguments.get(key, UND)
            bound.arguments = OrderedDict(kwargs)
        return bound


class _ActionCall(Component):
    """Represent a call to an Action object.

    _ActionCall encapsulates the original Action object along with the
    state of the arguments at the time of instantiation, which is the
    moment when the Action was called. This mechanism make it possible
    to "play" the call later, i.e. when `run` is called.

    Args:
        action: The Action object that will be executed.
        bound: The bound arguments to run the action with.

    Attributes:
        _action_: The Action object that will be executed.
        _bound_: The bound arguments to run the action with.
    """

    def __init__(self, action: Action, bound: inspect.BoundArguments) -> None:
        super().__init__()
        self._action_ = action
        self._bound_ = bound

    def __str__(self) -> str:
        ret = super().__str__()
        ret += f" <{self._action_._name_}"
        ret += f"""({', '.join('='.join([str(k), str(v)])
                for k, v in self._bound_.arguments.items())})>"""
        return ret

    def _compile_(self) -> _ActionCall:
        """
        Raises:
            WorkflowCompilationError: If Undefined arguments subsist
                in `_bound_`.

        Returns:
            The _ActionCall object.
        """
        if UND in self._bound_.arguments.values():
            raise WorkflowCompilationError(
                f"Action call has undefined arguments: '{self._bound_.arguments}'"
            )
        return self

    def _run_(self) -> Any:
        """Execute the function wrapped by the Action object.

        Returns:
            The result after executing the wrapped function.
        """
        return self._compiled_._action_._execute(
            *self._bound_.args, **self._bound_.kwargs
        )


class ActionContainer(NamedMixin, Entity):
    """Turn methods into Action objects.

    By inheriting from this class, all methods will be turned into
    `Actions`.
    Actions act at the *bound* method level, meaning unbound class
    functions will not be affected.
    Given a class `C` with a method `m` and an instance `i`:
    - `C.m` will return the unaltered function object.
    - `i.m` will return the Action instance.
      `i.m._func_` will be m. `i.m._instance_` will be i.
    Just like bound-methods, a different Action instance will be
    returned with each call to `i.m`
    (i.e. `i.m is i.m` returns `False`).
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        super().__init__(name)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattribute__(self, name: str) -> Any:
        value = super().__getattribute__(name)
        if (
            inspect.ismethod(value)
            and not name.startswith("__")
            and not name.endswith("__")
        ):
            value = Action(
                f"{self._name_}.{value.__name__}",
                func=value.__func__,
                instance=self,
            )
        return value


class Abstract(ActionContainer):
    """Use to defer the choice of a concrete ActionContainer.

    This is a special `ActionContainer` because all its attributes are
    actions that will raise an exception when executed. This is
    usefull to define a Container in a workflow structure and set the
    concrete implementation before execution.
    """

    __getattribute__ = object.__getattribute__

    def _abstract(self, *args: Any, **kwargs: Any) -> None:
        raise WorkflowExecutionError(f"{self._name_} is abstract and cannot be run.")

    def __getattr__(self, name: str) -> Action:
        return Action("Abstract Action", func=self._abstract, instance=self)
