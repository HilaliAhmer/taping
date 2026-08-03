# Changelog

All notable changes to TAPING are documented in this file.

The format is based on the principles of Keep a Changelog, and the project uses semantic versioning.

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

---

## [0.3.1] - 2026-07-16

### Added

* Added `-t` as the short option for continuous mode.
* Added `-w` as the short option for custom timeout values.

### Changed

* Continuous mode now behaves similarly to the Windows `ping -t` command.
* Kept `--loop` as the long form of `-t`.
* Kept `--timeout` as the long form of `-w`.
* Updated command examples and documentation.
* Standardized the default timeout for ICMP and TCP checks to 4000 milliseconds.

---

## [0.3.0] - 2026-07-16

### Added

* Added DNS hostname support.
* Added resolved IPv4 address display for hostnames.
* Added timestamps to ICMP and TCP result lines.
* Added configurable check intervals with `-i` and `--interval`.
* Added a standalone Windows executable.
* Added a PowerShell installer.
* Added service shortcuts for common TCP ports.

### Changed

* Improved ICMP ping reliability.
* Improved timeout behavior.
* Improved console output formatting.
* Expanded Windows installation and troubleshooting documentation.

---

## [0.2.2] - 2026-06-18

### Added

* Added standalone Windows release assets.
* Added the `taping-windows-x64.zip` package.
* Added the `install.ps1` PowerShell installer.

### Changed

* Improved the help output.
* Simplified installation for users without Python, pip, or Git.

---

## [0.2.1] - 2026-06-18

### Changed

* Improved TCP range output.
* TCP range results now display the target IP address and port more clearly.

---

## [0.2.0] - 2026-06-18

### Added

* Added colored console output.
* Added connection statistics.
* Added successful and failed connection counts.
* Added minimum, maximum, and average connection times.

---

## [0.1.0] - 2026-06-18

### Added

* Initial TAPING command-line application.
* Added single IPv4 ICMP checks.
* Added IPv4 range checks.
* Added TCP port checks.
* Added basic command-line options.

[Unreleased]: https://github.com/HilaliAhmer/taping/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/HilaliAhmer/taping/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/HilaliAhmer/taping/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/HilaliAhmer/taping/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/HilaliAhmer/taping/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/HilaliAhmer/taping/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/HilaliAhmer/taping/releases/tag/v0.1.0
