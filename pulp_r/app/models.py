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
    PublishedMetadata,
    Remote,
    RemoteArtifact,
    Repository,
    RepositoryContent,
    RepositoryVersion,
)

logger = getLogger(__name__)

class RPackage(Content):
    """
    The "r" content type representing an R package.
    """
    TYPE = "r"

    name = models.TextField()
    version = models.TextField()
    priority = models.TextField(default='')  # Add priority field
    summary = models.TextField()
    description = models.TextField()
    license = models.TextField()
    url = models.TextField()
    md5sum = models.TextField(default='')  # Add MD5sum field
    needs_compilation = models.BooleanField(default=False)  # Add NeedsCompilation field
    path = models.TextField(default='')  # Add Path field
    depends = models.JSONField(default=list)
    imports = models.JSONField(default=list)
    suggests = models.JSONField(default=list)
    requires = models.JSONField(default=list)

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ['name', 'version']

    def __str__(self):
        return self.name

class RPackageRepositoryVersion(models.Model):
    """
    Represents the relationship between an RPackage and a RepositoryVersion.
    """
    package = models.ForeignKey(RPackage, on_delete=models.CASCADE)
    repository_version = models.ForeignKey(RepositoryVersion, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('package', 'repository_version')
        default_related_name = "%(app_label)s_%(model_name)s"

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

class RPublishedMetadata(PublishedMetadata):
    """
    PublishedMetadata for RContent.
    """
    content = models.TextField(blank=True)

    class Meta:
        default_related_name = "r_published_metadata"
        
class MetadataContent(Content):
    """
    A custom Content subclass for the PACKAGES metadata file.
    """
    TYPE = 'metadata'
    
    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"