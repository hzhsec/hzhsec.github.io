---
title: "AICryptoProxy：AI 赋能逆向Web 加密流量"
slug: aicryptoproxy-ai-fu-neng-ni-xiang-web-jia-mi-liu-liang
cover: ""
date: 2026-05-08
categories:
  - 工具使用
halo:
  site: http://www.hzhsec.top
  name: be81123f-5025-4c6c-ab43-09187a0d5ad9
  publish: true
---

> 当 Burp Suite 里全是 base64 密文，你还在手动抠 JS、断点调试、Python 补环境吗？
> 让 AI 替你完成这一切 —— 从逆向分析到代理部署，5 分钟上线。

---

## 一、前言

想象一下这个画面：
你拿到一个渗透测试目标，打开 Burp Suite 配置好代理，满怀期待地点开第一个请求
```
POST /api/encrypt HTTP/1.1
Content-Type: application/x-www-form-urlencoded

encryptedData=U2FsdGVkX1+7PfewV3eJIzf0M2jL4...
```
你愣住了。所有参数都是密文。
你想修改 userId 越权测试？想重放请求测试重放漏洞？想在 Repeater 里观察响应变化？**全都做不到**，因为你看到的是一堆乱码。
传统解决路径只有一条：**JS 逆向 —— 扣代码 —— 补环境 —— 写代理脚本**。这一套下来，3 到 10 个小时就没了，而且每个加密目标都要重复一遍。
但现在，情况变了。

---

## 二、AICryptoProxy 是什么

> **一句话：AI 自动分析网站加密逻辑，生成加解密代理，让 Burp Suite 里只看到明文。**

项目地址：`https://github.com/hzhsec/AICryptoProxy`

核心思路极其简单：

```
传统模式: 人看混淆代码 → 人断点调试 → 人写 Python 脚本
AI 模式:  AI 操作浏览器 → AI 逆向分析 → AI 生成脚本 → 你只需启动
```

它基于 **Claude Code + MCP (js-reverse)** 的能力，让 AI 可以直接操控浏览器（打开页面、搜索脚本、下断点、读变量），像资深逆向工程师一样完成整套 JS 逆向工作流。

### 两种工作模式

| 模式 | 名称 | 一句话概括 | 适用场景 |
|------|------|-----------|---------|
| **A** | Direct Crypto | AI 逆向算法提取 Key，Python 本地计算 | 标准算法、Key 固定 |
| **B** | JSRPC Bridge | 浏览器原生执行加解密，WebSocket 桥接给代理 | 算法复杂、Key 动态、混淆严重 |

本文以 **模式 A** 为例，用一个真实的加密靶场带你完整走一遍流程。

---

## 三、测试环境

### 3.1 靶场介绍
靶场:[https://github.com/SwagXz/encrypt-labs](https://github.com/SwagXz/encrypt-labs)
这里使用 `encrypt` 靶场的 AES 加密接口：

- **URL**: `http://10.140.136.108:88/encrypt/aes.php`
- **请求格式**: `POST` + `application/x-www-form-urlencoded`
- **加密字段**: `encryptedData`
- **算法**: AES-128-CBC + PKCS7 填充
- **Key/IV**: 固定 16 字节（base64 编码后传输）
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506211114311.png)

正常请求：
```
POST /encrypt/aes.php
Content-Type: application/x-www-form-urlencoded

encryptedData=U2FsdGVkX18...
```

解密后明文（JSON）：
```json
{"username":"admin","password":"433214"}
```

### 3.2 本地环境
- 操作系统：Windows 11
- Python 3.12+
- Burp Suite Professional（监听 8080 端口）
- mitmproxy 10+
- Claude Code(DeepSeek附身)（已配置 js-reverse MCP 服务）
感谢DeepSeek的大力支持,大善人!!!
---

## 四、Step 1：启动 Claude Code 并连上浏览器

在项目根目录启动 Claude Code：

```bash
cd AICryptoProxy
claude
如果不想一直回车可以这样启动:claude --dangerously-skip-permissions
```

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506211316950.png)
首先需要加载`skill`进你的`claude`,直接和`claude`说就可以了:**将本地skills目录的skill加载到你的skill中**

