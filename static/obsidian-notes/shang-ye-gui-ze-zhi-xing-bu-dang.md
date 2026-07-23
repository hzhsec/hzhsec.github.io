---
title: "商业规则执行不当"
slug: shang-ye-gui-ze-zhi-xing-bu-dang
cover: ""
date: 2026-02-12
categories:
  - burpsuite靶场
tags:
  - 靶场复现
halo:
  site: http://www.hzhsec.top
  name: 243c019a-ce0a-43e9-9703-c718c7b6accb
  publish: true
---

---

# 靶场地址
[实验室：商业规则执行有缺陷 |网络安全学院](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-flawed-enforcement-of-business-rules)

启动靶场并进入
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212162041728.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212163210013.png)

实验目的是通过漏洞使用100美元购买1337美元的夹克

观察到优惠码
`NEWCUST5`
通过该优惠码可以减5美元
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212163653754.png)
但是不能重复添加
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212163955747.png)

首页最下面发现订阅框
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212164049944.png)


订阅可以获得另一个优惠码:`SIGNUP30`
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212164141886.png)

因为重复一个无法使用,那我们就交替重复
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260212165929018.png)
成功将价格变成0了

**像这种优惠卷的还可以使用高并发试试,看看可不可以重复使用优惠卷**