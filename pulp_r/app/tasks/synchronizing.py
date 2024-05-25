import asyncio
import gzip
import hashlib
import json
import logging
import os
import shutil
import tempfile
from gettext import gettext as _

import httpx
from asgiref.sync import sync_to_async
from django.db.models import Q
from pulpcore.plugin.models import (
    Artifact,
    ContentArtifact,
    ProgressReport,
    Remote,
    RemoteArtifact,
)
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
)

from pulp_r.app.models import RPackage, RRemote, RRepository

log = logging.getLogger(__name__)

CHUNK_SIZE = 50
MAX_PACKAGES_SYNC = 2000
PACKAGES_SYNC_START = 1500

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
    repository = RRepository.objects.get(pk=repository_pk)

    if not remote.url:
        raise ValueError(_("A remote must have a url specified to synchronize."))

    # Interpret policy to download Artifacts or not
    deferred_download = remote.policy != Remote.IMMEDIATE

    first_stage = RFirstStage(remote, deferred_download)
    # Run pipeline and create a new repository version with the content units associated
    DeclarativeVersion(first_stage, repository, mirror=mirror).create()

async def fetch_and_calculate_checksums(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raises an exception for 4xx/5xx responses

            data = response.content
            if not data:
                log.error(f"No data fetched from {url}")
                return None, 0, None

            # Save to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(data)
            temp_file_path = temp_file.name
            temp_file.close()

            # Calculate all required checksums
            checksums = {
                'sha512': hashlib.sha512(data).hexdigest(),
                'sha384': hashlib.sha384(data).hexdigest(),
                'sha256': hashlib.sha256(data).hexdigest(),
                'sha224': hashlib.sha224(data).hexdigest(),
            }
            return checksums, len(data), temp_file_path
    except httpx.HTTPStatusError as http_err:
        log.error(f"HTTP error occurred while fetching {url}: {http_err}")
    except Exception as err:
        log.error(f"Unexpected error occurred while fetching {url}: {err}")
    return None, 0, None

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
        progress_report = await sync_to_async(ProgressReport.objects.create)(
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
        await sync_to_async(progress_report.save)()

        chunk_size = CHUNK_SIZE
        for i in range(0, len(package_entries), chunk_size):
            chunk = package_entries[i:i + chunk_size]
            tasks = [self.process_package(entry) for entry in chunk]
            await asyncio.gather(*tasks)

    async def process_package(self, entry):
        """
        Process a package entry by fetching its content, calculating checksums, and creating the necessary objects.
        """
        # Fetch checksums, file size, and file path
        checksums, file_size, file_path = await fetch_and_calculate_checksums(entry['file_url'])

        if not checksums or file_size == 0 or not file_path:
            log.error(f"Failed to fetch and calculate checksums for {entry['file_url']}")
            return  # Skip further processing for this entry

        # Check if package already exists
        package, _ = await sync_to_async(RPackage.objects.get_or_create)(
            name=entry['Package'],
            version=entry['Version'],
            defaults={
                'priority': entry.get('Priority', ''),
                'summary': entry.get('Title', ''),
                'description': entry.get('Description', ''),
                'license': entry.get('License', ''),
                'url': entry.get('URL', ''),
                'md5sum': entry.get('MD5sum', ''),
                'needs_compilation': entry.get('NeedsCompilation', 'no') == 'yes',
                'path': entry.get('Path', ''),
                'depends': json.dumps(self.parse_dependencies(entry.get('Depends', ''))),
                'imports': json.dumps(self.parse_dependencies(entry.get('Imports', ''))),
                'suggests': json.dumps(self.parse_dependencies(entry.get('Suggests', ''))),
                'requires': json.dumps(self.parse_dependencies(entry.get('Requires', ''))),
            }
        )

        # Check if artifact already exists
        artifact, _ = await sync_to_async(Artifact.objects.get_or_create)(
            sha256=checksums['sha256'],
            defaults={
                'file': file_path,
                'size': file_size,
                'sha224': checksums['sha224'],
                'sha384': checksums['sha384'],
                'sha512': checksums['sha512'],
            }
        )

        # Check if content artifact already exists
        content_artifact, _ = await sync_to_async(ContentArtifact.objects.get_or_create)(
            content=package,
            artifact=artifact,
            defaults={'relative_path': entry['file_name']}
        )

        await sync_to_async(RemoteArtifact.objects.get_or_create)(
            url=entry['file_url'],
            content_artifact=content_artifact,
            defaults={
                'size': file_size,
                'sha224': checksums['sha224'],
                'sha256': checksums['sha256'],
                'sha384': checksums['sha384'],
                'sha512': checksums['sha512'],
                'remote': self.remote,
            }
        )

        # Create and emit the DeclarativeArtifact and DeclarativeContent
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

        # TODO: Remove temporary limit
        packages = packages[PACKAGES_SYNC_START:MAX_PACKAGES_SYNC]

        package_entries = []
        for package_info in packages:
            entry = {}
            current_key = None
            for line in package_info.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    entry[key] = value.strip()
                    current_key = key
                else:
                    value_line_ends_with_colon = line.endswith(':')
                    if current_key and value_line_ends_with_colon:
                        current_key, value = line.split(':', 1)
                        entry[current_key] = value.strip() if value else ''
                    else:
                        # continue to build the multiline value
                        entry[current_key] += f' {line.strip()}'

            base_url = self.remote.url.replace('/src/contrib/PACKAGES.gz', '')
            entry['file_url'] = f"{base_url}/src/contrib/{entry['Package']}_{entry['Version']}.tar.gz"
            entry['file_name'] = f"{entry['Package']}_{entry['Version']}.tar.gz"
            entry['SHA256'] = entry.get('SHA256', '')
            entry['Depends'] = self.parse_dependencies(entry.get('Depends', ''))
            entry['Imports'] = self.parse_dependencies(entry.get('Imports', ''))
            entry['Suggests'] = self.parse_dependencies(entry.get('Suggests', ''))
            entry['Requires'] = self.parse_dependencies(entry.get('Requires', ''))
            package_entries.append(entry)

        return package_entries

    def parse_dependencies(self, dep_string):
        """
        Parse package dependencies from a comma-separated string.

        Args:
            dep_string: A comma-separated string of dependencies
        """
        if isinstance(dep_string, list):
            return dep_string

        dependencies = []
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