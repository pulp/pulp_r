import gzip
import logging
import os
import tempfile
from gettext import gettext as _

from django.core.files import File
from pulpcore.plugin.models import (
    PublishedArtifact,
    PublishedMetadata,
    RepositoryVersion,
)

from pulp_r.app.models import RPackageRepositoryVersion, RPublication

log = logging.getLogger(__name__)

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

    with tempfile.TemporaryDirectory() as temp_dir:
        with RPublication.create(repository_version) as publication:
            # Write package artifacts to the file system
            for content in repository_version.content:
                for content_artifact in content.contentartifact_set.all():
                    published_artifact = PublishedArtifact(
                        relative_path=content_artifact.relative_path,
                        publication=publication,
                        content_artifact=content_artifact
                    )
                    published_artifact.save()

            # Write metadata files to the file system
            metadata_files = []

            # Write PACKAGES file
            packages_path = os.path.join(temp_dir, 'PACKAGES')
            with open(packages_path, 'w') as packages_file:
                for package_relation in RPackageRepositoryVersion.objects.filter(repository_version=repository_version):
                    package = package_relation.package
                    packages_file.write(generate_package_metadata(package))
                    packages_file.write('\n\n')
            metadata_files.append(packages_path)

            # Write PACKAGES.gz file
            packages_gz_path = os.path.join(temp_dir, 'PACKAGES.gz')
            with gzip.open(packages_gz_path, 'wb') as packages_gz_file:
                with open(packages_path, 'rb') as packages_file:
                    packages_gz_file.write(packages_file.read())
            metadata_files.append(packages_gz_path)

            # Write other metadata files (e.g., PACKAGES.rds, PACKAGES.json) if needed

            # Add metadata files to the publication using create_from_file method
            for metadata_file in metadata_files:
                with open(metadata_file, 'rb') as file:
                    PublishedMetadata.create_from_file(
                        file=File(file),
                        publication=publication,
                        relative_path=os.path.basename(metadata_file)
                    )

    log.info(_("Publication: {publication} created").format(publication=publication.pk))


def generate_package_metadata(package):
    """
    Generate the metadata string for a R package.

    Args:
        package (RPackage): The R package object.
    """
    metadata = [
        f"Package: {package.name}",
        f"Version: {package.version}",
        f"Title: {package.summary}",
        f"Description: {package.description}",
        f"License: {package.license}",
        f"URL: {package.url}",
        f"Depends: {', '.join(dep['package'] for dep in package.depends)}",
        f"Imports: {', '.join(dep['package'] for dep in package.imports)}",
        f"Suggests: {', '.join(dep['package'] for dep in package.suggests)}",
        f"Requires: {', '.join(dep['package'] for dep in package.requires)}",
    ]
    return '\n'.join(metadata)
