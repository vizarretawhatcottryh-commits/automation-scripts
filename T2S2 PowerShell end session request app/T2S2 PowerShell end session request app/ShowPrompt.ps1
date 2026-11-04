# ================================================================================================================================================================
# ENTERPRISE-GRADE SYSTEM MAINTENANCE AND USER NOTIFICATION FRAMEWORK
# VERSION: 2.4.3
# ================================================================================================================================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# GLOBAL CONFIGURATION VARIABLES
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
$global:TargetComputer   = $env:COMPUTERNAME
$global:LogDirectory     = "\\UTIL\c$\Logs"
$global:LogPath          = "$global:LogDirectory\Log_$global:TargetComputer`_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$global:shouldLogOff     = $false
$global:hasSnoozedBefore = $false
$global:actionTaken      = $false
$script:scriptLooping    = $true

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# LOGGING SUBSYSTEM
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
function Write-LiveLog ([string]$Message, [string]$Severity = "INFO") {
    $Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $FormattedEntry = "[ $Stamp ] [ $Severity ] [COMPUTER: $global:TargetComputer] : $Message"
    
    try {
        if (-not (Test-Path $global:LogDirectory)) {
            New-Item -Path $global:LogDirectory -ItemType Directory -ErrorAction SilentlyContinue | Out-Null
        }
        Add-Content -Path $global:LogPath -Value $FormattedEntry -ErrorAction SilentlyContinue
    } catch {
        $FallbackPath = "$env:TEMP\MaintLog_Fallback.txt"
        Add-Content -Path $FallbackPath -Value $FormattedEntry -ErrorAction SilentlyContinue
    }
    Write-Output $FormattedEntry
}

# --- REQUIREMENT 2: ACCOUNTABILITY LOGGING FOR PDQ INVENTORY ABORT EVENTS ---
function OnScriptProcessExit {
    if (-not $global:actionTaken -and $script:scriptLooping) {
        $Initiator = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        Write-LiveLog "PROCESS TERMINATION: The deployment tool session was forcefully aborted by: $Initiator" "WARNING"
    }
}
[System.AppDomain]::CurrentDomain.add_ProcessExit({ OnScriptProcessExit })

Write-LiveLog "System Maintenance Service started successfully for user: $env:USERNAME."

function Initialize-WindowStyles ([System.Windows.Forms.Form]$TargetForm, [string]$Title, [int]$W, [int]$H) {
    $TargetForm.Text           = $Title
    $TargetForm.Size           = New-Object System.Drawing.Size($W, $H)
    $TargetForm.StartPosition  = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $TargetForm.TopMost        = $true
    $TargetForm.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::Sizable
    $TargetForm.BackColor      = [System.Drawing.Color]::FromArgb(245, 245, 245)
}

