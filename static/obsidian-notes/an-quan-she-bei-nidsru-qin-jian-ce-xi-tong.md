---
title: "安全设备-NIDS入侵检测系统"
slug: an-quan-she-bei-nidsru-qin-jian-ce-xi-tong
cover: ""
date: 2026-04-09
categories:
  - 应急响应
tags:
  - 安全设备
halo:
  site: http://www.hzhsec.top
  name: 6d6ad29c-d866-460e-9844-7267779b53e4
  publish: true
---

---
# IDS-入侵检测系统
- 基于主机的入侵检测系统（HIDS）
- 基于网络的入侵检测系统（NIDS)
接下来简单讲解两款老牌的NIDS的使用和安装

# Snort
>一个开源的网络入侵检测系统（IDS）和入侵防御系统（IPS），它可以捕获通讯流量并对其做协议解析，识别或防御通讯流量中可疑或恶意的行为。国内大部分厂商基于流量的IDS的数据包捕获、协议解析、检测引擎等关键模块都是在此基础上做修改和扩展优化。

官网：https://www.snort.org/
## 安装
参考:https://mp.weixin.qq.com/s/haxqngjZBcrYs2QsQN7aqg
以`Ubuntu 22.04`为例子
### 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```
### 安装依赖
Snort 3 依赖比较多，这一步很关键：
```bash
sudo apt install -y build-essential cmake git libpcap-dev \  
libpcre3-dev libdumbnet-dev bison flex zlib1g-dev \  
liblzma-dev openssl libssl-dev pkg-config \  
libhwloc-dev luajit libluajit-5.1-dev \  
libunwind-dev libmnl-dev ethtool
```
### 安装 DAQ（数据采集库）

```bash
cd /usr/src  
sudo git clone https://github.com/snort3/libdaq.git  
cd libdaq  
sudo ./bootstrap  
sudo ./configure  
sudo make -j$(nproc)  
sudo make install
```
更新库路径：
```bash
sudo ldconfig
```
###  安装 Snort 3
```bash
cd /usr/src  
sudo git clone https://github.com/snort3/snort3.git  
cd snort3  
sudo ./configure_cmake.sh --prefix=/usr/local/snort  
cd build  
sudo make -j$(nproc)  
sudo make install
```
可能会缺失依赖
```bash
sudo apt install -y libpcre2-dev
```
### 配置环境变量
```bash
echo 'export PATH=$PATH:/usr/local/snort/bin' >> ~/.bashrc  
source ~/.bashrc
```
### 验证安装
```bash
snort -V
```
看到类似：
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409162524144.png)
说明成功 

## 测试使用：
配置文件，规则写法，使用参数
https://www.cnblogs.com/yuersan/p/15236326.html
https://blog.csdn.net/hexf9632/article/details/94715434
https://blog.csdn.net/qq_43968080/article/details/103378952
https://blog.csdn.net/weixin_42376192/article/details/155629548
**自写规则**：
snort3规则基本框架
```
动作 协议 源地址 源端口 方向 目标地址 目标端口 (规则选项)

比如TCP:
alert tcp any any -> any 80 (msg:"test"; content:"abc"; sid:1000001; rev:1;)
sid是唯一标识
```
1、ICMP协议流量警告测试
先修改`/usr/local/snort/etc/snort/snort.lua`的alert_fast取消注释改成
```
alert_fast = {
    file = true
}
```
获取到的信息会存到`执行命令`的目录,名字是`alert_fast.txt `

