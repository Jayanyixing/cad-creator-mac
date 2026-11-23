# cad-creator-mac

面向 macOS 的 **AI CAD 制图与 SketchUp 建模 Agent Skill**。支持无界面 DXF、原生 AutoCAD 桌面制图以及 SketchUp Ruby API 建模。CAD 工作流内置 GB/T 国标制图规范、批量事务助手与 L1–L4 分级验收，技能可安装在 Codex、Google Antigravity、Gemini CLI 和 Hermes 等客户端。

---

## 核心特性

- **CAD 工作流**提供无界面 DXF 和 AutoCAD for Mac 桌面操作。原生 DWG 编辑保留既有样式、块和外参，亦可创建 AutoCAD 三维实体或使用原生布局打印。
- **SketchUp MCP** 通过本机 Ruby 扩展创建几何、墙体、门窗、群组、材质与场景，并保存原生 SKP。
- **GB/T 国标制图内置**：涵盖幅面比例（GB/T 14689 / 14690）、图线与线宽层级（GB/T 17450）、`ByLayer` / 0 层建块铁律、标注三不原则、中文字体统一（防 `???` 与 SHX 混排）、剖视图后壁可见轮廓线规则。
- **安全批量执行与防踩坑**：提供 [batch-task.lsp](skills/cad-creator-mac/scripts/batch-task.lsp) 事务助手，执行前校验活动文档/空间/命令空闲状态，自动包裹撤销组并恢复临时系统变量（如 `OSMODE`、`CMDECHO`）；内置防串图、防 `_AUDIT`/`_PURGE` 交互挂起、`BACKGROUNDPLOT` 同步等待等实战护栏。
- **L1–L4 分级验收与熔断**：从脚本回执（L1）、实体数量（L2）、重开结构审计（L3）到同版 PDF 视觉交叉审查（L4）闭环把关；同类错误连续 3 次或上下文异常自动熔断排查。

## 工作方式选择

| 任务场景 | 推荐路线 | 说明 |
| :--- | :--- | :--- |
| 常规 2D DXF 新建、查询、批量修改、结构审计 | **无界面路线**（`cad-dxf` MCP / `ezdxf`） | 无需打开 AutoCAD，执行快、纯数据回读准确 |
| 已有 DWG 原位改图（保留布局/块/外参/样式） | **AutoCAD 桌面路线**（桌面操作 + AutoLISP） | 完整保留 DWG 原生编辑语义 |
| 原生三维实体、复杂交互命令、原生 PDF 打印 | **AutoCAD 桌面路线**（桌面操作 + AutoLISP） | 支持线宽层次打印、中文字体与原生布局出图 |
| 规则 2D 工程图需交付真实 DWG | **混合路线**（无界面生成 DXF → AutoCAD 另存 DWG） | 兼顾高精度生成与真实 DWG 交付 |
| SketchUp 几何与房间建模、材质、场景、SKP 交付 | **SketchUp 路线**（`sketchup` MCP + SU MCP Bridge） | 直接调用 SketchUp Ruby API |

---

## 安装

将仓库中的 [skills/cad-creator-mac](skills/cad-creator-mac) 复制到对应客户端的技能目录：

| 客户端 | 用户级技能目录 |
| :--- | :--- |
| Codex | `~/.codex/skills/cad-creator-mac` |
| Google Antigravity | `~/.gemini/config/skills/cad-creator-mac` |
| Gemini CLI | `~/.gemini/skills/cad-creator-mac` |
| Hermes | `~/.hermes/skills/cad-creator-mac` |

**命令行快速安装（以 Antigravity / Codex 为例）：**

```bash
git clone https://github.com/Jayanyixing/cad-creator-mac.git
cp -R cad-creator-mac/skills/cad-creator-mac ~/.gemini/config/skills/
# 或安装到 Codex：
cp -R cad-creator-mac/skills/cad-creator-mac ~/.codex/skills/
```

**Codex 对话内一键安装：**

> 安装这个 Skill https://github.com/Jayanyixing/cad-creator-mac/tree/main/skills/cad-creator-mac

---

## 环境要求

- **无界面 DXF 路线**：已配置 `cad-dxf` MCP（基于 [id0o0bi/autocad-mcp](https://github.com/id0o0bi/autocad-mcp)）或本机可用的 Python `ezdxf` 环境。配置步骤见 [headless-dxf.md](skills/cad-creator-mac/references/headless-dxf.md)。
- **AutoCAD 桌面路线**：macOS + Autodesk AutoCAD 桌面版（已在简体中文版 AutoCAD 2027 验证）+ 客户端可用的 macOS 桌面操作工具（如 Codex Computer Use、Antigravity `computer-use` MCP 或 Hermes `computer-use`）。
- **SketchUp 路线**需要 SketchUp 桌面版、SU MCP Bridge Ruby 扩展及客户端配置的 `sketchup` MCP。安装、连接和建模说明见 [sketchup-mcp.md](skills/cad-creator-mac/references/sketchup-mcp.md)，已在 macOS SketchUp 2026 上验证。

---

## 使用示例

在支持 Agent Skills 的客户端中调用 `$cad-creator-mac`，或直接说明制图和建模任务。

1. **无界面快速出图（DXF）**
   > 用 `cad-creator-mac` 无界面画一块 120 × 80 mm 的公制底板，四角各一个 Ø10 mm 通孔，按国标分层，生成 DXF 后做结构审计并回读核对。

2. **AutoCAD 桌面绘制国标工程图并打印 PDF**
   > 用 `cad-creator-mac` 在 AutoCAD 中新建公制空白图，绘制双视图法兰底座（含图层、线宽、中心线、45° 剖面线、原生标注和 A3 标题栏），另存 DWG 并开启对象线宽打印黑白 PDF 视觉核验。

3. **安全修改已有 DWG**
   > 用 `cad-creator-mac` 检查当前打开的 AutoCAD 图纸路径、单位与图层，另存副本后把全部 Ø10 mm 安装孔改为 Ø12 mm，更新对应标注并重开回读验证。

4. **SketchUp 建模并保存 SKP**
   > 用 `cad-creator-mac` 在 SketchUp 里建一个 4000 × 3200 mm 的房间，加一扇门和一扇窗，分配材质，创建平面与透视场景后另存 SKP。

---

## 仓库结构

```text
cad-creator-mac/
├── skills/cad-creator-mac/
│   ├── SKILL.md                             # 技能主入口与路由决策
│   ├── agents/openai.yaml                   # 客户端元数据与默认提示
│   ├── scripts/
│   │   └── batch-task.lsp                   # AutoLISP 安全事务与撤销组助手
│   └── references/
│       ├── gb-drafting-standards.md         # GB/T 国标制图规范与 L1–L4 验收
│       ├── headless-dxf.md                  # cad-dxf MCP 与 ezdxf 无界面操作指南
│       ├── sketchup-mcp.md                   # SketchUp Ruby 桥接、建模与 SKP 保存
│       ├── desktop-runners.md               # Codex / Antigravity / Hermes 桌面操作适配
│       ├── batch-workflow.md                # 批量脚本、故障恢复与熔断纪律
│       └── autocad-operations.md            # AutoLISP 实体读写、中文字体、线型与出图
└── tests/
    └── smoke-test.md                        # 可复现冒烟测试与验证记录
```

---

## 验证与许可证

- 冒烟测试用例与各客户端实测记录见 [tests/smoke-test.md](tests/smoke-test.md)。
- 本项目采用 [MIT](LICENSE) 许可证开源。
