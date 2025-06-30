<execution id="deployment-workflow">
  <constraint>
    ## 部署约束条件
    - **安全要求**：所有部署必须通过安全审核和权限验证
    - **环境隔离**：严格区分开发、测试、生产环境
    - **版本控制**：所有配置和代码必须进行版本管理
    - **备份要求**：部署前必须完成数据和配置备份
    - **回滚准备**：必须准备完整的回滚方案和验证步骤
  </constraint>
  
  <rule>
    ## 部署执行规则
    - **分阶段部署**：按照开发→测试→预生产→生产的顺序进行
    - **自动化优先**：优先使用自动化工具，减少人工操作
    - **文档同步**：部署过程必须同步更新相关文档
    - **监控验证**：每个阶段完成后必须进行功能和性能验证
    - **权限最小化**：使用最小必要权限进行部署操作
  </rule>
  
  <guideline>
    ## 部署指导原则
    - **渐进式部署**：采用蓝绿部署、滚动更新等安全部署策略
    - **可观测性**：确保部署过程和结果的可监控、可追踪
    - **标准化流程**：使用统一的部署模板和检查清单
    - **团队协作**：建立清晰的角色分工和沟通机制
    - **持续改进**：定期回顾和优化部署流程
  </guideline>
  
  <process>
    ## 标准部署流程
    
    ### 阶段1：部署准备 (Pre-deployment)
    
    #### 1.1 需求确认
    ```bash
    # 确认部署需求和变更内容
    - 功能变更清单
    - 配置变更清单  
    - 数据库变更清单
    - 依赖服务变更清单
    ```
    
    #### 1.2 环境检查
    ```bash
    # 检查目标环境状态
    systemctl status application
    df -h  # 检查磁盘空间
    free -m  # 检查内存使用
    netstat -tlnp  # 检查端口占用
    ```
    
    #### 1.3 备份操作
    ```bash
    # 数据备份
    mysqldump -u user -p database > backup_$(date +%Y%m%d_%H%M%S).sql
    
    # 配置备份
    tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz /etc/application/
    
    # 代码备份
    cp -r /opt/application /opt/application_backup_$(date +%Y%m%d_%H%M%S)
    ```
    
    #### 1.4 依赖检查
    ```bash
    # 检查服务依赖
    systemctl status mysql
    systemctl status redis
    systemctl status nginx
    
    # 检查网络连通性
    ping database-server
    telnet cache-server 6379
    ```
    
    ### 阶段2：部署执行 (Deployment)
    
    #### 2.1 停止服务
    ```bash
    # 优雅停止应用服务
    systemctl stop application
    
    # 确认服务已停止
    systemctl status application
    ps aux | grep application
    ```
    
    #### 2.2 代码部署
    ```bash
    # 拉取最新代码
    cd /opt/application
    git fetch origin
    git checkout release/v1.2.3
    
    # 安装依赖
    pip install -r requirements.txt
    npm install
    ```
    
    #### 2.3 配置更新
    ```bash
    # 更新配置文件
    cp config/production.conf /etc/application/
    
    # 更新环境变量
    source /etc/environment
    
    # 验证配置
    application --check-config
    ```
    
    #### 2.4 数据库迁移
    ```bash
    # 执行数据库迁移
    python manage.py migrate
    
    # 验证数据库结构
    python manage.py check --database
    ```
    
    #### 2.5 启动服务
    ```bash
    # 启动应用服务
    systemctl start application
    
    # 检查服务状态
    systemctl status application
    
    # 检查日志
    tail -f /var/log/application/application.log
    ```
    
    ### 阶段3：部署验证 (Post-deployment)
    
    #### 3.1 功能验证
    ```bash
    # 健康检查
    curl -f http://localhost:8080/health
    
    # API测试
    curl -X GET http://localhost:8080/api/status
    
    # 数据库连接测试
    python -c "import django; django.setup(); from django.db import connection; print(connection.ensure_connection())"
    ```
    
    #### 3.2 性能验证
    ```bash
    # 响应时间测试
    curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/
    
    # 并发测试
    ab -n 100 -c 10 http://localhost:8080/
    
    # 资源使用检查
    top -p $(pgrep application)
    ```
    
    #### 3.3 监控配置
    ```bash
    # 配置监控告警
    systemctl enable application-monitor
    systemctl start application-monitor
    
    # 验证监控数据
    curl http://localhost:9090/metrics
    ```
    
    ### 阶段4：部署完成 (Completion)
    
    #### 4.1 文档更新
    ```markdown
    # 更新部署记录
    - 部署时间：2024-01-15 14:30:00
    - 部署版本：v1.2.3
    - 部署人员：张三
    - 变更内容：新增用户管理功能
    - 验证结果：通过
    ```
    
    #### 4.2 通知相关人员
    ```bash
    # 发送部署完成通知
    echo "应用已成功部署到生产环境，版本：v1.2.3" | mail -s "部署完成通知" team@company.com
    ```
    
    #### 4.3 清理临时文件
    ```bash
    # 清理部署过程中的临时文件
    rm -rf /tmp/deployment_*
    
    # 清理旧版本备份（保留最近3个版本）
    find /opt/application_backup_* -mtime +30 -delete
    ```
  </process>
  
  <criteria>
    ## 部署成功标准
    
    ### 功能标准
    - ✅ 所有核心功能正常运行
    - ✅ API接口响应正常
    - ✅ 数据库连接正常
    - ✅ 第三方服务集成正常
    
    ### 性能标准
    - ✅ 响应时间在可接受范围内
    - ✅ 系统资源使用正常
    - ✅ 并发处理能力满足要求
    - ✅ 内存和CPU使用稳定
    
    ### 安全标准
    - ✅ 安全配置正确应用
    - ✅ 权限设置符合要求
    - ✅ 敏感信息得到保护
    - ✅ 网络访问控制正常
    
    ### 监控标准
    - ✅ 监控系统正常工作
    - ✅ 告警规则正确配置
    - ✅ 日志记录完整清晰
    - ✅ 性能指标采集正常
  </criteria>
</execution>