创建规则库文件夹`rules`
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409164807356.png)
将icmp规则`/usr/local/snort/etc/rules# cat icmp_check.rule `放入`icmp_check.rule`
```
snort -c /usr/local/snort/etc/snort/snort.lua -R /usr/local/snort/etc/rules/icmp_check.rule -i eth0
-c 加载配置文件
-R选择特定的规则文件
-i 选择监听网卡
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409165905554.png)
尝试使用另一台主机进行`ping`命令测试是否有用
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409170017570.png)
同级目录生成了文件:`alert_fast.txt`
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409170121180.png)

### 3.编写Snort规则

Snort规则由两部分组成：
`规则头（Rule Header）`和`规则选项（Rule Options）`。

- 规则头:定义流量匹配的基本信息，如协议、源和目的地址、端口等。  
- 规则选项:包含更详细的检测条件和告警信息。

#### 1. 规则头

规则头的基本格式如下：

```
动作 协议 源地址 源端口 方向 目标地址 目标端口 (规则选项)
<action> <protocol/service> <src_ip> <src_port> -> <dst_ip> <dst_port>
```
其中，各字段含义如下：

● `action`：规则动作，如alert、log、pass等。  
● `protocol/service`：协议或服务类型，如tcp、udp、icmp、http、dns等。  
● `src_ip`：源IP地址，可为IP、CIDR或any。  
● `src_port`：源端口，可为具体端口或any。  
● `dst_ip`：目的IP地址。  
● `dst_port`：目的端口。

示例规则头：
```snort
alert http any any -> 192.168.1.0/24 any
```
表示检测所有进入该网段的HTTP流量。

#### 2. 规则选项
规则选项位于规则头之后，由键值对组成，以分号分隔：
```
(key:value; ...)
```
常见选项包括：
- msg：告警信息  
- sid：规则ID（必须唯一）  
- rev：规则版本  
-  content：内容匹配  
- depth：匹配深度  
- offset：起始偏移  
- nocase：忽略大小写  
- classtype：分类类型
因为在 Snort 3 里，`nocase`、`fast_pattern`、`depth`、`offset`、`distance`、`within` 这些都属于 **content modifier**，是跟在某个 `content` 后面的,用逗号分隔
示例规则选项：
```snort
(msg:"Potential SQL Injection"; sid:1000001; rev:1; http_uri; content:"' or '1'='1",nocase;)
```
完整示例规则：
```snort
alert http any any -> any any (msg:"Potential SQL Injection"; sid:1000001; rev:1; http_uri; content:"' or '1'='1", nocase;)
```

#### 3. 规则编写技巧与方法

编写Snort规则需要掌握一些基本技巧和方法，以下是几个关键点：
1. 使用适当的动作根据网络环境和安全需求选择合适的动作，如：  
    ● alert：适用于需要生成告警事件的场景（Snort 3主要使用该动作）。  
    ● log：用于记录流量事件（较少单独使用，通常由输出模块控制）。  
    ● pass：用于放行流量并跳过检测（需谨慎使用，避免绕过检测链）。
    
2. 精确匹配协议和服务  
    Snort 3支持基于服务的规则（如http、dns等），建议优先使用服务类型而非仅依赖端口。  
    例如，对于HTTP流量，应优先使用`http`协议，而不是简单写`tcp 80`。

3. 合理使用内容匹配（Sticky Buffer机制）  
    内容匹配是Snort规则的重要部分，在Snort 3中需要结合缓冲区使用，例如：
```snort
http_uri;
content:"/admin";
```
表示在HTTP URI中匹配内容。
常见缓冲区包括：  
● http_uri  
● http_header  
● http_method  
● http_client_body
需要注意：匹配应尽量精确，避免模糊匹配，以减少误报。

4. 定义唯一的规则ID  
    每条规则必须有唯一的sid，以便于规则管理和事件关联。  
    推荐使用大于1000000的ID，以避免与官方规则冲突。

5. 分类和优先级设置  
    使用classtype和priority对规则进行分类和优先级标记，有助于告警分析。
例如：  
`classtype:attempted-recon; priority:2;`
6. 输出由Lua配置控制  
    Snort 3中不再主要依赖命令行参数控制输出，而是在snort.lua中配置，例如：
```lua
alert_fast = {
    file = true
}
```
表示启用fast格式告警并输出到文件。

#### 4. 完整示例（Snort 3）

1. nc反弹shell的特定端口告警:
==**注意有坑!**==
网卡通常开启了 **checksum offload（校验和卸载）**
导致snort抓到数据包,但是不会匹配而丢弃,需要关闭
```bash
ethtool -K eth0 rx off tx off
ethtool -K eth0 tso off gso off gro off lro off
```
攻击机:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409174739380.png)

受害机:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409174713416.png)

检测规则:
```rule
alert tcp any any -> any 7799 (msg:"检测到连接7799端口数据包"; gid:1;sid:10000002;rev:1;)
```
检测和查看命令:
```bash
snort -c /usr/local/snort/etc/snort/snort.lua -R /usr/local/snort/etc/rules/tcp_check.rule -i eth0
cat alert_fast.txt 
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409174919870.png)

2. SQL注入攻击警告：
```snort
alert http any any -> any any (msg:"Possible SQL Injection"; http_uri; content:"' OR 1=1 --",nocase; sid:10000003; rev:1;)
```
这个就简单起一个python的web页面,`python -m http.server 9999`
本机使用`hackbar`发送特征数据包就行
本机发包:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409180400985.png)
主机有数据了:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409180506448.png)
`snort`也是检测监听到sql注入
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409180548787.png)

3. 永恒之蓝特征警告

