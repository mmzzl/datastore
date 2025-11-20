#!/bin/bash
set -eux
# ========== 可改项 ==========
HOST_FQDN="$(hostname -f)"
HOST_IP="$(ip route get 1.1.1.1 | awk '{print $7; exit}')"
REALM="EXAMPLE.COM"
KAFKA_VERSION="3.8.0"
SCALA_VERSION="2.13"
# ============================

# 函数：检查并创建目录
check_and_create_dir() {
    local dir_path="$1"
    if [ ! -d "$dir_path" ]; then
        echo "创建目录: $dir_path"
        mkdir -p "$dir_path"
    else
        echo "目录已存在: $dir_path"
    fi
}

echo ">>> 0 前置检查"
# 检查root权限
[[ $EUID -eq 0 ]] || { echo "请用root运行此脚本"; exit 1; }

echo ">>> 1 检查并创建必要的目录"
# 检查并创建Kerberos相关目录
check_and_create_dir "/etc/krb5kdc"
check_and_create_dir "/var/lib/krb5kdc"
check_and_create_dir "/root"
check_and_create_dir "/root/kafka/logs"

echo ">>> 2 安装依赖"
# 更新包列表
apt-get update
# 安装必要的包
apt-get install -y openjdk-17-jdk krb5-kdc krb5-admin-server krb5-user wget

echo ">>> 3 配置Kerberos"
# 配置krb5.conf
cat > /etc/krb5.conf <<EOF
[libdefaults]
  default_realm = $REALM
  dns_lookup_realm = false
  dns_lookup_kdc  = false
[realms]
  $REALM = {
   kdc = $HOST_FQDN
   admin_server = $HOST_FQDN
  }
[domain_realm]
  .$HOST_FQDN = $REALM
  $HOST_FQDN = $REALM
EOF

# 配置hosts文件
if ! grep -q "$HOST_IP $HOST_FQDN" /etc/hosts; then
    echo "$HOST_IP $HOST_FQDN" >> /etc/hosts
fi

# 配置kdc.conf
cat > /etc/krb5kdc/kdc.conf <<EOF
[kdcdefaults]
 kdc_ports = 88
 kdc_tcp_ports = 88
[realms]
 $REALM = {
  database_name = /var/lib/krb5kdc/principal
  admin_keytab  = /etc/krb5kdc/kadm5.keytab
  acl_file      = /etc/krb5kdc/kadm5.acl
  key_stash_file = /var/lib/krb5kdc/.k5.$REALM
 }
EOF

# 配置kadm5.acl
cat > /etc/krb5kdc/kadm5.acl <<EOF
*/admin@$REALM *
EOF

echo ">>> 4 初始化Kerberos数据库"
# 如果数据库已存在，先删除
if [ -f /var/lib/krb5kdc/principal ]; then
    kdb5_util destroy -f
fi
# 创建新的Kerberos数据库
kdb5_util create -s -r $REALM -P password

echo ">>> 5 启动Kerberos服务"
systemctl enable --now krb5-kdc krb5-admin-server

echo ">>> 6 创建Kerberos主体和密钥表"
# 创建管理员主体
kadmin.local -q "addprinc -pw adminpw admin/admin"
# 创建Kafka服务主体
kadmin.local -q "addprinc -randkey kafka/$HOST_FQDN"
# 创建并导出Kafka服务密钥表
kadmin.local -q "ktadd -k /etc/kafka.keytab kafka/$HOST_FQDN"
# 设置密钥表权限
chmod 600 /etc/kafka.keytab

echo ">>> 7 下载并安装Kafka"
cd /root
KAFKA_TGZ="kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
if [ ! -f "$KAFKA_TGZ" ]; then
    wget -q https://downloads.apache.org/kafka/$KAFKA_VERSION/$KAFKA_TGZ
fi
tar -xf $KAFKA_TGZ
KAFKA_DIR="/root/kafka_${SCALA_VERSION}-${KAFKA_VERSION}"
ln -sfn $KAFKA_DIR kafka

echo ">>> 8 配置Kafka SASL认证"
# 创建服务器JAAS配置文件
cat > /root/kafka_server_jaas.conf <<EOF
KafkaServer {
  com.sun.security.auth.module.Krb5LoginModule required
  useKeyTab=true storeKey=true keyTab="/etc/kafka.keytab"
  principal="kafka/$HOST_FQDN@$REALM";
};
Client {
  com.sun.security.auth.module.Krb5LoginModule required
  useKeyTab=true storeKey=true keyTab="/etc/kafka.keytab"
  principal="kafka/$HOST_FQDN@$REALM";
};
EOF

# 配置Kafka服务器
SERVER_CFG="/root/kafka/config/server-sasl.properties"
cp $KAFKA_DIR/config/server.properties $SERVER_CFG
cat >> $SERVER_CFG <<EOF

# ---- Kerberos SASL ----
listeners=SASL_PLAINTEXT://$HOST_FQDN:9092
advertised.listeners=SASL_PLAINTEXT://$HOST_FQDN:9092
security.inter.broker.protocol=SASL_PLAINTEXT
sasl.mechanism.inter.broker.protocol=GSSAPI
sasl.enabled.mechanisms=GSSAPI
sasl.kerberos.service.name=kafka
authorizer.class.name=kafka.security.authorizer.AclAuthorizer
super.users=User:kafka
EOF

echo ">>> 9 启动Kafka服务"
export KAFKA_OPTS="-Djava.security.auth.login.config=/root/kafka_server_jaas.conf"
nohup $KAFKA_DIR/bin/kafka-server-start.sh -daemon $SERVER_CFG
sleep 10
tail $KAFKA_DIR/logs/server.log | grep -i "Kafka Server started" && echo "✅ Kafka 启动成功"

echo ">>> 10 创建客户端账号"
kadmin -p admin/admin -w adminpw -q "addprinc -pw alicepw alice"

echo ">>> 11 创建客户端JAAS配置"
cat > /root/kafka_client_jaas.conf <<EOF
KafkaClient {
  com.sun.security.auth.module.Krb5LoginModule required
  useTicketCache=true;
};
EOF

echo "==================== 使用步骤 ===================="
echo "1. 获取票据：  kinit alice      # 密码 alicepw"
echo "2. 导出变量：  export KAFKA_OPTS=\"-Djava.security.auth.login.config=/root/kafka_client_jaas.conf\""
echo "3. 生产消息：  $KAFKA_DIR/bin/kafka-console-producer.sh --bootstrap-server $HOST_FQDN:9092 --topic demo --producer.config $SERVER_CFG"
echo "4. 消费消息：  $KAFKA_DIR/bin/kafka-console-consumer.sh --bootstrap-server $HOST_FQDN:9092 --topic demo --from-beginning --consumer.config $SERVER_CFG"
echo "================================================="