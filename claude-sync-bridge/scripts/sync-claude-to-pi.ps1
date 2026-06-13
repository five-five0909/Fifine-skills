#requires -Version 7.0
<#
.SYNOPSIS
  Safely sync Claude Code global skills and MCP servers to Pi.

.DESCRIPTION
  Source of truth: Claude Code user config and skills.
  Target: Pi global agent config and skills.

  This script intentionally does NOT configure Pi mcp.json with
  imports: ["claude-code"], because a malformed Claude MCP server can break
  Pi MCP startup. Instead it materializes a filtered Pi-native mcp.json.

.PARAMETER DryRun
  Preview planned changes without writing files.

.PARAMETER VerifyPi
  After sync, run a lightweight Pi MCP status prompt.

.PARAMETER AllowBraveSearch
  Allow a server named brave-search if it is otherwise valid. Disabled by default.

.PARAMETER KeepPiClaudeSkillsReference
  Keep ~/.claude/skills entries in Pi settings.json. Disabled by default to avoid duplicates.
#>

[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$VerifyPi,
  [switch]$AllowBraveSearch,
  [switch]$KeepPiClaudeSkillsReference
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" }
function Write-Ok([string]$Message) { Write-Host "[OK]   $Message" }
function Write-WarnLine([string]$Message) { Write-Host "[WARN] $Message" }
function Write-Fail([string]$Message) { Write-Host "[FAIL] $Message" }

function ConvertTo-PlainObject {
  param($Value)

  if ($null -eq $Value) { return $null }

  if ($Value -is [System.Collections.IDictionary]) {
    $result = [ordered]@{}
    foreach ($key in $Value.Keys) {
      $result[[string]$key] = ConvertTo-PlainObject -Value $Value[$key]
    }
    return $result
  }

  if ($Value -is [pscustomobject]) {
    $result = [ordered]@{}
    foreach ($property in $Value.PSObject.Properties) {
      $result[$property.Name] = ConvertTo-PlainObject -Value $property.Value
    }
    return $result
  }

  if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
    $items = @()
    foreach ($item in $Value) {
      $items += ,(ConvertTo-PlainObject -Value $item)
    }
    return $items
  }

  return $Value
}

function Test-ServerEntryValid {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    $Entry
  )

  if ($null -eq $Entry) { return $false }

  $hasCommand = $false
  $hasUrl = $false

  if ($Entry -is [System.Collections.IDictionary]) {
    $hasCommand = $Entry.Contains('command') -and -not [string]::IsNullOrWhiteSpace([string]$Entry['command'])
    $hasUrl = $Entry.Contains('url') -and -not [string]::IsNullOrWhiteSpace([string]$Entry['url'])
  } else {
    $commandProperty = $Entry.PSObject.Properties['command']
    $urlProperty = $Entry.PSObject.Properties['url']
    $hasCommand = $null -ne $commandProperty -and -not [string]::IsNullOrWhiteSpace([string]$commandProperty.Value)
    $hasUrl = $null -ne $urlProperty -and -not [string]::IsNullOrWhiteSpace([string]$urlProperty.Value)
  }

  return ($hasCommand -or $hasUrl)
}

function Copy-DirectorySafe {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination
  )

  if (!(Test-Path -LiteralPath $Source)) {
    throw "source directory does not exist: $Source"
  }

  if (Test-Path -LiteralPath $Destination) {
    Remove-Item -LiteralPath $Destination -Recurse -Force
  }

  New-Item -ItemType Directory -Path $Destination -Force | Out-Null
  $children = Get-ChildItem -LiteralPath $Source -Force
  foreach ($child in $children) {
    Copy-Item -LiteralPath $child.FullName -Destination $Destination -Recurse -Force
  }
}

