param(
    [switch]$DryRun
)

# =============================================================================
# 24/7 Continuous Job-Application Watchdog & Quota-Recovery Runner
# =============================================================================
# 1. Auto-discovers newest VS Code / standalone Claude Code CLI (`claude`).
# 2. Streams live `[Claude]` & `[Claude Tool]` progress in PowerShell.
# 3. Detects REAL Claude session/quota limits ONLY on actual error results
#    (`is_error == true` or `exitCode != 0`), never false-matching file text.
# 4. Enforces HARD anti-shortcut gate: runs back-to-back (5s pause) while
#    `ready_to_submit_immediately` is non-empty OR ANY portal in
#    `sweep_state.json` lacks `backlog_14d_completed == true` +
#    `verified_14d_screened_count >= 15`. Switches to 30m real-time sweeps
#    ONLY after all 14-day portals pass verification.
# =============================================================================

$ErrorActionPreference = "Continue"
$HandoffDir    = $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $HandoffDir
Set-Location $WorkspaceRoot

$PythonExe  = if ($env:PYTHON_EXE) { $env:PYTHON_EXE } else { "python" }
$StopFile   = Join-Path $HandoffDir "STOP_24X7"
$StateFile  = Join-Path $HandoffDir "sweep_state.json"
$LogFile    = Join-Path $HandoffDir "watchdog_24x7.log"
$BridgeJs   = Join-Path $HandoffDir "cdp_bridge.js"

if (-not $DryRun -and (Test-Path $StopFile)) {
    Remove-Item $StopFile -Force
}

function Write-WatchdogLog([string]$msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ssK")
    $line = "[$ts] $msg"
    Write-Host $line -ForegroundColor Cyan
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Resolve-ClaudeCli {
    $extRoots = @(
        "$env:USERPROFILE\.vscode\extensions",
        "$env:USERPROFILE\.cursor\extensions",
        "$env:USERPROFILE\.antigravity\extensions"
    )
    $candidates = @()
    foreach ($root in $extRoots) {
        if (Test-Path $root) {
            $found = Get-ChildItem -Path $root -Directory -Filter "anthropic.claude-code-*" -ErrorAction SilentlyContinue |
                ForEach-Object { Join-Path $_.FullName "resources\native-binary\claude.exe" } |
                Where-Object { Test-Path $_ }
            $candidates += $found
        }
    }
    if ($candidates.Count -gt 0) {
        $newest = $candidates | Get-Item | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        return $newest.FullName
    }

    $standalonePaths = @(
        "$env:USERPROFILE\.local\bin\claude.exe",
        "$env:APPDATA\npm\claude.cmd"
    )
    foreach ($p in $standalonePaths) {
        if (Test-Path $p) { return $p }
    }

    $cmd = Get-Command claude -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notmatch "AnthropicClaude") {
        return $cmd.Source
    }
    return $null
}

