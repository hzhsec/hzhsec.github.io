---
title: "跨域安全与 UI 补偿攻击：JSONP 数据劫持与点击劫持深度解析"
slug: jsonp-data-leakage-and-clickjacking-defense
cover: ""
date: 2026-01-09
categories:
  - top10
  - XSS
tags:
  - 点击劫持
  - 前端安全
halo:
  site: http://www.hzhsec.top
  name: f690bb32-1ca2-43a3-9836-52662e1ba8b4
  publish: true
---

JSONP（JSON with Padding）是一种用于解决跨域数据请求的变通方案，核心原理是**利用 `<script>` 标签的跨域特性绕过同源策略**。通过将返回内容包裹在回调函数中，使得数据以 JavaScript 的形式被执行。



<!--more-->

# JSONP 点击劫持漏洞

JSONP（JSON with Padding）是一种用于解决跨域数据请求的变通方案，核心原理是**利用 `<script>` 标签的跨域特性绕过同源策略**。通过将返回内容包裹在回调函数中，使得数据以 JavaScript 的形式被执行。

早期前后端分离尚不成熟时，这类接口设计比较常见，若后端在返回时直接把敏感数据通过回调函数输出并信任 `callback` 参数，就可能被攻击者利用来窃取登录用户的数据。

---