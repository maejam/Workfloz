from __future__ import annotations

from abc import ABC
from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from uuid import uuid4

from workfloz.exceptions import WorkflowCompilationError
from workfloz.exceptions import WorkflowExecutionError


class Entity(ABC):  # noqa: B024
    """The base class for all entities.

    All entities have a name identifier. Those inheriting from
    `NamedMixin` will have a name given by the user upon
    instantiation. Others will be attributed a uuid name.
    Entity inherits from ABC, so does all the Mixin classes, in order
    to simplify MRO consistency.
    """

    def __init__(self, name: str | None = None, *args: Any, **kwargs: Any) -> None:
        self._name_ = str(uuid4()) if name is None else str(name)

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self._name_}"


class NamedMixinMeta(ABCMeta):
    def __call__(cls, name: str, *args: Any, **kwargs: Any) -> NamedMixin:
        try:
            instance: NamedMixin = NamedMixin._instances_[name]
            if not isinstance(instance, cls):
                raise TypeError(
                    f"The registered instance with name {name} "
                    f"is not compatible with type {cls.__name__}."
                )
            return instance
        except KeyError:
            instance = super().__call__(name, *args, **kwargs)
            return instance


class NamedMixin(metaclass=NamedMixinMeta):
    """A Mixin class for registering named entities.

    NamedEntities are identified by a user-given name, and
    instantiating a NamedEntity with an already existing name will
    return the same object, provided the class used for instantiation
    is the same as the registered object class (or a super-class
    thereof).

    Args:
        name: The name for this Entity.

    Attributes:
        _name_: The name of the Entity.
        _instances_: A dictionnary mapping the already given names and
            the corresponding objects.

    Raises:
        TypeError: If the class used to retrieve the entity is not
            compatible with the registered instance.
    """

    _instances_: dict[str, NamedMixin] = {}

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)  # type: ignore[call-arg]
        NamedMixin._instances_[name] = self


class ExecutableMixin(ABC):
    """A Mixin class for Entities that can be executed.

    Attributes:
        _compiled_: The state of the entity after compilation.
        _result_: The value returned by this entity after its
            execution.
    """

    @abstractmethod
    def _compile_(self) -> Any:
        """Define how an entity should be compiled.

        The goal of the compilation stage is to perform basic sanity
        checks to make sure the excecution stage will not encounter
        avoidable errors after some potentially long computations. It
        can also be used to perform some computations that are
        independent from the concrete entity.
        The implementation can be as simple as returning
        `self` if the entity does not need any compilation.
        """

    @abstractmethod
    def _run_(self) -> Any:
        """Perform the actual computation.

        This method usually acts on the *compiled* entity and returns
        the final result.
        The implementation can be as simple as returning
        `self._compiled_` if the entity does not need any extra step
        to be run.
        """

    def compile(self) -> None:
        """Compile this entity.

        The result of the compilation is contained in the entity's
        `_compiled_` attribute after this process is done and can be
        retrieved with the `compiled` function.
        """
        self._compiled_ = self._compile_()

    def run(self) -> None:
        """Run this entity.

        The result of the execution is contained in the entity's
        `_result_` attribute after this process is done and can be
        retrieved with the `result` function.

        Raises:
            WorkflowExecutionError: If the entity was not compiled
                before trying to run it.
        """
        try:
            self._result_ = self._run_()
        except AttributeError as e:
            if e.name == "_compiled_":
                raise WorkflowExecutionError(
                    f"The entity '{self._name_}' is not compiled yet. "  # type: ignore [attr-defined]
                    "Run the 'compile' method on it first. "
                    "Or use the 'start' method to compile and run in one step."
                ) from None
            else:
                raise

    def start(self) -> None:
        """Combine compilation and execution in one step."""
        self.compile()
        self.run()


def compiled(entity: ExecutableMixin) -> Any:
    """Use on an entity to retrieve its compiled state.

    Returns:
        The compiled state for the entity.

    Raises:
        TypeError: If the provided object is not an executable entity.
        WorkflowCompilationError: If the `_compiled_` attribute is not
            present on the entity.
    """
    if not isinstance(entity, ExecutableMixin):
        raise TypeError(
            "This object is not an executable entity. You can't call 'compiled' on it."
        )
    try:
        return entity._compiled_
    except AttributeError as e:
        raise WorkflowCompilationError(
            f"'{entity._name_}' has not been compiled yet. "  # type: ignore [attr-defined]
            "Call the 'compile' or 'start' method on it before.",
            e.obj,
        ) from None


def result(entity: Entity) -> Any:
    """Use on an entity to retrieve the result after its execution.

    Returns:
        The final result after running the entity.

    Raises:
        TypeError: If the provided object is not an executable entity.
        WorkflowExecutionError: If the `_result_` attribute cannot be
            found on the entity.
    """
    if not isinstance(entity, ExecutableMixin):
        raise TypeError(
            "This object is not an executable entity. You can't call 'result' on it."
        )
    try:
        return entity._result_
    except AttributeError as e:
        message = (
            f"The result for '{entity._name_}' has not been computed yet. "
            "Call the 'run' method on it before."
        )
        if not hasattr(entity, "_compiled_"):
            message += (
                "\nBesides, it is not compiled either. Use the 'start' method to "
                "perform both steps at the same time."
            )
        raise WorkflowExecutionError(message, e.obj) from None
