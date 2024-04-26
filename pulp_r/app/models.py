"""
Check `Plugin Writer's Guide`_ for more details.

.. _Plugin Writer's Guide:
    https://docs.pulpproject.org/pulpcore/plugins/plugin-writer/index.html
"""

from logging import getLogger

from django.db import models
from pulpcore.plugin.models import (
    Content,
    ContentArtifact,
    Distribution,
    Publication,
    Remote,
    Repository,
)

logger = getLogger(__name__)

class RPackage(Content):
    """
    The "r" content type representing an R package.
    """
    TYPE = "r"

    name = models.TextField()
    version = models.TextField()
    summary = models.TextField()
    description = models.TextField()
    license = models.TextField()
    url = models.TextField()
    depends = models.JSONField(default=list)
    imports = models.JSONField(default=list)
    suggests = models.JSONField(default=list)
    requires = models.JSONField(default=list)

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ['name', 'version']

class RPublication(Publication):
    """
    A Publication for RContent.
    """
    TYPE = "r"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

class RRemote(Remote):
    """
    A Remote for RContent.
    """
    TYPE = "r"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

class RRepository(Repository):
    """
    A Repository for RContent.
    """
    TYPE = "r"
    CONTENT_TYPES = [RPackage]

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

class RDistribution(Distribution):
    """
    A Distribution for RContent.
    """
    TYPE = "r"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"