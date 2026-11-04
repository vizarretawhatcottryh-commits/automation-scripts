# ================================================================================================================================================================
# T2S2 MONITOR SUB-SYSTEM
# VERSION: 2.4.0
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# --- REQUIREMENT 3: AUTO-HIDE BLUE POWERSHELL WINDOW ON LAUNCH ---
# ================================================================================================================================================================
$DllImports = '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);'
$User32 = Add-Type -MemberDefinition $DllImports -Name "User32" -Namespace "Win32" -PassThru
$Hwnd = [System.Diagnostics.Process]::GetCurrentProcess().MainWindowHandle
if ($Hwnd -ne [IntPtr]::Zero) { 
    $User32::ShowWindow($Hwnd, 0) # 0 = SW_HIDE (Hides the console window completely)
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Form = New-Object System.Windows.Forms.Form
$Form.Text = "T2S2 Monitor - Active"
$Form.Size = New-Object System.Drawing.Size(800, 500)
$Form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::Sizable
$Form.BackColor = [System.Drawing.Color]::Black
$Form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen

$Text = New-Object System.Windows.Forms.TextBox
$Text.Multiline = $true; $Text.Dock = 'Fill'; $Text.ReadOnly = $true
$Text.BackColor = [System.Drawing.Color]::Black; $Text.ForeColor = [System.Drawing.Color]::Chartreuse
$Form.Controls.Add($Text)

# Only track files created after this moment
$SessionStartTime = Get-Date
$FilesTracked = @{}

# Flash Timer
$defaultColor = $Form.BackColor
$FlashTimer = New-Object System.Windows.Forms.Timer
$FlashTimer.Interval = 500
$FlashTimer.Add_Tick({
    if ($Form.BackColor -eq $defaultColor) { $Form.BackColor = [System.Drawing.Color]::Yellow } 
    else { $Form.BackColor = $defaultColor }
})

# Polling Timer replacing the while loop to keep UI thread perfectly responsive (Fixes minimize/maximize freeze)
$LogPollTimer = New-Object System.Windows.Forms.Timer
$LogPollTimer.Interval = 1000
$LogPollTimer.Add_Tick({
    $CurrentFiles = Get-ChildItem -Path "\\UTIL\c$\Logs\" -Filter "Log_*.txt" | Where-Object { $_.CreationTime -ge $SessionStartTime }
    
    foreach ($File in $CurrentFiles) {
        if (-not $FilesTracked.ContainsKey($File.FullName)) { $FilesTracked[$File.FullName] = 0 }
        
        if ($File.Length -gt $FilesTracked[$File.FullName]) {
            $NewContent = Get-Content $File.FullName -Tail 1 -ErrorAction SilentlyContinue
            if ($NewContent) {
                $Text.AppendText("[$($File.Name)] $NewContent`r`n")
                $Text.ScrollToCaret()
                
                # Trigger Alert without locking up application threads
                [System.Console]::Beep(1000, 200)
                $FlashTimer.Start()
                
                # Quick synchronous flash reset sequence
                $ResetTimer = New-Object System.Windows.Forms.Timer
                $ResetTimer.Interval = 1000
                $ResetTimer.Add_Tick({
                    $FlashTimer.Stop()
                    $Form.BackColor = $defaultColor
                    $ResetTimer.Stop()
                    $ResetTimer.Dispose()
                })
                $ResetTimer.Start()
            }
            $FilesTracked[$File.FullName] = $File.Length
        }
    }
})

$LogPollTimer.Start()
[System.Windows.Forms.Application]::Run($Form)