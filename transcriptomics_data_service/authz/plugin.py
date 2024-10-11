import importlib.util
import sys

from fastapi import Depends, Request

__all__ = ["get_request_authorization"]


def import_module_from_path(path):
    spec = importlib.util.spec_from_file_location("authz_plugin", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# TODO find a way to allow plugin writers to specify additional dependencies to be installed

AUTHZ_MODULE_PATH = "/tds/lib/authz.module.py"
authz_plugin = import_module_from_path(AUTHZ_MODULE_PATH)


async def get_request_authorization(req: Request):
    return await authz_plugin.get_current_user_authorization(req)
