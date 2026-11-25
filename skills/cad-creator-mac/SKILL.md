---
name: cad-creator-mac
description: 在 macOS 上用 cad-dxf MCP 或 ezdxf 处理 DXF，用 AutoCAD 桌面和 AutoLISP 编辑 DWG、建模与打印，用 SketchUp MCP 建模与保存原生 SKP，以及全套 Blender 5.2+/5.3（SKP 导入、Metal Cycles/EEVEE 渲染、Live MCP 操控及内置 28 个 3D 全流程子技能）。
license: MIT
---

# macOS CAD 制图、SketchUp 建模与 Blender 全流程

## 选择工作方式

- **常规 DXF 与 DXF→DWG 优先走无界面流程。** 用 [cad-dxf MCP 操作指南](references/headless-dxf.md) 创建、查询、修改和回读 DXF；缺少 MCP 时，沿用已可用的 `ezdxf` 环境处理 DXF。需要将规则 DXF 转为原生 DWG 时，优先调用 [dxf_to_dwg.py](scripts/dxf_to_dwg.py)（基于 macOS AutoCAD 自带 `AcCoreConsole.app` 无界面转存并只读回读校验），无需拉起 AutoCAD 桌面端。
- **需要交互式原生 CAD 时再进入桌面流程。** 用户明确要求操作 AutoCAD 桌面端，或任务需要保留 DWG 既有布局手动调整、创建 AutoCAD 原生三维实体、使用既有布局交互打印时，使用下文的 AutoCAD 桌面操作。用户指定 AutoLISP 或原生打印时，按指定工序执行。
- **SketchUp 建模或交付 SKP 时走 Ruby 桥接。** 使用 [SketchUp MCP 指南](references/sketchup-mcp.md) 核对活动模型，直接通过 `sketchup` MCP 创建几何、墙体、门窗、群组、材质与场景并保存 SKP。建模和保存通过 SketchUp Ruby API 完成。
- **SKP 转 Blender 与 Blender 全流程控制（Live MCP / 无界面脚本 + 内置 28 个子技能）。**
  - SKP 导出衔接、端口隔离（SketchUp `9876` / Blender MCP `9877`）与一键场景构建/出图优先用 [Blender 渲染指南](references/blender-render.md) 与 [blender_render.py](scripts/blender_render.py)（支持 CLI 无界面与 Live MCP 中 `blender_render.run(...)`）。
  - 其余完整 Blender 5.2+/5.3 3D 任务（建模、雕刻、拓扑 UV、PBR 材质、贴图烘焙、几何节点、绑定、动画、布料、毛发、日夜天气、物理仿真、风格化、视频剪辑、引擎导出与资产 QA）已全量内置于 [blender-skills/](blender-skills/)，直接加载入口 [blender-core](blender-skills/blender-core/SKILL.md) 并按其路由表调度对应子技能（其中 `<skills_dir>` 即本技能内的 `blender-skills/` 目录；编写或排错 `bpy` 时查阅 [api-changes-5x.md](blender-skills/blender-core/references/api-changes-5x.md) 与 [bpy-patterns.md](blender-skills/blender-core/references/bpy-patterns.md)）。
- CAD 工程图先确认图纸单位、修改范围、交付格式和关键尺寸。新建工程图或用户未指定完整制图规范时，按 [国标制图规范与分级验收](references/gb-drafting-standards.md) 落实幅面、线宽、图层、标注、剖视后壁轮廓与 L1–L4 验收门禁。局部改图沿用原图标准，保留无关图层、布局、块、外参和样式。先从需求记下关键几何、实体类型、语义图层及输出格式作为验收依据。

- 建筑局部改图先对齐底模，再按[建筑改版与出图验收](references/gb-drafting-standards.md#建筑改版与出图验收)核对受影响的图纸、模型和说明。交付可编辑 SKP 时按 [SketchUp 建模与验收](references/sketchup-mcp.md#建模与验收)检查最终文件。

## AutoCAD 桌面操作

1. 用 [桌面操作指南](references/desktop-runners.md) 聚焦 AutoCAD。2027 版 bundle ID 是 `com.autodesk.AutoCAD2027`。开始页先打开目标文件，或为新图选择符合单位的样板；接到新建图纸任务时，若当前活动文档已有实体，必须先新建空白图（公制优先 `acadiso.dwt`），不得在上一轮遗留图纸上直接续画或覆盖。修改前回读完整路径、`CTAB`、`TILEMODE`、`CVPORT` 和 `INSUNITS`，确认图面单位、空间、WCS/UCS 和目标对象。布局标签内也可能在编辑视口中的模型。按用户要求原位更新、另存或建立副本。
2. 从可访问性树定位 `commandPane` 下的 `cmdInput`。确认目标窗口和提示符空闲，原样输入一条命令或完整单行表达式，核对文本与焦点，再按一次 `Return`。空输入框上的 `Return` 可能重复上一条命令。
3. 简单操作可直接用 AutoLISP。多实体修改按 [批量脚本与失败恢复](references/batch-workflow.md) 先加载助手，再执行本次任务。脚本写入前核对上下文，记录返回结果，恢复临时变量，并将本次操作放入一个撤销组。
4. 用 `cmdHistory` 或可见提示符核对结果。遇到弹窗、切换文档或结果不明时，刷新窗口状态并先读回已有改动，再决定是否重试。无法聚焦确切图纸时暂停发送命令。
5. 按 [AutoLISP 与文件操作](references/autocad-operations.md) 保存和验证。重开 DWG/DXF 核对关键坐标、尺寸、空间、图层和原生实体类型。PDF 检查同版实际页面、图幅、比例、字体、线型、线宽和裁切。交付 DWG 时核对重开首屏，打印带尺寸的工程图时按[出图验收](references/gb-drafting-standards.md#建筑改版与出图验收)比对实际标注读数，并在定比例视图量取最终 PDF 的纸面距离。汇报实际完成的检查与交付文件。
