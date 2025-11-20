#!/bin/bash
# 可改项
HOST_FQDN="$(hostname -f)"
HOST_IP="$(ip route get 1.1.1.1 | awk '{print $7; exit}')"
REALM="EXAMPLE.COM"
KAFKA_VERSION="3.8.0"
SCALA_VERSION="2.13"
set -eux

# 0 前置检查
if [[ $EUID -ne 0 ]]; then
  echo "请用 root 跑" ; exit 1
fi
which java &>/dev/null || yum -y install java-17-openjdk java-17-openjdk-devel
yum -y install krb5-server krb5-workstation wget

# 1 写 krb5.conf（幂等）
teef="/etc/krb5.conf"
\cp -f /etc/krb5.conf ${teef}.bak 2>/dev/null || true
tee $teef <<EOF
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

# 2 写 hosts（单机演示用）
grep -q "$HOST_IP $HOST_FQDN" /etc/hosts || echo "$HOST_IP $HOST_FQDN" >> /etc/hosts

# 3 若数据库已存在则先毁掉重建
if [ -f /var/kerberos/krb5kdc/principal ]; then
  kdb5_util destroy -f
fi
kdb5_util create -s -r $REALM -P password  # 统一用简单密码，实验环境
systemctl enable --now krb5kdc kadmin

# 4 建管理员 / kafka / 客户端账号
kadmin.local -q "addprinc -pw adminpw admin/admin"
kadmin.local -q "addprinc -randkey kafka/$HOST_FQDN"
kadmin.local -q "ktadd -k /etc/kafka.keytab kafka/$HOST_FQDN"
chmod 600 /etc/kafka.keytab

# 5 下载 Kafka
KAFKA_TGZ="kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
cd /root
[ -f $KAFKA_TGZ ] || wget -q https://downloads.apache.org/kafka/${KAFKA_VERSION}/$KAFKA_TGZ
tar -xf $KAFKA_TGZ
KAFKA_DIR="/root/kafka_${SCALA_VERSION}-${KAFKA_VERSION}"
ln -sfn $KAFKA_DIR kafka

# 6 JAAS
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

# 7 生成 broker 配置
SERVER_CFG="/root/kafka/config/server-sasl.properties"
\cp /root/kafka/config/server.properties $SERVER_CFG
cat <<EOF >> $SERVER_CFG

# ---- Kerberos SASL 追加 ----
listeners=SASL_PLAINTEXT://$HOST_FQDN:9092
advertised.listeners=SASL_PLAINTEXT://$HOST_FQDN:9092
security.inter.broker.protocol=SASL_PLAINTEXT
sasl.mechanism.inter.broker.protocol=GSSAPI
sasl.enabled.mechanisms=GSSAPI
sasl.kerberos.service.name=kafka
authorizer.class.name=kafka.security.authorizer.AclAuthorizer
super.users=User:kafka
EOF

# 8 启动 Kafka
export KAFKA_OPTS="-Djava.security.auth.login.config=$JAAS_SERVER"
nohup /root/kafka/bin/kafka-server-start.sh -daemon $SERVER_CFG
sleep 10
tail /root/kafka/logs/server.log | grep -i "Kafka Server started" && echo "✅ Kafka 启动成功"

# 9 客户端测试账号
kadmin -p admin/admin -w adminpw -q "addprinc -pw alicepw alice"

# 10 客户端 JAAS（复用 ticket cache 版）
JAAS_CLIENT="/root/kafka_client_jaas.conf"
tee $JAAS_CLIENT <<EOF
KafkaClient {
  com.sun.security.auth.module.Krb5LoginModule required
  useTicketCache=true;
};
EOF

# 11 一次性环境变量说明
echo "======== 使用方式 ========"
echo "1. 生产/消费前先 kinit:"
echo "   kinit alice   # 密码 alicepw"
echo "2. 导出客户端变量:"
echo "   export KAFKA_OPTS=\"-Djava.security.auth.login.config=$JAAS_CLIENT\""
echo "3. 跑客户端:"
echo "   /root/kafka/bin/kafka-console-producer.sh --bootstrap-server $HOST_FQDN:9092 --topic demo --producer.config $SERVER_CFG"
echo "================================"