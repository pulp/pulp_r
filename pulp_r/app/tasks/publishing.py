import gzip
import json
import logging
import os
import tempfile
from gettext import gettext as _

from django.db import IntegrityError
from pulpcore.plugin.models import (
    Artifact,
    ContentArtifact,
    PublishedArtifact,
    PublishedMetadata,
    RepositoryVersion,
)

from pulp_r.app.models import MetadataContent, RPublication

log = logging.getLogger(__name__)

def format_dependencies(deps):
    """
    Format dependencies list as a comma-separated string.
    """
    if not deps:
        return ''
    
    # Ensure deps is a list of dictionaries
    if isinstance(deps, str):
        deps = json.loads(deps)
    
    return ', '.join(
        f"{dep.get('package', '')}" + (f" ({dep.get('version', '')})" if 'version' in dep else '')
        for dep in deps
    )

def generate_packages_file_content(repository_version):
    """
    Generate the content for the PACKAGES file based on the repository version.
    """
    packages_content = ""
    content_artifacts = ContentArtifact.objects.filter(
        content__pk__in=repository_version.content.values_list('pk', flat=True)
    )

    for content_artifact in content_artifacts:
        package = content_artifact.content.cast()
        package_entry = (
            f"Package: {package.name}\n"
            f"Version: {package.version}\n"
            f"Depends: {format_dependencies(package.depends)}\n"
            f"Imports: {format_dependencies(package.imports)}\n"
            f"Suggests: {format_dependencies(package.suggests)}\n"
            f"License: {package.license}\n"
            f"MD5sum: {package.md5sum}\n"
            f"NeedsCompilation: {'yes' if package.needs_compilation else 'no'}\n\n"
        )
        packages_content += package_entry

    return packages_content.strip()

def publish(repository_version_pk):
    """
    Create a Publication based on a RepositoryVersion.

    Args:
        repository_version_pk (str): Create a publication from this repository version.
    """
    repository_version = RepositoryVersion.objects.get(pk=repository_version_pk)
    log.info(
        _("Publishing: repository={repo}, version={ver}").format(
            repo=repository_version.repository.name,
            ver=repository_version.number,
        )
    )

    with RPublication.create(repository_version) as publication:
        # Get all content artifacts associated with the repository version
        content_artifacts = ContentArtifact.objects.filter(
            content__pk__in=repository_version.content.values_list('pk', flat=True)
        )

        # Create PublishedArtifacts for each ContentArtifact
        published_artifacts = []
        for content_artifact in content_artifacts:
            # Published Artifacts are served at path: <CONTENT_PATH_PREFIX>/<distribution_path>/<relative_path>
            published_artifact = PublishedArtifact(
                relative_path=content_artifact.relative_path,
                publication=publication,
                content_artifact=content_artifact
            )
            published_artifacts.append(published_artifact)

        # Bulk create the PublishedArtifacts
        PublishedArtifact.objects.bulk_create(published_artifacts)

        # Generate the PACKAGES file content
        packages_content = generate_packages_file_content(repository_version)

        # Save the compressed PACKAGES file
        metadata_file_path = 'PACKAGES'
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                with gzip.open(temp_file.name, 'wb') as gzip_file:
                    gzip_file.write(packages_content.encode('utf-8'))
                temp_file_path = temp_file.name

            with open(temp_file_path, 'rb') as temp_file:
                try:
                    PublishedMetadata.create_from_file(
                        file=temp_file,
                        publication=publication,
                        relative_path=metadata_file_path
                    )
                except IntegrityError:
                    log.warning(
                        f"Duplicate metadata entry for path {metadata_file_path} in publication {publication.pk}, updating existing entry."
                    )
                    existing_metadata = PublishedMetadata.objects.get(
                        publication=publication,
                        relative_path=metadata_file_path
                    )
                    existing_metadata.delete()
                    PublishedMetadata.create_from_file(
                        file=temp_file,
                        publication=publication,
                        relative_path=metadata_file_path
                    )

            # Create a new Artifact for the PACKAGES file
            with open(temp_file_path, 'rb') as temp_file:
                artifact = Artifact.init_and_validate(temp_file_path)
                artifact.save()

            # Create a MetadataContent instance for the PACKAGES file
            content = MetadataContent.objects.create()

            # Create a ContentArtifact that associates the PACKAGES file Artifact with the Content
            content_artifact = ContentArtifact.objects.create(
                artifact=artifact,
                content=content,
                relative_path=metadata_file_path
            )

            # Create a PublishedArtifact for the PACKAGES file
            try:
                PublishedArtifact.objects.create(
                    relative_path=metadata_file_path,
                    publication=publication,
                    content_artifact=content_artifact
                )
            except IntegrityError:
                log.warning(
                    f"Duplicate artifact entry for path {metadata_file_path} in publication {publication.pk}, updating existing entry."
                )
                existing_artifact = PublishedArtifact.objects.get(
                    publication=publication,
                    relative_path=metadata_file_path
                )
                existing_artifact.delete()
                PublishedArtifact.objects.create(
                    relative_path=metadata_file_path,
                    publication=publication,
                    content_artifact=content_artifact
                )

            # Clean up the temporary file
            os.unlink(temp_file_path)
        except Exception as e:
            log.error(f"Error creating PublishedMetadata for {metadata_file_path}: {str(e)}")

    log.info(_("Publication: {publication} created").format(publication=publication.pk))