function Ensure-CdpBridge {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:9333" -Method Get -TimeoutSec 3
        if ($resp -eq "OK") { return }
    } catch {}
    Write-WatchdogLog "Starting persistent Chrome CDP bridge on http://127.0.0.1:9333..."
    Start-Process -FilePath "node" -ArgumentList "`"$BridgeJs`"" -WindowStyle Hidden
    Start-Sleep -Seconds 4
}

function Get-OpenBacklogPortals {
    if (-not (Test-Path $StateFile)) { return @("sweep_state_missing") }
    try {
        $st = Get-Content $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $open = @()
        if ($st.ready_to_submit_immediately -and @($st.ready_to_submit_immediately).Count -gt 0) {
            $open += "ready_to_submit_immediately"
        }
        if ($st.portals) {
            foreach ($prop in $st.portals.PSObject.Properties) {
                $pVal = $prop.Value
                $done = [bool]$pVal.backlog_14d_completed
                $cnt  = 0
                if ($null -ne $pVal.verified_14d_screened_count) {
                    $cnt = [int]$pVal.verified_14d_screened_count
                }
                if ((-not $done) -or ($cnt -lt 15)) {
                    $open += $prop.Name
                }
            }
        }
        if ($st.backlog_14d_all_complete -eq $false -and $open.Count -eq 0) {
            $open += "backlog_flag_false"
        }
        return $open
    } catch {
        return @("state_parse_retry")
    }
}

$ClaudeExe = Resolve-ClaudeCli
if (-not $ClaudeExe) {
    Write-Host "ERROR: Could not locate Claude Code CLI binary (claude) on this machine." -ForegroundColor Red
    exit 1
}

$ver = & $ClaudeExe --version 2>&1 | Out-String
Write-WatchdogLog ("Resolved Claude Code CLI: " + $ClaudeExe + " -> " + $ver.Trim())

$initialOpen = Get-OpenBacklogPortals
Write-WatchdogLog ("Open 14-day backlog portals on disk (" + $initialOpen.Count + "): " + ($initialOpen -join ", "))

if ($DryRun) {
    Write-WatchdogLog "DryRun verified OK. Ready for 24/7 execution!"
    exit 0
}

$RunPrompt = @"
run
YOU ARE THE SOLE ACTIVE AGENT IN $WorkspaceRoot (only stop if _agent_handoff/STOP_24X7 exists). Do NOT stop early!
Read CLAUDE.md, AGENTS.md, candidate_profile.json, and _agent_handoff/sweep_state.json, then execute high-throughput applications:
1. Run "$PythonExe" "_agent_handoff/sync_status.py".
2. Drain sweep_state.json -> ready_to_submit_immediately first if non-empty.
3. Run discovery & screening scripts:
   - "$PythonExe" "_agent_handoff/ats_poll.py" - 1
   - "$PythonExe" "_agent_handoff/ats_poll.py" - 14
   - powershell -ExecutionPolicy Bypass -File "_agent_handoff/cdp_scripts/run.ps1" -Script "_agent_handoff/cdp_scripts/s_sp.js"
   - "$PythonExe" "_agent_handoff/screen_google.py" "_agent_handoff/_sp_out.json"
   - "$PythonExe" "_agent_handoff/harvest_all_portals.py" --window 24h
   - "$PythonExe" "_agent_handoff/screen_harvest.py" "_agent_handoff/latest_multi_portal_harvest.json"
4. PHASE 1 (<24h Sweep FIRST) + PHASE 2 (14-Day Open Portals in sweep_state.json):
   - Sweep <24h new postings first, then work deeply through AT LEAST 3-5 unfinished backlog_14d_completed == false portals in sweep_state.json per session (state_upd.py requires --screened <N> with N >= 15!).
   - For EVERY Green Zone match: build tailored 1-page Resume + humanized Cover Letter (auto_tailor.py + validate_resume_pdf.py + ats_keyword_check.py + gen_ats_analysis.py), submit via background Chrome tab (http://127.0.0.1:9333), save confirmation.png inside the job folder, and log immediately to Application_Tracker.xlsx (update_tracker_batch.py) or Manual_Apply_Queue.xlsx (update_manual_queue.py if gated by CAPTCHA/security/legal declaration).
"@

Write-WatchdogLog "=== 24/7 Autonomous Job-Application Watchdog Running in $WorkspaceRoot ==="

while (-not (Test-Path $StopFile)) {
    $CurrentClaude = Resolve-ClaudeCli
    if ($CurrentClaude) { $ClaudeExe = $CurrentClaude }

    Ensure-CdpBridge
    Write-WatchdogLog "Launching Claude autonomous sweep cycle (live progress streaming below)..."

    $resultIsError = $false
    $resultMessage = ""
    $nonJsonErrors = New-Object System.Text.StringBuilder

    & $ClaudeExe -p $RunPrompt --dangerously-skip-permissions --output-format stream-json --verbose 2>&1 | ForEach-Object {
        $rawLine = [string]$_
        Add-Content -Path $LogFile -Value $rawLine -Encoding UTF8

        if ($rawLine.StartsWith("{")) {
            try {
                $evt = $rawLine | ConvertFrom-Json -ErrorAction Stop
                if ($evt.type -eq "assistant" -and $evt.message -and $evt.message.content) {
                    foreach ($blk in $evt.message.content) {
                        if ($blk.type -eq "text" -and $blk.text) {
                            Write-Host ("[Claude] " + $blk.text.Trim()) -ForegroundColor Green
                        } elseif ($blk.type -eq "tool_use") {
                            Write-Host ("[Claude Tool] " + $blk.name) -ForegroundColor Yellow
                        }
                    }
                } elseif ($evt.type -eq "result") {
                    $resultIsError = [bool]$evt.is_error
                    $resultMessage = [string]$evt.result
                    if ($resultIsError) {
                        Write-Host ("[Claude Error] " + $resultMessage) -ForegroundColor Red
                    } else {
                        Write-Host ("[Claude Cycle Complete] Turns: " + $evt.num_turns) -ForegroundColor Cyan
                    }
                }
            } catch {}
        } elseif ($rawLine.Trim().Length -gt 0) {
            [void]$nonJsonErrors.AppendLine($rawLine)
            Write-Host $rawLine
        }
    }

    $exitCode = $LASTEXITCODE
    $errCheckText = ($resultMessage + "`n" + $nonJsonErrors.ToString())

    if (($resultIsError -or $exitCode -ne 0) -and ($errCheckText -match "(?i)(hit your limit|rate.?limit|usage limit|out of extra usage|quota|resets \d|429|overloaded)")) {
        Write-WatchdogLog "REAL session token / 5h quota limit reached (exit=$exitCode). Sleeping 15 minutes and auto-resuming when quota resets..."
        for ($i = 0; $i -lt 15; $i++) {
            if (Test-Path $StopFile) { break }
            Start-Sleep -Seconds 60
        }
        continue
    }

    if ($exitCode -ne 0 -and $resultIsError) {
        Write-WatchdogLog "Unexpected CLI error (exit=$exitCode). Retrying in 2 minutes..."
        for ($i = 0; $i -lt 2; $i++) {
            if (Test-Path $StopFile) { break }
            Start-Sleep -Seconds 60
        }
        continue
    }

    $openPortals = Get-OpenBacklogPortals
    if ($openPortals.Count -gt 0) {
        Write-WatchdogLog ("14-day backlog still has " + $openPortals.Count + " open portals (" + ($openPortals -join ", ") + ") -> continuing next batch IMMEDIATELY in 5 seconds...")
        Start-Sleep -Seconds 5
        continue
    }

    Write-WatchdogLog "All <24h + 14-day backlog portals verified complete (>=15 cards each)! Sleeping 30 minutes before next real-time 21-portal sweep..."
    for ($i = 0; $i -lt 30; $i++) {
        if (Test-Path $StopFile) { break }
        Start-Sleep -Seconds 60
    }
}

Write-WatchdogLog "=== STOP_24X7 detected. Watchdog exited cleanly. ==="
