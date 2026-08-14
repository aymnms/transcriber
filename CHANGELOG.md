# CHANGELOG

<!-- version list -->

## v0.3.0 (2026-08-14)

### Continuous Integration

- Skip the CI matrix on docs-only changes
  ([`5644361`](https://github.com/aymnms/transcriber/commit/5644361d058ace1eb444c8e916ad4c91b37f88c7))

- **experiment**: Add AppImage and Windows installer diagnostic jobs
  ([`473351d`](https://github.com/aymnms/transcriber/commit/473351d20b0eeb317bc2d9b8390d420e494b4a64))

### Documentation

- Close out J6 — automated release validated in production
  ([`b749af1`](https://github.com/aymnms/transcriber/commit/b749af18489b17c702095d55cb3fe57fa0c7d471))

- Fix broken table-of-contents anchor link (#feature -> #features)
  ([`83e687b`](https://github.com/aymnms/transcriber/commit/83e687b6da8720694c9d12d40182e6438612aa92))

- Revamp README with a cleaner, more complete structure
  ([`74f08b1`](https://github.com/aymnms/transcriber/commit/74f08b1888acf65cc21aa8000ef5db9cec50684b))

### Features

- **release**: Attach AppImage and Windows installer to releases
  ([`6f658b6`](https://github.com/aymnms/transcriber/commit/6f658b675667ab69b81079d4741a33dfca80e569))


## v0.2.0 (2026-08-14)

### Bug Fixes

- **deps**: Pin av==14.2.0, replacing a PyPI-rotted av==14.3.0
  ([`1173c21`](https://github.com/aymnms/transcriber/commit/1173c216dbac115080ec9ed645cb631d9a118ab6))

### Continuous Integration

- Add multi-OS GitHub Actions matrix (macOS Intel/ARM, Windows, Linux)
  ([`c17870e`](https://github.com/aymnms/transcriber/commit/c17870ed7854c3703b674922fa201a6d0529259d))

- Build and test macOS Intel via Rosetta on macos-latest
  ([`3b8fbbe`](https://github.com/aymnms/transcriber/commit/3b8fbbeba52d2d3d892f36f70357feddaf57c788))

- Cancel superseded runs on the same branch (concurrency group)
  ([`2c0eb79`](https://github.com/aymnms/transcriber/commit/2c0eb7957c7fe04556ea48320c962b9d6b2ebe7a))

- Drop macos-13 from the matrix, keep macos-latest only
  ([`5704bd2`](https://github.com/aymnms/transcriber/commit/5704bd2e9d54a363aaf79a25639a3efd1f03b5d4))

- **experiment**: Add rosetta-diagnostic job to probe Intel build feasibility
  ([`5c727a4`](https://github.com/aymnms/transcriber/commit/5c727a4301722a6140c61115235913ba7ebd6539))

### Documentation

- Add full audit and cross-platform migration plan
  ([`a7925b1`](https://github.com/aymnms/transcriber/commit/a7925b1002a3820be0c4dbb1e11613ff0ad930d6))

- Add Node.js 20 deprecation warning to PLAN.md backlog
  ([`ab23f13`](https://github.com/aymnms/transcriber/commit/ab23f13ad5f40e8d4ad85e700009a9c9f5da2668))

- Add Windows/Linux build instructions, fix inaccurate release claim
  ([`d5b2850`](https://github.com/aymnms/transcriber/commit/d5b28508596bec50b7f5058aab21dc98cf9427c0))

- Close out the migration plan — MVP portable reached
  ([`d2f2c16`](https://github.com/aymnms/transcriber/commit/d2f2c16440f4a74eff04f86255a840df7d8c2457))

- Record the Rosetta-based Intel CI resolution
  ([`33b2c97`](https://github.com/aymnms/transcriber/commit/33b2c97de24d0f9bfbfc757c173bd0f3b652750f))

- Update PLAN.md — CI green on 3/4 OS, macos-13 pending runner assignment (external)
  ([`efdea5b`](https://github.com/aymnms/transcriber/commit/efdea5b54b07b85d28858c473b87dcce724326f8))

- Update PLAN.md — J1 complete, starting J2 (multi-OS CI)
  ([`a524cbb`](https://github.com/aymnms/transcriber/commit/a524cbb4c53b3050ba6e754acef6e9adeb9af82b))

### Features

- **domain**: Extract pure business logic from app_whisper.py
  ([`a7de84f`](https://github.com/aymnms/transcriber/commit/a7de84f84c1257f2a575b00759646d30d86871c6))

- **platform**: Wire app_whisper.py to domain/platform_ layers
  ([`ae3cd79`](https://github.com/aymnms/transcriber/commit/ae3cd7928d4fde95723b88a6884e1780c2eb46c9))

- **release**: Set up automated releases with python-semantic-release
  ([`9084a3f`](https://github.com/aymnms/transcriber/commit/9084a3f9e4f9d36a9122b11aede5cbe314be73ec))

### Testing

- **e2e**: Add real end-to-end transcription smoke test
  ([`db10c28`](https://github.com/aymnms/transcriber/commit/db10c28086a54be33a4ce085711a97ff7c2dd1b7))

- **functional**: Add headless smoke-import test for app_whisper.py
  ([`18acd58`](https://github.com/aymnms/transcriber/commit/18acd58dbaabb84c0ea783ec2e33eeef2b166b6e))


## v0.1.0 (2025-04-26)

- Initial Release
