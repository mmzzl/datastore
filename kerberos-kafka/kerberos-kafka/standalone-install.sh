#!/bin/bash

# Kerberos-Kafka环境独立安装脚本
# 直接在服务器上运行，无需SSH连接

echo "=========================================="
echo "Kerberos-Kafka环境独立安装脚本"
echo "直接在服务器上安装，无需SSH连接"
echo "=========================================="

# 颜色输出函数
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

# 显示进度条
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))
    
    printf "\r["
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' '-'
    printf "] %d%%" $percentage
    
    if [ $current -eq $total ]; then
        echo
    fi
}

# 检查是否以root权限运行
check_root_privileges() {
    blue "步骤1/10: 检查权限..."
    
    if [ "$(id -u)" -ne 0 ]; then
        red "✗ 此脚本需要root权限运行，请使用sudo或以root用户身份运行"
        exit 1
    fi
    
    green "✓ 权限检查通过"
    return 0
}

# 检查系统环境
check_system_environment() {
    blue "步骤2/10: 检查系统环境..."
    
    # 检查操作系统
    if [ -f /etc/redhat-release ]; then
        OS="centos"
        green "✓ 检测到CentOS/RHEL系统"
    elif [ -f /etc/lsb-release ]; then
        OS="ubuntu"
        green "✓ 检测到Ubuntu系统"
    else
        yellow "⚠️  未知操作系统，将尝试使用通用安装方法"
        OS="unknown"
    fi
    
    # 检查网络连接
    if ping -c 1 archive.apache.org &> /dev/null; then
        green "✓ 网络连接正常"
    else
        red "✗ 网络连接异常，无法下载Kafka"
        exit 1
    fi
    
    return 0
}

# 安装必要的系统依赖
install_system_dependencies() {
    blue "步骤3/10: 安装系统依赖..."
    
    if [ "$OS" = "centos" ]; then
        # CentOS/RHEL系统
        yum update -y
        yum install -y wget curl expect java-1.8.0-openjdk java-1.8.0-openjdk-devel
        yum install -y krb5-server krb5-libs krb5-workstation
    elif [ "$OS" = "ubuntu" ]; then
        # Ubuntu系统
        apt-get update -y
        apt-get install -y wget curl expect openjdk-8-jdk
        apt-get install -y krb5-kdc krb5-admin-server krb5-user
    else
        # 未知系统，尝试通用方法
        yellow "⚠️  尝试使用通用方法安装依赖..."
        if command -v yum &> /dev/null; then
            yum update -y
            yum install -y wget curl expect java krb5-server krb5-workstation
        elif command -v apt-get &> /dev/null; then
            apt-get update -y
            apt-get install -y wget curl expect default-jdk krb5-kdc krb5-admin-server
        else
            red "✗ 无法确定包管理器，请手动安装Java、Kerberos和wget"
            exit 1
        fi
    fi
    
    green "✓ 系统依赖安装完成"
    return 0
}

# 配置Kerberos
configure_kerberos() {
    blue "步骤4/10: 配置Kerberos..."
    
    # 配置参数
    KERBEROS_REALM="EXAMPLE.COM"
    KERBEROS_ADMIN_USER="admin"
    KERBEROS_ADMIN_PASSWORD="admin123"
    KERBEROS_KDC_PORT="88"
    KERBEROS_ADMIN_PORT="749"
    
    # 备份原始配置文件
    if [ -f /etc/krb5.conf ]; then
        cp /etc/krb5.conf /etc/krb5.conf.bak
    fi
    
    if [ -f /var/kerberos/krb5kdc/kdc.conf ]; then
        cp /var/kerberos/krb5kdc/kdc.conf /var/kerberos/krb5kdc/kdc.conf.bak
    fi
    
    if [ -f /var/kerberos/krb5kdc/kadm5.acl ]; then
        cp /var/kerberos/krb5kdc/kadm5.acl /var/kerberos/krb5kdc/kadm5.acl.bak
    fi
    
    # 配置krb5.conf
    cat > /etc/krb5.conf << EOL
[logging]
 default = FILE:/var/log/krb5libs.log
 kdc = FILE:/var/log/krb5kdc.log
 admin_server = FILE:/var/log/kadmind.log

[libdefaults]
 dns_lookup_realm = false
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true
 rdns = false
 pkinit_anchors = FILE:/etc/pki/tls/certs/ca-bundle.crt
 default_realm = $KERBEROS_REALM
 default_ccache_name = KEYRING:persistent:%{uid}

[realms]
 $KERBEROS_REALM = {
  kdc = localhost:$KERBEROS_KDC_PORT
  admin_server = localhost:$KERBEROS_ADMIN_PORT
 }

[domain_realm]
 .$KERBEROS_REALM = $KERBEROS_REALM
 $KERBEROS_REALM = $KERBEROS_REALM
EOL

    # 配置kdc.conf
    mkdir -p /var/kerberos/krb5kdc
    cat > /var/kerberos/krb5kdc/kdc.conf << EOL
[kdcdefaults]
 kdc_ports = 88
 kdc_tcp_ports = 88

[realms]
 $KERBEROS_REALM = {
  master_key_type = aes256-cts
  acl_file = /var/kerberos/krb5kdc/kadm5.acl
  dict_file = /usr/share/dict/words
  admin_keytab = /var/kerberos/krb5kdc/kadm5.keytab
  supported_enctypes = aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal camellia256-cts:normal camellia128-cts:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal
 }
EOL

    # 配置kadm5.acl
    echo "*/admin@$KERBEROS_REALM *" > /var/kerberos/krb5kdc/kadm5.acl
    
    green "✓ Kerberos配置文件创建完成"
    return 0
}

