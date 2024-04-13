from __future__ import annotations

from typing import Any

from workfloz.cluster import getcluster
from workfloz.entity import Entity
from workfloz.entity import ExecutableMixin
from workfloz.entity import NamedMixin


class Component(NamedMixin, ExecutableMixin, Entity):
    """Entities at the base of the hierarchy in a workflow.

    Args:
        name: The name for this component.
    """

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        cluster = getcluster()
        if cluster:
            cluster._entities_.append(self)
