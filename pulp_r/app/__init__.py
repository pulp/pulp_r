from pulpcore.plugin import PulpPluginAppConfig


class PulpCranPluginAppConfig(PulpPluginAppConfig):
    """Entry point for the cran plugin."""

    name = "pulp_r.app"
    label = "cran"
    version = "0.1.0a1.dev"
    python_package_name = "pulp_r"
