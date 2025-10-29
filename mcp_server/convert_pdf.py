import requests
import json

# 准备MCP服务调用参数
request_data = {
    "method": "convert_pdf_to_md",
    "params": {
        "file_path": "d:\work\datastore\芯片手册\lm5176.pdf"
    }
}

# 发送POST请求到MCP服务API接口
service_url = "http://127.0.0.1:8081/api/invoke"
try:
    response = requests.post(
        service_url,
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    # 检查响应状态码
    response.raise_for_status()
    
    # 解析和打印响应
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 如果成功，打印输出文件路径
    if result.get("status") == "success":
        print(f"\n转换成功！输出文件: {result['data']['output_file']}")
    
except Exception as e:
    print(f"转换失败: {str(e)}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"响应内容: {e.response.text}")