import os
import csv
import time
import datetime
import sys
import subprocess  # Added for running external terminal commands (q and dig)

try:
    import dns.resolver
except ImportError:
    print("\n[!] MISSING DEPENDENCY")
    print("Please install the 'dnspython' package to run this script.")
    print("Run this command in your terminal: sudo pacman -S python-dnspython\n")
    sys.exit(1)

# 1. Setup working directory and results folder
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

results_folder = os.path.join(script_dir, "results")
if not os.path.exists(results_folder):
    os.makedirs(results_folder)
    print("Created 'results' folder to store outputs.")

# Define file paths
dns_file = "dns-servers.txt"
test_file = "test-servers.txt"
date_string = datetime.datetime.now().strftime("%Y-%m-%d")

# 2. Smart File Naming for Daily Results
base_output_file = os.path.join(results_folder, f"Results-{date_string}")
output_file = f"{base_output_file}.csv"
counter = 1

while os.path.exists(output_file):
    output_file = f"{base_output_file}-{counter:02d}.csv"
    counter += 1

# 3. Setup Historical File and Determine Starting recordID
historical_file = os.path.join(results_folder, "DNSB-Historical-Results.csv")
next_record_id = 1

if os.path.exists(historical_file):
    try:
        with open(historical_file, mode='r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            if reader and reader[-1].get('recordID', '').isdigit():
                next_record_id = int(reader[-1]['recordID']) + 1
    except Exception:
        pass

# Check if required text files exist
if not os.path.exists(dns_file) or not os.path.exists(test_file):
    print("Error: Make sure 'dns-servers.txt' and 'test-servers.txt' are in the same folder as this script.")
    sys.exit(1)

# Load the CSV data
dns_list = []
with open(dns_file, mode='r', encoding='utf-8') as f:
    dns_list = list(csv.DictReader(f))

test_list = []
with open(test_file, mode='r', encoding='utf-8') as f:
    test_list = list(csv.DictReader(f))

# Prompt for Provider with Default
print("\nAvailable DNS Providers:")
print("- All (Test every provider in the list)")
for provider in sorted(list(set(s['Provider'] for s in dns_list))):
    print(f"- {provider}")

chosen_provider = input("\nEnter the DNS Provider you want to test, or type 'All' [Default: All]: ").strip()
if not chosen_provider:
    chosen_provider = "All"

# Filter servers based on choice
if chosen_provider.lower() == "all":
    selected_servers = dns_list
else:
    selected_servers = [s for s in dns_list if s['Provider'].lower() == chosen_provider.lower()]

if not selected_servers:
    print("Provider not found. Please check your spelling and try again.")
    sys.exit(1)

# Prompt for Frequency with Default
frequency = 0
while frequency < 1 or frequency > 10:
    input_freq = input("How many times should we test each server? (1-10) [Default: 5]: ").strip()
    if not input_freq:
        frequency = 5
    elif input_freq.isdigit() and 1 <= int(input_freq) <= 10:
        frequency = int(input_freq)
    else:
        print("Please enter a number strictly between 1 and 10.")

# Configure the DNS resolver
res = dns.resolver.Resolver(configure=False)
res.timeout = 2.0
res.lifetime = 2.0

# Pre-build a tracking list for all the combinations we need to test
results_tracker = []
for server in selected_servers:
    for site in test_list:
        results_tracker.append({
            "dns_desc": server['Description'],
            "dns_ip": server['IP4 Address'],
            "target_web": site['web-address'],
            "query_times": [],
            "failed_count": 0
        })

print(f"\nStarting benchmark tests... We will sweep through the list {frequency} time(s).\n")

# Benchmark tests execution
for current_run in range(1, frequency + 1):
    print(f"--- Run {current_run} of {frequency} ---")
    
    for item in results_tracker:
        res.nameservers = [item['dns_ip']]
        print(f"  -> {item['dns_desc']} querying {item['target_web']}... ", end='', flush=True)
        
        try:
            start_time = time.perf_counter()
            res.resolve(item['target_web'], 'A')
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            item['query_times'].append(elapsed_ms)
            print(f"{round(elapsed_ms, 2)} ms")
        except Exception:
            item['failed_count'] += 1
            print("FAILED")
            
    print("")

print("Compiling final averages and saving data...")

results = []
historical_results = []
query_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for item in results_tracker:
    if item['query_times']:
        avg_time = sum(item['query_times']) / len(item['query_times'])
        avg_display = f"{round(avg_time, 2)} ms"
        avg_csv = round(avg_time, 2)
        formatted_times = ", ".join([str(round(t, 2)) for t in item['query_times']])
        
        if item['failed_count'] > 0:
            formatted_times += f" ({item['failed_count']} failures)"
    else:
        avg_csv = "FAILED"
        formatted_times = f"All {frequency} attempts failed"
        
    results.append({
        "DNS Tested": item['dns_desc'],
        "Target Website": item['target_web'],
        "Query Times (ms)": formatted_times,
        "Date Tested": date_string,
        "Frequency Tested": frequency,
        "Avg Query Time": avg_csv
    })
    
    historical_results.append({
        "recordID": next_record_id,
        "DNS Tested": item['dns_desc'],
        "Target Website": item['target_web'],
        "Query Times (ms)": formatted_times,
        "datetime": query_datetime,
        "Frequency Tested": frequency,
        "Avg Query Time": avg_csv
    })
    
    next_record_id += 1

# Export benchmark results
daily_fieldnames = ["DNS Tested", "Target Website", "Query Times (ms)", "Date Tested", "Frequency Tested", "Avg Query Time"]
with open(output_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=daily_fieldnames)
    writer.writeheader()
    writer.writerows(results)

hist_fieldnames = ["recordID", "DNS Tested", "Target Website", "Query Times (ms)", "datetime", "Frequency Tested", "Avg Query Time"]
write_header = not os.path.exists(historical_file)
with open(historical_file, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=hist_fieldnames)
    if write_header:
        writer.writeheader()
    writer.writerows(historical_results)

print(f"- Benchmark snapshot saved to: {output_file}")
print(f"- Benchmark historical log appended to: {historical_file}")

# =====================================================================
# NEW PHASE: DNS Secure Capabilities Checking (DoQ and DoH)
# =====================================================================
print("\nStarting DNS Secure Capabilities Check (DoQ and DoH)...")

secure_results_file = os.path.join(results_folder, "dns-secure-capabilities.csv")
secure_results = []
secure_test_domain = "google.com"

# Loop through all servers originally loaded from the dns-servers.txt file
for server in dns_list:
    server_id = server['ID']
    dns_ip = server['IP4 Address']
    dns_desc = server['Description']
    
    print(f"  -> Testing {dns_desc} ({dns_ip}) ... ", end='', flush=True)
    
    # 1. Test DoQ using 'q'
    # Command syntax: q @quic://<IP> google.com --timeout 3s
    quic_capable = "NA"
    try:
        # run the command, capture output, and enforce a 5s hard timeout on the python side
        q_proc = subprocess.run(
            ["q", f"@quic://{dns_ip}", secure_test_domain, "--timeout", "3s"],
            capture_output=True, text=True, timeout=5
        )
        if q_proc.returncode == 0:
            quic_capable = "Yes"
        elif "timeout" in q_proc.stderr.lower() or "i/o timeout" in q_proc.stderr.lower():
            quic_capable = "NA"
        else:
            quic_capable = "No"  # Actively refused or protocol error
    except FileNotFoundError:
        quic_capable = "Error: 'q' utility not found"
    except subprocess.TimeoutExpired:
        quic_capable = "NA"
    except Exception:
        quic_capable = "No"

    # 2. Test DoH using 'dig'
    # Command syntax: dig @<IP> +https google.com A +short +time=3 +tries=1
    https_capable = "NA"
    try:
        dig_proc = subprocess.run(
            ["dig", f"@{dns_ip}", "+https", secure_test_domain, "A", "+short", "+time=3", "+tries=1"],
            capture_output=True, text=True, timeout=5
        )
        if dig_proc.returncode == 0 and dig_proc.stdout.strip() != "":
            https_capable = "Yes"
        elif "connection refused" in dig_proc.stderr.lower() or "connection refused" in dig_proc.stdout.lower():
            https_capable = "No"
        elif "timed out" in dig_proc.stdout.lower() or "timed out" in dig_proc.stderr.lower() or dig_proc.stdout.strip() == "":
            https_capable = "NA"
        else:
            https_capable = "No"
    except FileNotFoundError:
        https_capable = "Error: 'dig' utility not found"
    except subprocess.TimeoutExpired:
        https_capable = "NA"
    except Exception:
        https_capable = "No"
        
    print(f"QUIC: {quic_capable} | HTTPS: {https_capable}")
    
    # Append the results for the current server
    secure_results.append({
        "ID": server_id,
        "DNS-IP4-Address": dns_ip,
        "QUIC-Capable": quic_capable,
        "HTTPS-Capable": https_capable,
        "Date-Last-Tested": query_datetime
    })

# Export Secure Capabilities Results (Overwrites file on each run)
secure_fieldnames = ["ID", "DNS-IP4-Address", "QUIC-Capable", "HTTPS-Capable", "Date-Last-Tested"]
with open(secure_results_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=secure_fieldnames)
    writer.writeheader()
    writer.writerows(secure_results)
    
print(f"\n- Secure capabilities log rewritten to: {secure_results_file}")
print("All tasks complete!\n")
