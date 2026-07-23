---
title: "cloud1"
slug: cloud1
cover: ""
date: 2026-01-09
halo:
  site: http://www.hzhsec.top
  name: e6aefc55-c746-4763-9bf3-c694cc3a999f
  publish: true
---

<!--more-->

## 任意上传 & 域名接管 & AccessKey 泄漏

### 概述（对象存储风险点）

- 云服务 — 对象存储 — 权限配置不当

- 云服务 — 对象存储 — 域名解析接管

- 云服务 — 对象存储 — AccessKey 泄漏
---
### 云服务简介
云服务即在云厂商上购买的在线产品服务。
```
国内：阿里云、腾讯云、华为云、天翼云、Ucloud、金山云  
国外：亚马逊 AWS、Google GCP、微软 Azure、IBM 云等。
```
示例（以 AWS 为例）：
```
S3 —— 对象存储（类似网盘）
EC2 —— 弹性计算服务（云上虚拟机）
RDS —— 云数据库（托管关系型数据库）
IAM —— 身份与访问管理（子账号权限管理）
```
---
### 对象存储各厂商命名
```
阿里云：OSS     腾讯云：COS     华为云：OBS  
谷歌云：GCS     微软云：Blob    亚马逊云：S3
```
---
### 对象存储常见问题
1. 权限配置错误
```
- 公共读或公共读写：可访问但不显示完整结构
- 授权策略错误：设置 ListObject 后可列出文件结构
- 公共读写：可直接 PUT 文件，实现任意上传
```

2. 域名解析 Bucket 接管
```
存储桶绑定域名后，若桶被删除而域名解析仍存在，可尝试接管。
```

- 返回 NoSuchBucket 说明可能能接管；返回 AccessDenied 则通常不可接管。

- 新建存储桶时需使用相同厂商与相同地域，否则无法接管成功。

3. AccessKeyId / SecretAccessKey 泄漏
- 泄漏来源：APP、小程序、JS、源码仓库、提交历史等
- 排查方式：搜索 AccessKey 特征或关键字


参考文档：https://wiki.teamssix.com/CloudService/more/

---
## 弹性计算 — 元数据、SSRF、AK（及云数据库外部连接与权限提升）

### 元数据说明
```
实例元数据（metadata）是云服务器实例在云厂商系统中的描述信息，
包括实例 ID、IP、MAC、操作系统类型等，用于配置和管理实例。
```

各大云元数据访问地址：
```
阿里云：http://100.100.100.200/
腾讯云：http://metadata.tencentyun.com/
华为云：http://169.254.169.254/
亚马逊云：http://169.254.169.254/
微软云：http://169.254.169.254/
谷歌云：http://metadata.google.internal/
```

阿里云文档参考：https://help.aliyun.com/zh/ecs/user-guide/manage-instance-metadata

---
云服务 — 弹性计算 — 元数据 & SSRF & AK
#### 1. 前提条件
```
- 弹性计算已配置访问控制角色
- 存在 SSRF 漏洞，或已取得云服务器权限（WebShell/RCE 可请求元数据地址）
```
#### 2. 利用场景一：已取得服务器权限后横向移动
```
curl http://100.100.100.200/latest/meta-data/
curl http://100.100.100.200/latest/meta-data/ram/security-credentials/
```

获取临时凭证：
```
curl http://100.100.100.200/latest/meta-data/ram/security-credentials/ecs
```

使用获取的临时 AK 进行横向移动或资源访问。
参考框架：CF 云渗透框架（https://wiki.teamssix.com/CF/
）

#### 3. 利用场景二：Web 资产存在 SSRF 漏洞

同样可通过 SSRF 请求上述元数据接口以获取临时凭证。
凭证一旦泄露，可用于进一步横向渗透或接管云资源。


云服务 — 云数据库（外部连接 & 权限提升）
常见获取方式
```
1. 账号密码：
   - 多出现在源码配置文件中
   - 或通过暴力破解获取

2. 连接方式：
   - 白名单开放或外网可连：可直接用 Navicat 等连接
   - 内网：需通过内网服务器转发或代理连接
```
### AK 利用（权限提升）

利用泄露或获取的 AK 访问云控制台或 API 接口，实现权限提升或控制其他资源。
参考：https://wiki.teamssix.com/CF/

总结

- **对象存储风险**：权限配置不当、域名接管、AccessKey 泄漏

- **弹性计算风险**：SSRF 或主机权限可导致元数据泄漏

- **云数据库风险**：凭据泄露与配置不当可导致外部连接与权限提升