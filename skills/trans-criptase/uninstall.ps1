#Requires -Version 7
<#
trans 双客户端卸载器。
默认只移除 Skill 链接 + MCP 注册，保留配置与索引数据（KeepData 是默认行为，无需显式传参）。
-Purge 才会删除 embed-config.json / config/config.json / index/ / data/ —— 会先列出将删除的路径并要求确认。

用法：
  .\uninstall.ps1 -Clients claude,codex
  .\uninstall.ps1 -Clients claude,codex -Purge
#>
param(
    [string[]]$Clients = @('claude', 'codex'),
    [switch]$Purge
)
$ErrorActionPreference = 'Stop'
$skillDir = $PSScriptRoot

function Remove-SkillLink {
    param([string]$Target)
    if (-not (Test-Path $Target)) { Write-Host "  = 不存在，跳过: $Target" -ForegroundColor DarkGray; return }
    $item = Get-Item $Target -Force
    $isLink = $item.LinkType -eq 'Junction' -or $item.LinkType -eq 'SymbolicLink'
    if (-not $isLink) {
        Write-Host "  ⚠ $Target 不是本安装器创建的链接（是普通目录），跳过，不删除" -ForegroundColor Yellow
        return
    }
    Remove-Item $Target -Force -Recurse
    Write-Host "  ✓ 已移除链接: $Target" -ForegroundColor Green
}

foreach ($c in $Clients) {
    switch ($c) {
        'claude' {
            Write-Host "`n[Claude Code]"
            Remove-SkillLink -Target (Join-Path $HOME '.claude\skills\trans')
            if (Get-Command claude -ErrorAction SilentlyContinue) {
                try { claude mcp remove trans *>$null; Write-Host '  ✓ 已移除 Claude MCP 注册' -ForegroundColor Green }
                catch { Write-Host '  ⚠ 移除 Claude MCP 注册失败（可能本就未注册）' -ForegroundColor Yellow }
            }
        }
        'codex' {
            Write-Host "`n[Codex CLI]"
            Remove-SkillLink -Target (Join-Path $HOME '.agents\skills\trans')
            if (Get-Command codex -ErrorAction SilentlyContinue) {
                try { codex mcp remove trans *>$null; Write-Host '  ✓ 已移除 Codex MCP 注册' -ForegroundColor Green }
                catch { Write-Host '  ⚠ 移除 Codex MCP 注册失败（可能本就未注册）' -ForegroundColor Yellow }
            }
        }
        default { Write-Host "未知客户端: $c（支持 claude / codex）" -ForegroundColor Yellow }
    }
}

if ($Purge) {
    $targets = @(
        (Join-Path $skillDir 'embed-config.json'),
        (Join-Path $skillDir 'config\config.json'),
        (Join-Path $skillDir 'index'),
        (Join-Path $skillDir 'data')
    ) | Where-Object { Test-Path $_ }

    if (-not $targets.Count) {
        Write-Host "`n-Purge：没有发现配置/索引数据，无需清理"
    } else {
        Write-Host "`n-Purge：将删除以下路径（配置 + 索引数据）：" -ForegroundColor Yellow
        $targets | ForEach-Object { Write-Host "  - $_" }
        $confirm = Read-Host '确认删除？输入 yes 继续'
        if ($confirm -eq 'yes') {
            $targets | ForEach-Object { Remove-Item $_ -Recurse -Force }
            Write-Host '  ✓ 已清理' -ForegroundColor Green
        } else {
            Write-Host '  已取消，未删除任何数据'
        }
    }
} else {
    Write-Host "`n配置与索引数据已保留（默认行为）。如需连数据一起删除，加 -Purge。"
}
