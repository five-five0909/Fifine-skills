#Requires -Version 7
<#
trans 双客户端安装器：Claude Code + Codex CLI 通用。

不会移动/复制仓库文件——共享源就是"当前运行本脚本所在的目录"，两个客户端都创建 Skill 链接指向这里，
满足"单一源码"原则，同时避免对用户的 git 工作区做有风险的自动搬迁。如果你想搬到统一的
~/.agent-tools/trans 共享目录，用 scripts/migrate-config.mjs（需交互确认，不会静默移动文件）。

用法：
  .\install.ps1                                     # 双客户端安装（缺哪个 CLI 跳过哪个，不中断）
  .\install.ps1 -Clients claude                      # 只装 Claude Code
  .\install.ps1 -Clients codex                       # 只装 Codex CLI
  .\install.ps1 -BaseUrl https://api.mistral.ai/v1 -ApiKey sk-xxx -Model mistral-embed
  .\install.ps1 -Provider local -LocalDtype q8        # 本地模型档
  .\install.ps1 -SkipIndex                            # 跳过初始索引
  .\install.ps1 -ExactOnly                            # 不配 embedding，仅关键词检索
#>
param(
    [string[]]$Clients = @('claude', 'codex'),
    [ValidateSet('api', 'local')][string]$Provider,
    [string]$BaseUrl,
    [string]$ApiKey,
    [string]$Model,
    [string]$RerankModel,
    [string]$LocalDtype,
    [switch]$SkipIndex,
    [switch]$ExactOnly
)
$ErrorActionPreference = 'Stop'
$skillDir = $PSScriptRoot

Write-Host "trans 安装器 —— 共享源目录: $skillDir" -ForegroundColor Cyan

function New-SkillLink {
    param([string]$Target, [string]$Source)
    $parent = Split-Path $Target -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    if (Test-Path $Target) {
        $item = Get-Item $Target -Force
        $isLink = $item.LinkType -eq 'Junction' -or $item.LinkType -eq 'SymbolicLink'
        if ($isLink) {
            $currentTarget = $item.Target
            if ($currentTarget -is [array]) { $currentTarget = $currentTarget[0] }
            if ($currentTarget -eq $Source) {
                Write-Host "  = 已存在且指向正确: $Target" -ForegroundColor DarkGray
                return
            }
            Write-Host "  ⚠ $Target 已是链接但指向别处 ($currentTarget)，重建为指向当前仓库" -ForegroundColor Yellow
            Remove-Item $Target -Force -Recurse
        } else {
            Write-Host "  ⚠ $Target 已存在且是普通目录（非本安装器创建的链接），跳过，不覆盖用户数据" -ForegroundColor Yellow
            return
        }
    }
    New-Item -ItemType Junction -Path $Target -Target $Source | Out-Null
    Write-Host "  ✓ 创建链接: $Target -> $Source" -ForegroundColor Green
}

function Install-ClaudeClient {
    $target = Join-Path $HOME '.claude\skills\trans'
    New-SkillLink -Target $target -Source $skillDir
}

function Install-CodexClient {
    $target = Join-Path $HOME '.codex\skills\trans'
    New-SkillLink -Target $target -Source $skillDir
    # 通用 agent 目录：部分 CLI/agent（含 Codex）以及未来客户端会去 ~/.agents/skills 发现 Skill，
    # 与上面 Codex 专属链接并存，两条都指向同一份源目录。
    $agentsTarget = Join-Path $HOME '.agents\skills\trans'
    New-SkillLink -Target $agentsTarget -Source $skillDir
}

# 1. 生成/更新配置（单一真相层：write-config.mjs，PS/bash 共用）
if ($ExactOnly) {
    node (Join-Path $skillDir 'scripts\write-config.mjs') --provider api --apiKey ''
    Write-Host '仅关键词模式：跳过 embedding 配置，semantic/hybrid 不可用，exact 立即可用'
} else {
    $cfgArgs = @()
    foreach ($p in @(
            @('provider', $Provider), @('baseUrl', $BaseUrl), @('apiKey', $ApiKey),
            @('model', $Model), @('rerankModel', $RerankModel), @('localDtype', $LocalDtype))) {
        if ($p[1]) { $cfgArgs += "--$($p[0])"; $cfgArgs += $p[1] }
    }
    node (Join-Path $skillDir 'scripts\write-config.mjs') @cfgArgs
}

# 2. 逐客户端安装
foreach ($c in $Clients) {
    switch ($c) {
        'claude' { Write-Host "`n[Claude Code]"; Install-ClaudeClient }
        'codex' { Write-Host "`n[Codex CLI]"; Install-CodexClient }
        default { Write-Host "未知客户端: $c（支持 claude / codex）" -ForegroundColor Yellow }
    }
}

# 3. 首次自检：验证 embedding 配置，并后台启动适合当前配置的初始索引。
$bootstrapArgs = @((Join-Path $skillDir 'scripts\bootstrap.mjs'), '--clients', ($Clients -join ','))
if ($SkipIndex) { $bootstrapArgs += '--no-index' }
node @bootstrapArgs

# 4. 汇总
Write-Host "`n── 安装完成 ──" -ForegroundColor Cyan
Write-Host "  共享源目录   : $skillDir"
Write-Host "  Claude Skill : $(Join-Path $HOME '.claude\skills\trans')"
Write-Host "  Codex Skill  : $(Join-Path $HOME '.codex\skills\trans')"
Write-Host "  Agents Skill : $(Join-Path $HOME '.agents\skills\trans')"
Write-Host "  验证         : node scripts\doctor.mjs"
Write-Host "  卸载         : .\uninstall.ps1 -Clients claude,codex        （加 -Purge 连索引/配置一起删）"
