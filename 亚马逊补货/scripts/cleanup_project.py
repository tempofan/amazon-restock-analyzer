#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目清理脚本 - 定期清理不必要的文件
"""

import os
import shutil
import glob
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup.log', encoding='utf-8')
    ]
)

def cleanup_project():
    """
    清理项目中的不必要文件
    """
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cleanup_patterns = [
        # 日志文件
        "*.log",
        "logs/*.log*",
        
        # 输出文件
        "output/*.xlsx",
        "output/*.json",
        
        # 测试结果文件
        "test/*_result_*.json",
        "test/diagnostic_result_*.json",
        "test/proxy_diagnostic_result_*.json",
        "test/root_cause_analysis_*.json",
        "test/implementation_guide_*.md",
        
        # Python缓存
        "__pycache__/",
        "**/__pycache__/",
        "*.pyc",
        "*.pyo",
        
        # IDE文件
        ".idea/",
        ".vscode/",
        
        # 临时文件
        "*.tmp",
        "*.temp",
        "*.bak",
        "*.backup",
        
        # 系统文件
        ".DS_Store",
        "Thumbs.db",
        "Desktop.ini",
    ]
    
    cleaned_files = []
    
    for pattern in cleanup_patterns:
        try:
            if pattern.endswith('/'):
                # 目录
                for path in glob.glob(pattern, recursive=True):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        cleaned_files.append(path)
                        logging.info(f"🗂️ 删除目录: {path}")
            else:
                # 文件
                for path in glob.glob(pattern, recursive=True):
                    if os.path.isfile(path):
                        os.remove(path)
                        cleaned_files.append(path)
                        logging.info(f"🗑️ 删除文件: {path}")
        except Exception as e:
            logging.error(f"❌ 清理 {pattern} 时出错: {e}")
    
    # 清理空目录
    empty_dirs = []
    for root, dirs, files in os.walk(project_root):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    empty_dirs.append(dir_path)
                    logging.info(f"📁 删除空目录: {dir_path}")
            except Exception as e:
                logging.error(f"❌ 删除空目录 {dir_path} 时出错: {e}")
    
    # 统计信息
    total_cleaned = len(cleaned_files) + len(empty_dirs)
    logging.info(f"✅ 清理完成！共清理了 {total_cleaned} 个项目")
    logging.info(f"   - 文件/目录: {len(cleaned_files)} 个")
    logging.info(f"   - 空目录: {len(empty_dirs)} 个")
    
    return cleaned_files, empty_dirs

def get_project_size():
    """
    获取项目大小统计
    """
    project_root = Path(__file__).parent.parent
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk(project_root):
        # 跳过虚拟环境和IDE目录
        dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', '.idea', '__pycache__']]
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                total_size += size
                file_count += 1
            except (OSError, IOError):
                pass
    
    # 转换为人类可读格式
    for unit in ['B', 'KB', 'MB', 'GB']:
        if total_size < 1024.0:
            break
        total_size /= 1024.0
    
    return f"{total_size:.2f} {unit}", file_count

if __name__ == "__main__":
    print("🧹 开始项目清理...")
    
    # 获取清理前的项目大小
    size_before, files_before = get_project_size()
    print(f"📊 清理前: {files_before} 个文件, 总大小 {size_before}")
    
    # 执行清理
    cleaned_files, empty_dirs = cleanup_project()
    
    # 获取清理后的项目大小
    size_after, files_after = get_project_size()
    print(f"📊 清理后: {files_after} 个文件, 总大小 {size_after}")
    
    print(f"🎉 项目清理完成！") 