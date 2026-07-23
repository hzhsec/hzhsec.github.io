---
title: "云服务器 Git 推送 问题与解决"
slug: yun-fu-wu-qi-git-tui-song-wen-ti-yu-jie-jue
cover: ""
date: 2026-01-09
categories:
  - 杂项
tags:
  - git推送
halo:
  site: http://www.hzhsec.top
  name: d51ccc28-5157-414d-adba-72788c2860ee
  publish: true
---

<!--more-->
# 概要

本文总结了在国内云服务器上遇到 Git 推送或拉取受限时的三种可行方案：

1. 在云服务器上借助 Clash 启动代理（可行但可能出现网络不稳定）
2. 把云上生成的文件拉回本地，在本地完成 Git 提交与推送（推荐）
3. 直接在云服务器上使用 SSH key 或 Deploy Key 将仓库通过 SSH 推送到 GitHub（推荐长期方案）

下面把三种方案的步骤、注意事项和常见问题整理得更清晰、易操作。

---

## 方案一：在云服务器上安装并使用 Clash（临时代理）

> 说明：此法适合你需要临时让云服务器具备外网访问能力时使用。但由于要先下载 Clash 及其资源（例如 Country.mmdb）可能本身就需要代理，建议先在本地下载好再上传到云端。

### 1. 系统更新

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. 下载并安装 Clash（离线或本地上传）

1. 创建工作目录：

```bash
mkdir -p ~/clash && cd ~/clash
```

2. 从本地或可信网络下载 Clash 二进制与资源（建议先在本地下载好再通过 scp 上传）：

```bash
# 本地先下载，再上传到服务器：
# 本地：wget https://github.com/doreamon-design/clash/releases/download/v2.0.24/clash_2.0.24_linux_amd64.tar.gz
# 本地：scp clash_2.0.24_linux_amd64.tar.gz root@your-server:/root/clash/

# 服务器上解压：
 tar -zxvf clash_2.0.24_linux_amd64.tar.gz
 mv clash-linux-amd64 clash
 chmod +x clash
```

> ⚠️ 请根据 `uname -m` / `uname -a` 确定架构（amd64 / arm64）。

3. 配置文件（config.yaml）

* 推荐在本地使用订阅或配置生成器下载好 `config.yaml` 与 `Country.mmdb`，然后通过 `scp` 上传到服务器 `~/clash` 目录。
* 如果选择服务器直接 curl，请务必把 URL 用引号括起来：

```bash
curl -f "https://free.datiya.com/" -o config.yaml
```

4. 启动 Clash：

```bash
# 在当前目录使用本地 config.yaml
./clash -d ./
```
![[屏幕截图 2025-10-11 214639.png]]
这样就是执行成功了

如果希望后台运行，可用 `nohup` 或 systemd：

```bash
nohup ./clash -d ./ > clash.log 2>&1 &
```

### 3. 配置系统代理（仅命令行进程生效）

```bash
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
# 测试
curl -I https://www.google.com || curl -I https://github.com

# 取消代理
unset http_proxy https_proxy
```

### 常见问题与建议

* **下载 Country.mmdb / config.yaml 时仍需代理**：先在本地下载并上传。
* **网络不稳定 / 超时**：考虑使用本地上拉取、或用 SSH 隧道（见下文）替代。
* **端口被占用**：确认 7890/7891 等端口未被占用。
* **权限/路径问题**：检查 `chmod +x`、路径是否正确。

---

## 方案二：本地拉取云文件，然后在本地完成 Git 提交/推送（最稳妥）

> 场景：云服务器能稳定生成静态文件（例如 Hugo 的 `public/`），但无法直接推送到 GitHub。

### 步骤

1. 在本地克隆仓库（如果还没有本地仓库）：

```bash
git clone https://github.com/yourname/your-repo.git
cd your-repo
```

2. 从云端把生成的静态文件拉到本地（可用 scp 或 rsync）：

```bash
# 使用 scp（递归复制）：
scp -r root@your-server:/usr/local/nginx/html/my-site/public/* ./

# 或使用 rsync（推荐，支持断点续传与增量）：
rsync -avz --progress root@your-server:/usr/local/nginx/html/my-site/public/ ./
```

