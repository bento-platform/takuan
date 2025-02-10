import pytest
from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.authz.plugin import import_module_from_path


class AuthzDisabled:
    authz_enabled = False

@pytest.mark.asyncio
async def test_import_authz_plugin_disabled():
    authz_plugin: BaseAuthzMiddleware = import_module_from_path("", AuthzDisabled())
    try:
        await authz_plugin.dispatch(None, None)
        assert False
    except NotImplementedError:
        # Expect an NotImplementedError from BaseAuthzMiddleware
        assert True
