---
title: "文件与目录安全漏洞分析：下载、删除、遍历与穿越"
slug: file-and-directory-security-vulnerabilities
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - 文件安全
  - top10
tags:
  - Web漏洞
  - 文件下载漏洞
  - 文件删除漏洞
  - 目录遍历
  - 目录穿越
  - 敏感文件
  - 白盒分析
halo:
  site: http://www.hzhsec.top
  name: dfbb198e-e184-4a00-9687-efad5c3460fd
  publish: true
---

<!--more-->



## 文件安全：下载与删除 - 黑白盒分析

### 1. 文件下载 = 读取

常见下载 URL：http://www.xiaodi8.com/upload/123.pdf

可能存在安全 URL：http://www.xiaodi8.com/xx.xx?file=123.pdf

#### 利用：
- 常规下载敏感文件，如数据库配置、中间件配置、系统密钥等文件信息。

### 2. 文件删除（常见于后台）

可能存在安全问题：
- 前台或后台存在删除功能，未严格控制删除权限。

#### 利用：
- 常规删除操作，可能会导致系统重装或敏感文件丢失，进而执行高危操作。

---

## 目录安全：遍历与穿越 - 黑白盒分析

### 1. 目录遍历

通过不当的目录权限控制，攻击者可能获取有价值的信息文件。

### 2. 目录穿越（常见于后台）

通过不当的目录权限控制，攻击者可能控制目录路径，穿越至其他目录并获取敏感文件。

### 黑盒分析：

#### 功能点：
- 文件上传、文件下载、文件删除、文件管理器等功能点。

#### URL 特征：
- 文件名：`download`、`down`、`readfile`、`read`、`del`、`dir`、`path`、`src`、`Lang` 等。
- 参数名：`file`、`path`、`data`、`filepath`、`readfile`、`url`、`realpath` 等。

### 白盒分析：

常见的文件操作函数：
- 上传类函数、删除类函数、下载类函数、目录操作函数、读取查看函数等。

---

## 常见的敏感文件路径

### Windows

- `C:\boot.ini`：查看系统版本。
- `C:\Windows\System32\inetsrv\MetaBase.xml`：IIS 配置文件。
- `C:\Windows\repair\sam`：存储系统初次安装的密码。
- `C:\Program Files\mysql\my.ini`：MySQL 配置。
- `C:\Windows\php.ini`：PHP 配置文件。

### Linux

- `/root/.ssh/authorized_keys`：SSH 登录公钥。
- `/etc/passwd`：用户信息。
- `/etc/shadow`：账户密码文件。
- `/etc/httpd/conf/httpd.conf`：Apache 配置文件。
- `/var/lib/mlocate/mlocate.db`：全文件路径索引。

---

## 绕过思路

1. **URL 编码替代字符：**
   - 使用 `%2F` 替代 `/`。
   - 示例：`?filename=..%2F..%2F..%2F..%2Fetc%2Fpasswd`

2. **二次编码：**
   - 使用 `%252F` 替代 `%2F`。
   - 示例：`?filename=..%252F..%252F..%252F..%252Fetc%2Fpasswd`

3. **加入 `+`：**
   - 示例：`?filename=.+./.+./bin/redacted.dll`

4. **使用 `%00` 截断：**
   - 示例：`?filename=.%00./file.php`
   - 示例：`/etc/passwd%00.jpg`

5. **使用反斜杠（`\`）：**
   - 示例：`?filename=..%5c..%5c/windows/win.ini`

6. **Java 安全模式绕过：**
   - 示例：`?filename=%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/etc/passwd`

---

## 用户目录下的敏感文件

常见敏感文件：
- `.bash_history`：用户历史命令记录。
- `.zsh_history`：Zsh 命令历史。
- `.psql_history`：PostgreSQL 命令历史。
- `.mysql_history`：MySQL 命令历史。
- `.profile`、`.bashrc`：用户配置文件。
- `.gitconfig`、`.viminfo`：版本控制和编辑器配置。

#### 风险：
- 这些文件常含有密码、路径、配置文件路径、日志文件等信息，可能直接暴露敏感数据。

---

## 主机凭证文件

### 私钥文件

- `/root/.ssh/id_rsa`：SSH 私钥。
- `/root/.ssh/authorized_keys`：SSH 公钥存储。
- `/root/.ssh/id_rsa.keystore`：记录访问公钥。

#### 利用：
- 如果私钥没有密码保护，可以直接使用 SSH 登录到服务器。
  - 命令：`ssh -i id_rsa root@IP`

### 系统密码文件

#### `/etc/passwd`

```text
root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/bin:/sbin/nologin
```

- 可查看哪些用户可以登录系统。

#### `/etc/shadow`

```
root:$1$v2wT9rQF$XSpGgoB93STC4EFSlgpjg1:14181:0:99999:7:::
```

- 密码加密信息（`salt`、`密文`）。

------

## 应用配置文件

获取站点配置、数据库配置等文件，进而可能获取到源码或敏感信息。

- **Java 站点：**
  - `/WEB-INF/web.xml`
  - `/WEB-INF/classes/applicationContext.xml`
- **Tomcat：**
  - `/usr/local/tomcat/conf/tomcat-users.xml`
- **Nginx：**
  - `/www/nginx/conf/nginx.conf`
- **Apache：**
  - `/etc/httpd/conf/httpd.conf`
- **Redis：**
  - `/etc/redis.conf`
- **SSH：**
  - `/etc/ssh/sshd_config`

------

## 总结

文件和目录安全是 Web 安全中的重要一环，涉及到文件下载、删除、遍历、穿越等多个方面。通过合适的黑盒和白盒分析方法，结合有效的绕过技巧，可以在渗透测试中识别并修复此类漏洞。对敏感文件和主机凭证的获取，往往能让攻击者进一步控制目标系统，因此要特别重视文件权限和配置的安全性。