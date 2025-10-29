# PDF转Markdown工具 Trae AI 集成指南

本指南介绍了如何将PDF转Markdown MCP工具接入Trae AI环境，使其成为Trae AI可调用的工具。

## 接入架构

![Trae AI 集成架构](https://example.com/diagram.png)

```
Trae AI <--> Trae AI适配器 <--> PDF转Markdown MCP服务
```

## 已完成的工作

✅ **Trae AI适配器开发**：创建了符合Trae AI规范的适配器模块
✅ **HTTP服务实现**：提供了标准化的Trae AI工具接口
✅ **服务端点配置**：实现了工具定义、健康检查和执行接口
✅ **参数验证与错误处理**：完善的请求验证和错误响应机制
✅ **CORS支持**：允许Trae AI跨域访问服务

## 服务端点

服务已在 `http://127.0.0.1:8081` 运行，提供以下端点：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 服务主页，显示基本信息 |
| `/health` | GET | 健康检查接口 |
| `/tool-definition` | GET | 获取工具定义（符合Trae AI规范） |
| `/execute` | POST | 执行PDF转Markdown工具 |

## Trae AI 工具定义

工具名称：`pdf_to_markdown_converter`

功能描述：将PDF文件转换为Markdown格式

### 输入参数

```json
{
  "file_path": "D:\path\to\document.pdf",  // 必需：PDF文件的完整路径
  "tesseract_cmd": "C:\Program Files\Tesseract-OCR\tesseract.exe",  // 可选：Tesseract OCR路径
  "poppler_path": "D:\Software\poppler\Library\bin"  // 可选：Poppler路径
}
```

### 返回结果

```json
{
  "status": "success",  // 操作状态：success 或 error
  "message": "PDF转换成功",  // 操作结果消息
  "data": {
    "original_file": "D:\path\to\document.pdf",  // 原始PDF文件路径
    "output_file": "D:\work\datastore\mcp_server\output\document.md",  // 输出的Markdown文件路径
    "content_preview": "# document\n\n## 转换信息\n...",  // 内容预览
    "content_length": 1234  // 内容长度
  }
}
```

## 在Trae AI中使用

### 方法1：通过Trae AI的工具调用接口

```python
# Trae AI Python客户端示例
from traeai import TraeAIClient

# 初始化客户端
client = TraeAIClient(api_key="your-api-key")

# 调用PDF转Markdown工具
result = client.call_tool(
    "pdf_to_markdown_converter",
    {
        "file_path": "D:\path\to\your.pdf",
        "tesseract_cmd": "C:\Program Files\Tesseract-OCR\tesseract.exe",
        "poppler_path": "D:\Software\poppler\Library\bin"
    }
)

# 处理结果
if result["status"] == "success":
    print(f"转换成功！输出文件: {result['data']['output_file']}")
else:
    print(f"转换失败: {result['message']}")
```

### 方法2：直接调用HTTP接口

```python
import requests
import json

# 准备请求参数
params = {
    "file_path": "D:\path\to\your.pdf",
    "tesseract_cmd": "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": "D:\Software\poppler\Library\bin"
}

# 发送POST请求
service_url = "http://127.0.0.1:8081/execute"
response = requests.post(
    service_url,
    json=params,
    headers={"Content-Type": "application/json"}
)

# 处理响应
if response.status_code == 200:
    result = response.json()
    if result["status"] == "success":
        print(f"转换成功！输出文件: {result['data']['output_file']}")
    else:
        print(f"转换失败: {result['message']}")
else:
    print(f"请求失败: {response.status_code} - {response.text}")
```

## 配置与部署

### 1. 环境要求

- Python 3.6+
- 必要的Python库：`pdf2image`, `pytesseract`, `numpy`, `opencv-python`, `Pillow`
- 外部依赖：
  - Tesseract OCR
  - Poppler

### 2. 配置选项

服务配置通过以下方式设置：

1. **命令行参数**：启动时指定
   ```bash
   python start_traer_server.py --host 127.0.0.1 --port 8081
   ```

2. **pdftomd.py 配置**：修改 CONFIG 字典
   - `output_dir`: 输出目录（默认：`output`）
   - `temp_dir`: 临时目录（默认：`temp`）
   - `tesseract_cmd`: Tesseract OCR路径
   - `poppler_path`: Poppler路径

### 3. 部署为系统服务

#### Windows部署示例

使用NSSM（Non-Sucking Service Manager）将服务安装为Windows服务：

```batch
rem 下载NSSM并放入系统路径
nssm install "PDF-to-Markdown-Trae-Service"
rem 在弹出的对话框中设置：
rem - Path: C:\Python38\python.exe
rem - Startup directory: D:\work\datastore\mcp_server
rem - Arguments: start_traer_server.py --host 127.0.0.1 --port 8081

rem 启动服务
nssm start "PDF-to-Markdown-Trae-Service"
```

#### Linux部署示例

使用systemd将服务配置为系统服务：

```bash
# 创建服务文件
cat > /etc/systemd/system/pdf-to-markdown-traer.service << EOF
[Unit]
Description=PDF to Markdown Trae AI Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mcp_server
ExecStart=/usr/bin/python3 start_traer_server.py --host 0.0.0.0 --port 8081
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
systemctl enable pdf-to-markdown-traer.service
systemctl start pdf-to-markdown-traer.service
```

## 故障排查

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用：`netstat -ano | findstr 8081`
   - 检查依赖是否正确安装

2. **转换失败**
   - 确认PDF文件路径正确
   - 检查Tesseract和Poppler路径配置
   - 查看日志文件：`traer_server.log`

3. **权限问题**
   - 确保服务有权限读写output和temp目录
   - 确保服务有权限读取指定的PDF文件

### 查看日志

服务日志保存在 `D:\work\datastore\mcp_server\traer_server.log`

## 安全注意事项

1. **文件访问权限**：服务需要读取指定的PDF文件，请确保权限设置合理
2. **路径验证**：服务会验证文件是否存在，但请避免传入敏感路径
3. **CORS配置**：当前配置允许所有来源访问（`Access-Control-Allow-Origin: *`），生产环境建议限制来源

## 版本历史

- **1.0.0** - 初始版本，支持PDF转Markdown基本功能和Trae AI集成

---

## 联系信息

如有问题或建议，请联系：
- 作者：MCP Team
- 邮箱：support@example.com
- 文档更新时间：2024-01-01