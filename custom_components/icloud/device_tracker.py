"""Support for tracking iCloud devices.

No changes from upstream are needed for this platform, so it's a
straight re-export rather than a duplicated copy.
"""

from homeassistant.components.icloud.device_tracker import (
    async_setup_entry,  # noqa: F401
)