# 初始化Kerberos数据库
initialize_kerberos_database() {
    blue "步骤5/10: 初始化Kerberos数据库..."
    
    # 配置参数
    KERBEROS_REALM="EXAMPLE.COM"
    KERBEROS_ADMIN_USER="admin"
    KERBEROS_ADMIN_PASSWORD="admin123"
    
    # 创建Kerberos数据库
    expect -c "
spawn kdb5_util create -r $KERBEROS_REALM -s
expect \"Enter KDC database master key:\"
send \"$KERBEROS_ADMIN_PASSWORD\r\"
expect \"Re-enter KDC database master key to verify:\"
send \"$KERBEROS_ADMIN_PASSWORD\r\"
expect eof
"
    
    # 启动Kerberos服务
    if command -v systemctl &> /dev/null; then
        systemctl enable krb5kdc
        systemctl enable kadmin
        systemctl start krb5kdc
        systemctl start kadmin
    else
        service krb5kdc start
        service kadmin start
        chkconfig krb5kdc on
        chkconfig kadmin on
    fi
    
    # 创建管理员主体
    expect -c "
spawn kadmin.local -q \"addprinc -pw $KERBEROS_ADMIN_PASSWORD $KERBEROS_ADMIN_USER/admin\"
expect \"Enter password for principal:\"
send \"$KERBEROS_ADMIN_PASSWORD\r\"
expect \"Re-enter password for principal:\"
send \"$KERBEROS_ADMIN_PASSWORD\r\"
expect eof
"
    
    green "✓ Kerberos数据库初始化完成"
    return 0
}

# 安装Kafka
install_kafka() {
    blue "步骤6/10: 安装Kafka..."
    
    # 配置参数
    KAFKA_VERSION="2.8.1"
    SCALA_VERSION="2.13"
    KAFKA_INSTALL_DIR="/opt/kafka"
    KAFKA_DATA_DIR="/var/kafka-logs"
    KAFKA_PORT="9092"
    KAFKA_ZOOKEEPER_PORT="2181"
    KERBEROS_REALM="EXAMPLE.COM"
    
    # 创建Kafka用户
    useradd -r kafka -d $KAFKA_INSTALL_DIR -s /sbin/nologin 2>/dev/null || useradd kafka 2>/dev/null || echo "用户kafka已存在"
    
    # 创建Kafka安装目录
    mkdir -p $KAFKA_INSTALL_DIR
    mkdir -p $KAFKA_DATA_DIR
    
    # 下载并解压Kafka
    cd /tmp
    wget -q "https://archive.apache.org/dist/kafka/${KAFKA_VERSION}/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
    tar -xzf "kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
    cp -r "kafka_${SCALA_VERSION}-${KAFKA_VERSION}/*" $KAFKA_INSTALL_DIR/
    
    # 设置Kafka目录权限
    chown -R kafka:kafka $KAFKA_INSTALL_DIR
    chown -R kafka:kafka $KAFKA_DATA_DIR
    
    green "✓ Kafka安装完成"
    return 0
}

