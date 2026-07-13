"""Expose iCloud photo albums as a media source.

No changes from upstream are needed here, so it's a straight re-export
rather than a duplicated copy.
"""

from homeassistant.components.icloud.media_source import (  # noqa: F401
    PhotoCache,
    async_get_media_source,
    async_setup_mediasource,
    async_setup_photo_cache,
)
