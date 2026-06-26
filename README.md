# DNS-Benchmarker (DNSB)
Although utilities like this already exist, I found them sometimes lacking in flexibly as well as extensibility. With that in mind I am trying to create, at first, a PowerShell utility designed to benchmark DNS server response times against a customizable list of target websites as well as a choice of DNS servers, which can altered or extended if needed. 
The idea is by testing multiple DNS providers (like NextDNS, Cloudflare, or Google) against real-world domains, DNSB helps identify the most efficient routing for your specific network location, outputting the results into a clean, timestamped CSV for easy analysis, for now. The idea is to extend this functionality in the future, even to the point of where I hope an updated list of DNS IP addresses can be pushed towards a locally installed DNS tool, like for example AdGuard ot Technitium . 
## Features (at initial release)
* **Automated Cache Flushing:** Ensures true query times by clearing the local DNS cache before every single test.
* **Batch Testing:** Test a single provider or run a complete sweep across all configured DNS servers at once.
* **Customizable Frequency:** Define how many times each query should run (1-10) to generate an accurate average response time.
* **Smart Output:** Automatically generates a `results` folder and intelligently names CSV files to prevent accidental overwrites.
* **Resilient Execution:** Neatly handling of dead or unreachable IP addresses without crashing the script.

## Prerequisites
* **Windows PowerShell:** Built-in to Windows.
* **Administrator Privileges:** Required to execute the `Clear-DnsClientCache` command. The script will automatically halt if run in a standard session.

## Configuration
DNSB relies on two CSV-formatted text files in the root directory:
1. `dns-servers.txt`: Your list of DNS providers and their IP addresses.
2. `test-servers.txt`: The target domains you want to test routing latency against (e.g., www.github.com).

## Usage
1. Open an Administrative PowerShell terminal.
2. Navigate to the directory containing the script.
3. Run the script:
   ```powershell
   .\DNS-Benchmarker.ps1
Or…
1. Run the batch file Run-DNS-Benchmark.bat by simply right-clicking in the Windows Explorer and choose “Run as Administrator”.

