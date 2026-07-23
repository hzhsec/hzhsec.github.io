---
title: "2.Windows 进阶提权：人工补丁筛选与土豆家族（Potato）全解析"
slug: windows-privilege-escalation-manual-potato
cover: ""
date: 2026-01-09
categories:
  - 权限提升
tags:
  - Windows提权
  - 土豆家族
  - 补丁筛选
  - 漏洞利用
halo:
  site: http://www.hzhsec.top
  name: 664fb40f-3406-4a2a-b718-4475550a0e00
  publish: true
---

<!--more-->
# 简介

Web 到 Windows 系统提权的两类典型方法：

1. **人工操作提权**：适用于在线工具或 EXP 不稳定、插件无法实时更新的环境。
2. **土豆家族提权**（Potato Exploit Family）：用于将低权限的服务用户提升为 `NT AUTHORITY\SYSTEM` 特权。

---

# 系统提权-人工操作

在某些场景下，如果无法直接执行命令，可以尝试上传 `cmd.exe` 到可读写目录再调用。

**优点**：

- 解决工具或 EXP 无法实时更新的问题

**缺点**：

- 操作繁琐，需要多次复现和调试

人工操作适合工具无法更新或集成较少的复杂场景。

## 1. 信息收集

可参考常用命令进行系统信息收集和环境分析。

示例命令（Windows）：

```powershell
systeminfo
whoami /all
net user
net localgroup
```

## 2. 补丁筛选

可使用自动化工具筛选系统补丁信息，以便定位潜在提权漏洞：

* [Hacking8 系统提权补丁筛选](https://i.hacking8.com/tiquan)
* [WES-NG](https://github.com/bitsadmin/wesng)

示例使用：

```bash
python wes.py systeminfo.txt --color
python wes.py systeminfo.txt --color -i "Elevation of Privilege"
```

## 3. EXP 获取与执行

可通过多种渠道获取漏洞利用代码：

```text
KernelHub         # 针对常用溢出编号查找 EXP
Poc-in-Github     # 按年份和编号查找 EXP
exploitdb         # 按类型和关键字查找 EXP
```

* [KernelHub](https://github.com/Ascotbe/Kernelhub)
* [PoC-in-GitHub](https://github.com/nomi-sec/PoC-in-GitHub)
* [ExploitDB 数据库](https://gitlab.com/exploit-database/exploitdb)

---

# 系统提权-土豆家族（Potato Exploit Family）

土豆家族提权通常用于已获得 Web 或数据库权限的情况下，将低权限服务用户提升至 `NT AUTHORITY\SYSTEM`。

参考资料：[土豆家族总结](https://mp.weixin.qq.com/s/OW4ybuqtErh_ovkTWLSr8w)

## 测试系统

* Windows 10/11（1809 / 21H2）
* Windows Server 2019 Datacenter（1809）
* Windows Server 2022 Datacenter（21H2）

## 测试结果

| 工具              | 测试结果 |
| ----------------- | -------- |
| SweetPotato       | OK       |
| RoguePotato       | -        |
| BadPotato         | OK       |
| EfsPotato         | OK       |
| GodPotato         | OK       |
| PetitPotato       | OK       |
| MultiPotato       | -        |
| CandyPotato       | -        |
| RasmanPotato      | OK       |
| CoercedPotato     | -        |
| JuicyPotatoNG     | -        |
| PrintNotifyPotato | OK       |

## 土豆家族工具地址

* **GodPotato**: [https://github.com/BeichenDream/GodPotato](https://github.com/BeichenDream/GodPotato)
* **SweetPotato**: [https://github.com/CCob/SweetPotato](https://github.com/CCob/SweetPotato)
* **RoguePotato**: [https://github.com/antonioCoco/RoguePotato](https://github.com/antonioCoco/RoguePotato)
* **BadPotato**: [https://github.com/BeichenDream/BadPotato](https://github.com/BeichenDream/BadPotato)
* **EfsPotato**: [https://github.com/zcgonvh/EfsPotato](https://github.com/zcgonvh/EfsPotato)
* **MultiPotato**: [https://github.com/S3cur3Th1sSh1t/MultiPotato](https://github.com/S3cur3Th1sSh1t/MultiPotato)
* **CandyPotato**: [https://github.com/klezVirus/CandyPotato](https://github.com/klezVirus/CandyPotato)
* **RasmanPotato**: [https://github.com/crisprss/RasmanPotato](https://github.com/crisprss/RasmanPotato)
* **PetitPotato**: [https://github.com/wh0amitz/PetitPotato](https://github.com/wh0amitz/PetitPotato)
* **JuicyPotatoNG**: [https://github.com/antonioCoco/JuicyPotatoNG](https://github.com/antonioCoco/JuicyPotatoNG)
* **PrintNotifyPotato**: [https://github.com/BeichenDream/PrintNotifyPotato](https://github.com/BeichenDream/PrintNotifyPotato)
* **CoercedPotato**: [https://github.com/Prepouce/CoercedPotato](https://github.com/Prepouce/CoercedPotato)

---

# 总结

1. **人工操作提权**适合复杂环境或工具/EXP不稳定场景，可手动完成提权，但操作繁琐。
2. **土豆家族提权**是低权限到系统权限提升的经典方法，适用于 Web、数据库权限已经获取的环境。