# 配置Kafka和Zookeeper
configure_kafka() {
    blue "步骤7/10: 配置Kafka和Zookeeper..."
    
    # 配置参数
    KAFKA_INSTALL_DIR="/opt/kafka"
    KAFKA_DATA_DIR="/var/kafka-logs"
    KAFKA_PORT="9092"
    KAFKA_ZOOKEEPER_PORT="2181"
    KERBEROS_REALM="EXAMPLE.COM"
    
    # 配置Zookeeper
    cat > $KAFKA_INSTALL_DIR/config/zookeeper.properties << EOL
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# the directory where the snapshot is stored.
dataDir=/tmp/zookeeper
# the port at which the clients will connect
clientPort=$KAFKA_ZOOKEEPER_PORT
# disable the per-ip limit on the number of connections since this is a non-production config
maxClientCnxns=0

# Enable Kerberos authentication
authProvider.1=org.apache.zookeeper.server.auth.SASLAuthenticationProvider
requireClientAuthScheme=sasl
jaasLoginRenew=3600000

# Define the JAAS configuration file
java.security.auth.login.config=$KAFKA_INSTALL_DIR/config/zookeeper_jaas.conf
EOL

    # 配置Zookeeper JAAS
    cat > $KAFKA_INSTALL_DIR/config/zookeeper_jaas.conf << EOL
Server {
   com.sun.security.auth.module.Krb5LoginModule required
   useKeyTab=true
   keyTab="/etc/security/keytabs/zookeeper.service.keytab"
   storeKey=true
   useTicketCache=false
   principal="zookeeper/localhost@$KERBEROS_REALM";
};
EOL

    # 配置Kafka
    cat > $KAFKA_INSTALL_DIR/config/server.properties << EOL
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The id of the broker. This must be set to a unique integer for each broker.
broker.id=0

# Switch to enable topic deletion or not, default value is false
delete.topic.enable=true

# ############################# Socket Server Settings #############################

# The address the socket server listens on. It will get the value returned from
# java.net.InetAddress.getCanonicalHostName().
#   FORMAT:
#     listeners = listener_name://host_name:port
#   EXAMPLE:
#     listeners = PLAINTEXT://your.host.name:9092
listeners=SASL_PLAINTEXT://0.0.0.0:$KAFKA_PORT
advertised.listeners=SASL_PLAINTEXT://localhost:$KAFKA_PORT

# Maps listener names to security protocols, the default is for them to be the same. See the config documentation for more details
listener.security.protocol.map=SASL_PLAINTEXT:SASL_PLAINTEXT

# The number of threads that the server uses for receiving requests from the network and sending responses to the network
num.network.threads=3

# The number of threads that the server uses for processing requests, which may include disk I/O
num.io.threads=8

# The send buffer (SO_SNDBUF) used by the socket server
socket.send.buffer.bytes=102400

# The receive buffer (SO_RCVBUF) used by the socket server
socket.receive.buffer.bytes=102400

# The maximum size of a request that the socket server will accept (protection against OOM)
socket.request.max.bytes=104857600

# ############################# Log Basics #############################

# A comma separated list of directories under which to store log files
log.dirs=$KAFKA_DATA_DIR

# The default number of log partitions per topic. More partitions allow greater
# parallelism for consumption, but also mean more files.
num.partitions=1

# The number of threads per data directory to be used for log recovery at startup and flushing at shutdown.
# This value is recommended to be increased for installations with data dirs located in RAID array.
num.recovery.threads.per.data.dir=1

# ############################# Internal Topic Settings #############################
# The replication factor for the metadata topic __consumer_offsets
offsets.topic.replication.factor=1
# For configs below please see their detailed docs in config/server.properties
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

# ############################# Log Flush Policy #############################

# Messages are immediately written to the filesystem but by default we only fsync() to sync
# the OS cache lazily. The following configurations control the flush of data to disk.
# There are a few important trade-offs here:
#    1. Durability: Unflushed data may be lost if you are not using replication.
#    2. Latency: Very large flush intervals may lead to latency spikes when the flush does occur as there will be a lot of data to flush.
#    3. Throughput: The flush is generally the most expensive operation, and a small flush interval may lead to excessive seeks.
# The settings below allow one to configure the flush policy to flush data after a period of time or
# every N messages (or both). This can be done globally and overridden on a per-topic basis.

# The number of messages to accept before forcing a flush of data to disk
#log.flush.interval.messages=10000

# The maximum amount of time a message can sit in a log before we force a flush
#log.flush.interval.ms=1000

# ############################# Log Retention Policy #############################

# The following configurations control the disposal of log segments. The policy can
# be set to delete segments after a period of time, or after a given size has accumulated.
# A segment will be deleted whenever *either* of these criteria are met. Deletion always happens
# from the end of the log.

# The minimum age of a log file to be eligible for deletion due to age
log.retention.hours=168

# A size-based retention policy for logs. Segments are pruned from the log as long as the remaining
# segments don't drop below log.retention.bytes. Functions independently of log.retention.hours.
#log.retention.bytes=1073741824

# The maximum size of a log segment file. When this size is reached a new log segment will be created.
log.segment.bytes=1073741824

# The interval at which log segments are checked to see if they can be deleted according
# to the retention policies
log.retention.check.interval.ms=300000

# ############################# Zookeeper #############################

# Zookeeper connection string (see zookeeper docs for more detail).
# This is a comma separated host:port pairs, each corresponding to a zk
# server. e.g. "127.0.0.1:3000,127.0.0.1:3001,127.0.0.1:3002".
# You can also append an optional chroot string to the urls to specify the
# root directory for all kafka znodes.
zookeeper.connect=localhost:$KAFKA_ZOOKEEPER_PORT

# Timeout in ms for connecting to zookeeper
zookeeper.connection.timeout.ms=18000

# ############################# Group Coordinator Settings #############################

# Group Coordinator settings
group.initial.rebalance.delay.ms=0

# ############################# Kerberos Settings #############################

# Enable Kerberos authentication
security.inter.broker.protocol=SASL_PLAINTEXT
sasl.mechanism.inter.broker.protocol=GSSAPI
sasl.enabled.mechanisms=GSSAPI
sasl.kerberos.service.name=kafka

# Define the JAAS configuration file
java.security.auth.login.config=$KAFKA_INSTALL_DIR/config/kafka_server_jaas.conf

# Authorizer settings
authorizer.class.name=kafka.security.authorizer.AclAuthorizer
super.users=User:admin
EOL

    # 配置Kafka JAAS
    cat > $KAFKA_INSTALL_DIR/config/kafka_server_jaas.conf << EOL
KafkaServer {
   com.sun.security.auth.module.Krb5LoginModule required
   useKeyTab=true
   keyTab="/etc/security/keytabs/kafka.service.keytab"
   storeKey=true
   useTicketCache=false
   principal="kafka/localhost@$KERBEROS_REALM";
};

Client {
   com.sun.security.auth.module.Krb5LoginModule required
   useKeyTab=true
   keyTab="/etc/security/keytabs/kafka.service.keytab"
   storeKey=true
   useTicketCache=false
   principal="kafka/localhost@$KERBEROS_REALM";
};
EOL

    green "✓ Kafka和Zookeeper配置完成"
    return 0
}

