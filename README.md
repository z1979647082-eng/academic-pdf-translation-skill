# academic-pdf-translation-skill

这是一个可复用的 Codex Skill，用于翻译学术 PDF、论文 PDF、专利 PDF、实验方案 PDF 或技术资料 PDF。它可以输出中文译文，并尽量保留原 PDF 中的图片，最终生成带原图的中文 PDF。

## 文件结构

- `SKILL.md`：Skill 的主说明文件，定义输入处理、翻译流程、术语表规则、图片提取和 PDF 输出规则。
- `scripts/`：PDF 检查、文本提取、文本拆分、图片提取和 PDF 导出的脚本。
- `prompts/`：术语表、翻译、质量检查、表格翻译等提示词模板。
- `resources/`：默认术语库、领域术语库、易冲突缩写表和单篇论文术语库目录。
- `requirements.txt`：运行脚本所需的 Python 依赖。
- `USAGE_EXAMPLES.md`：常用调用示例。

## 安装依赖

在 Skill 目录中运行：

```bash
python -m pip install -r requirements.txt
```

如果 Windows 上 `python` 命令不可用，可以尝试：

```bash
py -m pip install -r requirements.txt
```

如果 `python` 和 `py` 都不可用，请提供你自己的 Python 解释器路径。例如：

```text
C:\Users\用户名\AppData\Local\Programs\Python\Python312\python.exe
```

然后用该路径运行安装命令：

```bash
"C:\Users\用户名\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
```

## Codex 使用方法

上传 PDF 后，对 Codex 说：

```text
调用 academic-pdf-translation-skill 翻译我上传的 PDF，并输出带原图的中文 PDF。
```

Skill 默认会把上传的 PDF 保存为 `input.pdf`，然后进行 PDF 检查、文本提取、文本块拆分、术语表生成、翻译、质量检查、图片提取和带图 PDF 输出。

## 默认输出位置

最终带图中文 PDF 默认输出到：

```text
output/translation_final_inline_figures_final.pdf
```

常见输出还包括：

- `output/translation_final.md`
- `output/paper_glossary.csv`
- `output/merge_candidates.csv`
- `output/quality_check_full.md`
- `output/extracted_figures/`
- `output/figure_mapping_report.md`
- `output/inline_figure_report.md`

## 常见问题

### python 命令不可用怎么办？

先尝试 `py`：

```bash
py -m pip install -r requirements.txt
```

如果 `python` 和 `py` 都不可用，请安装 Python，或把你自己的 Python 解释器路径提供给 Codex。

### PyMuPDF 未安装怎么办？

运行：

```bash
python -m pip install -r requirements.txt
```

如果只想单独安装 PyMuPDF：

```bash
python -m pip install pymupdf
```

### 中文 PDF 显示方框乱码怎么办？

带图 PDF 应使用 ReportLab 并注册系统中文字体，不要用 PyMuPDF 直接写中文正文。Windows 下会优先尝试：

```text
C:\Windows\Fonts\msyh.ttc
C:\Windows\Fonts\simsun.ttc
C:\Windows\Fonts\simhei.ttf
```

如果仍然乱码，请确认系统中存在可用中文字体。

### CO₂ 显示成 CO 怎么办？

如果 PDF 字体或导出链路不能稳定显示 `CO₂`，导出 PDF 时应统一写为 `CO2`，不能丢失数字 `2`。

### 图片没有插入正文怎么办？

Skill 会优先把图片插入正文首次提到该图的位置附近。如果无法可靠定位某张图，会把该图放到文末图版部分，并在 `output/inline_figure_report.md` 或 `output/figure_mapping_report.md` 中说明原因。

### 术语表越来越大怎么办？

不要把每篇论文生成的 `output/paper_glossary.csv` 自动合并到长期术语库。Skill 默认只生成 `output/merge_candidates.csv` 供用户人工确认，只有长期可复用术语才建议加入 `resources/domain_glossary.csv`。

## 版权提醒

本 Skill 只提供 PDF 翻译和排版流程。用户应确保自己有权处理上传的 PDF。不要公开分享包含版权论文全文、原图或完整译文的 `output/` 文件。
