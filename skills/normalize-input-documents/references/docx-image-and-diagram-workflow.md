# DOCX 图片与图形补充流程

本文件是 `normalize-input-documents` 的内置参考，用于处理 `.docx` 中仅靠文本和表格抽取无法完整表达的信息。项目不依赖外部转换仓库或固定本机路径。

## 适用场景

当 `bin/normalize-office-input.py` 的 metadata 出现图片数量或转换警告时，进入本流程。

常见需要补充分析的内容包括：

- 架构图、流程图、时序图、状态图、部署图。
- EMF、Visio、Draw.io、截图或粘贴进 Word 的图片。
- 图片中承载接口、组件、状态流转、依赖关系、异常分支或业务规则。

页眉、页脚中的 logo、页码、装饰图通常不进入正文事实源；除非它们承载业务信息，只在过程记录中说明即可。

## 标准流程

1. 先运行输入归一化脚本，得到 Markdown 和 `.conversion.json`。

```bash
python bin/normalize-office-input.py <input.docx>
```

2. 查看 metadata 中的 `image_count` 和 `warnings`。如果图片可能承载设计事实，继续做图片补充。

3. 将 `.docx` 作为 zip 包解压到临时目录，列出 `word/media/` 下的图片。

```python
import zipfile
from pathlib import Path

docx_path = Path(r"<input.docx>")
extract_dir = Path(r"<temp-docx-extract-dir>")
extract_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(docx_path, "r") as package:
    package.extractall(extract_dir)

media_dir = extract_dir / "word" / "media"
for image in sorted(media_dir.glob("*")):
    print(image.name, image.stat().st_size)
```

4. 如果存在 EMF/WMF 等不适合直接视觉分析的格式，优先用 LibreOffice headless 转为 PNG；如果转换结果空白或只剩文字，使用 `strings` 等方式提取可读文本并在过程产物中说明降级。

```bash
libreoffice --headless --convert-to png --outdir <media-dir> <media-dir>/image2.emf
```

5. 对每张业务相关图片做视觉分析，判断类型并抽取事实。

推荐分析提示：

```text
请详细描述这张图片。判断它是架构图、流程图、时序图、状态图、接口图、UI截图、表格截图还是其他类型。
如果是图形，请列出所有节点、箭头、标签、条件、异常分支和依赖关系。
如果适合转 Mermaid，请给出 Mermaid；如果不适合，请给出可用于测试分析/测试设计的结构化文字描述。
```

6. 将补充结果追加到归一化输入的过程记录中，或在 `process/context-pack.md` 记录“图片补充事实源”。不要把未经确认的图片推断直接写入主交付件；主交付件只能承接已经有证据的接口、流程、状态或依赖。

## 图片插入位置识别

如果需要知道图片在正文中的上下文位置，可解析 `word/document.xml` 和 `word/_rels/document.xml.rels`。

核心方法：

- 读取 `document.xml.rels`，建立 relationship id 到图片文件名的映射。
- 在 `document.xml` 中搜索 drawing/blip 的 embed id。
- 取 embed 前后若干 XML 片段，结合附近段落或表格判断图片位置。
- 页眉页脚图片从 `header*.xml.rels` 或 `footer*.xml.rels` 识别，默认不写入正文。

示例片段：

```python
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

extract_dir = Path(r"<temp-docx-extract-dir>")
rels = extract_dir / "word" / "_rels" / "document.xml.rels"
doc_xml = extract_dir / "word" / "document.xml"

img_map = {}
rels_root = ET.parse(rels).getroot()
for rel in rels_root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
    if "image" in rel.get("Type", ""):
        img_map[rel.get("Id")] = os.path.basename(rel.get("Target", ""))

raw = doc_xml.read_text(encoding="utf-8", errors="ignore")
for match in re.finditer(r'embed="([^"]+)"', raw):
    embed_id = match.group(1)
    target = img_map.get(embed_id, embed_id)
    context = raw[max(0, match.start() - 500): match.end() + 500]
    print(target, context[:300])
```

## Markdown 补充格式

图片事实补充可以采用以下形式，供后续测试分析和测试设计读取。

图形适合 Mermaid 时：

````markdown
### 图片补充：<图片文件名或图题>

```mermaid
flowchart TD
  A["节点A"] --> B["节点B"]
```

- 来源：<docx 文件名> / <图片文件名>
- 说明：<从图片可确认的接口、流程、状态或依赖>
````

不适合 Mermaid 时：

```markdown
### 图片补充：<图片文件名或图题>

- 图片类型：UI 截图 / 架构截图 / 表格截图 / 其他
- 可确认事实：<逐条列出>
- 不确定内容：<无法从图片确认的部分>
```

## 常见风险

- 只抽取 Word 段落会漏掉图片中的接口名、状态机、异常分支和组件依赖。
- EMF/WMF 转换可能空白；需要记录降级处理。
- 图片里的箭头方向、条件文字和异常返回不能凭经验补写，必须以视觉可见内容为依据。
- 截图类图片不一定适合 Mermaid，优先转成结构化描述。
- 大量图片应按批次分析，避免遗漏和上下文混乱。
