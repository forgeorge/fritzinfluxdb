# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import importlib

from fritzinfluxdb.classes.fritzbox.service_groups import SERVICE_GROUP_MODULES, service_id

tr069_services = list()
lua_services = list()

_service_groups = dict()


def _load_service_group(group_name, module_name):
    tr069_start = len(tr069_services)
    lua_start = len(lua_services)

    importlib.import_module(f"{__name__}.{module_name}")

    for service in tr069_services[tr069_start:] + lua_services[lua_start:]:
        service["service_id"] = service_id(service["name"])

    _service_groups[group_name] = (
        tr069_services[tr069_start:],
        lua_services[lua_start:]
    )


for _group_name, _module_name in SERVICE_GROUP_MODULES.items():
    _load_service_group(_group_name, _module_name)


def get_service_ids():
    """
    Return the available configuration identifiers for each service group.
    """

    return {
        group_name: {
            service["service_id"]
            for service in group_tr069_services + group_lua_services
        }
        for group_name, (group_tr069_services, group_lua_services) in _service_groups.items()
    }


def get_services(selected_services):
    """
    Return TR-069 and Lua service definitions selected by group and service ID.
    """

    selected_tr069_services = list()
    selected_lua_services = list()

    for group_name, (group_tr069_services, group_lua_services) in _service_groups.items():
        selected_ids = selected_services[group_name]
        selected_tr069_services.extend(
            service for service in group_tr069_services if service["service_id"] in selected_ids
        )
        selected_lua_services.extend(
            service for service in group_lua_services if service["service_id"] in selected_ids
        )

    return selected_tr069_services, selected_lua_services
