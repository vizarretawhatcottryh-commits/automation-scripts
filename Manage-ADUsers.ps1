<#
.SYNOPSIS
    Active Directory Bulk User Status & Group Audit Script
.DESCRIPTION
    Queries Active Directory for disabled user accounts or members of 
    critical security groups to assist with regular access reviews.
#>

# Import the Active Directory module
Import-Module ActiveDirectory

$LogPath = "C:\Logs\AD_Audit_Log.txt"

# Ensure log directory exists
if (!(Test-Path "C:\Logs")) {
    New-Item -ItemType Directory -Path "C:\Logs" | Out-Null
}

Write-Host "Starting Active Directory User Audit..." -ForegroundColor Cyan

# Find inactive or disabled user accounts as an example
$DisabledUsers = Get-ADUser -Filter "Enabled -eq $false" -Properties LastLogonDate

foreach ($User in $DisabledUsers) {
    $LogEntry = "$(Get-Date): Disabled account found -> $($User.SamAccountName)"
    Add-Content -Path $LogPath -Value $LogEntry
}

Write-Host "Audit complete. Results logged to $LogPath" -ForegroundColor Green