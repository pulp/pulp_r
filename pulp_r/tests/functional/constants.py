"""Constants for Pulp Cran plugin tests."""

from urllib.parse import urljoin

from pulp_smash.constants import PULP_FIXTURES_BASE_URL
from pulp_smash.pulp3.constants import (
    BASE_DISTRIBUTION_PATH,
    BASE_PUBLICATION_PATH,
    BASE_REMOTE_PATH,
    BASE_REPO_PATH,
    BASE_CONTENT_PATH,
)

# FIXME: list any download policies supported by your plugin type here.
# If your plugin supports all download policies, you can import this
# from pulp_smash.pulp3.constants instead.
# DOWNLOAD_POLICIES = ["immediate", "streamed", "on_demand"]
DOWNLOAD_POLICIES = ["immediate"]

# FIXME: replace 'unit' with your own content type names, and duplicate as necessary for each type
CRAN_CONTENT_NAME = "cran.unit"

# FIXME: replace 'unit' with your own content type names, and duplicate as necessary for each type
CRAN_CONTENT_PATH = urljoin(BASE_CONTENT_PATH, "cran/units/")

CRAN_REMOTE_PATH = urljoin(BASE_REMOTE_PATH, "cran/cran/")

CRAN_REPO_PATH = urljoin(BASE_REPO_PATH, "cran/cran/")

CRAN_PUBLICATION_PATH = urljoin(BASE_PUBLICATION_PATH, "cran/cran/")

CRAN_DISTRIBUTION_PATH = urljoin(BASE_DISTRIBUTION_PATH, "cran/cran/")

# FIXME: replace this with your own fixture repository URL and metadata
CRAN_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "cran/")
"""The URL to a cran repository."""

# FIXME: replace this with the actual number of content units in your test fixture
CRAN_FIXTURE_COUNT = 3
"""The number of content units available at :data:`CRAN_FIXTURE_URL`."""

CRAN_FIXTURE_SUMMARY = {CRAN_CONTENT_NAME: CRAN_FIXTURE_COUNT}
"""The desired content summary after syncing :data:`CRAN_FIXTURE_URL`."""

# FIXME: replace this with the location of one specific content unit of your choosing
CRAN_URL = urljoin(CRAN_FIXTURE_URL, "")
"""The URL to an cran file at :data:`CRAN_FIXTURE_URL`."""

# FIXME: replace this with your own fixture repository URL and metadata
CRAN_INVALID_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "cran-invalid/")
"""The URL to an invalid cran repository."""

# FIXME: replace this with your own fixture repository URL and metadata
CRAN_LARGE_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "cran_large/")
"""The URL to a cran repository containing a large number of content units."""

# FIXME: replace this with the actual number of content units in your test fixture
CRAN_LARGE_FIXTURE_COUNT = 25
"""The number of content units available at :data:`CRAN_LARGE_FIXTURE_URL`."""
