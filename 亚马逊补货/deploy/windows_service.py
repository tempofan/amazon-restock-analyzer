# -*- coding: utf-8 -*-
"""
Windows服务配置脚本
用于将亚马逊补货工具注册为Windows服务
"""

import os
import sys
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil

# 添加项目路径
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

class AmazonRestockService(win32serviceutil.ServiceFramework):
    """
    亚马逊补货工具Windows服务类
    """
    _svc_name_ = "AmazonRestockService"
    _svc_display_name_ = "Amazon Restock Analysis Service"
    _svc_description_ = "亚马逊补货分析工具服务，提供数据获取和分析功能"
    
    def __init__(self, args):
        """
        初始化服务
        """
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True
        
    def SvcStop(self):
        """
        停止服务
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        
    def SvcDoRun(self):
        """
        运行服务主逻辑
        """
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
        
    def main(self):
        """
        服务主函数
        """
        try:
            # 切换到项目目录
            os.chdir(project_path)
            
            # 加载环境变量
            from main import load_env_file
            load_env_file()
            
            # 启动服务逻辑
            import time
            from datetime import datetime
            from utils.logger import api_logger
            
            api_logger.log_info("Amazon Restock Service started")
            
            while self.is_alive:
                # 这里可以添加定时执行的业务逻辑
                # 比如定时获取补货数据、清理日志等
                
                # 检查是否需要停止
                if win32event.WaitForSingleObject(self.hWaitStop, 30000) == win32event.WAIT_OBJECT_0:
                    break
                    
                # 记录心跳日志
                api_logger.log_info(f"Service heartbeat: {datetime.now()}")
                
        except Exception as e:
            # 记录错误日志
            servicemanager.LogErrorMsg(f"Service error: {str(e)}")
            api_logger.log_error(e, "Service runtime error")

def install_service():
    """
    安装Windows服务
    """
    try:
        win32serviceutil.InstallService(
            AmazonRestockService,
            AmazonRestockService._svc_name_,
            AmazonRestockService._svc_display_name_,
            description=AmazonRestockService._svc_description_
        )
        print("✅ Windows服务安装成功！")
        print(f"服务名称: {AmazonRestockService._svc_name_}")
        print(f"显示名称: {AmazonRestockService._svc_display_name_}")
        print("\n💡 使用以下命令管理服务:")
        print(f"启动服务: net start {AmazonRestockService._svc_name_}")
        print(f"停止服务: net stop {AmazonRestockService._svc_name_}")
        print(f"卸载服务: python {__file__} remove")
        
    except Exception as e:
        print(f"❌ 服务安装失败: {e}")

def remove_service():
    """
    卸载Windows服务
    """
    try:
        win32serviceutil.RemoveService(AmazonRestockService._svc_name_)
        print("✅ Windows服务卸载成功！")
    except Exception as e:
        print(f"❌ 服务卸载失败: {e}")

def start_service():
    """
    启动Windows服务
    """
    try:
        win32serviceutil.StartService(AmazonRestockService._svc_name_)
        print("✅ 服务启动成功！")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")

def stop_service():
    """
    停止Windows服务
    """
    try:
        win32serviceutil.StopService(AmazonRestockService._svc_name_)
        print("✅ 服务停止成功！")
    except Exception as e:
        print(f"❌ 服务停止失败: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # 作为服务运行
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AmazonRestockService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # 命令行操作
        command = sys.argv[1].lower()
        if command == 'install':
            install_service()
        elif command == 'remove':
            remove_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'debug':
            # 调试模式
            service = AmazonRestockService([])
            service.main()
        else:
            print("❌ 未知命令")
            print("使用方法:")
            print("  python windows_service.py install  - 安装服务")
            print("  python windows_service.py remove   - 卸载服务")
            print("  python windows_service.py start    - 启动服务")
            print("  python windows_service.py stop     - 停止服务")
            print("  python windows_service.py debug    - 调试模式运行") 