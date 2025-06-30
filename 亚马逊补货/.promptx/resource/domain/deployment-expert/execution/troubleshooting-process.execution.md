<execution id="troubleshooting-process">
  <constraint>
    ## 故障处理约束
    - **时间限制**：P0故障30分钟内响应，P1故障2小时内响应
    - **权限控制**：故障处理必须在授权范围内进行
    - **变更管控**：紧急修复也必须记录变更内容
    - **数据保护**：故障处理过程中确保数据安全
    - **影响最小化**：优先考虑减少对用户的影响
  </constraint>
  
  <rule>
    ## 故障处理规则
    - **先恢复后分析**：优先恢复服务，再深入分析根因
    - **分级响应**：根据故障级别采用不同的响应策略
    - **记录完整**：详细记录故障现象、处理过程、解决方案
    - **团队协作**：及时升级和寻求专业支持
    - **预防为主**：从每次故障中总结预防措施
  </rule>
  
  <guideline>
    ## 故障处理指导
    - **冷静分析**：保持冷静，避免盲目操作
    - **系统思维**：从整体架构角度分析问题
    - **数据驱动**：基于监控数据和日志进行判断
    - **渐进处理**：采用渐进式的问题解决方法
    - **经验积累**：建立故障知识库和最佳实践
  </guideline>
  
  <process>
    ## 故障处理标准流程
    
    ### 阶段1：故障发现与确认 (Detection & Confirmation)
    
    #### 1.1 故障发现
    ```bash
    # 监控告警确认
    # 检查告警详情
    curl -X GET "http://alertmanager:9093/api/v1/alerts"
    
    # 用户反馈确认
    # 记录用户报告的问题现象
    echo "用户反馈：$(date) - 问题描述" >> /var/log/incidents/user_reports.log
    ```
    
    #### 1.2 故障级别评估
    ```bash
    # P0: 系统完全不可用，影响所有用户
    # P1: 核心功能异常，影响大部分用户  
    # P2: 部分功能异常，影响少部分用户
    # P3: 性能问题或非核心功能异常
    
    # 记录故障级别
    echo "故障级别：P1 - $(date)" >> /var/log/incidents/current_incident.log
    ```
    
    #### 1.3 初步影响评估
    ```bash
    # 检查服务状态
    systemctl status application
    systemctl status nginx
    systemctl status mysql
    
    # 检查用户访问情况
    tail -n 100 /var/log/nginx/access.log | grep -c "200"
    tail -n 100 /var/log/nginx/access.log | grep -c "500"
    ```
    
    ### 阶段2：信息收集与分析 (Information Gathering)
    
    #### 2.1 日志收集
    ```bash
    # 应用日志
    tail -n 500 /var/log/application/error.log
    grep -i "error\|exception\|fatal" /var/log/application/application.log
    
    # 系统日志
    journalctl -u application --since "10 minutes ago"
    dmesg | tail -n 50
    
    # Web服务器日志
    tail -n 200 /var/log/nginx/error.log
    awk '$9 >= 400' /var/log/nginx/access.log | tail -n 50
    ```
    
    #### 2.2 系统状态检查
    ```bash
    # 资源使用情况
    top -bn1 | head -20
    df -h
    free -m
    iostat -x 1 3
    
    # 网络状态
    netstat -tlnp
    ss -tuln
    ping -c 3 database-server
    
    # 进程状态
    ps aux | grep application
    pgrep -f application | xargs ps -fp
    ```
    
    #### 2.3 监控数据分析
    ```bash
    # CPU使用率趋势
    curl -G 'http://prometheus:9090/api/v1/query_range' \
      --data-urlencode 'query=cpu_usage_percent' \
      --data-urlencode 'start=2024-01-15T14:00:00Z' \
      --data-urlencode 'end=2024-01-15T15:00:00Z'
    
    # 内存使用趋势
    curl -G 'http://prometheus:9090/api/v1/query' \
      --data-urlencode 'query=memory_usage_percent'
    
    # 响应时间分析
    curl -G 'http://prometheus:9090/api/v1/query' \
      --data-urlencode 'query=http_request_duration_seconds'
    ```
    
    ### 阶段3：问题诊断与定位 (Diagnosis)
    
    #### 3.1 分层诊断
    ```bash
    # 应用层检查
    curl -f http://localhost:8080/health
    curl -f http://localhost:8080/api/status
    
    # 中间件层检查
    mysql -u root -p -e "SHOW PROCESSLIST;"
    redis-cli ping
    
    # 系统层检查
    systemctl --failed
    mount | grep -v "^/dev/loop"
    ```
    
    #### 3.2 依赖服务检查
    ```bash
    # 数据库连接
    mysqladmin -u root -p ping
    mysql -u app_user -p -e "SELECT 1;"
    
    # 缓存服务
    redis-cli ping
    redis-cli info replication
    
    # 外部API
    curl -f https://api.external-service.com/health
    ```
    
    #### 3.3 配置验证
    ```bash
    # 应用配置
    application --check-config
    
    # Nginx配置
    nginx -t
    
    # 环境变量
    env | grep APP_
    ```
    
    ### 阶段4：问题解决 (Resolution)
    
    #### 4.1 临时修复
    ```bash
    # 重启服务
    systemctl restart application
    
    # 清理缓存
    redis-cli FLUSHALL
    
    # 释放资源
    echo 3 > /proc/sys/vm/drop_caches
    
    # 临时扩容
    docker service scale app=5
    ```
    
    #### 4.2 根本解决
    ```bash
    # 代码修复
    git checkout hotfix/critical-bug-fix
    
    # 配置修复
    sed -i 's/old_value/new_value/g' /etc/application/config.conf
    
    # 数据修复
    mysql -u root -p database < fix_data.sql
    ```
    
    #### 4.3 验证修复
    ```bash
    # 功能验证
    curl -f http://localhost:8080/api/test
    
    # 性能验证
    ab -n 100 -c 10 http://localhost:8080/
    
    # 监控验证
    curl http://localhost:9090/metrics | grep error_rate
    ```
    
    ### 阶段5：恢复验证 (Recovery Verification)
    
    #### 5.1 服务状态确认
    ```bash
    # 检查所有相关服务
    systemctl status application nginx mysql redis
    
    # 检查端口监听
    netstat -tlnp | grep -E ":(80|443|3306|6379|8080)"
    
    # 检查进程状态
    pgrep -f "application|nginx|mysql|redis" | wc -l
    ```
    
    #### 5.2 业务功能验证
    ```bash
    # 核心API测试
    curl -X POST http://localhost:8080/api/login \
      -H "Content-Type: application/json" \
      -d '{"username":"test","password":"test"}'
    
    # 数据库操作测试
    mysql -u app_user -p -e "SELECT COUNT(*) FROM users;"
    
    # 文件上传测试
    curl -X POST http://localhost:8080/api/upload \
      -F "file=@test.txt"
    ```
    
    #### 5.3 性能指标确认
    ```bash
    # 响应时间检查
    curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/
    
    # 资源使用检查
    top -bn1 | grep -E "Cpu|Mem"
    
    # 错误率检查
    tail -n 1000 /var/log/nginx/access.log | awk '{print $9}' | sort | uniq -c
    ```
    
    ### 阶段6：事后分析 (Post-Incident Analysis)
    
    #### 6.1 根因分析
    ```markdown
    ## 故障根因分析报告
    
    ### 故障概述
    - 发生时间：2024-01-15 14:30:00
    - 恢复时间：2024-01-15 15:15:00
    - 影响时长：45分钟
    - 影响范围：所有用户无法访问
    
    ### 直接原因
    - 数据库连接池耗尽
    - 应用无法获取数据库连接
    
    ### 根本原因
    - 慢查询导致连接长时间占用
    - 连接池配置过小
    - 缺乏有效的监控告警
    
    ### 解决方案
    - 优化慢查询SQL
    - 增加连接池大小
    - 添加连接池监控
    ```
    
    #### 6.2 改进措施
    ```bash
    # 添加监控告警
    cat > /etc/prometheus/rules/database.yml << EOF
    groups:
    - name: database
      rules:
      - alert: DatabaseConnectionPoolHigh
        expr: db_connection_pool_usage > 0.8
        for: 5m
        annotations:
          summary: "数据库连接池使用率过高"
    EOF
    
    # 优化配置
    sed -i 's/max_connections=20/max_connections=50/g' /etc/application/database.conf
    
    # 添加健康检查
    echo '*/5 * * * * curl -f http://localhost:8080/health || echo "Health check failed" | mail admin@company.com' | crontab -
    ```
    
    #### 6.3 知识库更新
    ```markdown
    # 故障处理知识库更新
    
    ## 数据库连接池耗尽问题
    
    ### 症状
    - 应用响应超时
    - 数据库连接错误
    - 连接池监控显示100%使用率
    
    ### 诊断步骤
    1. 检查应用日志中的数据库连接错误
    2. 查看数据库连接池监控指标
    3. 分析慢查询日志
    
    ### 解决方案
    1. 临时重启应用释放连接
    2. 优化慢查询SQL
    3. 调整连接池配置
    4. 添加连接池监控告警
    ```
  </process>
  
  <criteria>
    ## 故障处理成功标准
    
    ### 恢复标准
    - ✅ 服务完全恢复正常
    - ✅ 所有功能正常运行
    - ✅ 性能指标恢复正常
    - ✅ 用户可以正常访问
    
    ### 处理标准
    - ✅ 在规定时间内响应
    - ✅ 处理过程记录完整
    - ✅ 根因分析清晰准确
    - ✅ 改进措施具体可行
    
    ### 预防标准
    - ✅ 建立有效的监控告警
    - ✅ 完善故障处理文档
    - ✅ 更新知识库和最佳实践
    - ✅ 制定预防性措施
  </criteria>
</execution>