function Add-PiCompatibilityNote {
  param([Parameter(Mandatory = $true)][string]$SkillFile)

  if (!(Test-Path -LiteralPath $SkillFile)) { return }

  $text = Get-Content -LiteralPath $SkillFile -Raw -Encoding UTF8
  if ($text -match 'Pi 同步兼容说明') { return }

  $note = @'

> Pi 同步兼容说明：此 skill 由 `claude-sync-bridge` 从 Claude Code 全局 skills 同步而来。若正文出现 Claude Code 专用工具名或命令，请在 Pi 中按可用工具替换；MCP 调用优先使用 Pi 的 `mcp(...)` 代理工具。

'@

  if ($text -match '(?s)^---\s*\r?\n.*?\r?\n---\s*\r?\n') {
    $updated = [regex]::Replace($text, '(?s)^(---\s*\r?\n.*?\r?\n---\s*\r?\n)', "`$1$note", 1)
  } else {
    $updated = $note + $text
  }

  Set-Content -LiteralPath $SkillFile -Value $updated -Encoding UTF8
}

function Get-RootMcpServersFromClaudeConfig {
  param([Parameter(Mandatory = $true)]$ClaudeConfig)

  $property = $ClaudeConfig.PSObject.Properties['mcpServers']
  if ($null -eq $property -or $null -eq $property.Value) {
    return [ordered]@{}
  }

  return ConvertTo-PlainObject -Value $property.Value
}

function ConvertTo-RedactedServerSummary {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)]$Entry
  )

  $mode = 'unknown'
  if ($Entry -is [System.Collections.IDictionary]) {
    if ($Entry.Contains('url')) { $mode = 'http' }
    elseif ($Entry.Contains('command')) { $mode = 'stdio' }
  }

  return "$Name ($mode)"
}

function Backup-FileIfExists {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (!(Test-Path -LiteralPath $Path)) { return $null }

  $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $backup = "$Path.bak-$timestamp"
  Copy-Item -LiteralPath $Path -Destination $backup -Force
  return $backup
}

function Remove-ClaudeSkillsReferencesFromPiSettings {
  param([Parameter(Mandatory = $true)][string]$SettingsPath)

  if (!(Test-Path -LiteralPath $SettingsPath)) {
    Write-WarnLine "Pi settings.json not found, skip skills reference cleanup: $SettingsPath"
    return
  }

  $settings = Get-Content -LiteralPath $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $skillsProperty = $settings.PSObject.Properties['skills']
  if ($null -eq $skillsProperty) { return }

  $oldSkills = @($skillsProperty.Value)
  $newSkills = @()
  foreach ($item in $oldSkills) {
    $text = [string]$item
    $normalized = $text.Replace('\\', '/').ToLowerInvariant()
    if ($normalized -eq '~/.claude/skills' -or $normalized.EndsWith('/.claude/skills')) {
      continue
    }
    $newSkills += $item
  }

  $settings.skills = $newSkills
  $settings | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $SettingsPath -Encoding UTF8
}

