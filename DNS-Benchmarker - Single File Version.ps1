# 1. Admin Verification
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "`n[!] ACCESS DENIED" -ForegroundColor Red
    Write-Host "This script must be run in an Administrative PowerShell session." -ForegroundColor Yellow
    Write-Host "Reason: The command 'Clear-DnsClientCache' requires elevated privileges to successfully flush the local DNS cache.`n" -ForegroundColor Gray
    Pause
    exit
}

# Set the working directory to the location of the script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# Define and create the results folder if it doesn't exist
$resultsFolder = Join-Path -Path $scriptPath -ChildPath "results"
if (!(Test-Path $resultsFolder)) {
    New-Item -ItemType Directory -Path $resultsFolder | Out-Null
    Write-Host "Created 'results' folder to store outputs." -ForegroundColor DarkGray
}

# Define file paths
$dnsFile = "dns-servers.txt"
$testFile = "test-servers.txt"
$dateString = Get-Date -Format "yyyy-MM-dd"

# 2. Smart File Naming (Prevent Overwrites)
$baseOutputFile = Join-Path -Path $resultsFolder -ChildPath "Results-$dateString"
$outputFile = "$baseOutputFile.csv"
$counter = 1

while (Test-Path $outputFile) {
    $formattedCounter = "{0:D2}" -f $counter
    $outputFile = "$baseOutputFile-$formattedCounter.csv"
    $counter++
}

# Check if required text files exist
if (!(Test-Path $dnsFile) -or !(Test-Path $testFile)) {
    Write-Host "Error: Make sure 'dns-servers.txt' and 'test-servers.txt' are in the same folder as this script." -ForegroundColor Red
    Pause
    exit
}

# Load the CSV data
$dnsList = Import-Csv -Path $dnsFile
$testList = Import-Csv -Path $testFile

# Prompt for Provider with Default
Write-Host "`nAvailable DNS Providers:" -ForegroundColor Cyan
Write-Host "- All (Test every provider in the list)"
$dnsList.Provider | Select-Object -Unique | ForEach-Object { Write-Host "- $_" }
Write-Host ""

$chosenProvider = Read-Host "Enter the DNS Provider you want to test, or type 'All' [Default: All]"
if ($chosenProvider.Trim() -eq "") {
    $chosenProvider = "All"
}

# Filter servers based on choice
if ($chosenProvider -match "^All$") {
    $selectedServers = $dnsList
}
else {
    $selectedServers = $dnsList | Where-Object { $_.Provider -match "^$chosenProvider$" }
}

if ($selectedServers.Count -eq 0) {
    Write-Host "Provider not found. Please check your spelling and try again." -ForegroundColor Red
    Pause
    exit
}

# Prompt for Frequency with Default
[int]$frequency = 0
while ($frequency -lt 1 -or $frequency -gt 10) {
    $inputFreq = Read-Host "How many times should we test each server? (1-10) [Default: 5]"
    
    if ($inputFreq.Trim() -eq "") {
        $frequency = 5
    }
    elseif ([int]::TryParse($inputFreq, [ref]$frequency)) {
        if ($frequency -lt 1 -or $frequency -gt 10) {
            Write-Host "Please enter a number strictly between 1 and 10." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "Invalid input. Please enter a number." -ForegroundColor Red
        $frequency = 0
    }
}

# Array to hold the final results
$results = @()

Write-Host "`nStarting tests... (This may take a moment)`n" -ForegroundColor Green
Write-Host "Note: If a DNS server IP is unreachable, your window may pause for 10-15 seconds before timing out.`n" -ForegroundColor DarkGray

# Loop through each DNS Server matched
foreach ($server in $selectedServers) {
    $dnsDesc = $server.Description
    $dnsIp = $server.'IP4 Address'
    
    Write-Host "Testing against $dnsDesc ($dnsIp)" -ForegroundColor Cyan
    
    # Loop through each website in the test list
    foreach ($site in $testList) {
        $targetWeb = $site.'web-address'
        $queryTimes = @()
        $failedCount = 0
        
        Write-Host "  -> Querying $targetWeb..." -NoNewline
        
        # Run the test 'x' times based on frequency
        for ($i = 1; $i -le $frequency; $i++) {
            Clear-DnsClientCache
            
            # 3. Error Handling for dead/typo IPs
            try {
                $measure = Measure-Command {
                    $null = Resolve-DnsName -Name $targetWeb -Server $dnsIp -ErrorAction Stop
                }
                $queryTimes += $measure.TotalMilliseconds
            }
            catch {
                $failedCount++
            }
        }
        
        # Calculate Average and Format Output
        if ($queryTimes.Count -gt 0) {
            $avgTime = ($queryTimes | Measure-Object -Average).Average
            $avgDisplay = "$([math]::Round($avgTime, 2)) ms"
            $avgCsv = [math]::Round($avgTime, 2)
            
            # Create a string of the successful run times
            $formattedTimes = ($queryTimes | ForEach-Object { [math]::Round($_, 2) }) -join ', '
            
            # Append failure notes if any runs failed
            if ($failedCount -gt 0) {
                $formattedTimes += " ($failedCount failures)"
            }
        }
        else {
            # All attempts failed (Server is likely completely dead/unreachable)
            $avgDisplay = "FAILED"
            $avgCsv = "FAILED"
            $formattedTimes = "All $frequency attempts failed"
        }
        
        if ($avgDisplay -eq "FAILED") {
            Write-Host " $avgDisplay" -ForegroundColor Red
        }
        else {
            Write-Host " Avg: $avgDisplay" -ForegroundColor White
        }
        
        # Create a custom object for our CSV row
        $results += [PSCustomObject]@{
            "DNS Tested"       = $dnsDesc
            "Target Website"   = $targetWeb
            "Query Times (ms)" = $formattedTimes
            "Date Tested"      = $dateString
            "Frequency Tested" = $frequency
            "Avg Query Time"   = $avgCsv
        }
    }
}

# Export the results to a CSV file
$results | Export-Csv -Path $outputFile -NoTypeInformation -Encoding UTF8

Write-Host "`nTesting complete! Results saved to $outputFile" -ForegroundColor Green
Pause