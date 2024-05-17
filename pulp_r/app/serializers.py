"""
Check `Plugin Writer's Guide`_ for more details.

.. _Plugin Writer's Guide:
    https://docs.pulpproject.org/pulpcore/plugins/plugin-writer/index.html
"""

import logging
from gettext import gettext as _

from pulpcore.plugin import serializers as platform
from rest_framework import serializers

from . import models

logger = logging.getLogger(__name__)


class RPackageSerializer(platform.SingleArtifactContentSerializer):
    """
    A Serializer for RPackage.
    """

    name = serializers.CharField(help_text=_("The name of the package"))
    version = serializers.CharField(help_text=_("The version of the package"))
    summary = serializers.CharField(help_text=_("A brief summary of the package"))
    description = serializers.CharField(help_text=_("A longer description of the package"))
    license = serializers.CharField(help_text=_("The license of the package"))
    url = serializers.CharField(help_text=_("The URL of the package homepage"))
    depends = serializers.JSONField(help_text=_("A list of package dependencies"))
    imports = serializers.JSONField(help_text=_("A list of imported packages"))
    suggests = serializers.JSONField(help_text=_("A list of suggested packages"))
    requires = serializers.JSONField(help_text=_("A list of required packages"))

    class Meta:
        fields = platform.SingleArtifactContentSerializer.Meta.fields + (
            'name', 'version', 'summary', 'description', 'license', 'url',
            'depends', 'imports', 'suggests', 'requires'
        )
        model = models.RPackage


class RRemoteSerializer(platform.RemoteSerializer):
    """
    A Serializer for RRemote.
    """

    policy = serializers.ChoiceField(
        help_text=_("The policy to use when downloading content. The possible values include: "
                    "'immediate', 'on_demand', and 'streamed'. 'immediate' is the default."),
        choices=models.Remote.POLICY_CHOICES,
        default=models.Remote.IMMEDIATE
    )

    class Meta:
        fields = platform.RemoteSerializer.Meta.fields
        model = models.RRemote


class RRepositorySerializer(platform.RepositorySerializer):
    """
    A Serializer for RRepository.
    """

    class Meta:
        fields = platform.RepositorySerializer.Meta.fields
        model = models.RRepository

class RPublicationSerializer(platform.PublicationSerializer):
    """
    A Serializer for RPublication.
    """

    repository_version = serializers.CharField(
        help_text=_("Repository Version to be published"),
        required=True,
        label=_("Repository Version"),
        write_only=True,
    )

    class Meta:
        fields = platform.PublicationSerializer.Meta.fields
        model = models.RPublication


class RDistributionSerializer(platform.DistributionSerializer):
    """
    A Serializer for RDistribution.
    """

    publication = platform.DetailRelatedField(
        required=False,
        help_text=_("Publication to be served"),
        view_name_pattern=r"publications(-.*/.*)?-detail",
        queryset=models.RPublication.objects.exclude(complete=False),
        allow_null=True,
    )

    class Meta:
        fields = platform.DistributionSerializer.Meta.fields + ("publication",)
        model = models.RDistribution