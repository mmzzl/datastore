# PDF转Markdown MCP远程服务

本目录包含将PDF转Markdown工具改造为可远程使用的MCP服务的完整实现。

## 功能特性

- **远程调用**: 通过HTTP API提供PDF转Markdown服务的远程访问
- **完整接口**: 提供转换、健康检查、配置更新等多个API端点
- **灵活配置**: 支持通过配置文件、环境变量或命令行参数进行配置
- **安全认证**: 可选的API密钥认证机制
- **服务发现**: 提供服务信息查询和健康状态检查
- **跨平台支持**: 支持Windows和Linux/Ubuntu环境

## 文件结构

```
mcp_server/
├── pdftomd.py         # 核心PDF转Markdown功能，已改造为MCP服务接口
├── __init__.py        # 模块初始化文件，提供服务注册和调用入口
├── mcp_service_config.py # MCP服务配置管理
├── start_mcp_server.py # MCP服务启动脚本
├── mcp_client_example.py # 客户端调用示例
└── README.md          # 本文档
```

## 快速开始

### 1. 环境要求

- Python 3.6+
- 必要的Python库：`opencv-python`, `numpy`, `Pillow`, `pytesseract`, `pdf2image`, `requests`
- 外部依赖：
  - Tesseract OCR
  - Poppler

### 2. 安装依赖

```bash
# 安装Python库
pip install opencv-python numpy Pillow pytesseract pdf2image requests

# Ubuntu系统安装外部依赖
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils python3-opencv

# Windows系统
# 1. 安装Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
# 2. 安装Poppler: https://github.com/oschwartz10612/poppler-windows/
```

### 3. 启动服务

**基本启动（默认配置）**:

```bash
cd mcp_server
python start_mcp_server.py
```

**指定主机和端口**:

```bash
python start_mcp_server.py --host 0.0.0.0 --port 8080
```

**启用认证**:

```bash
python start_mcp_server.py --auth --api-key your-secure-api-key
```

**使用配置文件**:

```bash
# 先创建配置文件
python -c "from mcp_service_config import MCPConfig; config = MCPConfig(); config.save('mcp_config.json')"

# 使用配置文件启动
python start_mcp_server.py --config mcp_config.json
```

## 服务端点

服务启动后提供以下HTTP端点：

| 端点 | 方法 | 功能描述 |
|------|------|----------|
| `/` | GET | 服务首页，显示基本信息 |
| `/health` | GET | 健康检查接口 |
| `/info` | GET | 获取服务详细信息 |
| `/api/invoke` | POST | 调用MCP服务方法的核心接口 |

## API使用示例

### 输出文件说明

**重要提示**：转换后的Markdown文件会自动保存到`output`目录中，与程序分离。临时图像文件会保存在`temp`目录中。两个目录均使用绝对路径，确保文件保存在正确的位置。

### 健康检查

```bash
curl http://localhost:8080/health
```

响应示例：
```json
{
  "status": "healthy",
  "service": "pdf-to-markdown-converter",
  "version": "1.0.0",
  "dependencies": {
    "tesseract_ocr": {"available": true, "version": "5.3.0"},
    "pdf_processing": {"available": true}
  },
  "config": {
    "output_dir": "output",
    "temp_dir": "temp"
  }
}
```

### 转换PDF文件

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-if-required" \
  -d '{"method":"convert_pdf_to_md","params":{"file_path":"/path/to/document.pdf"}}' \
  http://localhost:8080/api/invoke
```

响应示例：
```json
{
  "status": "success",
  "message": "PDF转换成功",
  "data": {
    "original_file": "/path/to/document.pdf",
    "output_file": "output/document.md",
    "content_preview": "# PDF转Markdown结果\n\n---\n# 第1页\n\n...",
    "content_length": 5234,
    "output_format": "markdown"
  }
}
```

### 更新服务配置

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"method":"update_config","params":{"output_dir":"/new/output/path","log_level":"DEBUG"}}' \
  http://localhost:8080/api/invoke
```

