"""Utilities for tests for the r plugin."""

from functools import partial
from tempfile import NamedTemporaryFile
from unittest import SkipTest

import requests
from pulp_smash import api, config, selectors
from pulp_smash.pulp3.utils import (
    gen_remote,
    gen_repo,
    get_content,
    require_pulp_3,
    require_pulp_plugins,
    sync,
)
from pulpcore.client.pulp_r import ApiClient as RApiClient
from pulpcore.client.pulpcore import (
    ApiClient as CoreApiClient,
)
from pulpcore.client.pulpcore import (
    ArtifactsApi,
    TasksApi,
)

from pulp_r.tests.functional.constants import (
    R_CONTENT_NAME,
    R_CONTENT_PATH,
    R_FIXTURE_URL,
    R_PUBLICATION_PATH,
    R_REMOTE_PATH,
    R_REPO_PATH,
    R_URL,
)

cfg = config.get_config()
configuration = cfg.get_bindings_config()


def set_up_module():
    """Skip tests Pulp 3 isn't under test or if pulp_r isn't installed."""
    require_pulp_3(SkipTest)
    require_pulp_plugins({"r"}, SkipTest)


def gen_r_client():
    """Return an OBJECT for r client."""
    return RApiClient(configuration)


def gen_r_remote(url=R_FIXTURE_URL, **kwargs):
    """Return a semi-random dict for use in creating a r Remote.

    :param url: The URL of an external content source.
    """
    return gen_remote(url, **kwargs)


def get_r_content_paths(repo, version_href=None):
    """Return the relative path of content units present in a r repository.

    :param repo: A dict of information about the repository.
    :param version_href: The repository version to read.
    :returns: A dict of lists with the paths of units present in a given repository.
        Paths are given as pairs with the remote and the local version for different content types.
    """
    # FIXME: The "relative_path" is actually a file path and name
    # It's just an example -- this needs to be replaced with an implementation that works
    # for repositories of this content type.
    return {
        R_CONTENT_NAME: [
            (content_unit["relative_path"], content_unit["relative_path"])
            for content_unit in get_content(repo, version_href)[R_CONTENT_NAME]
        ],
    }


def gen_r_content_attrs(artifact):
    """Generate a dict with content unit attributes.

    :param artifact: A dict of info about the artifact.
    :returns: A semi-random dict for use in creating a content unit.
    """
    return {
        "name": "test_package",
        "version": "1.0.0",
        "priority": "",
        "summary": "Test Package",
        "description": "A test R package",
        "license": "MIT",
        "url": "https://example.com",
        "md5sum": "",
        "needs_compilation": False,
        "path": "",
        "depends": [],
        "imports": [],
        "suggests": [],
        "requires": [],
        "file": artifact,
    }


def populate_pulp(cfg, url=R_FIXTURE_URL):
    """Add r contents to Pulp.

    :param pulp_smash.config.PulpSmashConfig: Information about a Pulp application.
    :param url: The r repository URL. Defaults to
        :data:`pulp_smash.constants.R_FIXTURE_URL`
    :returns: A list of dicts, where each dict describes one r content in Pulp.
    """
    client = api.Client(cfg, api.json_handler)
    remote = {}
    repo = {}
    try:
        remote.update(client.post(R_REMOTE_PATH, gen_r_remote(url)))
        repo.update(client.post(R_REPO_PATH, gen_repo()))
        sync(cfg, remote, repo)
    finally:
        if remote:
            client.delete(remote["pulp_href"])
        if repo:
            client.delete(repo["pulp_href"])
    return client.get(R_CONTENT_PATH)["results"]


def publish(cfg, repo, version_href=None):
    """Publish a repository.
    :param pulp_smash.config.PulpSmashConfig cfg: Information about the Pulp
        host.
    :param repo: A dict of information about the repository.
    :param version_href: A href for the repo version to be published.
    :returns: A publication. A dict of information about the just created
        publication.
    """
    if version_href:
        body = {"repository_version": version_href}
    else:
        body = {"repository": repo["pulp_href"]}

    client = api.Client(cfg, api.json_handler)
    call_report = client.post(R_PUBLICATION_PATH, body)
    tasks = tuple(api.poll_spawned_tasks(cfg, call_report))
    return client.get(tasks[-1]["created_resources"][0])


skip_if = partial(selectors.skip_if, exc=SkipTest)  # pylint:disable=invalid-name
"""The ``@skip_if`` decorator, customized for unittest.

:func:`pulp_smash.selectors.skip_if` is test runner agnostic. This function is
identical, except that ``exc`` has been set to ``unittest.SkipTest``.
"""

core_client = CoreApiClient(configuration)
tasks = TasksApi(core_client)


def gen_artifact(url=R_URL):
    """Creates an artifact."""
    response = requests.get(url)
    with NamedTemporaryFile() as temp_file:
        temp_file.write(response.content)
        temp_file.flush()
        artifact = ArtifactsApi(core_client).create(file=temp_file.name)
        return artifact.to_dict()