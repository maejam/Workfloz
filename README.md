# Workfloz
A simple library for building complex workflows.
___

Workfloz is meant to be very easy to use, abstracting away most of the complexity one needs to deal with when building Workflows.
This is done through the use of extensions, where the complexity resides, and through a clean and easy to learn syntax.

## Installing
```shell
pip install workfloz
```

## Vision
Although Workfloz is built to be a general-purpose tool,
the first set of extensions will be about machine learning. Once stable, the library should be able to run the following code:
```python
# 1. Instantiate tools provided by extension
loader = CSVLoader("loader", file="data.csv") # Set as concrete directly.
processor = DataProcessor("processor")
processors = Pipeline("processors", processor.remove_duplicates())
builder = Abstract("builder") # Set as abstract and set concrete later.
trainer = ModelTrainer("trainer", auto_from=builder) # Automatically choose right trainer based on builder.
mlf_logger = MLFlowLogger("mlflogger", url="http://...")
file_logger = FileLogger("filelogger", dir="logs/")

# 2. Build workflow template
with Job("Machine Learning") as ML:

    with Task("prepare inputs", mode="async"): # 'async' applies on a line basis
        loader.load() | processors.run() > trainer.data
        builder.build() > trainer.model
    
    with Task("train", mode="async"):
        trainer.train()
        when("training_started", trainer) >> [mlf_logger.log_parameters(), file_logger.log_parameters()]
        when("epoch_ended", trainer) >> [mlf_logger.log_metrics(), file_logger.log_metrics()]
        when("training_ended", trainer) >> [mlf_logger.log_model(), file_logger.log_model()]
              
# 3. Define different Workflows from base template above.
forest10 = Job("forest-10", blueprint=ML)
# Set missing concrete strategies
forest10["builder"] = SKLForestBuilder(num_estimators=10)

forest50 = Job("forest-50", blueprint=ML)
forest50["builder"] = SKLForestBuilder(num_estimators=50)

forest50-scaled = Job("forest-50s", blueprint=forest50)
# Add processor to Pipeline
processors.then(processor.Scale())

# 4. Start workflows	
forest10.start()
forest50.start()
forest50s.start()
```
In pratice, 1 and 2 could be provided by the extension. The end user would only need to define 3 and 4.
Extensions for Scikit learn, HuggingFace and MLFlow are planned.

## Status of current version
The library is under active development but it will take some time before the example above can run. The API is not to be considered stable before v1.0.0 is released.  
The following example is already possible though (available in '/examples'):

```python
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
```
