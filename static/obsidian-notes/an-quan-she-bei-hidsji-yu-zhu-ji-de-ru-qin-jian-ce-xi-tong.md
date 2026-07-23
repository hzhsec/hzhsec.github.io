---
title: "安全设备-HIDS基于主机的入侵检测系统"
slug: an-quan-she-bei-hidsji-yu-zhu-ji-de-ru-qin-jian-ce-xi-tong
cover: ""
date: 2026-04-24
categories:
  - 应急响应
tags:
  - HIDS
halo:
  site: http://www.hzhsec.top
  name: c39f9d22-d59b-407e-aab6-83426043634b
  publish: true
---

---
>HIDS 通常通过在主机部署 Agent，采集系统日志、进程、文件、网络连接、登录行为等主机侧数据进行检测。

![image.png|600](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260416184521760.png)

接下来以两款免费的`HIDS`的搭建和简单使用来介绍`HIDS`的基本作用
- Wazuh
- Elkeid

# Wazuh
>Wazuh 是一个开源的主机入侵检测与安全监控平台，通过在主机部署 Agent 采集日志与系统行为并进行分析，实现安全告警与集中管理。

## 搭建
### service
购买华为云的按量付费的|`4vCPUs `| `8GiB`|`40G`|的服务器,最低配置了已经
实验环境建议至少 `4C8G`，磁盘 `40G` 起步；生产环境需根据 Agent 数量和日志量扩容。
购买后
1. 搭建docker环境
docker 一键搭建:
```
bash <(curl -sSL https://xuanyuan.cloud/docker.sh)
```

2. 拉取镜像
```
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-manager:4.12.0
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-indexer:4.12.0
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-dashboard:4.12.0
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-certs-generator:0.0.2
```
拉取不了镜像源,可以使用这个项目配置镜像源
https://github.com/hzhsec/docker_proxy.git

3. 重新打 tag
```
docker tag swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-manager:4.12.0 wazuh/wazuh-manager:4.12.0
docker tag swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-indexer:4.12.0 wazuh/wazuh-indexer:4.12.0
docker tag swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-dashboard:4.12.0 wazuh/wazuh-dashboard:4.12.0
docker tag swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wazuh/wazuh-certs-generator:0.0.2 wazuh/wazuh-certs-generator:0.0.2
```
4. 验证
```
docker images | grep wazuh
```
5. 生成证书
```
docker compose -f generate-indexer-certs.yml run --rm generator
```

检查证书
```
ls -la config/wazuh_indexer_ssl_certs/
```

启动（使用 docker compose，不是 docker-compose）
```
docker compose up -d
```
查看状态
```
docker compose ps
```

获取docker-compose.yml配置文件
```
cd /data
git clone https://github.com/wazuh/wazuh-docker.git -b v4.12.0
cd wazuh-docker/single-node/
```

启动
`docker compose up -d`

Dashboard主页
```
https://<YOUR_SERVER_IP>:443
```

默认账号密码：
用户名：`admin`
密码：`SecretPassword`
公网部署后必须立即修改默认密码，避免被扫到后接管。

## agent
```bash
# 在被监控服务器上执行

# 下载 Agent（版本要和 Manager 匹配）
curl -so wazuh-agent-4.12.0-1.x86_64.rpm https://packages.wazuh.com/4.x/yum/wazuh-agent-4.12.0-1.x86_64.rpm

# 安装（替换为你的 Wazuh 服务器 IP）
WAZUH_MANAGER='<YOUR_WAZUH_SERVER_IP>' rpm -ihv wazuh-agent-4.12.0-1.x86_64.rpm

# 启动
systemctl daemon-reload
systemctl enable wazuh-agent
systemctl start wazuh-agent

# 检查状态
systemctl status wazuh-agent

```

等待几分钟,查看service端的状态



# Elkeid
>**Elkeid 是字节开源的主机入侵检测系统，通过在主机部署 Agent 采集内核与系统行为数据并实时分析，实现安全检测、告警与集中管控。**

Elkeid 后端会涉及数据存储、检索和可视化组件，功能上类似安全数据采集、分析、展示的一体化平台；

## 搭建
### 服务端安装
1. docker 一键搭建:
```
bash <(curl -sSL https://xuanyuan.cloud/docker.sh)
```
如果一键脚本安装` Docker Compose` 阶段长时间无响应，可以中断后手动安装 `Docker Compose` 插件。
![Snipaste_2026-04-16_17-38-23.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-38-23.png)
验证docker
`docker -v`
![Snipaste_2026-04-16_17-38-35.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-38-35.png)

2. 自己安装`docker compose`
创建目录
```bash
mkdir -p /usr/libexec/docker/cli-plugins
```
下载`docker compose`
```bash
curl -L https://gh.xmly.dev/https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64 -o /usr/libexec/docker/cli-plugins/docker-compose
```
执行权限
```bash
chmod +x /usr/libexec/docker/cli-plugins/docker-compose
```
验证安装
```bash
docker compose version
```

