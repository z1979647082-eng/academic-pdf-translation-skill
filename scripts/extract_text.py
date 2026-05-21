import sys
import os
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path, output_path):
    """
    从 PDF 中提取文字，并保存为 txt 文件。
    每一页会保留页码标记，方便后续定位。
    """

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"无法打开 PDF 文件：{e}")
        return

    all_text = []

    print("=" * 60)
    print("开始提取 PDF 文字")
    print("=" * 60)
    print(f"文件路径：{pdf_path}")
    print(f"总页数：{len(doc)}")
    print("-" * 60)

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text("text").strip()

        page_number = page_index + 1

        all_text.append(f"\n\n===== Page {page_number} =====\n\n")
        all_text.append(text)

        print(f"第 {page_number} 页：提取 {len(text)} 个字符")

    doc.close()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

    print("-" * 60)
    print("文字提取完成")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法：")
        print("python scripts\\extract_text.py your_file.pdf")
        print("或者：")
        print("python scripts\\extract_text.py your_file.pdf output\\extracted_text.txt")
    else:
        pdf_path = sys.argv[1]

        if len(sys.argv) >= 3:
            output_path = sys.argv[2]
        else:
            output_path = "output\\extracted_text.txt"

        extract_text_from_pdf(pdf_path, output_path)