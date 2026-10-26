# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2023 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

import importlib

from fritzinfluxdb.classes.fritzbox.service_groups import SERVICE_GROUP_MODULES

tr069_services = list()
lua_services = list()

_service_groups = dict()


def _load_service_group(group_name, module_name):
    tr069_start = len(tr069_services)
    lua_start = len(lua_services)

    importlib.import_module(f"{__name__}.{module_name}")

    _service_groups[group_name] = (
        tr069_services[tr069_start:],
        lua_services[lua_start:]
    )


for _group_name, _module_name in SERVICE_GROUP_MODULES.items():
    _load_service_group(_group_name, _module_name)


def get_services(selected_groups):
    """
    Return TR-069 and Lua service definitions for the selected groups.
    """

    selected = set(selected_groups)
    selected_tr069_services = list()
    selected_lua_services = list()

    for group_name, (group_tr069_services, group_lua_services) in _service_groups.items():
        if group_name not in selected:
            continue

        selected_tr069_services.extend(group_tr069_services)
        selected_lua_services.extend(group_lua_services)

    return selected_tr069_services, selected_lua_services
