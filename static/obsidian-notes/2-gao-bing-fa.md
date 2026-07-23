---
title: "(2)高并发"
slug: 2-gao-bing-fa
cover: ""
date: 2026-02-12
categories:
  - 业务逻辑漏洞
tags:
  - 逻辑漏洞
halo:
  site: http://www.hzhsec.top
  name: 9694b694-c90f-4375-a655-d6d8b6f99668
  publish: true
---

---
> 就是客户端在同一时间对服务端的接口进行多次请求,容易造成服务端还没有来得及校验就通过了

**单场景并发**
>顾名思义,就是对一个接口进行的并发,一个功能点的测试,例如点赞,优惠卷的使用等等

**测试案例**:
burpsuit靶场
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260120164440060.png)

**目的**:
使用50美元买一件1377美元的夹克

**思路**:
在使用优惠卷时,使用并发,从而造成多个优惠卷使用成功

**并发步骤**:
将夹克加入购物车,选择优惠口令
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260120165115503.png)



并发有两种方法
1. 使用burpsuit拦截多个使用优惠卷的数据包
拦截了25个
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260120165354070.png)
直接放行:
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260120165433669.png)

2. 在repteater模块,先创建一个group,再使用Ctrl+r复制数据包,修改发送模式为send group (parallel)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260120170155798.png)
发送


两种方法区别:
第一种方法是手动点击生成的数据包,可以有效的对付服务端的token校验
第二种呢,就是同一个数据包的多次发送,容易被防重放拦截