try {
  $homePath = [Environment]::GetFolderPath('UserProfile')
  if ([string]::IsNullOrWhiteSpace($homePath)) {
    throw 'Unable to resolve USERPROFILE.'
  }

  $claudeConfigPath = Join-Path $homePath '.claude.json'
  $claudeSkillsPath = Join-Path $homePath '.claude/skills'
  $piAgentPath = Join-Path $homePath '.pi/agent'
  $piMcpPath = Join-Path $piAgentPath 'mcp.json'
  $piSettingsPath = Join-Path $piAgentPath 'settings.json'
  $piSkillsPath = Join-Path $piAgentPath 'skills'

  Write-Info "Mode: $(if ($DryRun) { 'dry-run' } else { 'apply' })"
  Write-Info 'Source: Claude Code global config and skills'
  Write-Info 'Target: Pi global agent config and skills'

  if (!(Test-Path -LiteralPath $claudeConfigPath)) {
    throw "Claude Code config not found: $claudeConfigPath"
  }

  if (!(Test-Path -LiteralPath $claudeSkillsPath)) {
    Write-WarnLine "Claude skills directory not found, skills sync will be skipped: $claudeSkillsPath"
  }

  if (!(Test-Path -LiteralPath $piAgentPath)) {
    if ($DryRun) {
      Write-WarnLine "Pi agent directory does not exist and would be created: $piAgentPath"
    } else {
      New-Item -ItemType Directory -Path $piAgentPath -Force | Out-Null
    }
  }

  $claudeConfig = Get-Content -LiteralPath $claudeConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $sourceServers = Get-RootMcpServersFromClaudeConfig -ClaudeConfig $claudeConfig

  $filteredServers = [ordered]@{}
  $skippedServers = @()

  foreach ($name in $sourceServers.Keys) {
    $entry = $sourceServers[$name]

    if ($name -eq 'brave-search' -and -not $AllowBraveSearch) {
      $skippedServers += "$name (blocked by default)"
      continue
    }

    if (!(Test-ServerEntryValid -Name $name -Entry $entry)) {
      $skippedServers += "$name (invalid: missing command/url)"
      continue
    }

    $filteredServers[$name] = $entry
  }

  $targetMcp = [ordered]@{
    mcpServers = $filteredServers
  }

  Write-Info "Valid MCP servers to sync: $($filteredServers.Count)"
  foreach ($name in $filteredServers.Keys) {
    Write-Host "  + $(ConvertTo-RedactedServerSummary -Name $name -Entry $filteredServers[$name])"
  }

  if ($skippedServers.Count -gt 0) {
    Write-WarnLine "Skipped MCP servers:"
    foreach ($item in $skippedServers) { Write-Host "  - $item" }
  }

  $skillDirs = @()
  if (Test-Path -LiteralPath $claudeSkillsPath) {
    $skillDirs = Get-ChildItem -LiteralPath $claudeSkillsPath -Directory | Where-Object {
      Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md')
    }
  }

  Write-Info "Claude skills to sync: $($skillDirs.Count)"
  foreach ($dir in $skillDirs) { Write-Host "  + $($dir.Name)" }

  if ($DryRun) {
    Write-Ok 'Dry-run complete. No files were changed.'
    Write-Info "Would write Pi MCP: $piMcpPath"
    Write-Info "Would sync skills into: $piSkillsPath"
    if (-not $KeepPiClaudeSkillsReference) {
      Write-Info "Would remove ~/.claude/skills from Pi settings: $piSettingsPath"
    }
    exit 0
  }

  New-Item -ItemType Directory -Path $piAgentPath -Force | Out-Null
  New-Item -ItemType Directory -Path $piSkillsPath -Force | Out-Null

  $mcpBackup = Backup-FileIfExists -Path $piMcpPath
  if ($null -ne $mcpBackup) { Write-Info "Backed up old Pi MCP config: $mcpBackup" }

  $targetMcp | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $piMcpPath -Encoding UTF8
  Get-Content -LiteralPath $piMcpPath -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
  Write-Ok "Wrote Pi MCP config: $piMcpPath"

  foreach ($dir in $skillDirs) {
    $destination = Join-Path $piSkillsPath $dir.Name
    Copy-DirectorySafe -Source $dir.FullName -Destination $destination
    Add-PiCompatibilityNote -SkillFile (Join-Path $destination 'SKILL.md')
  }
  Write-Ok "Synced skills into Pi: $piSkillsPath"

  if (-not $KeepPiClaudeSkillsReference) {
    Remove-ClaudeSkillsReferencesFromPiSettings -SettingsPath $piSettingsPath
    if (Test-Path -LiteralPath $piSettingsPath) {
      Get-Content -LiteralPath $piSettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
    }
    Write-Ok "Cleaned Pi settings skills reference: $piSettingsPath"
  } else {
    Write-WarnLine 'Kept Pi settings reference to ~/.claude/skills by request.'
  }

  if ($VerifyPi) {
    $piCommand = Get-Command pi -ErrorAction SilentlyContinue
    if ($null -eq $piCommand) {
      Write-WarnLine 'pi command not found in PATH, skip Pi verification.'
    } else {
      Write-Info 'Running Pi MCP verification...'
      $env:PI_OFFLINE = '1'
      $env:PI_SKIP_VERSION_CHECK = '1'
      $env:PI_TELEMETRY = '0'
      & pi -p 'mcp({ })' --no-prompt-templates --no-themes --no-context-files
    }
  }

  Write-Ok 'Claude Code → Pi sync complete.'
  Write-Host ''
  Write-Host 'Next step: run /reload in Pi or restart Pi to activate new MCP and skills.'
  Write-Host 'Claude Code config was not modified.'
} catch {
  Write-Fail $_.Exception.Message
  Write-Host 'Suggested next step: run this script again with -DryRun and inspect the warning list.'
  exit 1
}
