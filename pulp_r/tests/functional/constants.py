"""Constants for Pulp Cran plugin tests."""

from urllib.parse import urljoin

from pulp_smash.constants import PULP_FIXTURES_BASE_URL
from pulp_smash.pulp3.constants import (
    BASE_CONTENT_PATH,
    BASE_DISTRIBUTION_PATH,
    BASE_PUBLICATION_PATH,
    BASE_REMOTE_PATH,
    BASE_REPO_PATH,
)

# FIXME: list any download policies supported by your plugin type here.
# If your plugin supports all download policies, you can import this
# from pulp_smash.pulp3.constants instead.
# DOWNLOAD_POLICIES = ["immediate", "streamed", "on_demand"]
DOWNLOAD_POLICIES = ["immediate"]

# FIXME: replace 'unit' with your own content type names, and duplicate as necessary for each type
R_CONTENT_NAME = "r.unit"

# FIXME: replace 'unit' with your own content type names, and duplicate as necessary for each type
R_CONTENT_PATH = urljoin(BASE_CONTENT_PATH, "r/units/")

R_REMOTE_PATH = urljoin(BASE_REMOTE_PATH, "r/r/")

R_REPO_PATH = urljoin(BASE_REPO_PATH, "r/r/")

R_PUBLICATION_PATH = urljoin(BASE_PUBLICATION_PATH, "r/r/")

R_DISTRIBUTION_PATH = urljoin(BASE_DISTRIBUTION_PATH, "r/r/")

# FIXME: replace this with your own fixture repository URL and metadata
R_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "r/")
"""The URL to a r repository."""

# FIXME: replace this with the actual number of content units in your test fixture
R_FIXTURE_COUNT = 3
"""The number of content units available at :data:`R_FIXTURE_URL`."""

R_FIXTURE_SUMMARY = {R_CONTENT_NAME: R_FIXTURE_COUNT}
"""The desired content summary after syncing :data:`R_FIXTURE_URL`."""

# FIXME: replace this with the location of one specific content unit of your choosing
R_URL = urljoin(R_FIXTURE_URL, "")
"""The URL to an r file at :data:`R_FIXTURE_URL`."""

# FIXME: replace this with your own fixture repository URL and metadata
R_INVALID_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "r-invalid/")
"""The URL to an invalid r repository."""

# FIXME: replace this with your own fixture repository URL and metadata
R_LARGE_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "r_large/")
"""The URL to a r repository containing a large number of content units."""

# FIXME: replace this with the actual number of content units in your test fixture
R_LARGE_FIXTURE_COUNT = 25
"""The number of content units available at :data:`R_LARGE_FIXTURE_URL`."""
