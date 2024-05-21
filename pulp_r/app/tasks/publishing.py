import gzip
import logging
import os
import tempfile
from gettext import gettext as _

from pulpcore.plugin.models import (
    PublishedArtifact,
    RepositoryVersion,
)

from pulp_r.app.models import (
    RPackageRepositoryVersion,
    RPublication,
    RPublishedMetadata,
)

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

        # Generate and store metadata files
        # PACKAGES file
        try:
            packages_content = generate_packages_content(repository_version)
            log.info(f"Generated PACKAGES content:\n{packages_content}")
            RPublishedMetadata.objects.create(
                publication=publication,
                relative_path='src/contrib/PACKAGES',
                content=packages_content
            )
        except Exception as e:
            log.error(f"Error generating PACKAGES content: {str(e)}")
            raise

        # PACKAGES.gz file
        try:
            packages_gz_content = gzip.compress(packages_content.encode('utf-8'))
            RPublishedMetadata.objects.create(
                publication=publication,
                relative_path='src/contrib/PACKAGES.gz',
                content=packages_gz_content
            )
        except Exception as e:
            log.error(f"Error generating PACKAGES.gz content: {str(e)}")
            raise

        # TODO: Generate and store other metadata files (e.g., PACKAGES.rds, PACKAGES.json) if needed

    log.info(_("Publication: {publication} created").format(publication=publication.pk))

def generate_packages_content(repository_version):
    """
    Generate the content of the PACKAGES file for a repository version.

    Args:
        repository_version (RepositoryVersion): The repository version.

    Returns:
        str: The generated PACKAGES content.
    """
    package_relations = RPackageRepositoryVersion.objects.filter(repository_version=repository_version)
    log.info(f"Found {package_relations.count()} package relations for repository version {repository_version.pk}")

    packages_content = []
    for package_relation in package_relations:
        package = package_relation.package
        log.info(f"Processing package: {package.name}")
        package_metadata = generate_package_metadata(package)
        log.info(f"Generated package metadata:\n{package_metadata}")
        packages_content.append(package_metadata)

    return '\n\n'.join(packages_content)

def generate_package_metadata(package):
    """
    Generate the metadata string for an R package.

    Args:
        package (RPackage): The R package object.
    """
    metadata = [
        f"Package: {package.name}",
        f"Version: {package.version}",
        f"Priority: {package.priority}",  # Add priority field
        f"Depends: {', '.join(dep['package'] for dep in package.depends)}",
        f"Suggests: {', '.join(dep['package'] for dep in package.suggests)}",
        f"License: {package.license}",
        f"MD5sum: {package.md5sum}",  # Add MD5sum field
        f"NeedsCompilation: {'yes' if package.needs_compilation else 'no'}",  # Add NeedsCompilation field
        f"Path: {package.path}",  # Add Path field
        f"Title: {package.summary}",
        f"Description: {package.description}",
        f"URL: {package.url}",
        f"Imports: {', '.join(dep['package'] for dep in package.imports)}",
        f"Requires: {', '.join(dep['package'] for dep in package.requires)}",
    ]
    return '\n'.join(metadata)