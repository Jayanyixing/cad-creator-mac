# AutoCAD for Mac 验证用例

在各客户端用独立公制测试图运行，记录客户端、AutoCAD 版本和每项结果。

| 步骤 | 预期结果 |
| --- | --- |
| 查询活动图纸、单位和空间 | 完整路径匹配，公制样图单位为毫米，当前空间符合任务 |
| 传入与实际不同的文件名，或开启一个已有撤销组后运行助手 | 返回 `CADMAC-REFUSED`，对象数和变量未变化 |
| 在测试副本执行批量脚本 | WCS 外形 100 × 60 mm，两个原生 Ø10 mm 圆位于 `(25,30,0)` 和 `(75,30,0)`；孔中心距原生标注为 50 mm，带中文说明和中心线 |
| 在独立副本中写入一个测试实体后调用 `(/ 1 0)`，或在测试专用 `getstring` 时按 Esc | 返回失败或取消；临时变量恢复原值，助手的撤销组已关闭。确认测试修改是最近操作后，执行一次 `_.U` 并回读对象数 |
| 另存 DWG 并重开 | 原生实体、圆心、直径、标注测量值及图层与预期一致 |
| 打印同版 PDF 并打开 | 页面、比例、中文、线宽和线型符合任务，尺寸文字未遮住轮廓 |

## 无界面 DXF 用例

在配置 `cad-dxf` 的客户端，用 [操作指南](../skills/cad-creator-mac/references/headless-dxf.md) 生成板件样例。回读确认一条闭合轮廓和四个 Ø10 mm 原生圆。另存副本并将四孔改为 Ø12 mm。重开核对单位、板件四角、孔径和结构审计结果，并检查源 DXF 内容未被改写。

## 已记录的验证范围

- Codex 与简体中文版 AutoCAD 2027 已在此前验证读图、创建圆、另存 DWG 和重开回读。
- 本次更新提供批量脚本和上述验证用例。实际批量执行、故障恢复与 PDF 出图有待在 AutoCAD 中重跑。Gemini / Antigravity 与 Hermes 的 AutoCAD 实机流程也有待分别复验。

- `cad-dxf` 已用 Codex 注册的 stdio 命令实测样例创建、另存修改、回读和 ezdxf 结构审计。
- `dxf_to_dwg.py` 已在 macOS + AutoCAD 2027（`AcCoreConsole`）实测带中文/空格/括号路径实图转存、重复覆盖写、空 DXF 边界、`/readonly` 布局/实体回读校验及零 `.log` 泄漏；亦在 Antigravity 实测通过 `System Events` + 台前调度 `batch` 驱动 AutoCAD 桌面命令行。

## SKP → Blender 渲染用例

- **脚本自检**：运行 `python3 skills/cad-creator-mac/scripts/blender_render.py --self-test` 返回 `SELF_TEST_OK`。
- **实测模型**：已在 macOS 27.3（Apple M5）+ SketchUp 2026（26.0.428 / SU MCP Bridge 1.6.0）+ Blender 5.3.0 上以 374 MB 建筑组团实图完成闭环验证：
  - 通过 Bridge `127.0.0.1:9876` 执行 `export_for_render` 导出米制 OBJ（682 MiB / 4297 贴图 / 27568 继承材质面烘焙）与相机 JSON；
  - `blender_render.py` 用时 6.9s 导入 762 万面 / 4331 材质，自动启用 `METAL:Apple M5 (GPU - 8 cores)`、修复材质 `Kd` 与玻璃/水体粗糙度、配置 `SINGLE_SCATTERING` 物理天空与下半球背景填充并保存 `.blend`；
  - 验证默认视角、`--camera birdseye` 与 `--eye/--target` 自定义中庭视角 Cycles 渲染（1600px / 48–64 采样，约 10–18s 出图）及 `--info` 只读回读。
