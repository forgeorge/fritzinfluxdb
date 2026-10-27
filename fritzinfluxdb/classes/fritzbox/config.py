# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import configparser
import os
import pytz

from fritzinfluxdb.log import get_logger
from fritzinfluxdb.classes.common import ConfigBase
from fritzinfluxdb.classes.fritzbox.service_groups import SERVICE_GROUP_MODULES

log = get_logger()


class FritzBoxConfig(ConfigBase):
    """
        class which defines the FritzBox config options
    """

    hostname = {
        "type": str,
        "alt": "host",
        "default": "192.168.178.1"
    }
    username = {
        "type": str,
        "default": None
    }
    password = {
        "type": str,
        "default": None
    }
    port = {
        "type": int,
        "default": 49000
    }
    tls_enabled = {
        "type": bool,
        "alt": "ssl",
        "default": False
    }
    verify_tls = {
        "type": bool,
        "alt": "verify_ssl",
        "default": False
    }
    connect_timeout = {
        "type": int,
        "alt": "timeout",
        "default": 10
    }
    request_interval = {
        "type": int,
        "alt": "interval",
        "default": 10
    }
    box_tag = {
        "type": str,
        "default": "fritz.box"
    }
    timezone = {
        "type": str,
        "default": "Europe/Berlin"
    }
    services_connection_info = {"type": str, "default": "all"}
    services_homeauto = {"type": str, "default": "all"}
    services_logs = {"type": str, "default": "all"}
    services_network_hosts = {"type": str, "default": "all"}
    services_system_stats = {"type": str, "default": "all"}
    services_telephone_list = {"type": str, "default": "all"}
    services_tr069 = {"type": str, "default": "all"}
    services_vpn_data = {"type": str, "default": "all"}

    config_section_name = "fritzbox"

    def __init__(self, config_data):

        super().__init__(config_data)

        self._fw_version = None
        self.model = None
        self.link_type = None

    def parse_config(self, config_data: configparser.ConfigParser):

        super().parse_config(config_data)

        min_request_interval = self.__class__.request_interval.get("default")
        if getattr(self, "request_interval") < min_request_interval:
            log.info(f"Setting minimum FritzBox request interval to {min_request_interval} seconds")
            self.request_interval = min_request_interval

        from fritzinfluxdb.classes.fritzbox import service_definitions

        available_service_ids = service_definitions.get_service_ids()
        self.selected_services = {
            group_name: set(ids)
            for group_name, ids in available_service_ids.items()
        }

        for group_name in SERVICE_GROUP_MODULES:
            option_name = f"services_{group_name}"
            if not config_data.has_option(self.config_section_name, option_name) and \
                    f"{self.config_section_name}_{option_name}".upper() not in os.environ:
                continue

            configured_services = self._parse_service_list(getattr(self, option_name))
            if not configured_services:
                self.parser_error = True
                log.error(f"FritzBox option '{option_name}' must contain 'all', 'none', or service IDs")
            elif configured_services == {"all"}:
                self.selected_services[group_name] = set(available_service_ids[group_name])
            elif configured_services == {"none"}:
                self.selected_services[group_name] = set()
            elif "all" in configured_services or "none" in configured_services:
                self.parser_error = True
                log.error(f"FritzBox option '{option_name}' cannot combine 'all' or 'none' with service IDs")
            else:
                unknown_services = configured_services - available_service_ids[group_name]
                if unknown_services:
                    self.parser_error = True
                    log.error(
                        f"Unknown service ID(s) for FritzBox group '{group_name}': "
                        f"{', '.join(sorted(unknown_services))}. "
                        f"Available IDs: {', '.join(sorted(available_service_ids[group_name]))}"
                    )
                else:
                    self.selected_services[group_name] = configured_services

        # validate data
        for key in ["username", "password"]:
            if getattr(self, key) is None or len(getattr(self, key)) == 0:
                self.parser_error = True
                log.error(f"FritzBox {key} not defined")

        # noinspection PyBroadException
        try:
            self.timezone = pytz.timezone(self.timezone)
        except Exception as e:
            log.error(f"Defined FritzBox time zone '{self.timezone}' is invalid/unknown")
            self.parser_error = True

        # set TR-069 TLS port if undefined
        if self.tls_enabled is True and self.port == self.__class__.port.get("default"):
            self.port += 443

    @staticmethod
    def _parse_service_list(value):
        return {
            service.strip().lower()
            for service in value.split(",")
            if service.strip()
        }

    @property
    def fw_version(self):
        return self._fw_version

    @fw_version.setter
    def fw_version(self, version):

        # noinspection PyBroadException
        try:
            _, major, minor = f"{version}".split(".")
            self._fw_version = f"{int(major)}.{int(minor)}"
        except Exception:
            pass
