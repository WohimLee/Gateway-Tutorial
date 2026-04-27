from __future__ import annotations

from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GatewayClientId(StrEnum):
    WEBCHAT_UI = "webchat-ui"
    CONTROL_UI = "wigainneo-control-ui"
    TUI = "wigainneo-tui"
    WEBCHAT = "webchat"
    CLI = "cli"
    GATEWAY_CLIENT = "gateway-client"
    MACOS_APP = "wigainneo-macos"
    IOS_APP = "wigainneo-ios"
    ANDROID_APP = "wigainneo-android"
    NODE_HOST = "node-host"
    TEST = "test"
    FINGERPRINT = "fingerprint"
    PROBE = "wigainneo-probe"


GATEWAY_CLIENT_IDS: Mapping[str, GatewayClientId] = MappingProxyType(
    {member.name: member for member in GatewayClientId}
)

# Back-compat naming (internal): these values are IDs, not display names.
GATEWAY_CLIENT_NAMES = GATEWAY_CLIENT_IDS
GatewayClientName = GatewayClientId


class GatewayClientMode(StrEnum):
    WEBCHAT = "webchat"
    CLI = "cli"
    UI = "ui"
    BACKEND = "backend"
    NODE = "node"
    PROBE = "probe"
    TEST = "test"


GATEWAY_CLIENT_MODES: Mapping[str, GatewayClientMode] = MappingProxyType(
    {member.name: member for member in GatewayClientMode}
)


class GatewayClientInfo(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    id: GatewayClientId
    version: str
    platform: str
    mode: GatewayClientMode
    display_name: str | None = Field(default=None, alias="displayName")
    device_family: str | None = Field(default=None, alias="deviceFamily")
    model_identifier: str | None = Field(default=None, alias="modelIdentifier")
    instance_id: str | None = Field(default=None, alias="instanceId")

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = normalize_gateway_client_id(value)
            return normalized if normalized is not None else value
        return value

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = normalize_gateway_client_mode(value)
            return normalized if normalized is not None else value
        return value


class GatewayClientCap(StrEnum):
    TOOL_EVENTS = "tool-events"


GATEWAY_CLIENT_CAPS: Mapping[str, GatewayClientCap] = MappingProxyType(
    {member.name: member for member in GatewayClientCap}
)

GATEWAY_CLIENT_ID_SET = frozenset(GatewayClientId)
GATEWAY_CLIENT_MODE_SET = frozenset(GatewayClientMode)


def normalize_gateway_client_id(raw: str | None = None) -> GatewayClientId | None:
    normalized = raw.strip().lower() if raw is not None else ""
    if not normalized:
        return None
    try:
        return GatewayClientId(normalized)
    except ValueError:
        return None


def normalize_gateway_client_name(raw: str | None = None) -> GatewayClientName | None:
    return normalize_gateway_client_id(raw)


def normalize_gateway_client_mode(raw: str | None = None) -> GatewayClientMode | None:
    normalized = raw.strip().lower() if raw is not None else ""
    if not normalized:
        return None
    try:
        return GatewayClientMode(normalized)
    except ValueError:
        return None


def has_gateway_client_cap(
    caps: Sequence[str] | None,
    cap: GatewayClientCap,
) -> bool:
    if not isinstance(caps, list):
        return False
    return cap in caps
