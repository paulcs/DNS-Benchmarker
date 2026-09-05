import os
import csv
import time
import datetime
import sys

try:
    import dns.resolver
except ImportError:
    print("\n[!] MISSING DEPENDENCY")
    print("Please install the 'dnspython' package to run this script.")
    print("Run this command in your terminal: pip install dnspython\n")
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

results = []
historical_results = []

print("\nStarting tests... (This may take a moment)\n")

# Configure the DNS resolver
res = dns.resolver.Resolver(configure=False)
res.timeout = 2.0
res.lifetime = 2.0

for server in selected_servers:
    dns_desc = server['Description']
    dns_ip = server['IP4 Address']
    
    print(f"Testing against {dns_desc} ({dns_ip})")
    res.nameservers = [dns_ip]
    
    for site in test_list:
        target_web = site['web-address']
        query_times = []
        failed_count = 0
        
        print(f"  -> Querying {target_web}...", end='', flush=True)
        
        for _ in range(frequency):
            try:
                # Measure exact resolution time
                start_time = time.perf_counter()
                res.resolve(target_web, 'A')
                end_time = time.perf_counter()
                query_times.append((end_time - start_time) * 1000)
            except Exception:
                failed_count += 1
                
        query_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate Average and Format Output
        if query_times:
            avg_time = sum(query_times) / len(query_times)
            avg_display = f"{round(avg_time, 2)} ms"
            avg_csv = round(avg_time, 2)
            formatted_times = ", ".join([str(round(t, 2)) for t in query_times])
            if failed_count > 0:
                formatted_times += f" ({failed_count} failures)"
        else:
            avg_display = "FAILED"
            avg_csv = "FAILED"
            formatted_times = f"All {frequency} attempts failed"
            
        if avg_display == "FAILED":
            print(f" {avg_display}")
        else:
            print(f" Avg: {avg_display}")
            
        results.append({
            "DNS Tested": dns_desc,
            "Target Website": target_web,
            "Query Times (ms)": formatted_times,
            "Date Tested": date_string,
            "Frequency Tested": frequency,
            "Avg Query Time": avg_csv
        })
        
        historical_results.append({
            "recordID": next_record_id,
            "DNS Tested": dns_desc,
            "Target Website": target_web,
            "Query Times (ms)": formatted_times,
            "datetime": query_datetime,
            "Frequency Tested": frequency,
            "Avg Query Time": avg_csv
        })
        
        next_record_id += 1

# Export daily results
daily_fieldnames = ["DNS Tested", "Target Website", "Query Times (ms)", "Date Tested", "Frequency Tested", "Avg Query Time"]
with open(output_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=daily_fieldnames)
    writer.writeheader()
    writer.writerows(results)

# Export or Append historical results
hist_fieldnames = ["recordID", "DNS Tested", "Target Website", "Query Times (ms)", "datetime", "Frequency Tested", "Avg Query Time"]
write_header = not os.path.exists(historical_file)
with open(historical_file, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=hist_fieldnames)
    if write_header:
        writer.writeheader()
    writer.writerows(historical_results)

print("\nTesting complete!")
print(f"- Daily snapshot saved to: {output_file}")
print(f"- Historical log appended to: {historical_file}")