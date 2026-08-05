# 安全与合规政策

Academic Component Hook Radar 系统遵守以下安全规则。

## 1. 开放 API 优先

默认只使用以下完全开放的 API：
- arXiv REST API
- Semantic Scholar API
- OpenAlex API
- Crossref REST API
- Unpaywall API
- Papers with Code API

以上 API 均无需账号，无需 Cookie，无需机构认证。

## 2. CDP 浏览器自动化

CDP（Chrome DevTools Protocol）模式为可选功能，默认禁用。

- 启用方式：运行时加 `--cdp` 参数
- 仅复用用户本机 Chrome 已存在的合法登录态
- 不保存、不导出、不持久化任何 Cookie / Session Token
- 不创建新账号，不执行任何登录操作

## 3. PDF 获取

- 只自动下载 `pdf_status = open_pdf` 的合法开放资源
- 需要机构权限的论文标记为 `pdf_status = needs_institution`，由用户手动下载
- 不绕过付费墙、验证码、Cloudflare、机构认证

## 4. 明确禁止

- 禁止使用 Sci-Hub、LibGen 或任何非法镜像
- 禁止使用 WebVPN、Tor 或任何代理绕过访问限制
- 禁止保存账号密码到项目任何文件中
- 禁止将机构认证 Cookie / Session Token 导出到项目目录
- 禁止爬取未公开授权的付费数据库内容

## 5. 数据存储

- 所有输出文件（HTML/Markdown/JSON）只存储论文元数据和分析结果
- 不存储任何用户认证凭据
- outputs/ 目录建议加入 .gitignore，避免意外提交大量报告文件