之后就是调用skill技能:
- `mitm_proxy`是使用传统逆向参数的手法,写逆向脚本,进行加解密
- `jsrpc-mitm-auto `是使用jsrpc远程调试技术,直接在浏览器进行调用浏览器自带的加解密函数,进行加解密
Claude Code 启动后,调用指定skill，它会先自动通过 MCP 的 `js-reverse` 服务连接 Chrome 浏览器。你可以看到类似这样的日志输出：

```
[js-reverse] 正在连接 Chrome DevTools...
[js-reverse] 连接成功，调试端口: 9222
```

---

## 五、Step 2：实战:让 AI 自动分析靶场加密逻辑

在 Claude Code 中输入指令。模式 A 对应的 Skill 叫 `mitm_proxy`：

```
用 mitm_proxy 技能帮我分析 http://10.140.136.108:88 的加密逻辑，生成加解密代理
```

接下来就是见证奇迹的时刻 —— AI 会自动执行以下流程：

### Stage 1：观察（Observe）

AI 通过 MCP 连接浏览器，打开目标网页，收集所有 JavaScript 脚本：

```
[AI] 正在连接浏览器...
[AI] 已导航到 http://10.140.136.108:88
[AI] 正在搜索加密关键字...
[AI] 在以下文件中发现可疑加密代码:
  - /encrypt/aes.php (匹配: encrypt, AES)
  - 页面内联脚本 (匹配: CryptoJS)
[AI] 检测到算法: AES-CBC-Pkcs7
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506212000409.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506212042676.png)
对了要手动点击确认,失败登录时,不然会一直卡着
**分析完成:**
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506212503515.png)
选择工作模式,双向代理(浏览器--->mitmproxy解密---->burpsuite---->mitmproxy加密)
**AI 在这一步自动执行了：**
- `new_page("http://10.140.136.108:88")` → 打开靶场
- `search_in_sources("encrypt")` → 全局搜索加密关键字
- `list_scripts` → 列出页面加载的所有 JS
- `detect_crypto(code)` → 调用代码分析识别算法类型
### Stage 2：捕获（Capture）

AI 自动定位到加密函数，通过 hook 追踪调用并提取 Key：

```
[AI] 正在追踪加密函数调用...
[AI] 发现加密函数: CryptoJS.AES.encrypt
[AI] 正在提取加密参数...
[AI] 已提取:
  - 算法: AES-CBC-Pkcs7
  - Key:  "1234567890123456"
  - IV:   "1234567890123456"
  - 输出编码: Base64
```

**AI 在这一步自动执行了：**

- `hook_function("CryptoJS.AES.encrypt")` → 追踪加密调用
- `get_hook_data(hookId)` → 捕获函数的参数和返回值
- `evaluate_script("key")` → 在浏览器中提取 Key 的变量值
- `network_request(action="list")` → 查看真实发出的网络请求格式

### Stage 3：重建（Rebuild）

AI 分析完加密逻辑后，自动在 `10.140.136.108_88` 目录下生成两个完整的 mitmproxy 代理脚本：

**下游解密代理** `downstream_decrypt_proxy.py`（浏览器 -> Burp 方向解密密文）
**上游加密代理** `upstream_encrypt_proxy.py`（Burp -> 服务器方向加密明文）
**加密分析报告**`ANALYSIS_REPORT.md`
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213220684.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213235864.png)
### Stage 4：部署（Patch）

AI 给出完整的启动命令：

```
[AI] 所有脚本已生成至 proxy_scripts/ 目录
[AI] 启动顺序：
  1. Burp Suite → 监听 127.0.0.1:8080
  2. 启动下游解密代理:
     mitmdump -s proxy_scripts/downstream_decrypt_proxy.py ^
              --mode upstream:http://127.0.0.1:8080 -p 8082
  3. 启动上游加密代理:
     mitmdump -s proxy_scripts/upstream_encrypt_proxy.py -p 8083
  4. 浏览器代理 → 127.0.0.1:8082
  5. Burp 上游代理 → 127.0.0.1:8083
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213338041.png)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213352387.png)

---

## 六、Step 3：配置并启动代理链路

根据 AI 给出的启动命令，我们依次启动各个组件。

### 6.1 启动 Burp Suite

