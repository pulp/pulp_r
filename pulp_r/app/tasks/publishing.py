import logging
import os
import tempfile
from gettext import gettext as _

from django.db import IntegrityError
from pulpcore.plugin.models import (
    ContentArtifact,
    PublishedArtifact,
    PublishedMetadata,
    RepositoryVersion,
)

from pulp_r.app.models import RPublication

log = logging.getLogger(__name__)

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
            f"Priority: {package.priority}\n"
            f"Title: {package.summary}\n"
            f"Description: {package.description}\n"
            f"License: {package.license}\n"
            f"URL: {package.url}\n"
            f"MD5sum: {package.md5sum}\n"
            f"NeedsCompilation: {package.needs_compilation}\n"
            f"File: {content_artifact.relative_path}\n"
            f"SHA256: {content_artifact.artifact.sha256}\n\n"
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

        # Save the PACKAGES file as PublishedMetadata
        packages_file_path = 'src/contrib/PACKAGES'
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(packages_content.encode('utf-8'))
                temp_file_path = temp_file.name

            with open(temp_file_path, 'rb') as temp_file:
                try:
                    PublishedMetadata.create_from_file(
                        file=temp_file,
                        publication=publication,
                        relative_path=packages_file_path
                    )
                except IntegrityError:
                    log.warning(
                        f"Duplicate metadata entry for path {packages_file_path} in publication {publication.pk}, updating existing entry."
                    )
                    existing_metadata = PublishedMetadata.objects.get(
                        publication=publication,
                        relative_path=packages_file_path
                    )
                    existing_metadata.delete()
                    PublishedMetadata.create_from_file(
                        file=temp_file,
                        publication=publication,
                        relative_path=packages_file_path
                    )

            # Clean up the temporary file
            os.unlink(temp_file_path)
        except Exception as e:
            log.error(f"Error creating PublishedMetadata for {packages_file_path}: {str(e)}")

        # Generate PublishedMetadata files from PublishedArtifacts
        for published_artifact in published_artifacts:
            try:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(published_artifact.content_artifact.artifact.file.read())
                    temp_file_path = temp_file.name

                with open(temp_file_path, 'rb') as temp_file:
                    try:
                        PublishedMetadata.create_from_file(
                            file=temp_file,
                            publication=publication,
                            relative_path=published_artifact.relative_path
                        )
                    except IntegrityError:
                        log.warning(
                            f"Duplicate metadata entry for path {published_artifact.relative_path} in publication {publication.pk}, updating existing entry."
                        )
                        existing_metadata = PublishedMetadata.objects.get(
                            publication=publication,
                            relative_path=published_artifact.relative_path
                        )
                        existing_metadata.delete()
                        PublishedMetadata.create_from_file(
                            file=temp_file,
                            publication=publication,
                            relative_path=published_artifact.relative_path
                        )

                # Clean up the temporary file
                os.unlink(temp_file_path)
            except Exception as e:
                log.error(f"Error creating PublishedMetadata for {published_artifact.relative_path}: {str(e)}")

    log.info(_("Publication: {publication} created").format(publication=publication.pk))
