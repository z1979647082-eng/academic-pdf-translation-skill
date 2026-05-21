import sys
import fitz  # PyMuPDF


def inspect_pdf(pdf_path):
    """
    检查 PDF 基本信息：
    1. 总页数
    2. 每页能否提取文字
    3. 每页文字长度
    4. 判断是否可能需要 OCR
    """

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"无法打开 PDF 文件：{e}")
        return

    print("=" * 60)
    print("PDF 检查报告")
    print("=" * 60)
    print(f"文件路径：{pdf_path}")
    print(f"总页数：{len(doc)}")
    print("-" * 60)

    ocr_pages = []

    for page_index in range(len(doc)):
        page = doc[page_index]

        text = page.get_text("text").strip()
        text_length = len(text)

        # 简单判断：如果一页提取出来的文字少于 50 个字符，可能是扫描页或图片页
        needs_ocr = text_length < 50

        if needs_ocr:
            ocr_pages.append(page_index + 1)

        print(f"第 {page_index + 1} 页")
        print(f"可提取文字长度：{text_length}")

        if needs_ocr:
            print("判断结果：可能需要 OCR")
        else:
            print("判断结果：可直接提取文字")

        print("-" * 60)

    print("总结")
    print("-" * 60)

    if ocr_pages:
        print(f"可能需要 OCR 的页面：{ocr_pages}")
    else:
        print("没有发现明显需要 OCR 的页面。")

    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法：")
        print("python scripts\\inspect_pdf.py your_file.pdf")
    else:
        pdf_path = sys.argv[1]
        inspect_pdf(pdf_path)