Burp Suite 监听在 `127.0.0.1:8080`，作为中间节点接收下游代理转发的明文请求。
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213529351.png)

### 6.2 启动下游解密代理

```bash
 mitmdump -s "10.140.136.108_88/downstream_decrypt_proxy.py" --mode upstream:http://127.0.0.1:8080 -p 8082
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213643264.png)

**注意**：`--mode upstream:http://127.0.0.1:8080` 这个参数**不能少**，它告诉下游代理解密后把流量转发到 Burp 的 8080 端口。

### 6.3 启动上游加密代理

```bash
mitmdump -s 10.140.136.108_88/upstream_encrypt_proxy.py -p 8083
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213721870.png)

### 6.4 配置浏览器代理

使用浏览器代理插件（如 SwitchyOmega 或 Proxy SwitchySharp），将流量指向下游代理：
- **代理地址**: `127.0.0.1`
- **端口**: `8082`
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213801232.png)
### 6.5 配置 Burp 上游代理

在 Burp Suite 中设置上游代理（Upstream Proxy）：

```
Burp → Settings → Network → Connections → Upstream Proxy Servers
  Destination Host: *
  Proxy Host: 127.0.0.1
  Proxy Port: 8083
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506213927571.png)

---

## 七、Step 4：验证 —— 见证奇迹的时刻

### 7.1 在靶场页面提交数据

回到浏览器，在靶场表单中输入 username 和 password，点击提交。

> 图片: 靶场页面输入数据的截图

### 7.2 查看 Burp Proxy —— 全是明文！

回到 Burp Suite，在 Proxy -> HTTP History 中找到刚才的请求：

```
POST /encrypt/aes.php HTTP/1.1
Content-Type: application/json
Host: 10.140.136.108:88

{"username":"admin","password":"123456"}
```

**没有乱码，没有 base64，只有清晰可见的明文 JSON！**

> 图片: Burp Suite 中显示明文请求的截图 —— 这是最激动人心的一步

### 7.3 查看终端日志

在下游代理的终端窗口中，你可以看到解密日志：

```
[下游解密] http://10.140.136.108:88/encrypt/aes.php
    [请求解密] username: admin
    [请求解密] password: 123456
```
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506214137695.png)

在上游代理的终端中，你会看到加密日志：
```
[上游加密] http://10.140.136.108:88/encrypt/aes.php
    [加密] {"username":"admin","password":"123456"} -> encryptedData=U2FsdGVkX1...
```
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506214214036.png)


**Burpsuite**:
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506214016679.png)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506214103133.png)

### 7.4 在 Repeater 中修改重放

现在你可以像对待普通接口一样，在 Repeater 中修改 JSON 参数并发送：
测试爆破模块,进行爆破:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260506214528641.png)
Burp 发送的是明文 JSON，上游代理会自动加密后发给服务器。**你完全感受不到加密的存在。**

---

## 八、整个链路的完整流程

```
浏览器 (用户输入表单)
    │ POST /encrypt/aes.php
    │ encryptedData=U2FsdGVkX1...  (浏览器原生加密)
    ▼
┌──────────────────────────────────────────────────┐
│ 下游解密代理 (mitmdump :8082)                      │
│  1. 收到密文请求                                   │
│  2. AES-CBC 解密 encryptedData                     │
│  3. 替换请求体为 JSON 明文                          │
│  4. 转发给 Burp                                   │
│  --mode upstream:http://127.0.0.1:8080            │
└─────────────────┬────────────────────────────────┘
                  │ {"username":"admin","password":"123456"}
                  ▼
┌──────────────────────────────────────────────────┐
│  Burp Suite (:8080)  ← 在这里操作明文！             │
│  - 修改参数测试越权                                 │
│  - Repeater 重放测试                                │
│  - Scanner 扫描明文接口                             │
└─────────────────┬────────────────────────────────┘
                  │ {"username":"admin","password":"123456"}
                  ▼
┌──────────────────────────────────────────────────┐
│ 上游加密代理 (mitmdump :8083)                      │
│  1. 收到 Burp 的明文 JSON                          │
│  2. AES-CBC 加密为 base64                          │
│  3. 包装为 form-urlencoded 格式                     │
│  4. 转发给目标服务器                               │
└─────────────────┬────────────────────────────────┘
                  │ encryptedData=U2FsdGVkX1...
                  ▼
           目标服务器 (接收到的还是密文)
```

