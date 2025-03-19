import logging
import uuid
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .base import BaseTracer, EventLevel
from .callback import wrap_callback

if TYPE_CHECKING:
    from langchain.callbacks.base import BaseCallbackHandler


logger = logging.getLogger("ocs.tracing")


class TracingServiceWrapper:
    def __init__(self, tracers: list[BaseTracer]):
        self._tracers = tracers
        self.deactivated = True

        self.inputs: dict[str, dict] = defaultdict(dict)
        self.inputs_metadata: dict[str, dict] = defaultdict(dict)
        self.outputs: dict[str, dict] = defaultdict(dict)
        self.outputs_metadata: dict[str, dict] = defaultdict(dict)

        self.run_name: str | None = None
        self.run_id: UUID | None = None
        self.session_id: str | None = None
        self.user_id: str | None = None

    def _reset_io(self) -> None:
        self.inputs = defaultdict(dict)
        self.inputs_metadata = defaultdict(dict)
        self.outputs = defaultdict(dict)
        self.outputs_metadata = defaultdict(dict)

    def initialize(self, session_id: str, run_name: str, user_id: str) -> None:
        if not self._tracers:
            return

        self.deactivated = False
        self.session_id = session_id
        self.run_name = run_name
        self.user_id = user_id
        self.run_id = uuid.uuid4()

        for tracer in self._tracers:
            try:
                tracer.initialize(run_name, self.run_id, session_id, user_id)
            except Exception:  # noqa BLE001
                logger.error("Error initializing tracer %s", tracer.__class__.__name__, exc_info=True)

    def _start_traces(
        self,
        trace_id: str,
        trace_name: str,
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.inputs[trace_id] = inputs
        self.inputs_metadata[trace_id] = metadata or {}
        if self.deactivated:
            return

        for tracer in self._tracers:
            if not tracer.ready:
                continue

            try:
                tracer.start_span(
                    span_id=trace_id,
                    trace_name=trace_name,
                    inputs=inputs,
                    metadata=metadata or {},
                )
            except Exception:  # noqa BLE001
                logger.exception(f"Error starting trace {trace_name}")

    def _end_traces(self, trace_id: str, trace_name: str, error: Exception | None = None) -> None:
        if self.deactivated:
            return

        for tracer in self._tracers:
            if not tracer.ready:
                continue

            try:
                tracer.end_span(
                    span_id=trace_id,
                    outputs=self.outputs[trace_id],
                    error=error,
                )
            except Exception:  # noqa BLE001
                logger.exception(f"Error ending trace {trace_name}")

    def end(self, outputs: dict, error: Exception | None = None) -> None:
        if self.deactivated:
            return

        for tracer in self._tracers:
            if not tracer.ready:
                continue
            try:
                tracer.end(self.inputs, outputs=self.outputs, error=error, metadata=outputs)
            except Exception:  # noqa BLE001
                logger.exception("Error ending all traces")
        self._reset_io()

    @contextmanager
    def trace_context(
        self,
        trace_id: str,
        trace_name: str,
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ):
        if self.deactivated:
            yield self
            return

        self._start_traces(
            trace_id,
            trace_name,
            inputs,
            metadata,
        )
        try:
            yield self
        except Exception as e:
            self._end_traces(trace_id, trace_name, e)
            raise
        else:
            self._end_traces(trace_id, trace_name)

    def set_outputs(
        self,
        trace_id: str,
        outputs: dict[str, Any],
        output_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.outputs[trace_id] |= outputs or {}
        self.outputs_metadata[trace_id] |= output_metadata or {}

    def event(
        self,
        name: str,
        message: str,
        level: EventLevel = "DEFAULT",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self.deactivated:
            return

        for tracer in self._tracers:
            if not tracer.ready:
                continue

            try:
                tracer.event(name, message, level, metadata)
            except Exception:  # noqa BLE001
                logger.exception(f"Error sending event {name}")

    def get_langchain_callbacks(self) -> list["BaseCallbackHandler"]:
        if self.deactivated:
            return []

        callbacks = []
        for tracer in self._tracers:
            if not tracer.ready:
                continue

            callback = tracer.get_langchain_callback()
            if callback:
                callbacks.append(wrap_callback(callback))

        return callbacks

    def get_current_trace_info(self) -> list[dict[str, Any]]:
        if self.deactivated:
            return []

        trace_info = []
        for tracer in self._tracers:
            if not tracer.ready:
                continue

            try:
                info = tracer.get_current_trace_info()
                trace_info.append(info.model_dump())
            except Exception:  # noqa BLE001
                logger.exception("Error getting trace info")
                continue

        return trace_info