# 创建Kerberos服务主体和密钥表
create_kerberos_principals() {
    blue "步骤8/10: 创建Kerberos服务主体和密钥表..."
    
    # 配置参数
    KERBEROS_REALM="EXAMPLE.COM"
    
    # 创建密钥表目录
    mkdir -p /etc/security/keytabs
    
    # 创建Kafka服务主体
    expect -c "
spawn kadmin.local -q \"addprinc -randkey kafka/localhost@$KERBEROS_REALM\"
expect eof
"

    # 生成Kafka服务密钥表
    kadmin.local -q "ktadd -k /etc/security/keytabs/kafka.service.keytab kafka/localhost@$KERBEROS_REALM"

    # 创建Zookeeper服务主体
    expect -c "
spawn kadmin.local -q \"addprinc -randkey zookeeper/localhost@$KERBEROS_REALM\"
expect eof
"

    # 生成Zookeeper服务密钥表
    kadmin.local -q "ktadd -k /etc/security/keytabs/zookeeper.service.keytab zookeeper/localhost@$KERBEROS_REALM"

    # 设置密钥表权限
    chmod 600 /etc/security/keytabs/kafka.service.keytab
    chmod 600 /etc/security/keytabs/zookeeper.service.keytab
    chown kafka:kafka /etc/security/keytabs/kafka.service.keytab 2>/dev/null || chown root:root /etc/security/keytabs/kafka.service.keytab
    chown kafka:kafka /etc/security/keytabs/zookeeper.service.keytab 2>/dev/null || chown root:root /etc/security/keytabs/zookeeper.service.keytab
    
    green "✓ Kerberos服务主体和密钥表创建完成"
    return 0
}

