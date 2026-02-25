# 创建Windows服务的PowerShell脚本
# 使用NSSM (Non-Sucking Service Manager)来管理服务

# 脚本配置
$ServiceName = "SpiderService"
$ServiceDisplayName = "爬虫管理服务"
$ServiceDescription = "用于管理和运行爬虫的服务"
$PythonScriptPath = "D:\new_apps\datastore\case\apps\python-web-scraper\spider_service.py"
$NssmPath = "C:\Program Files\nssm\nssm.exe"  # NSSM的安装路径

# 检查NSSM是否安装
if (-not (Test-Path $NssmPath)) {
    Write-Host "NSSM未找到，请先下载并安装NSSM: https://nssm.cc/download"
    Write-Host "建议安装到: C:\Program Files\nssm\"
    exit 1
}

# 检查Python脚本是否存在
if (-not (Test-Path $PythonScriptPath)) {
    Write-Host "Python脚本未找到: $PythonScriptPath"
    exit 1
}

# 创建服务
Write-Host "正在创建服务: $ServiceDisplayName"
& $NssmPath install $ServiceName python $PythonScriptPath "start"

# 配置服务
Write-Host "正在配置服务..."
& $NssmPath set $ServiceName DisplayName $ServiceDisplayName
& $NssmPath set $ServiceName Description $ServiceDescription
& $NssmPath set $ServiceName AppDirectory "D:\new_apps\datastore\case\apps\python-web-scraper"
& $NssmPath set $ServiceName Start SERVICE_AUTO_START  # 设置为自动启动

# 启动服务
Write-Host "正在启动服务..."
& $NssmPath start $ServiceName

# 检查服务状态
Write-Host "检查服务状态..."
& $NssmPath status $ServiceName

Write-Host "服务创建完成！"
Write-Host "使用以下命令管理服务:"
Write-Host "  启动服务: nssm start $ServiceName"
Write-Host "  停止服务: nssm stop $ServiceName"
Write-Host "  重启服务: nssm restart $ServiceName"
Write-Host "  查看状态: nssm status $ServiceName"
Write-Host "  删除服务: nssm remove $ServiceName confirm"
