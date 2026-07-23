---
title: "4.计算机用户提权与降权实战：从服务启动到令牌窃取"
slug: computer-user-privilege-elevation-and-reduction
cover: ""
date: 2026-01-09
categories:
  - 权限提升
tags:
  - 权限维持
  - 令牌窃取
  - MSF
halo:
  site: http://www.hzhsec.top
  name: fc61f296-f016-4e32-8478-1828a6220f54
  publish: true
---

<!--more-->
计算机管理员-->系统管理员(提权)  

系统管理员/计算机管理员-->普通用户(降权)

**应用场景**：

1、常规某个机器被钓鱼后门攻击后，我们需要做更高权限操作或权限维持等。  
2、内网域中某个机器被钓鱼后门攻击后，我们需要对后续内网域做安全测试。  

**主要当前技术入口点**：

- 当前权限由钓鱼攻击获取  

技术应用点：

- 当前受控机在内网域环境  

1、提权system与内网交互  
2、降权到域用户与内网交互  

---
