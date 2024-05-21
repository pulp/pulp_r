import asyncio
import gzip
import json
import logging
import os
import shutil
from gettext import gettext as _

import httpx
from pulpcore.plugin.models import Artifact, ProgressReport, Remote, Repository
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
)

from pulp_r.app.models import RPackage, RRemote

log = logging.getLogger(__name__)

CHUNK_SIZE = 50

def synchronize(remote_pk, repository_pk, mirror):
    """
    Sync content from the remote repository.

    Create a new version of the repository that is synchronized with the remote.

    Args:
        remote_pk (str): The remote PK.
        repository_pk (str): The repository PK.
        mirror (bool): True for mirror mode, False for additive.

    Raises:
        ValueError: If the remote does not specify a URL to sync
    """
    remote = RRemote.objects.get(pk=remote_pk)
    repository = Repository.objects.get(pk=repository_pk)

    if not remote.url:
        raise ValueError(_("A remote must have a url specified to synchronize."))

    # Interpret policy to download Artifacts or not
    deferred_download = remote.policy != Remote.IMMEDIATE

    first_stage = RFirstStage(remote, deferred_download)
    DeclarativeVersion(first_stage, repository, mirror=mirror).create()


class RFirstStage(Stage):
    """
    The first stage of a pulp_r sync pipeline.
    """

    def __init__(self, remote, deferred_download):
        """
        The first stage of a pulp_r sync pipeline.

        Args:
            remote (FileRemote): The remote data to be used when syncing
            deferred_download (bool): if True the downloading will not happen now. If False, it will happen immediately.
        """
        super().__init__()
        self.remote = remote
        self.deferred_download = deferred_download

    async def run(self):
        """
        Build and emit `DeclarativeContent` from the PACKAGES metadata.

        Args:
            in_q (asyncio.Queue): Unused because the first stage doesn't read from an input queue.
            out_q (asyncio.Queue): The out_q to send `DeclarativeContent` objects to
        """
        downloader = self.remote.get_downloader(url=self.remote.url)
        result = await downloader.run()

        # Directly call the parse_packages_file method since it's already asynchronous
        package_entries = await self.parse_packages_file(result.path)

        # Use an async context to handle the tasks
        await self.parse_and_report_packages(package_entries)

    async def parse_and_report_packages(self, package_entries):
        """
        Asynchronously parse packages and report progress.

        Args:
            package_entries (list): List of package entries
        """
        # Create ProgressReport in a synchronous context
        progress_report = ProgressReport.objects.create(
            message='Parsing R metadata', code='parsing.metadata'
        )

        await self.update_progress_report(progress_report, package_entries)

    async def update_progress_report(self, progress_report, package_entries):
        """
        Update the progress report and process packages asynchronously.

        Args:
            progress_report: ProgressReport instance
            package_entries (list): List of package entries
        """
        progress_report.total = len(package_entries)
        progress_report.done = progress_report.total
        progress_report.save()

        chunk_size = CHUNK_SIZE
        for i in range(0, len(package_entries), chunk_size):
            chunk = package_entries[i:i + chunk_size]
            tasks = [self.process_package(entry) for entry in chunk]
            await asyncio.gather(*tasks)

    async def process_package(self, entry):
        package = RPackage(
            name=entry['Package'],
            version=entry['Version'],
            summary=entry.get('Title', ''),
            description=entry.get('Description', ''),
            license=entry.get('License', ''),
            url=entry.get('URL', ''),
            depends=json.dumps(self.parse_dependencies(entry, 'Depends')),
            imports=json.dumps(self.parse_dependencies(entry, 'Imports')),
            suggests=json.dumps(self.parse_dependencies(entry, 'Suggests')),
            requires=json.dumps(self.parse_dependencies(entry, 'Requires')),
        )

        artifact = Artifact(size=entry['file_size'])
        da = DeclarativeArtifact(
            artifact=artifact,
            url=entry['file_url'],
            relative_path=entry['file_name'],
            remote=self.remote,
            deferred_download=self.deferred_download,
        )
        dc = DeclarativeContent(content=package, d_artifacts=[da])
        await self.put(dc)

    async def parse_packages_file(self, path):
        """
        Parse the PACKAGES file containing R package metadata.

        Args:
            path: Path to the PACKAGES file
        """
        # Check if the file is a valid gzip file
        try:
            with gzip.open(path, 'rt') as f:
                f.read(1)
        except OSError as e:
            log.error(f"Error reading gzip file at {path}: {e}")
            raise

        # Decompress the gzip file
        decompressed_path = path + ".decompressed"
        with gzip.open(path, 'rb') as f_in:
            with open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Parse the decompressed PACKAGES file
        with open(decompressed_path, 'rt') as f:
            packages_info = f.read()

        os.remove(decompressed_path)  # Clean up the decompressed file

        # Parse the PACKAGES file into individual package entries
        packages = packages_info.strip().split('\n\n')
        package_entries = []
        for package in packages:
            entry = {}
            for line in package.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    entry[key] = value.strip()
            base_url = self.remote.url.replace('/src/contrib/PACKAGES.gz', '')
            entry['file_url'] = f"{base_url}/src/contrib/{entry['Package']}_{entry['Version']}.tar.gz"
            entry['file_name'] = f"{entry['Package']}_{entry['Version']}.tar.gz"
            entry['file_size'] = await self.get_file_size(entry['file_url'])
            
            package_entries.append(entry)

        return package_entries

    async def get_file_size(self, url):
        """
        Get the file size of a remote package file.

        Args:
            url: The URL of the package file
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.head(url)
                response.raise_for_status()
                file_size = int(response.headers.get('Content-Length', 0))
                return file_size
            except httpx.RequestError as e:
                log.error(f"Error retrieving file size for {url}: {e}")
                return 0

    def parse_dependencies(self, entry, dep_type):
        """
        Parse package dependencies from a R metadata entry.

        Args:
            entry: A dictionary representing a R package metadata entry
            dep_type: The type of dependency to parse (Depends, Imports, Suggests, Requires)
        """
        dependencies = []
        dep_string = entry.get(dep_type, '')
        if dep_string:
            for dep in dep_string.split(','):
                dep = dep.strip()
                if '(' in dep:
                    pkg, version = dep.split('(')
                    version = version.rstrip(')')
                    dependencies.append({'package': pkg.strip(), 'version': version.strip()})
                else:
                    dependencies.append({'package': dep.strip()})
        return dependencies


def create_remote(data):
    """
    Create a new remote.
    """
    remote = RRemote.objects.create(**data)
    return remote


def update_remote(instance, data):
    """
    Update an existing remote.
    """
    for attr, value in data.items():
        setattr(instance, attr, value)
    instance.save()
    return instance


def delete_remote(instance):
    """
    Delete an existing remote.
    """
    instance.delete()
    return instance