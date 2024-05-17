import json
import logging
import tarfile
from gettext import gettext as _

from pulpcore.plugin.models import Artifact, ProgressReport, Remote, Repository
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
)
from asgiref.sync import sync_to_async
import asyncio

from pulp_r.app.models import RPackage, RRemote

log = logging.getLogger(__name__)


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

        # Use sync_to_async to handle synchronous operations in an async context
        await sync_to_async(self.parse_and_report_packages)(result.path)

    def parse_and_report_packages(self, packages_path):
        """
        Synchronously parse packages and report progress.

        Args:
            packages_path (str): Path to the packages file
        """
        with ProgressReport(message='Parsing R metadata', code='parsing.metadata') as pb:
            pb.total = len(list(self.parse_packages_file(packages_path)))
            pb.done = pb.total

            for entry in self.parse_packages_file(packages_path):
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
                artifact = Artifact()
                da = DeclarativeArtifact(
                    artifact,
                    entry['file_url'],
                    entry['file_name'],
                    self.remote,
                    deferred_download=self.deferred_download,
                )
                dc = DeclarativeContent(content=package, d_artifacts=[da])
                # Run the async put method in the event loop
                asyncio.run_coroutine_threadsafe(self.put(dc), asyncio.get_event_loop())

    def parse_packages_file(self, path):
        """
        Parse the PACKAGES file containing R package metadata.

        Args:
            path: Path to the PACKAGES file
        """
        with tarfile.open(path, "r:gz") as tar:
            with tar.extractfile('./PACKAGES') as packages_file:
                packages_info = packages_file.read().decode('utf-8')

        # Parse the PACKAGES file into individual package entries
        packages = packages_info.strip().split('\n\n')
        for package in packages:
            entry = {}
            for line in package.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    entry[key] = value.strip()
            entry['file_url'] = f"{self.remote.url}/src/contrib/{entry['Package']}_{entry['Version']}.tar.gz"
            entry['file_name'] = f"{entry['Package']}_{entry['Version']}.tar.gz"
            yield entry

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