**关键要点**：
- **Burp 只看到明文** —— 可以自由修改、重放、扫描
- **浏览器与服务器间始终是密文** —— 不会触发前端校验
- **下游代理必须用 `--mode upstream`** —— 否则流量不会经过 Burp，你就会看到密文

---

## 九、常见问题

### Q1：Burp 里看到的还是密文？

**原因**：下游代理没有正确转发流量给 Burp。

**检查**：启动下游代理时是否加了 `--mode upstream:http://127.0.0.1:8080` 参数？

```
正确: mitmdump -s downstream_decrypt_proxy.py --mode upstream:http://127.0.0.1:8080 -p 8082
错误: mitmdump -s downstream_decrypt_proxy.py -p 8082
```

### Q2：上游代理报解密失败？

**检查点**：
1. 浏览器是否已经信任了 mitmproxy 的 CA 证书？
2. 靶场的 Key/IV 是否和脚本中一致？
3. 浏览器代理是否配置为 8082 端口？

### Q3：AI 提取的 Key 不对怎么办？

在指令中提供更多上下文，例如：

```
"加密函数在页面的内联脚本中，Key 是固定字符串 '1234567890123456'"
```

---

## 十、总结

### 10.1 我们做到了什么？

在不到 **5 分钟** 的时间里，我们完成了：

1. AI 自动逆向靶场的 AES-CBC 加密逻辑
2. AI 自动提取 Key 和 IV
3. AI 自动生成两个完整的 mitmproxy 代理脚本
4. 配置浏览器和 Burp 的代理链路
5. **在 Burp Suite 中直接操作明文请求**

### 10.2 核心优势

| 维度 | 传统手动逆向 | AICryptoProxy |
|------|------------|---------------|
| 平均耗时 | 3 - 10 小时 | 5 - 15 分钟 |
| 经验要求 | 精通 JS 混淆和逆向 | 零门槛 |
| 动态 Key | 需要额外分析 | 模式 B 自动适配 |
| 重复劳动 | 每个目标重来一遍 | AI 自动完成 |

### 10.3 什么时候用模式 B？

如果你的目标满足以下任一条件，建议使用模式 B（JSRPC Bridge）：

- 加密 Key 是动态生成的，每次请求都不一样
- 算法是自定义的，无法用标准库解密
- 代码混淆严重，AI 也难提取关键参数
- 你只是想快速开始测试，不想花时间等 AI 分析

模式 B 的思路更"暴力"：**完全不逆向算法**，直接把加解密逻辑留在浏览器里执行，通过 WebSocket 桥接给 mitmproxy 调用。

### 10.4 最后的建议

AI 工具再强大，也只是辅助。理解原理、能排查问题，才是你自己的能力。建议你在 AI 生成的脚本基础上，试着读懂 AES-CBC 加解密的代码逻辑，这样遇到异常时才能快速定位问题。

毕竟，**AI 替你干活，但你不能变成只会发指令的人。**

---

## 参考资源

- [AICryptoProxy](https://github.com/hzhsec/AICryptoProxy) — 完整项目代码
- [JsRpc](https://github.com/jxhczhl/JsRpc) — JSRPC 远程调用浏览器方法
- [mitmproxy 官方文档](https://docs.mitmproxy.org/) — mitmproxy 脚本开发指南
- [Claude Code](https://claude.ai/code) — AI 编程助手
- [Burp Suite](https://portswigger.net/burp) — Web 安全测试工具
**参考文章**
[1] 前端自动化加解密: mitmproxy+burpsuit联动 [https://mp.weixin.qq.com/s/3xXpkObDQ3x7UB_yGCk6cw](https://mp.weixin.qq.com/s/3xXpkObDQ3x7UB_yGCk6cw)
[2] Web Crypto Proxy Skill 全自动网站加密逻辑分析与双向透明加解密代理工具 [https://mp.weixin.qq.com/s/wxgVCYm8yqEuN8JXqQsBqQ](https://mp.weixin.qq.com/s/wxgVCYm8yqEuN8JXqQsBqQ)