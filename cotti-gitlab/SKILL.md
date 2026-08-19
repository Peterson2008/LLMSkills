---
name: cotti-gitlab
description: 访问 Cotti 公司内网服务（git.yummy.tech 内网 GitLab、ODPS、内网看板）时绕开本机代理。当克隆/拉取内网 git 仓库，或 curl/pip/请求内网地址报 SSL_ERROR_SYSCALL、502 Bad Gateway、连接被重置或卡住时使用。根因通常是本机 clash 代理（127.0.0.1:7897）把内网 host 一起劫持了。给出诊断与绕代理方法；git 优先走 SSH。不用于外网站点的普通代理配置。
---

# Cotti GitLab / 内网代理

本机常年开着 clash 类代理（典型 `127.0.0.1:7897`），环境变量里 `http_proxy` /
`https_proxy` / `all_proxy` 都指向它。这套代理是为**翻墙访问外网**服务的，但它会把
**公司内网 host** 也一并劫持——内网地址本该直连，走了代理反而连不通。

`no_proxy` 里通常**只登记了个别内网 IP，没登记内网域名**（如 `git.yummy.tech`），
所以内网域名默认还是走代理，就会出问题。

## 症状（命中任一，基本就是代理劫持内网）

- git clone / fetch 内网仓库：`LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to <host>:443`
- curl 内网 HTTPS：TLS 握手中断（`SSL_ERROR_SYSCALL`）
- curl 内网 HTTP：`HTTP/1.1 502 Bad Gateway`，响应头带 `Proxy-Connection`
- 请求长时间卡住后超时；而 `ping` / `nc -z host 443` 却是通的

## 快速判定

```bash
env | grep -iE 'proxy'                       # 看代理指向哪，no_proxy 有没有这个域名
nslookup <host>                              # 内网域名一般解析到 10.x / 内网 DNS
curl -sSv --noproxy '*' --max-time 10 https://<host> 2>&1 | tail -20
```

若**加 `--noproxy '*'` 后 TLS 能正常握手**，就证实是代理劫持——按下面绕开即可。

## 绕开代理（内网直连）

### git —— 优先用 SSH

内网 GitLab 的私有仓库走 HTTPS 还要账密，而 SSH key 一般已配好（看同机其它内网仓库
的 remote 多是 `git@<host>:...`）。**把 HTTPS 地址转成 SSH 直接克隆最省事**：

```bash
# https://git.yummy.tech/GROUP/REPO.git  →  git@git.yummy.tech:GROUP/REPO.git
git clone git@git.yummy.tech:GROUP/REPO.git
```

确认现有仓库怎么连（照抄它的方式）：

```bash
git -C <某个内网仓库> remote -v
```

若必须走 HTTPS，则连 env 代理带 git 配置一起关掉：

```bash
unset all_proxy ALL_PROXY HTTP_PROXY http_proxy HTTPS_PROXY https_proxy
git -c http.proxy= -c https.proxy= clone https://<host>/GROUP/REPO.git
```

### curl / 通用命令

```bash
# 单次：--noproxy '*' 让 curl 忽略所有代理变量
curl --noproxy '*' https://<host>/...

# 或在子 shell 里清掉全部代理变量后再跑（注意大小写两套都要 unset）
( unset all_proxy ALL_PROXY HTTP_PROXY http_proxy HTTPS_PROXY https_proxy; <命令> )
```

> 只 `unset https_proxy` 往往不够：curl 还会回落到 `all_proxy`（socks5）。
> 大小写两套 + `all_proxy` 都要清，或直接 `--noproxy '*'`。

### 长期修复（可选，建议告知用户手动做）

把内网域名加进 `no_proxy` / `NO_PROXY`，让所有工具默认直连：

```dotenv
no_proxy=localhost,127.0.0.1,<原有内网IP>,git.yummy.tech,*.yummy.tech
NO_PROXY=同上
```

clash 用户也可在其配置的 rules 里给内网域名加 `DIRECT`。这类改动会影响用户整机
环境，**先说明再改，不要擅自动用户的 shell 配置或代理软件设置**。

## 注意

- 先诊断再动手：确认是「代理劫持内网」而非真的网络/权限问题（`--noproxy '*'` 能否握手是关键判据）。
- 绕代理只对**内网 host** 用；外网 host 仍需走代理，别一刀切全局关代理。
- 别把凭证/token 写进 remote URL 或提交进仓库；认证优先用已配置好的 SSH key。
- host、IP、端口逐字引用，不猜测；不同机器代理端口/内网网段可能不同，以 `env | grep proxy` 实测为准。
