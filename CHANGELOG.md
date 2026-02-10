# Changelog[^1]

Notable changes to Takagi are documented here.

Takagi adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html).

## <a name="1-1-0">1.1.0 — 2026-02-10</a>

### Added

- The `/authorize` now accepts a boolean `return` parameter. This parameter allows `TAKAGI_RETURN_TO_REFERRER` to be overriden on a per-request basis (see [Configuration](https://github.com/celsiusnarhwal/takagi/tree/main?tab=readme-ov-file#configuration)).

### Fixed

- Fixed an error in which the `/introspect` endpoint would return the application's client ID for the `sub` claim
instead of the user ID of the token owner.

## <a name="1-0-1">1.0.1 — 2026-02-08</a>

### Fixed

- Fixed a bug in which an error would occur if HTTP Basic credentials were not provided to the `/token` endpoint.

## <a name="1-0-0">1.0.0 — 2026-02-05</a>

This is the initial release of Takagi.

[^1]: Format based on [Keep a Changelog](https://keepachangelog.com).
