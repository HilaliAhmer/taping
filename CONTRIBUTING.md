# Contributing to TAPING

Thank you for your interest in improving TAPING.

Bug reports, documentation improvements, feature suggestions, and pull requests are welcome.

## Before You Start

Before creating a new issue:

1. Check the existing GitHub issues.
2. Confirm that you are using the latest TAPING release.
3. Verify that the problem can be reproduced.
4. Remove passwords, private hostnames, public IP addresses, and other sensitive information from logs or screenshots.

## Reporting a Bug

Create a GitHub issue and include:

* TAPING version
* Windows version
* Installation method
* Command used
* Expected result
* Actual result
* Full error message
* Whether the issue occurs in PowerShell, CMD, or both

Check the TAPING version with:

```powershell
taping --version
```

Example bug report:

```text
TAPING version: 0.3.1
Windows version: Windows 11 24H2
Installation: Standalone EXE
Terminal: PowerShell

Command:
taping range 192.168.1.1-10 --up

Expected:
Reachable devices should be displayed.

Actual:
No devices are displayed.

Additional information:
Normal Windows ping works for 192.168.1.1.
```

Do not include confidential company information, internal DNS names, credentials, or unrestricted network diagrams.

## Requesting a Feature

Create a GitHub issue and explain:

* What problem the feature would solve
* How you expect the command to work
* An example command
* An example of the expected output
* Whether the feature affects ICMP, TCP, DNS, range scanning, installation, or output formatting

Example:

```text
Feature:
CSV output

Example command:
taping range 192.168.1.1-100 --csv results.csv

Reason:
The results could be imported into reporting and inventory tools.
```

## Development Setup

Development instructions are available in [DEVELOPMENT.md](DEVELOPMENT.md).

The basic setup is:

```powershell
git clone https://github.com/HilaliAhmer/taping.git
cd taping
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Making Changes

Create a new branch:

```powershell
git checkout -b feature/short-description
```

Examples:

```text
feature/json-output
fix/range-validation
docs/update-installation
```

Keep each pull request focused on one change.

Avoid combining unrelated formatting changes, new features, and bug fixes in the same pull request.

## Code Guidelines

Contributions should:

* Support Windows.
* Remain compatible with Python 3.9 or newer.
* Preserve existing command-line behavior unless a breaking change is clearly discussed.
* Use readable function and variable names.
* Provide clear error messages.
* Avoid unnecessary third-party dependencies.
* Avoid embedding private IP addresses, credentials, or company-specific information.
* Keep the CLI output readable in both PowerShell and CMD.
* Work when terminal color output is unavailable.

## Command-Line Compatibility

Existing options should not be removed or renamed without discussion.

Current important options include:

```text
-p, --port
-t, --loop
-c, --count
-w, --timeout
-i, --interval
--up
--version
```

Current service shortcuts include:

```text
--http
--https
--ssh
--rdp
--smb
--zebra
--winrm
--winrms
```

New options should not conflict with existing options.

## Testing Changes

At minimum, run:

```powershell
python -m py_compile .\taping\cli.py
python -m taping.cli --version
python -m taping.cli help
python -m taping.cli 8.8.8.8 -c 3
python -m taping.cli google.com --https
python -m taping.cli range 192.168.1.1-10 --up
```

Test any command or feature changed by the pull request.

When changing input validation, also test invalid input.

Examples:

```powershell
python -m taping.cli 8.8.8.8 -c 0
python -m taping.cli 8.8.8.8 -p 70000
python -m taping.cli range 192.168.1.20-10
```

## Documentation Changes

Update the relevant documentation when behavior changes:

* `README.md` for normal users
* `DEVELOPMENT.md` for build or release processes
* `CHANGELOG.md` for user-visible changes
* `CONTRIBUTING.md` for contribution rules

Command examples in the documentation must match the actual CLI behavior.

## Commit Messages

Use clear and focused commit messages.

Good examples:

```text
Add JSON output option
Fix reversed IPv4 range validation
Improve TCP timeout message
Update Windows installation instructions
```

Avoid messages such as:

```text
update
fix
changes
final
test
```

## Pull Requests

A pull request should include:

* A short description of the change
* The reason for the change
* Commands used for testing
* Any known limitations
* Updated documentation when required

Example:

```text
## Summary

Adds CSV output for IPv4 range results.

## Reason

Allows administrators to import TAPING results into reporting tools.

## Tests

- ICMP single target
- ICMP range
- TCP range
- Empty result
- Invalid output path

## Documentation

README and CHANGELOG updated.
```

## Security Issues

Do not publicly disclose a vulnerability that could put users at risk.

For non-sensitive bugs, create a normal GitHub issue.

For a potentially sensitive security problem, contact the project maintainer privately before publishing technical details.

## License

By contributing to TAPING, you agree that your contribution will be licensed under the project's MIT License.