```snort
alert tcp any any -> $HOME_NET any (msg:"ET EXPLOIT Possible ETERNALBLUE MS17-010"; flow:to_server,established; content:"|00 00 00 31 ff|SMB",depth:16; fast_pattern; content:"|4a 6c 4a 6d 49 68 43 6c 42 73 72 00|", distance:0; classtype:trojan-activity; sid:2024220; rev:1;)
```
（说明：Snort 3中对SMB支持依赖检测模块，通常仍使用tcp规则匹配特征）
snort官方库:https://www.snort.org/
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409181213322.png)
[规则库](https://www.snort.org/downloads#rules)

后续可以分析各种工具特征流量,编自己的`snort规则库`
将以下工具特征进行规则编写与检测：
- `sqlmap`（SQL注入工具）  
```
数据包头默认带有sqlmap字段
数据包带有sql语句
```
- `冰蝎`（Behinder）  
```
请求头常见:Accept: application/json, text/javascript, */*; q=0.01
UA头设置了10种随机选择
冰蝎与webshell建立连接的同时，javaw也与目的主机建立tcp连接，每次连接使用本地端口在49700左右，每连接一次，每建立一次新的连接，端口就依次增加。
连接密码:默认时，所有冰蝎4.0 webshell都有“e45e329feb5d925b” 一串密钥。该密钥为连接密码32位md5值的前16位，默认连接密码rebeyond
```
- `哥斯拉`（Godzilla）  
```
UA头固定几个
content_type固定有application/octet-stream
内容通常是AES\BASE64,哥斯拉会把一个32位的md5字符串按照一半拆分，分别放在base64编码的数据的前后两部分。整个响应包的结构体征为：md5前十六位+base64+md5后十六位。
参数会出现pass=,password=,pwd=
```
- C2工具（如CS Beacon）  
- FRP（内网穿透工具）
重点关注：
- HTTP特征（URI / Header / Body）
- User-Agent异常
- Base64 / 加密流量特征
- 心跳流量模式（Beacon）


# Suricata
>一个开源的网络入侵检测系统（IDS）和入侵防御系统（IPS），它可以捕获通讯流量并对其做协议解析，识别或防御通讯流量中可疑或恶意的行为。

项目：https://github.com/OISF/suricata
参考：https://suricata.readthedocs.io/
## 安装
https://docs.suricata.io/en/latest/install.html
```bash
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt-get update
sudo apt-get install suricata
```
配置：https://docs.suricata.io/en/latest/quickstart.html
```bash
ip addr
sudo vim /etc/suricata/suricata.yaml
```
**查看**
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409184322622.png)
**修改**
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409184235547.png)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409184417607.png)

## 默认目录结构:
```
/etc/suricata/        # 主配置目录
/etc/suricata/suricata.yaml   # 主配置文件
/var/log/suricata/   # 日志目录
/usr/share/suricata/rules/    # 默认规则目录
```

日志解析：
`suricata.log` ，包含 Suricata 运行时的日志信息，如启动、关闭、规则加载等，用于故障排除和监视。
`stats.log`，包含 Suricata 的统计信息，如流量统计、规则匹配统计等，，用于性能调优和网络活动分析。
`fast.log`，就是告警输出日志了，通常看这个就可以。
`eve.json`，详细的事件记录，以 JSON 格式呈现，包括有关规则匹配事件的详细信息，包括协议解析、源和目标地址、端口、负载数据等，用于深入分

## 规则下载

#### **开源规则**
Suricata规则下载：
http://47.108.150.136:8080/IDS
https://github.com/al0ne/suricata-rules
https://github.com/ptresearch/AttackDetection
https://mp.weixin.qq.com/s/VjWPSVzP0whafH-oCmmvLA
#### 官方系统规则更新
`suricata-update`
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409191757673.png)

## 自写规则

自写规则,与`snort`类似,但是和`snort3`有些不同
几乎可以`通用`:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409193645335.png)

参考案例：https://mp.weixin.qq.com/s/iaztHJYAtQSCDUS0_5fgtQ
1、`SQLMAP`工具特征：
```
suricata -c /etc/suricata/suricata.yaml -i eth0 -s /etc/suricata/rules/sqlmap.rules

规则写法
alert http any any -> any any (msg:"SQLMAP攻击!"; content:"sqlmap"; http_user_agent; nocase; sid:1000001; rev:1;)
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409192847960.png)
2、C2工具特征:
`sslblacklist.rules`
```
指纹能够识别
alert tls any any -> any any (msg:"SSLBL: Malicious SSL certificate detected (CobaltStrike C&C)"; tls.fingerprint:"6e:ce:5e:ce:41:92:68:3d:2d:84:e2:5b:0b:a7:e0:4f:9c:b7:eb:7c"; reference:url, sslbl.abuse.ch/ssl-certificates/sha1/6ece5ece4192683d2d84e25b0ba7e04f9cb7eb7c/; sid:902202003; rev:1;)
```
3.`哥斯拉webshell`管理工具特征
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409210532253.png)
`gesila.rule`
```
alert http any any -> any any (msg:"哥斯拉攻击!";flow:to_server,established;content:"Gecko";http_user_agent;nocase;content:"Content-Type|3A| application/octet-stream";http_header;nocase;sid:20260409;rev:1;)
匹配头部两个特征
```
`flow:to_server,established;`
含义是：
**只匹配：已经建立连接，并且从客户端发往服务器的流量**
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260409212234470.png)

# 集成系统：securityonion
集成snort/suricata、bro(zeek)、elk、ossec等
https://securityonionsolutions.com/software