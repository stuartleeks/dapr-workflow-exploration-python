# dapr-workflow-exploration-python

## Contents

This repo contains an example of using the Dapr worflow SDK in Python, along with an exploration for an alternative approach using Python decorators.

Key content:

| Path                      | Description                                                          |
| ------------------------- | -------------------------------------------------------------------- |
| `src/workflow_sdk`        | The starting project using the 'vanilla' Dapr workflow SDK in Python |
| `src/workflow_decorators` | An exploration of an alternative approach using Python decorators    |
| `submit_workflow.http`    | A VS Code REST client file for submitting workflow requests          |


## Dapr Workflow SDK

This project (`src/workflow_sdk`) is the starting point for the exploration.#
It uses the Dapr workflow SDK in Python to implement a simple workflow.

The `app.py` file sets up a Flask API for submitting workflow requests and getting the results.
The workflow code is in `workflow.py`.

To run the project:

```bash
pip install -r src/workflow_sdk/requirements.txt
dapr run -f dapr-workflow-sdk.yaml
```

To submit a workflow request, use the VS Code REST client file with `submit_workflow.http`.
The workflow request is a POST to `http://localhost:5000/workflow` with a JSON body like:

```json
{
	"steps": [
		{
			"name": "simple_test",
			"actions" : [
				{
					"content" : "Hello World"
				}
			]
		}
	]
}
```

The request body contains a set of steps, each of which contains a set of actions.
Steps are processed sequentially, and actions within a step are processed in parallel.

## Workflow Decorators

The `src/workflow_decorators` project is an exploration of an alternative approach to Dapr workflows using Python decorators.

As with the SDK project, `app.py` sets up a Flask API for submitting workflow requests and getting the results, and the workflow code is in `workflow.py`.

The `workflow_app.py` file contains the code for the decorator which could be moved to a separate package.


To run the project:

```bash
pip install -r src/workflow_decorators/requirements.txt
dapr run -f dapr-workflow-decorators.yaml
```


To submit a workflow request, use the VS Code REST client file with `submit_workflow.http`.
The workflow request is a POST to `http://localhost:5000/workflow` with a JSON body like:

```json
{
	"steps": [
		{
			"name": "simple_test",
			"actions" : [
				{
					"content" : "Hello World"
				}
			]
		}
	]
}
```

The request body contains a set of steps, each of which contains a set of actions.
Steps are processed sequentially, and actions within a step are processed in parallel.

### Decorator features

#### Tracking and registration

The general structure of the workflow app using decorators is shown below.

```python
wf_app = WorkflowApp()


@wf_app.workflow
def processing_workflow(context: DaprWorkflowContext, input):
    # orchestrator code here
	pass


@wf_app.activity
def activity1(context: WorkflowActivityContext, input: Activity1Input):
    # activity code here
	pass

def activity2(context: WorkflowActivityContext, input: Activity2Input):
	# Code for another activity  here
	pass

```

In this example, `wf_app` is created as an instance of the `WorkflowApp`.
The orchestrator function is decorated with `@wf_app.workflow` and the activity functions are decorated with `@wf_app.activity`.

When methods are decorated, the decorator code registers the method with the `WorkflowApp` instance.
As a result of this tracking, the `WorkflowApp` instance can be used to register the components with the Dapr Workflow runtime, as shown below.

```python
workflowRuntime = WorkflowRuntime(host, grpc_port)
wf_app.register_components(workflowRuntime)
```

#### Direct calls to activities

When working with the SDK, invoking an activity is done using the `context.call_activity` method, as shown below.

```python
# Call the save_state activity
yield context.call_activity(save_state, input=asdict(results))
```

With Python decorators we can modify the function returned from the decorator.
In this case, the decorator returns a function which injects the `call_activity` enabling the orchestrator function to call the activity directly, as shown below.

```python
yield save_state(input=results)
```

To support this, the workflow decorator code captures the `DaprWorkflowContext` instance passed to the orchestrator and stores it in a `ContextVar` in the `WorkflowApp` instance.
This `DaprWorkflowContext` instance is then used to invoke the activity function via `call_activity`.

#### Dataclass handling

With the Dapr workflow SDK, passing a dataclass as an input parameter to `call_activity` results in a `SimpleNamespace` instance being passed in to the activity function when it is invoked.
One way to work around this is to convert the dataclass to a dictionary before passing it to `call_activity`, and then convert back to the dataclass in the activity function.

This conversion (to dictionary and back to dataclass) is handled automatically by the decorator code, so the orchestrator can pass the dataclass instance directly to the activity and the activity function will receive a dataclass instance.

#### Limitations

Currently the decorator code requires that the input parameter to the orchestrator function is called `input`.
This was simply for ease/speed of exploration rather than a fundamental limitation.

The `WorkflowApp` has currently only been tested in the context of the `workflow_decorators` project.
