---
title: "ReconInspector-一款集 FOFA、Nuclei 与poc模板调试于一体的可视化安全巡检平台"
slug: reconinspector-yi-kuan-ji-fofa-nuclei-yu-pocmo-ban-diao-shi-yu-yi-ti-de-ke-shi-hua-an-quan-xun-jian-ping-tai
cover: ""
date: 2026-04-12
categories:
  - 工具使用
halo:
  site: http://www.hzhsec.top
  name: beb1f3d2-b3a2-4e3b-9402-6f334203d043
  publish: true
---

---
>**免责声明：** 本文内容仅用于安全研究与学习，请在合法授权的环境中使用，严禁用于任何非法用途。因使用不当造成的后果由使用者自行承担，并应遵守相关法律法规。

# **工具介绍**

`ReconInspector`是一款面向日常安全测试场景的可视化工具，围绕“`资产收集 → 漏洞验证 → 模板调试`”这一核心流程进行设计，将常用的多个环节整合到统一界面中，减少工具切换成本，提升整体测试效率。
`资产收集阶段`
平台支持通过配置用户自身的 `FOFA Cookie` 进行数据获取，模拟浏览器访问行为完成资产测绘，`无需依赖官方 API Key`。这种方式在部分场景下更加灵活，能够适配不同账号权限与查询需求，同时降低接入门槛。
`漏洞验证方面`
平台集成 `Nuclei 批量扫描`能力，支持模板选择、目标导入、实时结果展示等功能，实现从资产获取到漏洞检测的一体化流程。
`Nuclei POC 编写`
平台内置漏洞模板工作台，支持根据 HTTP 请求/响应快速生成 Nuclei 模板，并提供正则表达式调试、分组提取与匹配验证等功能。同时结合` AI 辅助能力`，可用于生成模板或优化 extractor 规则，帮助用户在实际测试过程中快速完成 POC 编写与调试，大幅降低模板开发与排错成本。
此外，平台还内置`编码解码`、`哈希计算`、`HTTP 发包`、JSON 处理等常用安全辅助工具，满足日常测试中的零散需求，使用户无需频繁切换外部工具即可完成大部分操作。
整体定位并非大而全的安全平台，而是一个更偏向实用与效率提升的轻量级巡检工具，适合在资产收集、漏洞验证与规则调试等场景中使用。

**工具功能**

#  功能模块介绍

```text
安全巡检平台围绕日常安全测试流程进行设计，主要划分为以下几个核心功能模块：
```

---

##  1. FOFA 资产测绘模块

```text
- 支持完整 FOFA 语法输入与自动编码
- 支持使用用户自身 FOFA Cookie 进行资产抓取，无需依赖 API Key
- 模拟浏览器请求行为，适配不同账号权限与查询场景
- 支持分页获取、结果统计与数据导出
- 支持资产存活探测与基础筛选整理
- 支持一键将结果导入 Nuclei 模块进行后续验证
```

核心亮点：

> **基于 Cookie 的资产获取机制，灵活且更贴近实际使用场景**

---


## 2. 漏洞模板工作台

```text
- 支持根据 HTTP 请求/响应快速生成 Nuclei 模板
- 支持 AI 辅助生成模板或单独生成正则表达式
- 支持正则调试、分组提取与匹配验证
- 支持响应包查看与调试分析
- 支持模板调试过程中的快速验证与优化
```

核心：

> **将“写模板 + 调试 + 验证”整合在同一界面，大幅降低调试成本**

---

## 3. Nuclei 扫描模块

```text
- 图形化配置 nuclei 路径、模板目录与输出目录
- 支持模板树浏览、搜索、批量勾选与编辑
- 支持多目标批量导入与实时扫描
- 支持扫描结果实时输出与分级展示（critical/high/medium/low）
- 支持模板验证场景下的命中结果反馈
```

**核心**：
> **从资产到漏洞验证的一体化流程，无需手动拼接工具**



---

##  4. 常用安全工具模块

```text
- 编码/解码：Base64、URL、Hex、HTML 实体
- 哈希计算：MD5、SHA1、SHA256、SHA512
- HTTP 发包：支持自定义方法、Header、Body、代理与 SSL
- JSON 工具：格式化、压缩与校验
- URL 解析：参数提取与结构分析
- 时间工具：时间戳与日期互转
```
**核心**：
> **减少工具切换，一站式完成日常测试中的零散操作**

---
##  5. 调试与辅助功能
```text
- 优化响应数据展示，避免内容截断或解析异常
- 支持目标格式自动识别（host / host:port / URL）
- 调整调试窗口体验，提升可用性
- 支持配置快速重置（如 AI 接口与参数）
```

---

##  模块设计总结
```text
整体模块设计围绕“资产收集 → 漏洞验证 → 模板调试 → 辅助分析”这一完整流程展开，通过将多个高频使用的功能集中在统一界面中，有效减少工具切换带来的效率损耗，使安全测试流程更加连贯。
```

---
# 工具演示

## 1. 修改配置信息
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412182132818.png)

## 2. fofa资产查询
指定fofa语法,获取网上opencode的资产信息
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412182406830.png)

## 3.漏洞模板构造/测试页面
根据漏洞CVE特征,编写`nuclei`的CVE漏洞模板并且测试
支持`ai制作/修改模板`,`返回包调试`,`正则调试`等等
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412182951929.png)

结果展示
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412195601858.png)

响应包调试
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412195814995.png)

![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412200042035.png)


## 4. 小工具页面
使用发包测试
![image.png](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/20260412194924094.png)

# 工具获取
关注公众号回复:`ReconInspector`

>本文原创发布于微信公众号 hzhsec，更多网安干货、工具、复现教程欢迎关注 hzhsec（搜索 hzhsec 即可）。