3. 在本地添加、提交并推送：

```bash
git add .
git commit -m "update site files"
git push origin main   # 或 master，根据仓库分支而定
```

### 优势

* 本地网络稳定、可以使用本地代理加速。
* 可以在本地预览、校验再推送。
* 无需在云服务器上配置复杂的代理或修改 SSH 设置。

---

## 方案三：在云服务器上使用 SSH Key / Deploy Key 直接通过 SSH 推送（长期推荐）

> 说明：通过 SSH key 或仓库的 Deploy Key，让云服务器具有对目标 GitHub 仓库的写权限，这是长期稳定且被广泛采纳的做法。

### A. 作为个人账号的 SSH Key

1. 在云服务器上生成 SSH 密钥（不设置 passphrase 或使用 ssh-agent）：

```bash
# 在云服务器上（或本地根据需要）
ssh-keygen -t ed25519 -C "your-server-identifier" -f ~/.ssh/id_ed25519
# 如果系统不支持 ed25519，可用 rsa：ssh-keygen -t rsa -b 4096
```

2. 将公钥复制并添加到你的 GitHub 账户 "Settings → SSH and GPG keys → New SSH key"：

```bash
# 在服务器上打印公钥并复制
cat ~/.ssh/id_ed25519.pub
```

3. 测试 SSH 连接：

```bash
ssh -T git@github.com
# 你应该看到类似：Hi <username>! You've successfully authenticated...
```

4. 在服务器上使用 SSH 方式克隆或修改 remote：

```bash
# 克隆（SSH）
git clone git@github.com:yourname/your-repo.git

# 或修改已存在仓库的 remote 为 SSH
cd /path/to/your/repo
git remote set-url origin git@github.com:yourname/your-repo.git

git add .
git commit -m "update"
git push origin main
```

### B. 使用仓库 Deploy Key（更适合 CI / 单仓库写入）

Deploy Key 是绑定到单个仓库的公钥，适用于服务器只需要访问（read/write）该仓库的场景。

1. 在服务器上生成密钥对（如上）。
2. 在 GitHub 仓库页面 → Settings → Deploy keys → Add deploy key，粘贴公钥并勾选 "Allow write access"（如果需要推送）。
3. 在服务器上使用 SSH 克隆仓库（与个人 SSH key 一样）：

```bash
git clone git@github.com:yourname/your-repo.git
```

> 优点：权限最小化、便于审计；适合自动化部署场景。

### 常见问题与排查

* **`Permission denied (publickey)`**：检查公钥是否正确添加到 GitHub、私钥权限是否受限（`chmod 600 ~/.ssh/id_ed25519`），以及 `ssh-agent` 是否正确加载。
* **SSH 走代理/墙内问题**：若服务器网络到 GitHub 的 SSH (port 22) 被阻断，可尝试：

  * 使用 HTTPS + PAT（个人访问令牌）作为备选推送方法；
  * 使用 `ssh -T -p 443 git@ssh.github.com` 连接到端口 443（若网络允许）；
  * 使用跳板机或本地端口转发（SSH 隧道）。
* **CI/自动化推送失败**：确认私钥仅能被部署用户读取，并考虑使用 Deploy Key。

---

## 附：通过 HTTPS + PAT 在服务器上推送（替代方案）

如果你不想配置 SSH，也可使用 HTTPS + GitHub Personal Access Token（PAT）：

```bash
# 给 Git remote 设置包含 TOKEN 的 URL（不建议把 TOKEN 明文写入脚本）
git remote set-url origin https://<TOKEN>@github.com/yourname/your-repo.git

git push origin main
```

建议将 TOKEN 存在环境变量或使用 git-credential-store 管理。

---

## 小结与建议

* **临时**：如果只需临时访问外网，Clash 可试，但稳定性不保证。
* **稳妥（推荐）**：在本地拉取云端产物再推送到 GitHub，操作简单、可靠。
* **长期（推荐）**：为云服务器配置 SSH Key 或 Deploy Key，使其能直接以安全方式将变更推送到 GitHub。