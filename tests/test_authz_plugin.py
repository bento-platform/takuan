from transcriptomics_data_service.authz.plugin import import_module_from_path


def test_import_authz_plugin_disabled():
    config = lambda: None
    config.bento_authz_enabled = False
    authz_plugin = import_module_from_path("", config)
    assert authz_plugin == None