function Execute-SystemLogOff {
    Write-LiveLog "Initiating final log-off security handshake..."
    $Warning = "WARNING: System maintenance is non-negotiable. All open unsaved data will be permanently lost upon disconnection."
    $Result  = [System.Windows.Forms.MessageBox]::Show($Warning, "Final Security Warning", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Stop)
    
    if ($Result -eq [System.Windows.Forms.DialogResult]::Yes) {
        Write-LiveLog "User authorization granted for session termination. Proceeding to Shutdown/Log-off."
        Shutdown.exe /l /f
    } else {
        Write-LiveLog "User denied termination request. Returning to active session."
    }
}

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# MAIN APPLICATION STATE MACHINE
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
while ($script:scriptLooping) {
    $script:userAction      = ""
    $script:waitTimeMinutes = 0
    $global:actionTaken     = $false

    # [STAGE 1] INITIAL NOTIFICATION WINDOW
    if (-not $global:hasSnoozedBefore) {
        Write-LiveLog "State: Entering Stage 1 (Initial Alert)."
        $Form1 = New-Object System.Windows.Forms.Form
        Initialize-WindowStyles -TargetForm $Form1 -Title "T2S2 Maintenance Alert" -W 650 -H 250
        
        # --- TIMER DE PARPADEO PARA LA VENTANA 1 ---
        $DefaultColor1 = $Form1.BackColor
        $FlashTimer1 = New-Object System.Windows.Forms.Timer
        $FlashTimer1.Interval = 500
        $FlashTimer1.Add_Tick({
            if ($Form1.BackColor -eq $DefaultColor1) { $Form1.BackColor = [System.Drawing.Color]::Yellow } 
            else { $Form1.BackColor = $DefaultColor1 }
        })

        $Lbl1 = New-Object System.Windows.Forms.Label
        $Lbl1.Text = "Attention User:`n`nT2S2 needs this computer for system maintenance. Please make sure you saved your work before logging off."
        $Lbl1.Location = New-Object System.Drawing.Point(30, 30)
        $Lbl1.Size = New-Object System.Drawing.Size(580, 80)
        $Lbl1.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
        $Form1.Controls.Add($Lbl1)

        $BtnProceed = New-Object System.Windows.Forms.Button; $BtnProceed.Text = "PROCEED"; $BtnProceed.Location = New-Object System.Drawing.Point(350, 150); $BtnProceed.Size = New-Object System.Drawing.Size(120, 40)
        $BtnProceed.Add_Click({ $global:actionTaken = $true; $global:shouldLogOff = $true; $script:userAction = "YES"; $Form1.Close() })
        
        $BtnDefer = New-Object System.Windows.Forms.Button; $BtnDefer.Text = "DEFER"; $BtnDefer.Location = New-Object System.Drawing.Point(480, 150); $BtnDefer.Size = New-Object System.Drawing.Size(120, 40)
        $BtnDefer.Add_Click({ $global:actionTaken = $true; $script:userAction = "NO"; $Form1.Close() })
        
        $Form1.Controls.AddRange(@($BtnProceed, $BtnDefer))
        
        $FlashTimer1.Start()
        $Form1.ShowDialog() | Out-Null
        $FlashTimer1.Stop()
        $FlashTimer1.Dispose()
    } else {
        $script:userAction = "NO"
    }

    # [STAGE 2] POSTPONEMENT SELECTION WINDOW
    if ($script:userAction -eq "NO") {
        Write-LiveLog "State: Entering Stage 2 (Postponement Options)."
        $global:actionTaken = $false
        $Form2 = New-Object System.Windows.Forms.Form
        Initialize-WindowStyles -TargetForm $Form2 -Title "T2S2 Maintenance Deferral Panel" -W 700 -H 530
        
        # --- TIMER DE PARPADEO PARA LA VENTANA 2 ---
        $DefaultColor2 = $Form2.BackColor
        $FlashTimer2 = New-Object System.Windows.Forms.Timer
        $FlashTimer2.Interval = 500
        $FlashTimer2.Add_Tick({
            if ($Form2.BackColor -eq $DefaultColor2) { $Form2.BackColor = [System.Drawing.Color]::Yellow } 
            else { $Form2.BackColor = $DefaultColor2 }
        })

        $Form2.Add_FormClosing({
            if (-not $global:actionTaken) {
                Write-LiveLog "USER ACTION: The postponement panel was closed manually by user."
                $script:scriptLooping = $false
            }
        })

        # Instructions Label
        $Instructions = New-Object System.Windows.Forms.Label
        $Instructions.Text = "Select your preferred deferral duration from the options below."
        $Instructions.Location = New-Object System.Drawing.Point(30, 15)
        $Instructions.Size = New-Object System.Drawing.Size(600, 20)
        $Form2.Controls.Add($Instructions)

        # Policy Textbox (Redimensionado con precisión para ajustarse al texto resaltado de tu captura)
        $PolicyBox = New-Object System.Windows.Forms.TextBox
        $PolicyBox.Location = New-Object System.Drawing.Point(30, 40)
        $PolicyBox.Size = New-Object System.Drawing.Size(620, 65)
        $PolicyBox.Multiline = $true
        $PolicyBox.ReadOnly = $true
        $PolicyBox.ScrollBars = 'Vertical'
        $PolicyBox.Text = "ADMINISTRATIVE POLICY REGARDING SYSTEM MAINTENANCE:`n`n1. Maintenance is mandatory for security compliance.`n2. Users may defer these requests for short intervals.`n3. All open documents and active applications should be saved and closed to ensure data integrity during the system update process.`n`nShould you require further assistance, please contact the T2S2 IT Service Desk at T2S2-Support@utah.gov."
        $Form2.Controls.Add($PolicyBox)

        # User Note Label (Reposicionado justo debajo de la nueva área ajustada de política)
        $LblNote = New-Object System.Windows.Forms.Label
        $LblNote.Text = "If you would like to send only a custom message, type it below and press the Send a CUSTOM Message button:"
        $LblNote.Location = New-Object System.Drawing.Point(30, 120)
        $LblNote.Size = New-Object System.Drawing.Size(600, 20)
        $Form2.Controls.Add($LblNote)

        # Active User Input Textbox (Agrandado sustancialmente ocupando todo el espacio optimizado)
        $UserInputBox = New-Object System.Windows.Forms.TextBox
        $UserInputBox.Location = New-Object System.Drawing.Point(30, 145)
        $UserInputBox.Size = New-Object System.Drawing.Size(620, 235)
        $UserInputBox.Multiline = $true
        $UserInputBox.ScrollBars = 'Vertical'
        $Form2.Controls.Add($UserInputBox)

        # Bottom Row Control Alignment Layout
        $BCustom = New-Object System.Windows.Forms.Button; $BCustom.Text = "Send CUSTOM Message"; $BCustom.Location = New-Object System.Drawing.Point(30, 410); $BCustom.Size = New-Object System.Drawing.Size(110, 50)
        
        $B5 = New-Object System.Windows.Forms.Button; $B5.Text = "Defer for 5 Min and Send Message"; $B5.Location = New-Object System.Drawing.Point(150, 410); $B5.Size = New-Object System.Drawing.Size(110, 50)
        $B10 = New-Object System.Windows.Forms.Button; $B10.Text = "Defer for 10 Min and Send Message"; $B10.Location = New-Object System.Drawing.Point(270, 410); $B10.Size = New-Object System.Drawing.Size(110, 50)
        $B30 = New-Object System.Windows.Forms.Button; $B30.Text = "Defer for 30 Min and Send Message"; $B30.Location = New-Object System.Drawing.Point(390, 410); $B30.Size = New-Object System.Drawing.Size(110, 50)
        
        $BEnd = New-Object System.Windows.Forms.Button; $BEnd.Text = "LOG OFF NOW"; $BEnd.Location = New-Object System.Drawing.Point(530, 410); $BEnd.Size = New-Object System.Drawing.Size(120, 50)

        # Gray out options if a previous snooze time has expired
        if ($global:hasSnoozedBefore) {
            $B5.Enabled  = $false
            $B10.Enabled = $false
            $B30.Enabled = $false
        }

        # Event Bindings
        $BCustom.Add_Click({ 
            $global:actionTaken = $true
            $UserText = if ([string]::IsNullOrWhiteSpace($UserInputBox.Text)) { "[Blank / No User Entry Provided]" } else { $UserInputBox.Text }
            Write-LiveLog "USER ACTION [CUSTOM]: Button Pressed. Custom Entry: $UserText"
            $Form2.Close() 
        })
        
        $B5.Add_Click({ 
            $global:actionTaken = $true; 
            $UserText = if ([string]::IsNullOrWhiteSpace($UserInputBox.Text)) { "[Blank / No User Entry Provided]" } else { $UserInputBox.Text }
            Write-LiveLog "USER SELECTION: Postponed 5 minutes. Custom Entry: $UserText"; 
            $script:waitTimeMinutes = 5; 
            $Form2.Close() 
        })
        
        $B10.Add_Click({ 
            $global:actionTaken = $true; 
            $UserText = if ([string]::IsNullOrWhiteSpace($UserInputBox.Text)) { "[Blank / No User Entry Provided]" } else { $UserInputBox.Text }
            Write-LiveLog "USER SELECTION: Postponed 10 minutes. Custom Entry: $UserText"; 
            $script:waitTimeMinutes = 10; 
            $Form2.Close() 
        })

        $B30.Add_Click({ 
            $global:actionTaken = $true; 
            $UserText = if ([string]::IsNullOrWhiteSpace($UserInputBox.Text)) { "[Blank / No User Entry Provided]" } else { $UserInputBox.Text }
            Write-LiveLog "USER SELECTION: Postponed 30 minutes. Custom Entry: $UserText"; 
            $script:waitTimeMinutes = 30; 
            $Form2.Close() 
        })
        
        $BEnd.Add_Click({ 
            $global:actionTaken = $true; 
            $global:shouldLogOff = $true; 
            Write-LiveLog "USER SELECTION: Immediate log-off requested."; 
            $script:scriptLooping = $false; 
            $Form2.Close() 
        })
        
        $Form2.Controls.AddRange(@($BCustom, $B5, $B10, $B30, $BEnd))
        
        $FlashTimer2.Start()
        $Form2.ShowDialog() | Out-Null
        $FlashTimer2.Stop()
        $FlashTimer2.Dispose()
    } else {
        $script:scriptLooping = $false
    }

    # Monitor update countdown execution logic
    if ($script:waitTimeMinutes -gt 0) {
        $global:hasSnoozedBefore = $true
        $TotalSeconds = $script:waitTimeMinutes * 60
        
        while ($TotalSeconds -gt 0) {
            $RemainingMinutes = [Math]::Ceiling($TotalSeconds / 60)
            Write-LiveLog "COUNTDOWN: Deferral active. Remaining minutes: $RemainingMinutes"
            
            $SleepInterval = [System.Math]::Min(60, $TotalSeconds)
            Start-Sleep -Seconds $SleepInterval
            $TotalSeconds -= $SleepInterval
        }
    } else {
        $scriptLooping = $false
    }
}

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# FINALIZATION
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
if ($global:shouldLogOff) { 
    Execute-SystemLogOff 
} else {
    Write-LiveLog "SESSION: Log-off was not required by user choice."
}

Write-LiveLog "Task execution trace ended. Cleanup complete."
exit 0