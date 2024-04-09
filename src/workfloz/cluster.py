from __future__ import annotations

import contextvars
from contextlib import ContextDecorator
from types import TracebackType
from typing import Any

from workfloz.entity import _ExecutableEntity
from workfloz.exceptions import WorkflowDefinitionError

_cluster: contextvars.ContextVar[_Cluster | None] = contextvars.ContextVar(
    "cluster", default=None
)


def getcluster() -> _Cluster | None:
    """Return the active cluster.

    Returns:
        The currently active cluster if one is set. `None` otherwise.
    """
    return _cluster.get()


def setcluster(cluster: _Cluster | None) -> contextvars.Token[_Cluster | None]:
    """Set the active cluster.

    Args:
        cluster: The cluster object to be set as active. `None` is also
            a valid input.

    Returns:
        A Token object that can be used to restore the active cluster
        to its previous state via the `resetcluster` function.

    Raises:
        WorkflowDefinitionError: If an attempt is made to set the
            active cluster to something other than a `_Cluster` object
            or `None`.
    """
    if not isinstance(cluster, _Cluster | type(None)):
        raise WorkflowDefinitionError(
            "Only a Cluster object or 'None' can be set as an active cluster."
        )
    return _cluster.set(cluster)


def resetcluster(token: contextvars.Token[_Cluster | None]) -> None:
    """Reset the active cluster to its previous state.

    Args:
        token: A Token object returned by a call to `setcluster`.
    """
    _cluster.reset(token)


class _Cluster(_ExecutableEntity, ContextDecorator):
    """An entity that can contain other executable entities.

    Args:
        name: The name for this entity.

    Attributes:
        _entities_: A list containing all the entities within that
            cluster.
    """

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        self._entities_: list[_ExecutableEntity] = []

    def __enter__(self) -> _Cluster:
        self._enter_()
        cluster = getcluster()
        if cluster:
            cluster._entities_.append(self)
        self._token = setcluster(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """The logic when exiting a cluster.

        Raises:
            WorkflowDefinitionError: If an attempt is made to define a
                cluster inside itself.
        """
        self._exit_(exc_type, exc_value, traceback)
        try:
            resetcluster(self._token)
        except RuntimeError:
            raise WorkflowDefinitionError(
                "You cannot set a cluster inside itself."
            ) from None

    def _enter_(self) -> None:
        """Define additional logic to be run when entering a cluster."""

    def _exit_(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Define additional logic to be run when exiting a cluster."""

    def _compile_(self) -> _Cluster:
        """The custom compilation logic for clusters.

        Calling `compile` on a cluster will compile all its member
        entities, including other clusters.

        Returns:
            The cluster object.
        """
        for entity in self._entities_:
            entity.compile()
        return self

    def _run_(self) -> Any:
        """The custom execution logic for clusters.

        Calling `run` on a cluster will execute all its member
        entities, including other clusters.

        Returns:
            The compiled cluster object.
        """
        for entity in self._entities_:
            entity.run()
        return self._compiled_


class Job(_Cluster):
    """Top level cluster."""

    def _enter_(self) -> None:
        """Limit the use of Jobs to the highest level context.

        Raises:
            WorkflowDefinitionError: If a Job is defined inside another
                cluster.
        """
        if getcluster():
            raise WorkflowDefinitionError(
                "A Job cannot be created inside another cluster."
            )


class Task(_Cluster):
    """Low level cluster."""

    def _enter_(self) -> None:
        """Limit the use of Tasks inside another cluster.

        Raises:
            WorkflowDefinitionError: If a Task is not defined inside
                another cluster.
        """
        if not getcluster():
            raise WorkflowDefinitionError(
                "A Task can only be created inside another cluster."
            )
