<knowledge id="deployment-knowledge">
  <domain>部署运维专业知识体系</domain>
  
  <category name="云平台部署">
    ## AWS云平台部署知识
    
    ### EC2实例管理
    ```bash
    # 创建EC2实例
    aws ec2 run-instances \
      --image-id ami-0abcdef1234567890 \
      --count 1 \
      --instance-type t3.medium \
      --key-name my-key-pair \
      --security-group-ids sg-903004f8 \
      --subnet-id subnet-6e7f829e
    
    # 配置安全组
    aws ec2 create-security-group \
      --group-name web-servers \
      --description "Security group for web servers"
    
    aws ec2 authorize-security-group-ingress \
      --group-id sg-903004f8 \
      --protocol tcp \
      --port 80 \
      --cidr 0.0.0.0/0
    ```
    
    ### ELB负载均衡配置
    ```bash
    # 创建应用负载均衡器
    aws elbv2 create-load-balancer \
      --name my-load-balancer \
      --subnets subnet-12345678 subnet-87654321 \
      --security-groups sg-12345678
    
    # 创建目标组
    aws elbv2 create-target-group \
      --name my-targets \
      --protocol HTTP \
      --port 80 \
      --vpc-id vpc-12345678
    
    # 注册目标
    aws elbv2 register-targets \
      --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/my-targets/1234567890123456 \
      --targets Id=i-1234567890abcdef0,Port=80
    ```
    
    ### RDS数据库部署
    ```bash
    # 创建RDS实例
    aws rds create-db-instance \
      --db-instance-identifier mydbinstance \
      --db-instance-class db.t3.micro \
      --engine mysql \
      --master-username admin \
      --master-user-password mypassword \
      --allocated-storage 20
    
    # 创建数据库子网组
    aws rds create-db-subnet-group \
      --db-subnet-group-name mydbsubnetgroup \
      --db-subnet-group-description "My DB subnet group" \
      --subnet-ids subnet-12345678 subnet-87654321
    ```
    
    ### S3存储配置
    ```bash
    # 创建S3存储桶
    aws s3 mb s3://my-deployment-bucket
    
    # 配置存储桶策略
    aws s3api put-bucket-policy \
      --bucket my-deployment-bucket \
      --policy file://bucket-policy.json
    
    # 启用版本控制
    aws s3api put-bucket-versioning \
      --bucket my-deployment-bucket \
      --versioning-configuration Status=Enabled
    ```
  </category>
  
  <category name="容器化部署">
    ## Docker容器化知识
    
    ### Dockerfile最佳实践
    ```dockerfile
    # 多阶段构建示例
    FROM node:16-alpine AS builder
    WORKDIR /app
    COPY package*.json ./
    RUN npm ci --only=production
    
    FROM node:16-alpine AS runtime
    RUN addgroup -g 1001 -S nodejs
    RUN adduser -S nextjs -u 1001
    WORKDIR /app
    COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
    COPY --chown=nextjs:nodejs . .
    USER nextjs
    EXPOSE 3000
    CMD ["npm", "start"]
    ```
    
    ### Docker Compose编排
    ```yaml
    version: '3.8'
    services:
      web:
        build: .
        ports:
          - "3000:3000"
        environment:
          - NODE_ENV=production
          - DATABASE_URL=postgresql://user:pass@db:5432/mydb
        depends_on:
          - db
          - redis
        restart: unless-stopped
        
      db:
        image: postgres:13
        environment:
          POSTGRES_DB: mydb
          POSTGRES_USER: user
          POSTGRES_PASSWORD: pass
        volumes:
          - postgres_data:/var/lib/postgresql/data
        restart: unless-stopped
        
      redis:
        image: redis:6-alpine
        restart: unless-stopped
        
    volumes:
      postgres_data:
    ```
    
    ### Kubernetes部署配置
    ```yaml
    # Deployment配置
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web-app
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: web-app
      template:
        metadata:
          labels:
            app: web-app
        spec:
          containers:
          - name: web-app
            image: myapp:latest
            ports:
            - containerPort: 3000
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: url
            resources:
              requests:
                memory: "256Mi"
                cpu: "250m"
              limits:
                memory: "512Mi"
                cpu: "500m"
    
    ---
    # Service配置
    apiVersion: v1
    kind: Service
    metadata:
      name: web-app-service
    spec:
      selector:
        app: web-app
      ports:
      - protocol: TCP
        port: 80
        targetPort: 3000
      type: LoadBalancer
    ```
  </category>
  
  <category name="CI/CD自动化">
    ## Jenkins流水线配置
    
    ### Jenkinsfile示例
    ```groovy
    pipeline {
        agent any
        
        environment {
            DOCKER_REGISTRY = 'your-registry.com'
            IMAGE_NAME = 'myapp'
            KUBECONFIG = credentials('kubeconfig')
        }
        
        stages {
            stage('Checkout') {
                steps {
                    git branch: 'main', url: 'https://github.com/your-repo/myapp.git'
                }
            }
            
            stage('Test') {
                steps {
                    sh 'npm install'
                    sh 'npm test'
                }
            }
            
            stage('Build') {
                steps {
                    script {
                        def image = docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}")
                        docker.withRegistry('https://' + DOCKER_REGISTRY, 'docker-registry-credentials') {
                            image.push()
                            image.push('latest')
                        }
                    }
                }
            }
            
            stage('Deploy') {
                steps {
                    sh """
                        kubectl set image deployment/web-app web-app=${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}
                        kubectl rollout status deployment/web-app
                    """
                }
            }
        }
        
        post {
            always {
                cleanWs()
            }
            failure {
                emailext (
                    subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                    body: "Build failed. Check console output at ${env.BUILD_URL}",
                    to: "team@company.com"
                )
            }
        }
    }
    ```
    
    ### GitHub Actions工作流
    ```yaml
    name: CI/CD Pipeline
    
    on:
      push:
        branches: [ main ]
      pull_request:
        branches: [ main ]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
        - uses: actions/checkout@v3
        - name: Setup Node.js
          uses: actions/setup-node@v3
          with:
            node-version: '16'
            cache: 'npm'
        - run: npm ci
        - run: npm test
        
      build-and-deploy:
        needs: test
        runs-on: ubuntu-latest
        if: github.ref == 'refs/heads/main'
        steps:
        - uses: actions/checkout@v3
        - name: Build Docker image
          run: |
            docker build -t ${{ secrets.DOCKER_REGISTRY }}/myapp:${{ github.sha }} .
            docker tag ${{ secrets.DOCKER_REGISTRY }}/myapp:${{ github.sha }} ${{ secrets.DOCKER_REGISTRY }}/myapp:latest
        - name: Push to registry
          run: |
            echo ${{ secrets.DOCKER_PASSWORD }} | docker login ${{ secrets.DOCKER_REGISTRY }} -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
            docker push ${{ secrets.DOCKER_REGISTRY }}/myapp:${{ github.sha }}
            docker push ${{ secrets.DOCKER_REGISTRY }}/myapp:latest
        - name: Deploy to Kubernetes
          run: |
            echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
            export KUBECONFIG=kubeconfig
            kubectl set image deployment/web-app web-app=${{ secrets.DOCKER_REGISTRY }}/myapp:${{ github.sha }}
            kubectl rollout status deployment/web-app
    ```
  </category>
  
  <category name="监控运维">
    ## Prometheus监控配置
    
    ### Prometheus配置文件
    ```yaml
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "alert_rules.yml"
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093
    
    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']
      
      - job_name: 'node-exporter'
        static_configs:
          - targets: ['node-exporter:9100']
      
      - job_name: 'application'
        static_configs:
          - targets: ['app:3000']
        metrics_path: '/metrics'
        scrape_interval: 5s
    ```
    
    ### 告警规则配置
    ```yaml
    groups:
    - name: application
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"
      
      - alert: DiskSpaceLow
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low"
          description: "Disk usage is above 80%"
    ```
    
    ### Grafana仪表板配置
    ```json
    {
      "dashboard": {
        "title": "Application Monitoring",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total[5m])",
                "legendFormat": "{{method}} {{status}}"
              }
            ]
          },
          {
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "singlestat",
            "targets": [
              {
                "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
              }
            ]
          }
        ]
      }
    }
    ```
  </category>
  
  <category name="安全配置">
    ## SSL/TLS证书配置
    
    ### Let's Encrypt自动化
    ```bash
    # 安装Certbot
    sudo apt-get update
    sudo apt-get install certbot python3-certbot-nginx
    
    # 获取证书
    sudo certbot --nginx -d example.com -d www.example.com
    
    # 自动续期
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
    ```
    
    ### Nginx SSL配置
    ```nginx
    server {
        listen 443 ssl http2;
        server_name example.com www.example.com;
        
        ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        location / {
            proxy_pass http://localhost:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    
    server {
        listen 80;
        server_name example.com www.example.com;
        return 301 https://$server_name$request_uri;
    }
    ```
    
    ### 防火墙配置
    ```bash
    # UFW防火墙配置
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw enable
    
    # iptables规则
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    iptables -A INPUT -j DROP
    ```
  </category>
  
  <category name="数据库部署">
    ## MySQL高可用部署
    
    ### 主从复制配置
    ```sql
    -- 主服务器配置
    CREATE USER 'replication'@'%' IDENTIFIED BY 'password';
    GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
    FLUSH PRIVILEGES;
    SHOW MASTER STATUS;
    
    -- 从服务器配置
    CHANGE MASTER TO
        MASTER_HOST='master-server',
        MASTER_USER='replication',
        MASTER_PASSWORD='password',
        MASTER_LOG_FILE='mysql-bin.000001',
        MASTER_LOG_POS=154;
    START SLAVE;
    SHOW SLAVE STATUS\G;
    ```
    
    ### MySQL配置优化
    ```ini
    [mysqld]
    # 基础配置
    port = 3306
    socket = /var/lib/mysql/mysql.sock
    datadir = /var/lib/mysql
    
    # 性能优化
    innodb_buffer_pool_size = 1G
    innodb_log_file_size = 256M
    innodb_flush_log_at_trx_commit = 2
    innodb_flush_method = O_DIRECT
    
    # 复制配置
    server-id = 1
    log-bin = mysql-bin
    binlog-format = ROW
    expire_logs_days = 7
    
    # 连接配置
    max_connections = 200
    max_connect_errors = 10000
    wait_timeout = 28800
    interactive_timeout = 28800
    ```
    
    ### Redis集群部署
    ```bash
    # Redis集群配置
    port 7000
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
    
    # 启动集群
    redis-cli --cluster create \
      127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
      127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
      --cluster-replicas 1
    ```
  </category>
  
  <category name="性能优化">
    ## 应用性能优化
    
    ### Nginx性能调优
    ```nginx
    # 工作进程配置
    worker_processes auto;
    worker_rlimit_nofile 65535;
    
    events {
        worker_connections 65535;
        use epoll;
        multi_accept on;
    }
    
    http {
        # 基础优化
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        keepalive_requests 100;
        
        # 压缩配置
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
        
        # 缓存配置
        location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # 限流配置
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req zone=api burst=20 nodelay;
    }
    ```
    
    ### 系统性能调优
    ```bash
    # 内核参数优化
    echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
    echo 'net.ipv4.tcp_max_syn_backlog = 65535' >> /etc/sysctl.conf
    echo 'net.core.netdev_max_backlog = 5000' >> /etc/sysctl.conf
    echo 'net.ipv4.tcp_fin_timeout = 30' >> /etc/sysctl.conf
    echo 'net.ipv4.tcp_keepalive_time = 1200' >> /etc/sysctl.conf
    sysctl -p
    
    # 文件描述符限制
    echo '* soft nofile 65535' >> /etc/security/limits.conf
    echo '* hard nofile 65535' >> /etc/security/limits.conf
    
    # 内存优化
    echo 'vm.swappiness = 10' >> /etc/sysctl.conf
    echo 'vm.dirty_ratio = 15' >> /etc/sysctl.conf
    echo 'vm.dirty_background_ratio = 5' >> /etc/sysctl.conf
    ```
  </category>
</knowledge>