![Snipaste_2026-04-16_17-38-54.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-38-54.png)


3. 换docker镜像源
```bash
yum install git -y
git clone https://github.com/hzhsec/docker_proxy.git
cd docker_proxy.sh
chmod +x ./*.sh
./docker_yuan.sh
```
![Snipaste_2026-04-16_17-40-13.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-40-13.png)

4. 开始安装`elkeid`
创建工作目录
```bash
mkdir -p /opt/elkeid
cd /opt/elkeid
```
下载压缩包
```bash
wget https://gh.xmly.dev/https://github.com/bytedance/Elkeid/releases/download/v1.9.1.4/elkeidup_image_v1.9.1.tar.gz.00
wget https://gh.xmly.dev/https://github.com/bytedance/Elkeid/releases/download/v1.9.1.4/elkeidup_image_v1.9.1.tar.gz.01
wget https://gh.xmly.dev/https://github.com/bytedance/Elkeid/releases/download/v1.9.1.4/elkeidup_image_v1.9.1.tar.gz.02
wget https://gh.xmly.dev/https://github.com/bytedance/Elkeid/releases/download/v1.9.1.4/elkeidup_image_v1.9.1.tar.gz.03
```
![Snipaste_2026-04-16_17-40-38.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-40-38.png)
![Snipaste_2026-04-16_17-40-48.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-40-48.png)
合成并加载
```bash
cat elkeidup_image_v1.9.1.tar.gz.* > elkeidup_image_v1.9.1.tar.gz
docker load -i elkeidup_image_v1.9.1.tar.gz
```
启动容器
```bash
docker run -d --name elkeid_community \
  --restart=unless-stopped \
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
  -p 8071:8071 -p 8072:8072 -p 8080:8080 \
  -p 8081:8081 -p 8082:8082 -p 8089:8080 -p 8090:8090 \
  --privileged \
  elkeid/all-in-one:v1.9.1
```
进入容器
```bash
docker exec -it elkeid_community bash
```
5. 执行初始化操作
```bash
cd /root/.elkeidup/
./elkeidup public ip(自己的公网ip)
./elkeidup agent init
./elkeidup agent build
./elkeidup agent policy create
```

![Snipaste_2026-04-16_17-53-59.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-53-59.png)

查看密码
```bash
cat ~/.elkeidup/elkeid_passwd
```
`elkeid_console`：console 地址和账号密码
`elkeid_hub_frontend`：hub 前端地址和账号密码
`grafana`：grafana 地址和账号密码
`elkeid_service_discovery`：服务发现地址。
访问后台地址`http://ip:8082`
账号密码:`root` `7rkm95s09kl23o85diZP`
![Snipaste_2026-04-16_17-54-44.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_17-54-44.png)

6. 服务端安装成功
![Snipaste_2026-04-16_18-02-50.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_18-02-50.png)

### **客户端安装**

服务端
```text
点击系统管理->安装配置->复制安装命令
```

客户端执行复制命令
```bash
bash -c "if (command -v curl); then (curl -sS http://139.9.34.127:8080/agent/install.sh | bash);else (wget -q -O - http://139.9.34.127:8080/agent/install.sh | bash); fi"
```
![Snipaste_2026-04-16_18-28-50.png|293](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_18-28-50.png)

查看服务状态
```bash
systemctl status elkeid-agent
```
等待上线,可能要久一点
如果没有上线检查刚刚填的是不是自己主机的公网ip
- 检查是否开了防火墙
- 检查service端的安全组的是否阻断了服务
![Snipaste_2026-04-16_18-37-09.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Snipaste_2026-04-16_18-37-09.png)

## 使用

### ELK端口说明

| 组件            | 端口       | 作用                  |
| ------------- | -------- | ------------------- |
| Elasticsearch | **9200** | HTTP API（查询数据）      |
| Elasticsearch | **9300** | 集群通信（一般不用管）         |
| Kibana        | **5601** | Web界面               |
| Logstash      | **5044** | Beats输入（Filebeat常用） |
| Logstash      | **9600** | 监控接口                |
### 资产中心
里面主要是对agent主机的各种资产,基本信息进行展示
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260416195605375.png)

### 主机和容器防护
主要分为
- 对agent的告警事件进行监控和处理
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260416195935370.png)

- 对agent主机进行基本的漏洞扫描及基线扫描
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260416195950837.png)

### 应用运行时防护

Elkeid 的 RASP 插件主要面向应用运行时安全，通过插桩/Hook 等方式感知应用内部调用链、请求上下文和危险函数调用，从而检测或阻断攻击行为。
`RASP` 是一种运行时应用自保护技术，通过在应用内部对关键函数进行 `Hook`，在代码执行阶段检测并阻断攻击行为，相比 WAF 能获取更精细的上下文信息。
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260416200642128.png)
**配置管理页面**
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260416201459633.png)