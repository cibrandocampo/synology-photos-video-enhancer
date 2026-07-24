"""Build-time application version.

CI injects the output of `git describe --tags --always --abbrev=5` as the
`APP_VERSION` build arg, which the Dockerfile promotes to an env var. Local
and development builds get "dev", so an unversioned image is obvious at a
glance instead of masquerading as a release.
"""

import os


APP_VERSION = os.getenv("APP_VERSION", "dev")
