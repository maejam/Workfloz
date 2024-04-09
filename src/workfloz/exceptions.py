class WorkflozError(Exception):
    """The base class for all exceptions."""


class WorkflozUserError(WorkflozError):
    """Raised as a result of an incorrect use of Workfloz."""


class WorkflowDefinitionError(WorkflozUserError):
    """Raised when the definition of a Workflow is incorrect."""


class WorkflowCompilationError(WorkflozUserError):
    """Raised when an error occurs while compiling an Entity."""


class WorkflowExecutionError(WorkflozUserError):
    """Raised when an error occurs while executing an Entity."""
