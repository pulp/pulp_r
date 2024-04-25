"""
Check `Plugin Writer's Guide`_ for more details.

.. _Plugin Writer's Guide:
    https://docs.pulpproject.org/pulpcore/plugins/plugin-writer/index.html
"""

from django.db import transaction
from drf_spectacular.utils import extend_schema
from pulpcore.plugin import viewsets as core
from pulpcore.plugin.actions import ModifyRepositoryActionMixin
from pulpcore.plugin.models import ContentArtifact
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)
from pulpcore.plugin.tasking import dispatch
from pulpcore.plugin.viewsets import RemoteFilter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models, serializers, tasks


class CRANPackageFilter(core.ContentFilter):
    """
    FilterSet for CRANPackage.
    """

    class Meta:
        model = models.CRANPackage
        fields = [
            'name',
            'version',
            'license',
        ]


class CRANPackageViewSet(core.ContentViewSet):
    """
    A ViewSet for CRANPackage.
    """

    endpoint_name = 'packages'
    queryset = models.CRANPackage.objects.all()
    serializer_class = serializers.CRANPackageSerializer
    filterset_class = CRANPackageFilter

    @transaction.atomic
    def create(self, request):
        """
        Perform bookkeeping when saving Content.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artifact = serializer.validated_data.pop('_artifact')
        content = serializer.save(file=artifact)

        if content.pk:
            ContentArtifact.objects.create(
                artifact=artifact,
                content=content,
                relative_path=content.name + '_' + content.version + '.tar.gz'
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CRANRemoteFilter(RemoteFilter):
    """
    A FilterSet for CRANRemote.
    """

    class Meta:
        model = models.CRANRemote
        fields = [
            'name',
            'url',
        ]


class CRANRemoteViewSet(core.RemoteViewSet):
    """
    A ViewSet for CRANRemote.
    """

    endpoint_name = 'cran'
    queryset = models.CRANRemote.objects.all()
    serializer_class = serializers.CRANRemoteSerializer
    filterset_class = CRANRemoteFilter
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        """
        Create a new remote.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CRANRepositoryViewSet(core.RepositoryViewSet, ModifyRepositoryActionMixin):
    """
    A ViewSet for CRANRepository.
    """

    endpoint_name = 'cran'
    queryset = models.CRANRepository.objects.all()
    serializer_class = serializers.CRANRepositorySerializer

    @extend_schema(
        description="Trigger an asynchronous task to sync content.",
        summary="Sync from remote",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Dispatches a sync task.
        """
        repository = self.get_object()
        serializer = RepositorySyncURLSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        remote = serializer.validated_data.get('remote')
        mirror = serializer.validated_data.get('mirror')

        result = dispatch(
            tasks.synchronize,
            [repository, remote],
            kwargs={
                'remote_pk': str(remote.pk),
                'repository_pk': str(repository.pk),
                'mirror': mirror,
            },
        )
        return core.OperationPostponedResponse(result, request)


class CRANRepositoryVersionViewSet(core.RepositoryVersionViewSet):
    """
    A ViewSet for a CRANRepositoryVersion represents a single repository version.
    """

    parent_viewset = CRANRepositoryViewSet


class CRANPublicationViewSet(core.PublicationViewSet):
    """
    A ViewSet for CRANPublication.
    """

    endpoint_name = 'cran'
    queryset = models.CRANPublication.objects.exclude(complete=False)
    serializer_class = serializers.CRANPublicationSerializer

    @extend_schema(
        description="Trigger an asynchronous task to publish content",
        responses={202: AsyncOperationResponseSerializer},
    )
    def create(self, request):
        """
        Publishes a repository.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repository_version = serializer.validated_data.get('repository_version')

        result = dispatch(
            tasks.publish,
            [repository_version.repository],
            kwargs={'repository_version_pk': str(repository_version.pk)},
        )
        return core.OperationPostponedResponse(result, request)


class CRANDistributionViewSet(core.DistributionViewSet):
    """
    A ViewSet for CRANDistribution.
    """

    endpoint_name = 'cran'
    queryset = models.CRANDistribution.objects.all()
    serializer_class = serializers.CRANDistributionSerializer