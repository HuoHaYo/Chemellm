# DWSIM 接入（`dwsim` 工具）

> 定位：把本机安装的 **DWSIM 9.0.5** 作为外部流程模拟引擎接入工作台；工作台负责调用、结果归档与数据链，不复制、不修改 DWSIM，也不随插件分发 DWSIM（GPL-3.0）。

## 1. 运行条件

- Windows x64；
- 本机已安装 DWSIM，默认路径 `%LOCALAPPDATA%\DWSIM`；
- 存在 `DWSIM.Automation.dll` 与 `DWSIM.exe`；
- 工作台内核侧有 `kernel/dwsim/DwsimRunner.exe`（C# .NET Framework 运行器，随插件提供）；
- 可用环境变量 `DWSIM_HOME` 指向自定义安装目录。

`DwsimRunner.exe` 通过 `DWSIM.Automation.Automation3` 加载并求解 flowsheet；DWSIM 的 .NET 依赖由运行器从安装目录解析。DWSIM 解压 `.dwxmz` 时会使用系统临时目录，运行器会先把 `TEMP/TMP` 指到 `data/kernel/dwsim-temp`。

## 2. 调用

### 2.1 状态检测

```text
chem_tool(projectId=..., tool="dwsim", arguments={"action": "status"})
```

返回：`installed`、`home`、`automation_dll`、`runner`、`samples`（安装自带样例名）。

### 2.2 运行 flowsheet

```text
chem_tool(projectId=..., tool="dwsim", arguments={
  "action": "run",
  "flowsheet_path": "C:\\Users\\<user>\\AppData\\Local\\DWSIM\\samples\\Cavett's Problem.dwxmz",
  "label": "Cavett"
})
```

- 支持 `.dwxmz`（压缩 flowsheet）与 `.dwxml`（XML flowsheet）；
- 只做**加载 + 求解 + 结果导出**，不在工作台内创建/编辑 DWSIM 流程图；
- 求解失败（`solved=false`）仍保留 JSON/CSV，并给出错误信息；不伪造结果。

## 3. 输出

| 文件 | 内容 |
|---|---|
| `DWSIM结果.json` | 引擎、版本、flowsheet 路径、solved/error、物流与单元操作列表 |
| `DWSIM物流表.csv` | `tag,name,type,temperature_K,pressure_Pa,mass_flow_kg_s,compounds,mole_fractions` |

单位：温度 **K**、压力 **Pa**、质量流量 **kg/s**；组成来自 DWSIM 物流的摩尔分数。`tag` 是 DWSIM GraphicObject 的 Tag，`name` 是对象 Name（部分样例为 GUID，因为样例没有命名标签）。

## 4. 已验证结果

用 DWSIM 自带 `samples\Cavett's Problem.dwxmz` 实测：

- 版本 9.0.5.0；`solved=true`；20 条物料流、15 个单元操作；
- 产物 JSON 23,190 B，物流表 CSV 10,084 B；
- `chem_review ready=true`（3 要求 / 1 成果 / 1 依据对象）、bundle 已生成。

该验证只证明“DWSIM 能被加载、求解并导出结果”，不证明 Cavett 样例对某工艺设计正确。

## 5. 边界

- DWSIM 为外部 GPL-3.0 软件，**不随插件分发**；目标机需单独安装；
- 结果取决于 flowsheet 内的物性包、单元模型、收敛设置与初始值，工作台不对其做独立物理验证；
- 不接入 DWSIM 动态模式/自定义脚本/Python 单元的高级交互；仅做静态 flowsheet 加载与求解；
- 不替代 Aspen/HTRI 等商业软件或专业审核；
- DWSIM 运行失败时工具返回明确错误（安装缺失、flowsheet 不存在、求解不收敛、单元不支持等），不会伪造物流数据。

## 6. 文件

- `kernel/dwsim_bridge.py`：检测、子进程调用、CSV 导出；
- `kernel/dwsim/DwsimRunner.cs` / `.exe`：.NET 运行器；`scripts/build-dwsim-runner.ps1` 可重编译；
- `docs/DWSIM.md`：本文档；
- 样例验证项目：`DWSIM 接入验证（Host / Cavett）`（Host 内核）与 `DWSIM 接入验证（Cavett）`（测试内核）。
