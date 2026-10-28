# Linux 部署与运行

目前提供源码部署包；2026-10-20已在阿里云Alibaba Cloud Linux 3上完成镜像构建、基础HTTP验收、Office转PDF、数值基准、源码复算、服务重启持久化及真实DeepSeek工具交互。实际环境、证据与未覆盖范围见[Linux实机验收](LINUX_VALIDATION.md)；域名未备案被拦截，公网HTTPS和压力验收尚未完成。

## 最低配置与构建

建议 x86_64 Linux、2 vCPU、4GB RAM、10GB 可用磁盘，安装 Docker Engine 和 Compose v2。模型在外部 API 时无需 GPU；Ollama 的 CPU/GPU/内存需求取决于所选模型。

解压源码包，进入 chemellm，复制 .env.example 为 .env。使用密码管理器或以下命令生成工作台口令并填写 CHEMELLM_AUTH_TOKEN：

源码包带有中文赛题文件名。部分发行版的旧 `unzip` 会错误转换文件名，导致 Dockerfile 的 `COPY` 找不到文件；建议在UTF-8环境用Python解压：

    LC_ALL=C.utf8 python3 -m zipfile -e chemellm-linux-source-0.1.0.zip ./release
    cd release/chemellm
    cp .env.example .env

工作台口令生成命令：

    python -c "import secrets; print(secrets.token_urlsafe(32))"

将 .env 权限设置为600，配置服务地址、模型 ID、密钥。不要把密钥放入前端或项目文档。

运行 docker compose up -d --build，然后用 docker compose ps、docker compose logs --tail=100 chemellm 和 /api/health 验证状态。Compose 没有工作台口令时拒绝启动。数据持久化至名为 chemellm-data 的 Docker volume，应用以 UID 10001 运行。

镜像包含 LibreOffice Writer/Impress 和 Noto CJK 字体。Office 转换使用独立临时 profile；最大执行时间60秒。首次构建需要访问 Debian 和 PyPI。

中国内地服务器如无法连接 Docker Hub，可先从官方 ECR 公共仓库下载相同的 Python 基础镜像，再标记为 Dockerfile 使用的名称：

    docker pull public.ecr.aws/docker/library/python:3.12-slim-bookworm
    docker tag public.ecr.aws/docker/library/python:3.12-slim-bookworm python:3.12-slim-bookworm

Debian/PyPI 下载过慢时，在项目目录创建 `compose.override.yaml`，为本次构建指定镜像源。默认 Dockerfile 仍使用官方源：

```yaml
services:
  chemellm:
    build:
      context: .
      args:
        DEBIAN_MIRROR: https://mirrors.aliyun.com/debian
        DEBIAN_SECURITY_MIRROR: https://mirrors.aliyun.com/debian-security
        PIP_INDEX_URL: https://mirrors.aliyun.com/pypi/simple
```

若预加载基础镜像后构建工具仍尝试访问 Docker Hub，可用 `DOCKER_BUILDKIT=0 docker compose build` 构建后再执行 `docker compose up -d`。这取决于 Docker/Compose 版本是否仍支持旧构建器。

2GB 主机只建议少量任务试运行；可在同一覆盖文件的 `chemellm` 下设置 `mem_limit: 1400m`，并在 `environment` 下将 `OPENBLAS_NUM_THREADS`、`OMP_NUM_THREADS`、`MKL_NUM_THREADS` 设为字符串 `"1"`。该限制不代表完整功能已能在2GB内稳定运行，也不限制构建阶段内存。默认3GB容器上限应配合至少4GB主机使用。

传统RapidOCR/ONNX已从运行镜像依赖中移除。平台默认使用PDF/Office/HTML原生文本解析；明确选择AI图像转录时，向配置模型发送压缩后的图像数据。`MODEL_VISION`可显式指定视觉模型，留空时复用`MODEL_BALANCED`；接口不接受图像时保留失败，不切换到其他识别器。当前真实模型端点视觉能力尚未实测资格化；参见[FULLTEXT_EVIDENCE.md](FULLTEXT_EVIDENCE.md)。

镜像也安装`simulation`扩展（Cantera 3.2.0、ruamel.yaml 0.18.16），用于固定机理的理想气相平衡与闭式反应器。调用在60秒超时子进程中执行，原生包保留实际模型及发行机理文件。Windows及Linux均已作局部资格对照，见[CANTERA_MODEL.md](CANTERA_MODEL.md)及实机记录。

源码包包含应用、网页、脚本、说明、测试和原赛题，不包含本地项目数据及模型密钥。它是在线构建所需的源码包，未附离线 Python wheel、系统软件包、容器镜像或 Ollama 权重；离线服务器需提前准备这些依赖。

## 访问

默认映射127.0.0.1:8000。在客户端通过 ssh -L 8000:127.0.0.1:8000 user@server 后打开本机 http://127.0.0.1:8000 。公开访问需在前面配置 HTTPS 反向代理；同源代理 / 到后端，保留原始 Host，上传限制设为26MiB，读取超时建议180秒。可信代理环境才启用相应 forwarded-header 信任设置。