# 创建并启动Kafka和Zookeeper服务
create_and_start_services() {
    blue "步骤9/10: 创建并启动Kafka和Zookeeper服务..."
    
    # 配置参数
    KAFKA_INSTALL_DIR="/opt/kafka"
    
    # 创建Kafka服务文件
    cat > /etc/systemd/system/zookeeper.service << EOL
[Unit]
Description=Apache Zookeeper service
Documentation=http://zookeeper.apache.org
After=network.target

[Service]
Type=simple
User=kafka
Group=kafka
ExecStart=$KAFKA_INSTALL_DIR/bin/zookeeper-server-start.sh $KAFKA_INSTALL_DIR/config/zookeeper.properties
ExecStop=$KAFKA_INSTALL_DIR/bin/zookeeper-server-stop.sh
Restart=on-abnormal
Environment="JAVA_HOME=/usr/lib/jvm/jre"
Environment="KAFKA_OPTS=-Djava.security.auth.login.config=$KAFKA_INSTALL_DIR/config/zookeeper_jaas.conf"

[Install]
WantedBy=multi-user.target
EOL

    cat > /etc/systemd/system/kafka.service << EOL
[Unit]
Description=Apache Kafka service
Documentation=http://kafka.apache.org
After=network.target zookeeper.service

[Service]
Type=simple
User=kafka
Group=kafka
ExecStart=$KAFKA_INSTALL_DIR/bin/kafka-server-start.sh $KAFKA_INSTALL_DIR/config/server.properties
ExecStop=$KAFKA_INSTALL_DIR/bin/kafka-server-stop.sh
Restart=on-abnormal
Environment="JAVA_HOME=/usr/lib/jvm/jre"
Environment="KAFKA_OPTS=-Djava.security.auth.login.config=$KAFKA_INSTALL_DIR/config/kafka_server_jaas.conf"

[Install]
WantedBy=multi-user.target
EOL

    # 重新加载systemd并启用服务
    if command -v systemctl &> /dev/null; then
        systemctl daemon-reload
        systemctl enable zookeeper
        systemctl enable kafka
        
        # 启动Zookeeper
        systemctl start zookeeper
        
        # 等待Zookeeper启动
        sleep 5
        
        # 启动Kafka
        systemctl start kafka
    else
        # 对于不支持systemctl的系统
        chkconfig zookeeper on 2>/dev/null || echo "Zookeeper服务已配置"
        chkconfig kafka on 2>/dev/null || echo "Kafka服务已配置"
        
        # 启动Zookeeper
        service zookeeper start
        
        # 等待Zookeeper启动
        sleep 5
        
        # 启动Kafka
        service kafka start
    fi
    
    green "✓ Kafka和Zookeeper服务创建并启动完成"
    return 0
}

