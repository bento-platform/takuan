from transcriptomics_data_service.authz.plugin import import_module_from_path


class AuthzDisabled:
    bento_authz_enabled = False


def test_import_authz_plugin_disabled():
    authz_plugin = import_module_from_path("", AuthzDisabled())
    assert authz_plugin is None
