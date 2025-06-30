#!/bin/bash
# 云服务器状态诊断脚本

echo "🔍 云服务器状态诊断报告"
echo "=========================="
echo "📅 检查时间: $(date)"
echo

echo "📂 当前目录和文件列表:"
pwd
ls -la
echo

echo "🔍 查找所有Python进程:"
ps aux | grep python | grep -v grep
echo

echo "🔍 查找云代理相关进程:"
ps aux | grep cloud_proxy | grep -v grep
echo

echo "🌐 检查8080端口占用:"
netstat -tlnp | grep :8080
echo

echo "🔍 查找所有cloud_proxy文件:"
find / -name "*cloud_proxy*" 2>/dev/null | head -20
echo

echo "📋 检查systemd服务:"
systemctl status lingxing-proxy 2>/dev/null || echo "无lingxing-proxy服务"
systemctl status cloud-proxy 2>/dev/null || echo "无cloud-proxy服务"
systemctl status amazon-restock 2>/dev/null || echo "无amazon-restock服务"
echo

echo "📁 检查常见部署目录:"
ls -la /opt/ 2>/dev/null | grep -i proxy || echo "/opt/ 无代理相关目录"
ls -la /home/ubuntu/ 2>/dev/null | grep -i proxy || echo "/home/ubuntu/ 无代理相关文件"
ls -la /root/ 2>/dev/null | grep -i proxy || echo "/root/ 无代理相关文件"
echo

echo "🔍 检查进程启动命令:"
ps aux | grep cloud_proxy | grep -v grep | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}'
echo

echo "📊 内存和CPU使用情况:"
free -h
top -bn1 | head -5
echo

echo "✅ 诊断完成" 