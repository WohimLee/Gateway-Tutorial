from .openai_compatible import chat_completions, embeddings, list_models, responses, retrieve_model
from .rest import (
    hook_agent,
    hook_mapping,
    hook_wake,
    invoke_tool,
    kill_session,
    live_probe,
    mattermost_command,
    mattermost_dynamic,
    plugin_route,
    ready_probe,
    slack_dynamic,
)
from .sse import session_history
from .static import a2ui_static, canvas_static, control_ui_static

__all__ = [
    "a2ui_static",
    "canvas_static",
    "chat_completions",
    "control_ui_static",
    "embeddings",
    "hook_agent",
    "hook_mapping",
    "hook_wake",
    "invoke_tool",
    "kill_session",
    "list_models",
    "live_probe",
    "mattermost_command",
    "mattermost_dynamic",
    "plugin_route",
    "ready_probe",
    "responses",
    "retrieve_model",
    "session_history",
    "slack_dynamic",
]
