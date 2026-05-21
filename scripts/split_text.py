import sys
import os
import json
import re


def split_text_into_blocks(input_path, output_path, max_chars=1800):
    """
    将 extracted_text.txt 拆分成较小的文本块，方便后续翻译。

    处理逻辑：
    1. 读取 extracted_text.txt
    2. 按页码标记识别页数
    3. 按空行拆分段落
    4. 如果段落太长，再按句子拆分
    5. 输出 text_blocks.json
    """

    if not os.path.exists(input_path):
        print(f"找不到输入文件：{input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 按 Page 标记切分，例如 ===== Page 1 =====
    page_pattern = r"===== Page (\d+) ====="
    parts = re.split(page_pattern, content)

    blocks = []
    block_id = 1

    # parts 结构大概是：["", "1", "第一页内容", "2", "第二页内容", ...]
    for i in range(1, len(parts), 2):
        page_number = int(parts[i])
        page_text = parts[i + 1].strip()

        if not page_text:
            continue

        # 按空行拆分段落
        paragraphs = re.split(r"\n\s*\n", page_text)

        for paragraph in paragraphs:
            paragraph = clean_paragraph(paragraph)

            if not paragraph:
                continue

            # 如果段落较短，直接保存
            if len(paragraph) <= max_chars:
                blocks.append({
                    "block_id": block_id,
                    "page": page_number,
                    "text": paragraph
                })
                block_id += 1
            else:
                # 如果段落太长，进一步按句子拆分
                sub_blocks = split_long_paragraph(paragraph, max_chars)

                for sub_block in sub_blocks:
                    blocks.append({
                        "block_id": block_id,
                        "page": page_number,
                        "text": sub_block
                    })
                    block_id += 1

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("文本拆分完成")
    print("=" * 60)
    print(f"输入文件：{input_path}")
    print(f"输出文件：{output_path}")
    print(f"共生成文本块：{len(blocks)}")
    print("-" * 60)

    if blocks:
        print("前 3 个文本块预览：")
        for block in blocks[:3]:
            preview = block["text"][:150].replace("\n", " ")
            print(f"Block {block['block_id']} | Page {block['page']} | {preview}...")


def clean_paragraph(text):
    """
    清理段落：
    1. 去掉多余空格
    2. 合并 PDF 提取造成的单行换行
    3. 保留基本段落结构
    """

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return ""

    # 简单合并行：英文 PDF 中同一段常被拆成多行
    paragraph = " ".join(lines)

    # 合并多个空格
    paragraph = re.sub(r"\s+", " ", paragraph)

    return paragraph.strip()


def split_long_paragraph(paragraph, max_chars):
    """
    将过长段落按英文句号、问号、感叹号等拆分。
    """

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)

    blocks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        if len(current) + len(sentence) + 1 <= max_chars:
            current = current + " " + sentence if current else sentence
        else:
            if current:
                blocks.append(current)
            current = sentence

    if current:
        blocks.append(current)

    return blocks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        input_path = "output\\extracted_text.txt"
    else:
        input_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = "output\\text_blocks.json"

    split_text_into_blocks(input_path, output_path)