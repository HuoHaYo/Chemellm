# ChemELLM DSH 插件架构

当前实现由 DSH 插件和本地 Python 内核组成。DSH 提供对话和工程面板，Python 负责确定性计算、项目持久化和成果生成。

## 调用链

```text
DSH tools → lib/tools.js → lib/kernel.js ─┐
                                        ├→ Python /v1/* → kernel/ + old/app/
DSH panel → /chemellm/* → lib/proxy.js ───┘
```

- `dsh-chemellm/index.js`：注册 12 个工具、提示词、代理路由与插件清理回调。
- `lib/kernel.js`：统一端点与令牌，选择开发或便携运行时，合并并发启动请求，限制启动等待，关闭自建子进程。令牌、门禁、数据目录与快照位置在启动时同步到 Python。
- `lib/tools.js`：保留公开工具名称和参数契约；通用工具目录使用 `/v1/tools` 的 `executable`，覆盖 P&ID、HAZOP、数据表等扩展能力。强制模式在写操作前读取最新项目阶段，列表查询不受写入门禁限制。
- `lib/proxy.js`：统一 `/chemellm/api/`、`/chemellm/files/`、`/chemellm/bundles/`，支持 HTTP(S)、流式文件、超时和上游错误。内核令牌只由 Host 注入。
- `client.js`：项目列表、概览、要求、计划、依据、计算、成果、验收与设置。统一异步操作处理错误和忙状态；只接受最新请求结果，卸载后不再更新状态。
- `kernel/server.py`：项目 JSON 是工程状态事实源；SQLite 保存计算与文件元数据；`old/app/` 仍是实际计算、证据、文档依赖。

## 数据位置

手动运行内核默认使用仓库 `data/` 和 `.chem/`。插件自动启动使用配置的 `dataDir`，默认 `<DSH_PROFILE_DIR>/chemellm-data`，其下包括 `projects/`、`kernel/`、`bundles/`、`.chem/`。重构不迁移或修改已有项目数据。

自动启动仅针对本机 HTTP loopback，其他端点连接已有服务。已有服务的令牌和阶段门禁需由服务启动环境配置；插件不接管或关闭外部服务。

## 分发

`package-plugin.ps1` 根据 `package.json.files` 收集插件文件，从便携 runtime 只取 Python、第三方库和依赖清单，再复制仓库当前 `kernel/` 与 `old/app/`。禁止整棵复制旧 runtime，以免夹带过期源码、用户项目、快照和习题材料。缓存被排除，SHA256 清单在分发目录重新生成。

```powershell
.\scripts\package-plugin.ps1 -ValidateOnly
.\scripts\package-plugin.ps1 -SkipArchive
.\scripts\package-plugin.ps1
```

## 清理与升级

已删除主插件可以替代的 `dsh-chemellm-legacy`、`dsh-chemellm-enforce`，5 组仅开发探测使用的 DWSIM Probe 源码与二进制，以及混有历史运行数据路径的源码目录 SHA256 清单。DWSIM 正式 Runner 与构建脚本保留。

旧安装应卸载两个伴生包，保留主插件，直接配置 `phaseGate: enforce`，然后重启 DSH Host。历史验收记录保留原文。

`old/app/` 不能作为无用归档删除。旧 Web、文档与测试作为历史归档保留，不参与插件装配或分发。已有 `data/`、`.chem/`、本地标准文件及便携依赖保持原位。

## 验证

```powershell
node --test dsh-chemellm/test/*.test.js
python -X utf8 scripts/test_kernel.py
node scripts/test_packaged_plugin.mjs
```

Node 回归测试覆盖公开工具注册、当前阶段校验、扩展工具目录、Host 令牌代理、预览与下载字节、上游错误、并发启动、配置传递与关闭。Python 回归使用独立临时数据目录，覆盖鉴权、阶段拒绝、计算、报告、下载、成果包 SHA256 与依据变更后的校核失效。

`test_packaged_plugin.mjs` 需先生成分发目录。它使用包内 Python 自动启动真实内核，串联 Host 工具与代理下载，数据写入独立临时目录并在结束后清理。

自动校核保持与专业审核分离。计算模型、图纸规则与工程判定口径沿用现有实现。
