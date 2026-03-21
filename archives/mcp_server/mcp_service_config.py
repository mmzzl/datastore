# -*- coding: utf-8 -*-
"""
MCP服务配置文件

用于配置PDF转Markdown服务的远程访问参数和运行时设置。
"""

import os
import json
from typing import Dict, Any, Optional

class MCPConfig:
    """
    MCP服务配置类
    管理服务的各种配置参数，支持从环境变量和配置文件加载
    """
    
    def __init__(self, config_file: Optional[str] = None):
        # 从配置文件加载设置（如果提供）
        self.config_file = config_file
        self._config_data = self._load_config()
        
        # 服务基本配置
        self.service_name = "pdf-to-markdown-converter"
        self.service_version = "1.0.0"
        
        # 网络配置 - 远程访问相关
        self.host = self._get_config("host", "0.0.0.0")  # 0.0.0.0允许所有网络接口访问
        self.port = int(self._get_config("port", 8080))
        self.max_workers = int(self._get_config("max_workers", 4))
        self.timeout = int(self._get_config("timeout", 300))  # 5分钟超时
        
        # 安全配置
        self.require_auth = self._get_config_bool("require_auth", False)
        self.api_key = self._get_config("api_key", None)
        
        # 文件路径配置
        self.temp_dir = self._get_config("temp_dir", "temp")
        self.output_dir = self._get_config("output_dir", "output")
        
        # 外部依赖配置
        self.tesseract_cmd = self._get_config("tesseract_cmd", None)
        self.poppler_path = self._get_config("poppler_path", None)
        
        # 日志配置
        self.log_level = self._get_config("log_level", "INFO")
        self.log_file = self._get_config("log_file", f"{self.service_name}.log")
        
        # 确保必要的目录存在
        for dir_path in [self.temp_dir, self.output_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        从配置文件加载设置
        """
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 无法加载配置文件 {self.config_file}: {str(e)}")
        return {}
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，优先从环境变量读取，然后是配置文件，最后是默认值
        """
        # 尝试从环境变量读取（大写并将.替换为_）
        env_key = f"MCP_{self.service_name.replace('-', '_').upper()}_{key.upper().replace('.', '_')}"
        if env_key in os.environ:
            return os.environ[env_key]
        
        # 尝试从配置文件读取
        if key in self._config_data:
            return self._config_data[key]
        
        return default
    
    def _get_config_bool(self, key: str, default: bool = False) -> bool:
        """
        获取布尔类型的配置值
        """
        value = self._get_config(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y', 't')
        return bool(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典格式
        """
        return {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "host": self.host,
            "port": self.port,
            "max_workers": self.max_workers,
            "timeout": self.timeout,
            "require_auth": self.require_auth,
            "api_key": "***" if self.api_key else None,  # 不在日志中显示真实API密钥
            "temp_dir": self.temp_dir,
            "output_dir": self.output_dir,
            "tesseract_cmd": self.tesseract_cmd,
            "poppler_path": self.poppler_path,
            "log_level": self.log_level,
            "log_file": self.log_file
        }
    
    def save(self, file_path: Optional[str] = None) -> bool:
        """
        保存配置到文件
        """
        try:
            save_path = file_path or self.config_file
            if not save_path:
                return False
                
            with open(save_path, 'w', encoding='utf-8') as f:
                # 不保存敏感信息
                config_data = self.to_dict()
                config_data['api_key'] = None  # 不保存API密钥
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False
    
    def get_pdftomd_config(self) -> Dict[str, Any]:
        """
        获取传递给pdftomd模块的配置
        """
        return {
            'tesseract_cmd': self.tesseract_cmd,
            'poppler_path': self.poppler_path,
            'output_dir': self.output_dir,
            'temp_dir': self.temp_dir
        }

# 默认配置实例
DEFAULT_CONFIG = MCPConfig()

# 配置示例JSON字符串
CONFIG_EXAMPLE = '''
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
'''

if __name__ == "__main__":
    # 打印默认配置
    print(f"默认MCP服务配置 ({DEFAULT_CONFIG.service_name} v{DEFAULT_CONFIG.service_version}):")
    print(json.dumps(DEFAULT_CONFIG.to_dict(), indent=2, ensure_ascii=False))
    
    print("\n配置示例:")
    print(CONFIG_EXAMPLE)
    print("\n使用方法:")
    print("1. 创建配置文件 mcp_config.json")
    print("2. 设置环境变量或在配置文件中配置参数")
    print("3. 在服务启动时加载配置")