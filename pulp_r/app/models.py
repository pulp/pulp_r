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

class CRANPackage(Content):
    """
    The "cran" content type representing a CRAN R package.
    """
    TYPE = "cran"

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

class CRANPublication(Publication):
    """
    A Publication for CRANContent.
    """
    TYPE = "cran"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

class CRANRemote(Remote):
    """
    A Remote for CRANContent.
    """
    TYPE = "cran"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

class CRANRepository(Repository):
    """
    A Repository for CRANContent.
    """
    TYPE = "cran"
    CONTENT_TYPES = [CRANPackage]

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

class CRANDistribution(Distribution):
    """
    A Distribution for CRANContent.
    """
    TYPE = "cran"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"