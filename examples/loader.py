import pandas as pd

from workfloz import ActionContainer
from workfloz import Job
from workfloz import Parameter
from workfloz import result
from workfloz import StringValidator


# Define tool
class CSVLoader(ActionContainer):  # Every method becomes an 'Action'
    """Return a pandas DataFrame from a CSV file."""

    # Attributes can be validated and documented
    file: str = Parameter(
        doc="The relative or absolute path.", validators=[StringValidator(max_len=50)]
    )
    separator: str = Parameter(default=",")

    def load(
        self, file, separator
    ):  # arguments will be filled in from above if not specified in call.
        return pd.read_csv(file, sep=separator)


# Instantiate tool
loader = CSVLoader("loader", file="iris.csv")
assert loader.file == "iris.csv"  # Attribute file is set on loader

# Define workflow
with Job("load data") as job:
    # A call to an 'Action' is recorded and will be executed on 'start'
    data = loader.load()
    # data = loader.load(separator=";") # Attr. could be overriden, only for this call

# start Job and check result
job.start()
print(result(data))