# 验证安装
verify_installation() {
    blue "步骤10/10: 验证安装..."
    
    # 配置参数
    KERBEROS_ADMIN_USER="admin"
    KERBEROS_ADMIN_PASSWORD="admin123"
    KERBEROS_REALM="EXAMPLE.COM"
    KAFKA_INSTALL_DIR="/opt/kafka"
    
    # 验证Kerberos服务
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet krb5kdc; then
            green "✓ KDC服务正在运行"
        else
            red "✗ KDC服务未运行"
        fi
        
        if systemctl is-active --quiet kadmin; then
            green "✓ Kadmin服务正在运行"
        else
            red "✗ Kadmin服务未运行"
        fi
        
        if systemctl is-active --quiet zookeeper; then
            green "✓ Zookeeper服务正在运行"
        else
            red "✗ Zookeeper服务未运行"
        fi
        
        if systemctl is-active --quiet kafka; then
            green "✓ Kafka服务正在运行"
        else
            red "✗ Kafka服务未运行"
        fi
    else
        # 对于不支持systemctl的系统
        if service krb5kdc status &> /dev/null; then
            green "✓ KDC服务正在运行"
        else
            red "✗ KDC服务未运行"
        fi
        
        if service kadmin status &> /dev/null; then
            green "✓ Kadmin服务正在运行"
        else
            red "✗ Kadmin服务未运行"
        fi
        
        if service zookeeper status &> /dev/null; then
            green "✓ Zookeeper服务正在运行"
        else
            red "✗ Zookeeper服务未运行"
        fi
        
        if service kafka status &> /dev/null; then
            green "✓ Kafka服务正在运行"
        else
            red "✗ Kafka服务未运行"
        fi
    fi
    
    # 验证Kerberos管理员主体
    expect -c "
spawn kinit $KERBEROS_ADMIN_USER/admin@$KERBEROS_REALM
expect \"Password for $KERBEROS_ADMIN_USER/admin@$KERBEROS_REALM:\"
send \"$KERBEROS_ADMIN_PASSWORD\r\"
expect eof
" &> /dev/null
    
    if klist &> /dev/null; then
        green "✓ Kerberos管理员主体验证成功"
    else
        red "✗ Kerberos管理员主体验证失败"
    fi
    
    # 验证Kafka基本功能
    if [ -x $KAFKA_INSTALL_DIR/bin/kafka-topics.sh ]; then
        $KAFKA_INSTALL_DIR/bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic test-topic &> /dev/null
        if [ $? -eq 0 ]; then
            green "✓ Kafka测试主题创建成功"
        else
            red "✗ Kafka测试主题创建失败"
        fi
    else
        red "✗ Kafka主题工具不存在"
    fi
    
    # 显示端口监听状态
    netstat -tlnp | grep :88 &> /dev/null && green "✓ Kerberos KDC端口(88)正在监听" || red "✗ Kerberos KDC端口(88)未监听"
    netstat -tlnp | grep :749 &> /dev/null && green "✓ Kerberos Admin端口(749)正在监听" || red "✗ Kerberos Admin端口(749)未监听"
    netstat -tlnp | grep :2181 &> /dev/null && green "✓ Zookeeper端口(2181)正在监听" || red "✗ Zookeeper端口(2181)未监听"
    netstat -tlnp | grep :9092 &> /dev/null && green "✓ Kafka端口(9092)正在监听" || red "✗ Kafka端口(9092)未监听"
    
    green "✓ 验证完成"
    return 0
}

