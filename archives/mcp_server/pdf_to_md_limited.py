import pdfplumber
import os

def pdf_to_markdown_limited(pdf_path, output_path, max_pages=10):
    """
    使用pdfplumber将PDF转换为Markdown，只处理前几页
    """
    try:
        print(f"正在处理PDF文件: {pdf_path}")
        
        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            print(f"错误: PDF文件不存在: {pdf_path}")
            return False
            
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF文件已打开，共 {len(pdf.pages)} 页")
            print(f"只处理前 {max_pages} 页")
            
            markdown_content = []
            
            for page_num, page in enumerate(pdf.pages[:max_pages], 1):
                print(f"正在处理第 {page_num} 页...")
                
                # 添加页面分隔符
                markdown_content.append(f"\n\n--- Page {page_num} ---\n\n")
                
                # 提取文本
                text = page.extract_text()
                if text:
                    markdown_content.append(text)
                    print(f"第 {page_num} 页提取了 {len(text)} 个字符")
                else:
                    print(f"第 {page_num} 页没有提取到文本")
            
            # 写入Markdown文件
            print(f"正在写入到: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as md_file:
                md_file.write('\n'.join(markdown_content))
            
            print(f"成功将PDF转换为Markdown: {output_path}")
            return True
            
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置输入和输出路径
    pdf_path = "../芯片手册/LVGL.pdf"
    output_path = "../芯片手册/LVGL.md"
    
    # 转换PDF到Markdown（只处理前10页）
    success = pdf_to_markdown_limited(pdf_path, output_path, max_pages=10)
    
    if success:
        print("转换完成!")
    else:
        print("转换失败!")