"""
Check `Plugin Writer's Guide`_ for more details.

.. _Plugin Writer's Guide:
    https://docs.pulpproject.org/pulpcore/plugins/plugin-writer/index.html
"""

from gettext import gettext as _

from pulpcore.plugin import serializers as platform
from rest_framework import serializers

from . import models


class CRANPackageSerializer(platform.SingleArtifactContentSerializer):
    """
    A Serializer for CRANPackage.
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
        model = models.CRANPackage


class CRANRemoteSerializer(platform.RemoteSerializer):
    """
    A Serializer for CRANRemote.
    """

    policy = serializers.ChoiceField(
        help_text=_("The policy to use when downloading content. The possible values include: "
                    "'immediate', 'on_demand', and 'streamed'. 'immediate' is the default."),
        choices=models.Remote.POLICY_CHOICES,
        default=models.Remote.IMMEDIATE
    )

    class Meta:
        fields = platform.RemoteSerializer.Meta.fields
        model = models.CRANRemote


class CRANRepositorySerializer(platform.RepositorySerializer):
    """
    A Serializer for CRANRepository.
    """

    class Meta:
        fields = platform.RepositorySerializer.Meta.fields
        model = models.CRANRepository


class CRANPublicationSerializer(platform.PublicationSerializer):
    """
    A Serializer for CRANPublication.
    """

    class Meta:
        fields = platform.PublicationSerializer.Meta.fields
        model = models.CRANPublication


class CRANDistributionSerializer(platform.DistributionSerializer):
    """
    A Serializer for CRANDistribution.
    """

    publication = platform.DetailRelatedField(
        required=False,
        help_text=_("Publication to be served"),
        view_name_pattern=r"publications(-.*/.*)?-detail",
        queryset=models.Publication.objects.exclude(complete=False),
        allow_null=True,
    )

    class Meta:
        fields = platform.DistributionSerializer.Meta.fields + ("publication",)
        model = models.CRANDistribution