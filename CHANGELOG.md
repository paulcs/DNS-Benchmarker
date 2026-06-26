# Changelog

All notable changes to the DNS-Benchmarker project will be documented in this file.

## [Unreleased]
### Planned / Ideas
* Add feature to visualize CSV results in a simple HTML graph.
* Add MS-Excel or Google Sheets file to easily review the data (or via a small internal web-site).
* Create a user-friendly GUI to update and change the text file, dns-servers.txt, controlling the DNS entries.
* Create a user-friendly GUI to update and change the text file, test-servers.txt, controlling the sites for testing.
* Extend the functionality by adding a website to maintain settings and review the results, possibly historical ones as well. 
* Allow for pushing the fastest DNS servers as your selection of forwarders inside your local AdGuard or Technitium DNS server(s). 

## [1.0.0] - 2026-06-26
### Added
* Initial release of DNS-Benchmarker (DNSB).
* Core benchmarking loop using `Resolve-DnsName` and `Measure-Command`.
* CSV export functionality with smart-naming to prevent overwrites.
* Admin privilege verification to ensure cache flushing works.
* Error handling for unreachable DNS IP addresses.
* Default selections for quick execution (Enter for "All" servers, Enter for "5" tests).
