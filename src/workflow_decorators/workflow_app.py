import contextvars
import functools
import inspect

from dataclasses import dataclass, asdict, is_dataclass

from dapr.ext.workflow import (
    DaprWorkflowContext,
    WorkflowActivityContext,
    WorkflowRuntime,
)
import dapr.ext.workflow as wf
from dapr.clients import DaprClient


class WorkflowApp:
    def __init__(self) -> None:
        self.context = contextvars.ContextVar("workflow_context", default=None)
        self.workflow_functions = []
        self.activity_functions = []

    def workflow(self, fn):
        @functools.wraps(fn)
        def decorator(context: DaprWorkflowContext, input):
            # track the workflow context for use in the activity decorator
            self.context.set(context)

            result = fn(context, input)
            return result

        # Track function to register
        # Here we register the decorator so that we capture the context
        self.workflow_functions.append(decorator)

        return decorator

    def activity(self, fn):
        # Track function to register. Default to original function passed in
        fn_to_register = fn

        argspec = inspect.getfullargspec(fn)
        # Currently requiring the input to be called 'input' to get data class deserialisation
        # as a PoC
        input_annotation = argspec.annotations.get("input") # TODO - determine the parameter without using the name!
        if input_annotation and is_dataclass(input_annotation):
            # replace inner_fn with a function that auto-deserialises the data class
            @functools.wraps(fn)
            def inner(context, input):
                nonlocal input_annotation

                # deserialise from dict
                input_dataclass = input_annotation(**input)

                return fn(context, input_dataclass)

            # register the inner function with workflow runtime
            fn_to_register = inner

        self.activity_functions.append(fn_to_register)

        # Create a function that is returned from the decorator
        # This omits the context from the signature as it is injected by the decorator
        @functools.wraps(fn)
        def decorator(input):
            context = self.context.get(None)
            if not context:
                raise Exception(
                    "Context not set - activity functions can only be invoked from workflow functions"
                )

            # Since auto-serialised data classes get serialised as SimpleNamespace
            # convert to a dict here
            if is_dataclass(input):
                input = asdict(input)

            return context.call_activity(fn_to_register, input=input)

        return decorator

    def register_components(self, workflow_runtime: WorkflowRuntime):
        for fn in self.workflow_functions:
            workflow_runtime.register_workflow(fn)
        for fn in self.activity_functions:
            workflow_runtime.register_activity(fn)