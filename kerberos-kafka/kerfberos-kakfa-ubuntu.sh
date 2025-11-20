#!/bin/bash
set -euo pipefail
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

echo ">>> 0 检测 root"
[[ $EUID -eq 0 ]] || { echo "请用 root 跑"; exit 1; }

echo ">>> 1 检查并创建必要的目录"
# 检查并创建Kerberos相关目录
check_and_create_dir "/etc/krb5kdc"
check_and_create_dir "/var/lib/krb5kdc"
check_and_create_dir "/root"
check_and_create_dir "/root/kafka/logs"
check_and_create_dir "/root/kafka/config"
check_and_create_dir "/root/kafka/zookeeper"

echo ">>> 2 装包"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y install openjdk-17-jdk krb5-kdc krb5-admin-server krb5-user wget

echo ">>> 3 写 krb5.conf"
tee /etc/krb5.conf <<EOF
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

echo ">>> 4 写 hosts（若未写过）"
grep -q "$HOST_IP $HOST_FQDN" /etc/hosts || echo "$HOST_IP $HOST_FQDN" >> /etc/hosts

echo ">>> 5 建 kdc.conf（Ubuntu 必备）"
tee /etc/krb5kdc/kdc.conf <<EOF
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

echo ">>> 6 初始化数据库 & 起服务"
# 若库已存在则先毁掉
[ -f /var/lib/krb5kdc/principal ] && kdb5_util destroy -f || true
kdb5_util create -s -r $REALM -P password
systemctl enable --now krb5-kdc krb5-admin-server

echo ">>> 7 建账号"
kadmin.local -q "addprinc -pw adminpw admin/admin"
kadmin.local -q "addprinc -randkey kafka/$HOST_FQDN"
kadmin.local -q "ktadd -k /etc/kafka.keytab kafka/$HOST_FQDN"
chmod 600 /etc/kafka.keytab

echo ">>> 8 下载 Kafka"
cd /root
KAFKA_TGZ="kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
[ -f "$KAFKA_TGZ" ] || wget -q https://downloads.apache.org/kafka/$KAFKA_VERSION/$KAFKA_TGZ
tar -xf $KAFKA_TGZ
KAFKA_DIR="/root/kafka_${SCALA_VERSION}-${KAFKA_VERSION}"
ln -sfn $KAFKA_DIR kafka

echo ">>> 9 配置Zookeeper"
# 创建Zookeeper配置文件
ZOO_CFG="/root/kafka/config/zookeeper.properties"
cat > $ZOO_CFG <<EOF
# Zookeeper配置
dataDir=/root/kafka/zookeeper
clientPort=2181
maxClientCnxns=0
admin.enableServer=true
admin.serverPort=8080
tickTime=2000
initLimit=10
syncLimit=5
EOF

echo ">>> 10 启动 Zookeeper"
nohup $KAFKA_DIR/bin/zookeeper-server-start.sh -daemon $ZOO_CFG
sleep 5
echo "✅ Zookeeper 启动成功"

echo ">>> 11 写 server JAAS"
JAAS_SERVER="/root/kafka_server_jaas.conf"
tee $JAAS_SERVER <<EOF
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

echo ">>> 12 生成 broker 配置"
SERVER_CFG="/root/kafka/config/server-sasl.properties"
cp $KAFKA_DIR/config/server.properties $SERVER_CFG
cat <<EOF >> $SERVER_CFG
# ---- Kerberos SASL ----
listeners=SASL_PLAINTEXT://0.0.0.0:9092
advertised.listeners=SASL_PLAINTEXT://$HOST_IP:9092
security.inter.broker.protocol=SASL_PLAINTEXT
sasl.mechanism.inter.broker.protocol=GSSAPI
sasl.enabled.mechanisms=GSSAPI
sasl.kerberos.service.name=kafka
authorizer.class.name=kafka.security.authorizer.AclAuthorizer
super.users=User:kafka
# Zookeeper连接配置
zookeeper.connect=localhost:2181
EOF

echo ">>> 13 启动 Kafka"
export KAFKA_OPTS="-Djava.security.auth.login.config=$JAAS_SERVER"
nohup $KAFKA_DIR/bin/kafka-server-start.sh -daemon $SERVER_CFG
sleep 10
tail $KAFKA_DIR/logs/server.log | grep -i "Kafka Server started" && echo "✅ Kafka 启动成功"

echo ">>> 13.1 检查Kafka进程和端口"
echo "检查Kafka进程："
ps aux | grep kafka | grep -v grep || echo "未找到Kafka进程"
echo "检查9092端口监听："
netstat -tlnp | grep 9092 || ss -tlnp | grep 9092 || echo "9092端口未监听"
echo "检查Kafka日志最后20行："
tail -n 20 $KAFKA_DIR/logs/server.log

echo ">>> 14 客户端账号"
kadmin -p admin/admin -w adminpw -q "addprinc -pw alicepw alice"

echo ">>> 15 客户端 JAAS（ticket cache 版）"
JAAS_CLIENT="/root/kafka_client_jaas.conf"
tee $JAAS_CLIENT <<EOF
KafkaClient {
  com.sun.security.auth.module.Krb5LoginModule required
  useTicketCache=true;
};
EOF

echo "==================== 使用步骤 ===================="
echo "1. 获取票据：  kinit alice      # 密码 alicepw"
echo "2. 导出变量：  export KAFKA_OPTS=\"-Djava.security.auth.login.config=$JAAS_CLIENT\""
echo "3. 生产消息：  $KAFKA_DIR/bin/kafka-console-producer.sh --bootstrap-server $HOST_IP:9092 --topic demo --producer.config $SERVER_CFG"
echo "4. 消费消息：  $KAFKA_DIR/bin/kafka-console-consumer.sh --bootstrap-server $HOST_IP:9092 --topic demo --from-beginning --consumer.config $SERVER_CFG"
echo "================================================="