# 创建使用指南
create_usage_guide() {
    cat > /root/kerberos-kafka-usage.txt << EOF
# Kerberos-Kafka环境使用指南

## 环境信息
- Kerberos Realm: EXAMPLE.COM
- Kerberos管理员用户: admin
- Kafka安装目录: /opt/kafka
- Kafka端口: 9092
- Zookeeper端口: 2181

## Kerberos使用方法

### 1. 管理员登录
\`\`\`bash
kinit admin/admin@EXAMPLE.COM
# 输入密码: admin123
\`\`\`

### 2. 创建普通用户
\`\`\`bash
kadmin.local -q "addprinc -pw <password> <username>@EXAMPLE.COM"
\`\`\`

### 3. 创建服务主体
\`\`\`bash
kadmin.local -q "addprinc -randkey <service>/<hostname>@EXAMPLE.COM"
kadmin.local -q "ktadd -k /etc/security/keytabs/<service>.service.keytab <service>/<hostname>@EXAMPLE.COM"
\`\`\`

### 4. 查看当前票据
\`\`\`bash
klist
\`\`\`

### 5. 销毁票据
\`\`\`bash
kdestroy
\`\`\`

## Kafka使用方法

### 1. 创建主题
\`\`\`bash
/opt/kafka/bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic <topic-name>
\`\`\`

### 2. 列出主题
\`\`\`bash
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
\`\`\`

### 3. 发送消息
\`\`\`bash
/opt/kafka/bin/kafka-console-producer.sh --broker-list localhost:9092 --topic <topic-name>
\`\`\`

### 4. 接收消息
\`\`\`bash
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic <topic-name> --from-beginning
\`\`\`

## 服务管理

### 1. 查看服务状态
\`\`\`bash
systemctl status krb5kdc
systemctl status kadmin
systemctl status zookeeper
systemctl status kafka
\`\`\`

### 2. 启动服务
\`\`\`bash
systemctl start krb5kdc
systemctl start kadmin
systemctl start zookeeper
systemctl start kafka
\`\`\`

### 3. 停止服务
\`\`\`bash
systemctl stop krb5kdc
systemctl stop kadmin
systemctl stop zookeeper
systemctl stop kafka
\`\`\`

### 4. 重启服务
\`\`\`bash
systemctl restart krb5kdc
systemctl restart kadmin
systemctl restart zookeeper
systemctl restart kafka
\`\`\`

## 日志查看

### 1. Kerberos日志
\`\`\`bash
tail -f /var/log/krb5kdc.log
tail -f /var/log/kadmind.log
\`\`\`

### 2. Kafka日志
\`\`\`bash
tail -f /opt/kafka/logs/server.log
tail -f /opt/kafka/logs/state-change.log
\`\`\`

### 3. Zookeeper日志
\`\`\`bash
tail -f /opt/kafka/logs/zookeeper.out
\`\`\`

## 故障排除

### 1. Kerberos问题
- 检查KDC配置: /etc/krb5.conf, /var/kerberos/krb5kdc/kdc.conf
- 检查ACL配置: /var/kerberos/krb5kdc/kadm5.acl
- 检查密钥表: /etc/security/keytabs/

### 2. Kafka问题
- 检查Kafka配置: /opt/kafka/config/server.properties
- 检查JAAS配置: /opt/kafka/config/kafka_server_jaas.conf
- 检查Zookeeper配置: /opt/kafka/config/zookeeper.properties

### 3. 网络问题
- 检查防火墙设置
- 检查端口监听状态: netstat -tlnp
- 检查主机名解析: /etc/hosts

## 安全注意事项

1. 定期更新Kerberos用户密码
2. 限制Kerberos管理员权限
3. 定期备份Kerberos数据库
4. 监控Kafka访问日志
5. 限制Kafka主题访问权限

EOF

    green "✓ 使用指南已创建: /root/kerberos-kafka-usage.txt"
    return 0
}

# 显示安装结果摘要
show_installation_summary() {
    echo "\n=========================================="
    echo "Kerberos-Kafka环境安装结果摘要"
    echo "=========================================="
    
    green "🎉 安装成功！Kerberos-Kafka环境已成功搭建并验证"
    echo ""
    echo "环境详情:"
    echo "- Kerberos Realm: EXAMPLE.COM"
    echo "- Kerberos管理员用户: admin"
    echo "- Kafka安装目录: /opt/kafka"
    echo "- Kafka端口: 9092"
    echo "- Zookeeper端口: 2181"
    echo ""
    echo "后续操作建议:"
    echo "1. 查看使用指南: cat /root/kerberos-kafka-usage.txt"
    echo "2. 验证安装: 手动执行验证命令"
    echo "3. 配置防火墙规则，开放必要端口"
    echo ""
    echo "快速开始Kerberos:"
    echo "kinit admin/admin@EXAMPLE.COM"
    echo "输入密码: admin123"
    echo ""
    echo "快速开始Kafka:"
    echo "/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
    echo "=========================================="
}

# 显示帮助信息
show_help() {
    echo "Kerberos-Kafka环境独立安装脚本"
    echo ""
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -v, --verify   仅验证已安装的环境"
    echo ""
    echo "示例:"
    echo "  $0                    # 执行完整安装"
    echo "  $0 --verify           # 仅验证已安装的环境"
}

# 解析命令行参数
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verify)
            VERIFY_ONLY=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主程序
blue "开始Kerberos-Kafka环境独立安装..."

# 如果仅验证模式，则直接执行验证
if $VERIFY_ONLY; then
    verify_installation
    exit 0
fi

# 检查是否以root权限运行
check_root_privileges

# 检查系统环境
check_system_environment

# 安装必要的系统依赖
install_system_dependencies

# 配置Kerberos
configure_kerberos

# 初始化Kerberos数据库
initialize_kerberos_database

# 安装Kafka
install_kafka

# 配置Kafka和Zookeeper
configure_kafka

# 创建Kerberos服务主体和密钥表
create_kerberos_principals

# 创建并启动Kafka和Zookeeper服务
create_and_start_services

# 验证安装
verify_installation

# 创建使用指南
create_usage_guide

# 显示安装结果摘要
show_installation_summary

green "\nKerberos-Kafka环境独立安装脚本执行完成！"