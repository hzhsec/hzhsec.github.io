---
title: "内网环境搭建之单域搭建"
slug: nei-wang-huan-jing-da-jian-zhi-dan-yu-da-jian
cover: ""
date: 2026-03-17
categories:
  - 环境搭建
tags:
  - 内网域
halo:
  site: http://www.hzhsec.top
  name: 3d2c0401-a0ea-4caf-8241-391b69f95905
  publish: true
---

---
## 一.环境准备

`WindowsServer2022` -----DC(域控)
`Windows10`  ----个人用户


## 二.搭建环境

### 1.网络配置

虚拟机的虚拟网络配置需要记一下
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317171304858.png)

NAT网段在`192.168.41.0~255`

将所有虚拟机改成`NAT`模式
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317171138116.png)

### 2.域控主机配置

**系统**
`WindowsServer2022`

**IP配置**
`192.168.41.11`

`WIN+R`–>`ncpa.cpl`

1. 选择网卡
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317171905700.png)

2. 双击协议配置
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317171928047.png)

3. 配置静态`ip`和`DNS`服务器
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317172127683.png)

**关闭防火墙**

搜索–>”winodows 防火墙”–>” 启用或关闭 Windows 防火墙”–> 专用 & 公用防火墙关闭
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317173413413.png)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317173439324.png)

**安装域控服务**

“服务器管理器”–>” 添加角色和功能”–>” 服务器角色”–> 勾选”Active Directory 域服务”
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317181203874.png)
然后一路下一步,勾选Active Directory 域服务,安装即可

**提升为域控制**

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317182045594.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317182134601.png)

一路下一步点击安装后,等待自动重启完成后并登录

**添加域用户**

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317182944574.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317183127586.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317183230760.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317183315446.png)
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317183534684.png)

### 3.域成员搭建

系统：`Windows10` 专业版

#### 配置ip地址

配置为:`192.168.41.12`

大致和之前一样:`WIN+R`–>`ncpa.cpl`–>”Ethernet0″–>” 属性”–>”Internet 协议版本 4 (TCP/IPv4)”–> 输入对应信息

就是把DNS服务器改成域控ip地址
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317172946982.png)

#### 关闭防火墙 (域成员)

搜索–>” 高级安全Windows防火墙”–>” Windows防火墙属性”

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317172822736.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317184507009.png)

#### PC加入域

`WIN+I`–>” 系统”–>” 关于”–>” 重命名电脑”->” 下一步”


![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317184938619.png)

==注意==:我把名字改成了`hzh-user`,因为不符合要求

选择并输入” 域”–> 输入在域控创建的用户账号 & 密码–> 重启主机–> 选择其它用户
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317185435269.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317185521405.png)

#### 重启

输入账户密码登录
账户：`hzhsec.cc`\\`user1`
或者：`hzh-user`

证明
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260317190249715.png)

至此单域环境搭建完成

注：本文章仅供学习和研究使用，请勿使用项目的技术手段用于非法用途，任何人造成的任何负面影响，与本人无关.

[文章来源：http://www.hzhsec.top](http://www.hzhsec.top)