## 使用Python客户端

使用提供的客户端示例代码：

```python
from mcp_client_example import MCPRemoteClient

# 创建客户端
client = MCPRemoteClient(
    base_url="http://localhost:8080",
    api_key="your-api-key-if-required"
)

# 转换PDF文件
success, result = client.convert_pdf_to_md("/path/to/document.pdf")

if success:
    print(f"转换成功! 输出文件: {result['data']['output_file']}")
    print(f"内容预览: {result['data']['content_preview']}")
else:
    print(f"转换失败: {result['message']}")
```

## 配置选项

### 配置文件格式 (JSON)

```json
{
  "host": "0.0.0.0",
  "port": 8080,
  "max_workers": 4,
  "timeout": 300,
  "require_auth": false,
  "api_key": "your-api-key-here",
  "temp_dir": "temp",
  "output_dir": "output",
  "tesseract_cmd": "/usr/bin/tesseract",
  "poppler_path": "/usr/bin",
  "log_level": "INFO",
  "log_file": "pdf-to-markdown-converter.log"
}
```

### 环境变量

所有配置选项都可以通过环境变量设置，格式为：`MCP_PDF_TO_MARKDOWN_CONVERTER_<配置项名>`

例如：
```bash
export MCP_PDF_TO_MARKDOWN_CONVERTER_PORT=8000
export MCP_PDF_TO_MARKDOWN_CONVERTER_REQUIRE_AUTH=true
export MCP_PDF_TO_MARKDOWN_CONVERTER_API_KEY=your-key
```

## 部署到Linux服务器

### 1. 系统准备

```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装必要软件
sudo apt-get install -y python3 python3-pip python3-venv git

# 安装依赖
sudo apt-get install -y tesseract-ocr poppler-utils python3-opencv
```

### 2. 创建虚拟环境

```bash
# 创建并激活虚拟环境
python3 -m venv pdfmd-venv
source pdfmd-venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install opencv-python numpy Pillow pytesseract pdf2image requests
```

### 3. 启动服务

```bash
# 复制代码到服务器后启动
cd mcp_server

# 方式1: 直接启动
python start_mcp_server.py --host 0.0.0.0 --port 8080

# 方式2: 使用nohup在后台运行
nohup python start_mcp_server.py --host 0.0.0.0 --port 8080 > mcp_server.log 2>&1 &

# 方式3: 使用systemd（推荐用于生产环境）
# 请参考systemd服务配置示例
```

### 4. 配置防火墙

```bash
# 允许8080端口
sudo ufw allow 8080
sudo ufw reload
```

## 安全建议

1. **启用认证**：在生产环境中始终启用API密钥认证
2. **定期更换API密钥**：确保安全性
3. **使用HTTPS**：考虑在生产环境中使用反向代理（如Nginx）添加HTTPS支持
4. **限制访问IP**：配置防火墙规则，只允许特定IP访问服务
5. **文件路径验证**：注意服务允许访问的文件路径范围，避免安全风险

## 故障排除

### 常见问题

1. **Tesseract OCR未找到**
   - 确保已正确安装Tesseract
   - 通过配置文件或环境变量指定正确的Tesseract路径

2. **Poppler未找到**
   - 确保已正确安装Poppler
   - 通过配置文件或环境变量指定正确的Poppler路径

3. **认证失败**
   - 检查API密钥是否正确
   - 确保在请求头中正确设置了`Authorization: Bearer <your-api-key>`

4. **文件访问权限**
   - 确保服务进程有权限访问PDF文件和写入输出目录

### 查看日志

服务日志默认保存在`pdf-to-markdown-converter.log`文件中，可以通过调整日志级别获取更详细的信息。

## 版本历史

- **v1.0.0** - 初始版本
  - 实现PDF转Markdown的远程服务功能
  - 提供完整的API接口和客户端示例
  - 支持灵活的配置和安全认证

## 许可证

本项目采用MIT许可证。