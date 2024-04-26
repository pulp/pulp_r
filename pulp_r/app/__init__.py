from pulpcore.plugin import PulpPluginAppConfig


class PulpRPluginAppConfig(PulpPluginAppConfig):
    """Entry point for the pulp_r plugin."""

    name = "pulp_r.app"
    label = "r"
    version = "0.1.0a1.dev"
    python_package_name = "pulp-r"
