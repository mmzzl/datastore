# PDF转Markdown工具

一个功能完善的PDF文件转换工具，可以将PDF中的文本、图片和公式转换为Markdown格式。

## 功能特点

- ✅ **文本提取**：使用OCR技术从PDF中提取文本内容
- ✅ **图片处理**：保存PDF中的页面图像并在Markdown中引用
- ✅ **公式检测**：基于图像处理识别PDF中的公式区域
- ✅ **Markdown格式化**：自动优化提取的文本为Markdown格式
- ✅ **多语言支持**：支持中英文文本识别
- ✅ **友好的错误处理**：提供详细的错误信息和日志

## 环境要求

### 1. Python环境

- Python 3.6+ （推荐Python 3.8+）
- pip 包管理器

### 2. 必需的外部软件

#### Windows环境配置

##### Tesseract OCR
- **用途**：进行文本识别
- **下载地址**：[Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- **详细安装步骤**：
  1. 从下载页面选择最新的安装包（通常是`tesseract-ocr-w64-setup-*.exe`）
  2. 运行安装程序，选择安装路径（默认通常为`C:\Program Files\Tesseract-OCR`）
  3. **重要**：在组件选择界面，确保勾选中文语言包（`chi_sim`）
  4. 安装完成后，将Tesseract的安装目录（如`C:\Program Files\Tesseract-OCR`）添加到系统环境变量PATH中
  5. 重启命令提示符或PowerShell以应用环境变量
  6. 验证安装：运行`tesseract --version`命令应显示版本信息

##### Poppler
- **用途**：PDF转换为图像的后端依赖
- **下载地址**：[Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
- **详细安装步骤**：
  1. 从GitHub Releases页面下载最新的ZIP文件
  2. 解压到任意目录（例如`D:\Software\poppler`）
  3. 将解压目录下的`bin`文件夹（例如`D:\Software\poppler\Library\bin`）添加到系统环境变量PATH中
  4. 重启命令提示符或PowerShell以应用环境变量
  5. 验证安装：运行`pdftotext -v`命令应显示版本信息

**注意**：检测结果显示Poppler 25.07.0版本已成功安装在您的系统中。

#### Ubuntu服务器环境配置

##### Tesseract OCR
- **用途**：进行文本识别
- **安装命令**：
  ```bash
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
  ```
- **验证安装**：
  ```bash
  tesseract --version
  ```
- **安装路径**：默认安装在`/usr/bin/tesseract`
- **语言包位置**：默认位于`/usr/share/tesseract-ocr/`目录

##### Poppler
- **用途**：PDF转换为图像的后端依赖
- **安装命令**：
  ```bash
  sudo apt-get update
  sudo apt-get install -y poppler-utils
  ```
- **验证安装**：
  ```bash
  pdftotext -v
  ```
- **安装路径**：默认安装在`/usr/bin/`目录下

##### 其他依赖
- 确保安装必要的图像处理库：
  ```bash
  sudo apt-get install -y libopencv-dev python3-opencv
  ```

### 3. MCP服务器配置

#### 安装MCP服务
- 在Ubuntu服务器上安装MCP服务：
  ```bash
  # 克隆MCP仓库
  git clone https://github.com/mcp-server/mcp.git
  cd mcp
  
  # 安装依赖
  pip install -e .
  ```

#### 配置pdftomd作为MCP服务
- 将本项目的`pdftomd.py`复制到MCP服务的适当目录
- 在MCP配置文件中添加服务定义
- 确保MCP服务有权限访问Tesseract和Poppler工具

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <项目仓库URL>  # 如果是从Git仓库获取
# 或者直接下载项目文件
```

### 2. 安装Python依赖

进入项目目录，运行以下命令：

```bash
cd d:\work\datastore\mcp_server
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 验证安装

运行单元测试以验证安装是否成功：

```bash
python test_pdftomd.py
```

如果所有测试通过，说明基本功能正常。

## 使用方法

### 方法1：使用演示脚本（推荐）

```bash
# 基本使用
python demo.py <PDF文件路径>

# 示例：转换芯片手册
python demo.py "../芯片手册/C31151_模数转换芯片ADC_AD9288BSTZ-100_规格书_WJ126841.PDF"
```

演示脚本会自动检查依赖并显示转换进度和结果。如果Tesseract或Poppler未添加到系统PATH，脚本会提示您手动指定它们的路径。

### 在Ubuntu服务器上运行

```bash
# 确保安装了所有依赖
cd /path/to/datastore/mcp_server
pip install -r requirements.txt

# 运行演示脚本
python demo.py /path/to/your.pdf
```

### 通过MCP服务使用

```bash
# 启动MCP服务
mcp-server start

# 通过API调用pdftomd服务
curl -X POST http://localhost:8000/api/services/pdftomd \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/your.pdf"}'
```

### 手动指定工具路径

如果您不想修改系统环境变量，可以在运行脚本时手动指定路径：

当脚本检测到工具未在PATH中时，会提示您输入路径，例如：

```
未找到Tesseract OCR。请输入Tesseract可执行文件路径（例如：C:\Program Files\Tesseract-OCR\tesseract.exe）：
未找到Poppler。请输入Poppler的bin目录路径（例如：D:\Software\poppler\Library\bin）：
```

### 方法2：在Python代码中调用

```python
from mcp_server.pdftomd import pdftomd

# 转换PDF文件
result = pdftomd("path/to/your.pdf")
print(result)
```

### 方法3：使用转换函数

```python
# 导入转换函数
from pdftomd import pdftomd

# 调用转换函数
pdf_path = "your_document.pdf"
markdown_content = pdftomd(pdf_path)

# 结果将保存为同名的.md文件
print(f"转换完成，结果保存在：{pdf_path.replace('.pdf', '.md')}")
```

## 转换结果说明

生成的Markdown文件包含以下内容：

- **标题**：自动生成的文档标题
- **页码分隔**：使用`---`分隔不同页面
- **文本内容**：从PDF提取的文本，已格式化
- **公式标记**：检测到的公式区域会有特殊标记
- **页面图像**：每个页面的图像引用

## 项目结构

```
d:\work\datastore/
├── mcp_server/                # 主要代码目录
│   ├── pdftomd.py            # 核心转换模块
│   ├── demo.py               # 演示脚本
│   ├── test_pdftomd.py       # 单元测试
│   └── requirements.txt      # Python依赖列表
├── 芯片手册/                  # 示例PDF文件目录
│   └── C31151_模数转换芯片ADC_AD9288BSTZ-100_规格书_WJ126841.PDF
└── README.md                 # 项目说明文档
```

## 常见问题解决

### 1. TesseractNotFoundError

**错误信息**：`tesseract is not installed or it's not in your PATH`

**解决方案**：
- 确保已正确安装Tesseract OCR
- 检查系统环境变量PATH中是否包含Tesseract的安装目录
- 重启命令行或IDE后重试
- 使用演示脚本的手动路径指定功能，直接输入Tesseract的安装路径

**检测结果**：您的系统当前未找到Tesseract OCR，请按照安装步骤进行安装。

### 2. PDF转换失败

**错误信息**：与pdf2image相关的错误

**解决方案**：
- 确保已正确安装Poppler
- 检查系统环境变量PATH中是否包含Poppler的bin目录
- 尝试更新pdf2image库：`pip install --upgrade pdf2image`
- 使用演示脚本的手动路径指定功能，直接输入Poppler的bin目录路径

**检测结果**：Poppler 25.07.0版本已成功安装在您的系统中。

### 3. 中文识别效果不佳

**解决方案**：
- 确保安装Tesseract时选择了中文语言包
- 检查Tesseract的` tessdata`目录中是否有`chi_sim.traineddata`文件
- 可以尝试调整OCR配置参数

## 注意事项

1. **转换质量**：OCR转换质量取决于PDF文件的清晰度和格式
2. **处理速度**：大文件可能需要较长时间处理
3. **公式支持**：当前仅提供公式区域检测，不进行公式内容识别
4. **临时文件**：转换过程中会生成临时图像文件
5. **依赖版本**：请确保使用兼容的Python和依赖库版本

## 系统要求

### Windows环境
- **操作系统**：Windows 7/8/10/11
- **硬件要求**：至少4GB内存，推荐8GB以上
- **存储空间**：至少100MB可用空间（不包括输入输出文件）

### Ubuntu服务器环境
- **操作系统**：Ubuntu 18.04 LTS 或更高版本
- **硬件要求**：至少2GB内存，推荐4GB以上
- **存储空间**：至少100MB可用空间
- **网络要求**：如需通过MCP服务提供API访问，需开放相应端口

## 许可证

本项目仅供学习和研究使用。

---

**联系信息**：如有问题，请在项目仓库中提交issue。
**更新日期**：2024年1月