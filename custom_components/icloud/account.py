"""iCloud account with an explicit auth fix for expired/rotated credentials."""

import logging

from homeassistant.components.icloud.account import (
    IcloudAccount as _UpstreamIcloudAccount,
)
from homeassistant.components.icloud.account import IcloudConfigEntry  # noqa: F401
from homeassistant.const import CONF_USERNAME
from homeassistant.exceptions import ConfigEntryNotReady
from pyicloud import PyiCloudService
from pyicloud.exceptions import (
    PyiCloudFailedLoginException,
    PyiCloudNoDevicesException,
    PyiCloudServiceNotActivatedException,
    PyiCloudServiceUnavailable,
)

_LOGGER = logging.getLogger(__name__)


class IcloudAccount(_UpstreamIcloudAccount):
    """iCloud account that explicitly requests a 2FA code before reauth.

    Only setup() is overridden here. Device polling, fetch scheduling,
    cancel_fetch, keep_alive, IcloudDevice, etc. are all inherited
    unchanged from homeassistant.components.icloud.account.IcloudAccount.
    """

    def setup(self) -> None:
        """Set up an iCloud account."""
        try:
            self.api = PyiCloudService(
                self._username,
                self._password,
                self._icloud_dir.path,
                with_family=self._with_family,
                # Auto-accept updated Apple terms of service. Newer pyicloud
                # versions otherwise raise PyiCloudAcceptTermsException on login.
                accept_terms=True,
            )

            if self.api.requires_2fa:
                # Trigger a new log in to ensure the user enters the 2FA code again.
                raise PyiCloudFailedLoginException("2FA Required")  # noqa: TRY301

        except PyiCloudFailedLoginException:
            self.api = None
            # Login failed which means credentials need to be updated.
            _LOGGER.error(
                (
                    "Your password for '%s' is no longer working; Go to the "
                    "Integrations menu and click on Configure on the discovered Apple "
                    "iCloud card to login again"
                ),
                self._config_entry.data[CONF_USERNAME],
            )

            self._require_reauth()
            return

        try:
            # Gets device owners infos
            user_info = self.api.devices.user_info
        except (
            PyiCloudServiceNotActivatedException,
            PyiCloudNoDevicesException,
            PyiCloudServiceUnavailable,
        ) as err:
            _LOGGER.error("No iCloud device found")
            raise ConfigEntryNotReady from err

        if user_info is None:
            raise ConfigEntryNotReady("No user info found in iCloud devices response")

        self._owner_fullname = (
            f"{user_info.get('firstName')} {user_info.get('lastName')}"
        )

        self._family_members_fullname = {}
        if user_info.get("membersInfo") is not None:
            for prs_id, member in user_info.get("membersInfo").items():
                self._family_members_fullname[prs_id] = (
                    f"{member['firstName']} {member['lastName']}"
                )

        self._devices = {}
        self.update_devices()
