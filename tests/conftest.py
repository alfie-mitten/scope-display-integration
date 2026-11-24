"""Shared fixtures: a fake scope box standing in for the HTTP client."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from custom_components.xy_scope.api import ScopeAuthError, ScopeConnectionError
from custom_components.xy_scope.const import API_VERSION


class FakeBox:
    """Behaves like the box's API, and records what it was sent."""

    def __init__(self) -> None:
        self.boot = "boot-1"
        self.scale = 0.6
        self.writes: list[float | None] = []
        self.down = False
        self.token_ok = True
        self.api = API_VERSION

    def status_dict(self) -> dict[str, Any]:
        return {"api": self.api, "boot": self.boot, "uptime": 1,
                "scale": self.scale, "max_scale": 0.63, "playing": True,
                "error": None, "fps": 50.0}

    def _check(self, write: bool) -> None:
        if self.down:
            raise ScopeConnectionError("down")
        if write and not self.token_ok:
            raise ScopeAuthError("HTTP 401")

    async def status(self) -> dict[str, Any]:
        self._check(False)
        if self.api != API_VERSION:
            from custom_components.xy_scope.api import ScopeVersionError
            raise ScopeVersionError("version")
        return self.status_dict()

    async def put_scale(self, scale: float | None = None) -> dict[str, Any]:
        self._check(True)
        self.writes.append(scale)
        if scale is not None:
            self.scale = min(scale, 0.63)
        return self.status_dict()

    async def check_token(self) -> None:
        await self.put_scale()

    base = "http://box:8080"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def box():
    fake = FakeBox()
    factory = lambda *a, **k: fake  # noqa: E731
    with patch("custom_components.xy_scope.ScopeClient", factory), \
         patch("custom_components.xy_scope.config_flow.ScopeClient", factory):
        yield fake
