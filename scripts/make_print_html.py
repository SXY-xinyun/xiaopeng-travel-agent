"""Generate a print-friendly HTML from tech_report.md for Ctrl+P → PDF."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "tech_report.md"
OUTS = [
    ROOT / "docs" / "tech_report_print.html",
    ROOT / "submission" / "tech_report_print.html",
]


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(md: str) -> str:
    md = re.sub(r"## 10\. 导出 PDF 步骤[\s\S]*", "", md)
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    in_table = False
    in_list = False
    buf: list[str] = []

    def flush_p() -> None:
        nonlocal buf
        if buf:
            out.append("<p>" + " ".join(buf) + "</p>")
            buf = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</table>")
            in_table = False

    for line in lines:
        if line.startswith("```"):
            flush_p()
            close_list()
            close_table()
            if not in_code:
                in_code = True
                out.append("<pre><code>")
            else:
                in_code = False
                out.append("</code></pre>")
            continue
        if in_code:
            out.append(html.escape(line) + "\n")
            continue

        if line.startswith("|") and "|" in line[1:]:
            flush_p()
            close_list()
            if re.match(r"^\|?\s*-+", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not in_table:
                out.append("<table>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue

        close_table()

        if not line.strip() or line.strip() == "---":
            flush_p()
            close_list()
            continue

        if line.startswith("# "):
            flush_p()
            close_list()
            out.append(f"<h1>{inline(line[2:])}</h1>")
            continue
        if line.startswith("## "):
            flush_p()
            close_list()
            out.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        if line.startswith("### "):
            flush_p()
            close_list()
            out.append(f"<h3>{inline(line[4:])}</h3>")
            continue
        if line.startswith("- "):
            flush_p()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue

        close_list()
        buf.append(inline(line))

    flush_p()
    close_list()
    close_table()
    return "\n".join(out)


def main() -> None:
    body = md_to_html(SRC.read_text(encoding="utf-8"))
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>技术方案报告 - 小鹏 AI 出行服务管家</title>
  <style>
    @page {{ margin: 16mm; size: A4; }}
    body {{
      font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
      font-size: 11pt; line-height: 1.55; color: #1a1a1a;
      max-width: 820px; margin: 24px auto; padding: 0 16px;
    }}
    h1 {{ font-size: 18pt; border-bottom: 2px solid #1a8f7a; padding-bottom: 8px; }}
    h2 {{ font-size: 13.5pt; margin-top: 1.35em; color: #0d3d34; }}
    h3 {{ font-size: 12pt; margin-top: 1em; }}
    code, pre {{ font-family: Consolas, "JetBrains Mono", monospace; font-size: 9.5pt; }}
    pre {{ background: #f4f7f6; padding: 10px; border-radius: 6px; white-space: pre-wrap; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10pt; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef6f3; }}
    li {{ margin: 3px 0; }}
    .hint {{
      background: #fff8e6; border: 1px solid #e6d28a; padding: 10px 12px;
      border-radius: 6px; margin-bottom: 18px; font-size: 10.5pt;
    }}
    @media print {{
      .hint {{ display: none; }}
      body {{ margin: 0; max-width: none; padding: 0; }}
    }}
  </style>
</head>
<body>
  <div class="hint">
    <strong>导出 PDF：</strong>用浏览器打开本文件 → Ctrl+P → 目标选「另存为 PDF」→
    取消页眉页脚 → 保存为 <code>submission/tech_report.pdf</code>（控制在 10 页内）。
  </div>
  {body}
</body>
</html>
"""
    for path in OUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(doc, encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
