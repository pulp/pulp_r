import logging
from gettext import gettext as _

from django.db import transaction
from drf_spectacular.utils import extend_schema
from pulpcore.plugin import viewsets as core
from pulpcore.plugin.actions import ModifyRepositoryActionMixin
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)
from pulpcore.plugin.tasking import dispatch
from pulpcore.plugin.viewsets import RemoteFilter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import models, serializers, tasks

logger = logging.getLogger(__name__)

class RPackageFilter(core.ContentFilter):
    """
    FilterSet for RPackage.
    """

    class Meta:
        model = models.RPackage
        fields = [
            'name',
            'version',
            'license',
        ]


class RPackageViewSet(core.ContentViewSet):
    """
    A ViewSet for RPackage.
    """
    endpoint_name = 'packages'
    queryset = models.RPackage.objects.all()
    serializer_class = serializers.RPackageSerializer
    filterset_class = RPackageFilter
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    @transaction.atomic
    def create(self, request):
        """
        Perform bookkeeping when saving Content.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RRemoteFilter(RemoteFilter):
    """
    A FilterSet for RRemote.
    """

    class Meta:
        model = models.RRemote
        fields = [
            'name',
            'url',
        ]


class RRemoteViewSet(core.RemoteViewSet):
    """
    A ViewSet for RRemote.
    """

    endpoint_name = 'r'
    queryset = models.RRemote.objects.all()
    serializer_class = serializers.RRemoteSerializer
    filterset_class = RRemoteFilter
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def create(self, request, *args, **kwargs):
        """
        Create a new remote.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update a remote.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a remote.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a remote.
        """
        instance = self.get_object()

        # TODO: Perform any necessary checks or cleanup before deleting the remote
        # Check if the remote is associated with any repositories and handle the deletion accordingly

        repositories = instance.repository_set.all()
        if repositories.exists():
            # Handle the case when the remote is associated with repositories
            # You can choose to raise an error, perform cleanup, or take other actions
            raise serializers.ValidationError(
                "Cannot delete the remote as it is associated with repositories."
            )

        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        """
        Perform the update on the instance.
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        Perform the deletion of the instance.
        """
        instance.delete()


class RRepositoryViewSet(core.RepositoryViewSet, ModifyRepositoryActionMixin):
    """
    A ViewSet for RRepository.
    """

    endpoint_name = 'r'
    queryset = models.RRepository.objects.all()
    serializer_class = serializers.RRepositorySerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    @action(detail=True, methods=["post"], serializer_class=serializers.RPackageSerializer)
    def upload_content(self, request, pk):
        repository = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        package = serializer.save()

        # Create a new RepositoryVersion
        with repository.new_version() as new_version:
            # Associate the package with the new RepositoryVersion
            new_version.add_content(models.RPackage.objects.filter(pk=package.pk))

        # Launch the publishing task
        publication_task = dispatch(
            tasks.publish,
            kwargs={'repository_version_pk': str(new_version.pk)}
        )

        return core.OperationPostponedResponse(publication_task, request)
    
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
            kwargs={
                'remote_pk': str(remote.pk),
                'repository_pk': str(repository.pk),
                'mirror': mirror,
            },
        )
        return core.OperationPostponedResponse(result, request)


class RRepositoryVersionViewSet(core.RepositoryVersionViewSet):
    """
    A ViewSet for a RRepositoryVersion represents a single repository version.
    """

    parent_viewset = RRepositoryViewSet


class RPublicationViewSet(core.PublicationViewSet):
    """
    A ViewSet for RPublication.
    """

    endpoint_name = 'r'
    queryset = models.RPublication.objects.exclude(complete=False)
    serializer_class = serializers.RPublicationSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    @extend_schema(
        description="Trigger an asynchronous task to publish content",
        responses={202: AsyncOperationResponseSerializer},
    )
    def create(self, request):
        """
        Publishes a repository.
        """
        logger.info(f"Received POST request to create publication with data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.error(f"Validation error: {e.detail}")
            raise

        repository_version_url = serializer.validated_data.get('repository_version')
        # Extract the pk correctly from the URL
        repository_version_pk = repository_version_url.rstrip('/').split('/')[-3]

        # Correcting the extraction
        version_number = repository_version_url.rstrip('/').split('/')[-1]

        try:
            repository_version = models.RepositoryVersion.objects.get(
                repository_id=repository_version_pk, number=version_number
            )
        except models.RepositoryVersion.DoesNotExist:
            raise ValidationError(f"RepositoryVersion with pk={repository_version_pk} and number={version_number} does not exist")

        logger.info(f"Retrieved repository version: {repository_version}")

        result = dispatch(
            tasks.publish,
            kwargs={'repository_version_pk': str(repository_version.pk)}
        )
        return core.OperationPostponedResponse(result, request)


class RDistributionViewSet(core.DistributionViewSet):
    """
    A ViewSet for RDistribution.
    """
    endpoint_name = 'r'
    queryset = models.RDistribution.objects.all()
    serializer_class = serializers.RDistributionSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating distribution: {str(e)}")
            raise