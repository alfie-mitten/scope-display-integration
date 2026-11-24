"""Constants for the XY Scope Display integration."""

from datetime import timedelta
import logging

DOMAIN = "xy_scope"
LOGGER = logging.getLogger(__package__)

# The box's push API version this integration speaks (GET /api/status "api").
API_VERSION = 1

DEFAULT_PORT = 8080

# How often the box's status is polled.
STATUS_INTERVAL = timedelta(seconds=60)

# Option: the smart outlet the scope is plugged into.
OPT_POWER = "power_switch"
