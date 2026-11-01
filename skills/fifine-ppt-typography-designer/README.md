# PPT Typography Designer

为 OMP、Claude Code、CodeBuddy 等支持 Agent Skills 的工具提供 PPT 字体设计。将本目录按对应工具的安装说明加入其技能目录。

## 字体范围与依赖

默认从 ModelScope 数据集 `fifine/fifine-font` 同步字体到 ModelScope 缓存；首次运行需要网络，字体不会安装到系统。数据集必须包含字体目录（根目录或 `PPT推荐字体/`），并保留方案子目录。其他位置可设置环境变量 `PPT_TYPOGRAPHY_FONT_ROOT` 或传 `--root`，优先级依次为 `--root`、环境变量、ModelScope。需要 Python 3 和 `pip install -r requirements.txt`。私有数据集可通过 `MODELSCOPE_API_TOKEN` 环境变量提供令牌，也可使用 ModelScope 登录凭据；不要把令牌写入仓库。若远端没有字体，将明确报错；请先上传完整字体库，或显式指定已有本地目录。字体授权需逐一核实。

在本源码项目中，若令牌保存在被 Git 忽略的 `.env.ppt-typography.local`，先执行 `set -a; source .env.ppt-typography.local; set +a`（Bash），再运行下列命令。该文件是明文，不随仓库分发；其他安装环境应自行配置环境变量。

字体意向涵盖思源宋体、思源黑体、MiSans、阿里巴巴普惠体、霞鹜文楷、优设标题黑、Space Grotesk、IBM Plex Mono、Nunito 和 Quicksand；目录中还记录了新愚公装甲宋 A/B。八套搭配见 `references/eight-design-styles.md`，历史 220 个字体文件及其 SHA256 见 `references/font-manifest.json`。清单不代表远端当前拥有这些文件，也不代表授权可用于分发。


旧式 `.ppt` 转换还需要 Windows、桌面版 PowerPoint 和 Python 包 `pywin32`；这些条件未满足时转换会明确失败，原文件保持不变。
## 使用

在本目录执行：

```text
python scripts/font_index.py build
python scripts/font_index.py search --name "Space Grotesk"
python scripts/recommend_typography.py --brief "为智控卫士设计一套高端黑金科技 PPT 字体方案"
python scripts/generate_preview.py --output 八套展示.pdf --format pdf
python scripts/generate_preview.py --output 展示.pptx --format pptx --style 03
python scripts/apply_typography.py --input 原稿.pptx --output 新稿.pptx --style 03
```

索引用文件大小和修改时间增量更新；若可能存在时间戳不变的文件替换，使用 `build --force`。索引记录路径相对于字体库根目录；换电脑后重新构建。若字体文件损坏、缺字、未确认安装或授权，报告会列明。可变字体是否由 PPT 软件完整支持取决于软件；预览不能保证 PowerPoint 显示相同。预览 PDF 使用实际字体在本机渲染，公开分发前必须核实字体授权。可编辑 PPTX 不嵌入字体，目标机器需要可用对应字体。

现有 PPTX 在独立输出文件操作，不覆盖原稿；旧版 PPT 需要 Windows PowerPoint 转换，转换可能改变原始文稿。无法安全识别的元素保留并在报告中标注。

OMP 示例：`使用 fifine-ppt-typography-designer，为智控卫士设计黑金科技 PPT 字体方案，并生成展示 PDF。`
