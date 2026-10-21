"""Compatibility exports for Atomic Agents tracing."""

from . import installation, span_attributes, tracing_config

TRACER_NAME = installation.TRACER_NAME
TRACED_MARKER = installation.TRACED_MARKER
install = installation.install
is_installed = installation.is_installed
uninstall = installation.uninstall
PayloadVisibility = tracing_config.PayloadVisibility
TracingConfig = tracing_config.TracingConfig
using_conversation = span_attributes.using_conversation

ATTR_MODEL = span_attributes.ATTR_MODEL
ATTR_MODE = span_attributes.ATTR_MODE
ATTR_INPUT_SCHEMA = span_attributes.ATTR_INPUT_SCHEMA
ATTR_OUTPUT_SCHEMA = span_attributes.ATTR_OUTPUT_SCHEMA
ATTR_HISTORY_MESSAGE_COUNT = span_attributes.ATTR_HISTORY_MESSAGE_COUNT
ATTR_CONTEXT_PROVIDERS = span_attributes.ATTR_CONTEXT_PROVIDERS
ATTR_SYSTEM_PROMPT_SHA256 = span_attributes.ATTR_SYSTEM_PROMPT_SHA256
ATTR_STREAM_CLOSED_EARLY = span_attributes.ATTR_STREAM_CLOSED_EARLY
ATTR_OPERATION = span_attributes.ATTR_OPERATION
ATTR_AGENT_NAME = span_attributes.ATTR_AGENT_NAME
ATTR_REQUEST_MODEL = span_attributes.ATTR_REQUEST_MODEL
ATTR_PROVIDER_NAME = span_attributes.ATTR_PROVIDER_NAME
ATTR_CONVERSATION_ID = span_attributes.ATTR_CONVERSATION_ID
ATTR_TOOL_NAME = span_attributes.ATTR_TOOL_NAME
ATTR_TOOL_DESCRIPTION = span_attributes.ATTR_TOOL_DESCRIPTION
ATTR_TOOL_TYPE = span_attributes.ATTR_TOOL_TYPE
ATTR_TOOL_ARGUMENTS = span_attributes.ATTR_TOOL_ARGUMENTS
ATTR_TOOL_RESULT = span_attributes.ATTR_TOOL_RESULT
ATTR_SPAN_KIND = span_attributes.ATTR_SPAN_KIND
ATTR_INPUT_VALUE = span_attributes.ATTR_INPUT_VALUE
ATTR_INPUT_MIME_TYPE = span_attributes.ATTR_INPUT_MIME_TYPE
ATTR_OUTPUT_VALUE = span_attributes.ATTR_OUTPUT_VALUE
ATTR_OUTPUT_MIME_TYPE = span_attributes.ATTR_OUTPUT_MIME_TYPE
ATTR_OI_AGENT_NAME = span_attributes.ATTR_OI_AGENT_NAME
ATTR_OI_TOOL_NAME = span_attributes.ATTR_OI_TOOL_NAME
ATTR_OI_TOOL_DESCRIPTION = span_attributes.ATTR_OI_TOOL_DESCRIPTION
ATTR_TOOL_PARAMETERS = span_attributes.ATTR_TOOL_PARAMETERS
ATTR_SESSION_ID = span_attributes.ATTR_SESSION_ID
ATTR_INPUT = span_attributes.ATTR_INPUT
ATTR_OUTPUT = span_attributes.ATTR_OUTPUT
ATTR_AGENT_CLASS = span_attributes.ATTR_AGENT_CLASS
ATTR_ERROR_TYPE = span_attributes.ATTR_ERROR_TYPE
ATTR_TOOL_CLASS = span_attributes.ATTR_TOOL_CLASS