宿主机Nginx代理到Docker时，后端通常看到Docker网络网关地址。查询实际网关，并在 `.env` 的 `FORWARDED_ALLOW_IPS` 中只加入该可信代理地址及回环地址；本次为 `172.19.0.1,127.0.0.1`，其他服务器不能直接照抄。配置后重建容器，使后端识别可信 `X-Forwarded-Proto: https` 并设置Secure Cookie。Nginx必须覆盖客户端传来的 `X-Forwarded-For` 和 `X-Forwarded-Proto`，保持应用端口仅绑定回环。

中国内地服务器的域名应先完成ICP备案。本次 `chemellm.online` 的A记录正确，但阿里云实际返回 `403 / Non-compliance ICP Filing`，HTTP-01证书验证因此失败。HTTPS未启用，也未启用证书续期任务。当前可通过项目专用SSH配置访问服务器工作台：

    ssh -F data/qa/linux-server/ssh_config -N -L 127.0.0.1:18000:127.0.0.1:8000 chemellm-server

保持终端运行，浏览器打开 `http://127.0.0.1:18000`。本机HTTP由加密SSH传输，不会以明文HTTP跨公网发送口令。当前用户的工作台口令单独保存在本机 `data/qa/linux-server/workbench-access.txt`，仅供本次部署使用，不在源码包中。

备案通过、阿里云拦截解除后，在本次服务器上执行以下已准备的操作。其他服务器需先另行安装ACME客户端和准备Nginx验证目录：

    /opt/chemellm-acme/run-certbot.sh certonly --webroot --webroot-path /var/www/chemellm-acme --domain chemellm.online --cert-name chemellm.online --non-interactive --agree-tos --register-unsafely-without-email
    python3 /opt/chemellm-linux-qa/20261020/enable_https.py
    /opt/chemellm-acme/run-certbot.sh renew --dry-run

启用脚本要求有效证书，备份并验证Nginx配置后才重载，同时设置每天两次、随机延迟的systemd证书续期检查。缺少证书时拒绝更改配置；该退出路径已验证，实际HTTPS及续期路径仍待备案后实测。然后核对阿里云安全组允许80/443，从外部网络验证证书链、HTTP跳转、登录Cookie的Secure属性及已有文件下载。当前ACME账户没有配置邮件地址。

浏览器以 HttpOnly、SameSite=Strict cookie 保存工作台口令；真实 HTTPS 下设置 Secure 属性。当前为共享工作台鉴权，不含每用户项目授权、SSO、速率限制及完整访问审计。多租户对外服务需先补齐这些能力。

## 模型

兼容 API 使用 /chat/completions、function tools、tool result 消息。不是 Responses API 适配器。模型必须支持工具调用；具体可用性由服务商/账户决定，未随部署包附带任何密钥或模型权重。

Ollama 在宿主机时使用 http://host.docker.internal:11434/v1，并确保 Docker 网关能访问服务；不要把无认证的 Ollama 直接暴露公网。模型需先下载，模型名称需与服务器一致。

MODEL_TIMEOUT_SECONDS 默认120秒；MAX_AGENT_ITERATIONS 默认8。工具执行失败反馈给模型；达到上限后保存上下文等待继续。取消任务在当前 HTTP 请求/工具返回后的边界生效，不能强制中断已经开始的计算或撤销已生成文件。

数值计算在进程内排队执行，以保护 thermo/Chemicals 的共享数据初始化；较大精馏任务可能占用约数秒到60秒。当前不支持多 worker。并发数值调用会等待当前计算完成。

## 备份、恢复、升级

一致性备份时先 docker compose stop chemellm，备份数据 volume 中 SQLite 数据库及整个 artifacts 目录，再启动。模型密钥另行安全备份。恢复需保持 CHEMELLM_DATA_DIR=/app/data；数据库目前存储绝对文件路径，跨不同数据根目录需做路径迁移。

升级前备份数据并保存当前源码包与校验和。解压新版本后重新构建。启动以CREATE TABLE IF NOT EXISTS增量建立全文快照、论断、证据和审核表；尚无版本迁移框架或现有列结构变更脚本，未来修改已有schema须提供迁移。

## 部署验收

- 健康接口200，静态页面正常加载，未登录 API 返回401。
- 上传赛题建立35项要求，PDF原件下载字节一致。
- 运行物料衡算、单位换算、PR闪蒸，检查闭合与异常输入拒绝。
- DOCX/PPTX 上传后确实产生PDF保真预览；下载原件可打开。
- 真实模型至少执行一次工具调用、一次错误修正和一次追问后继续。
- 重启后已有文件/记录存在，中断任务可继续。
- 解压项目成果包，在独立环境执行复算。
- 在Linux执行`python scripts/cantera_benchmark.py`，并对HTTP生成的原生包执行`simulation.py`及项目包复算；保留平台、依赖版本、哈希和结果。

以上为完整验收清单，不能只凭Windows测试或健康接口宣称全部通过。本次Linux已完成的条目见[实机记录](LINUX_VALIDATION.md)；真实模型基础交互已通过，公网HTTPS仍待备案解除拦截后执行。

可先运行提供的 HTTP 检查：

    docker compose exec chemellm python scripts/deployment_smoke.py --require-office

该命令创建标为“部署验收 QA”的项目，并将检查报告写入数据卷 qa/deployment-results.json。它校验赛题哈希/要求、数值工具、Office/PDF 原件及预览、成果包；--require-office 强制两个 Office 格式都生成 PDF 预览。模型真实调用、重启恢复和独立复算仍需另行执行，不能只凭该脚本宣称部署全部验收。
