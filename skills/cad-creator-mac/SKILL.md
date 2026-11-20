---
name: cad-creator-mac
description: 通过 macOS 桌面操作工具和 AutoLISP 命令行控制 Autodesk AutoCAD 桌面版。用于打开和检查当前 DWG、读取图层与实体、原生绘图和改图、另存 DWG/DXF 或导出/打印 PDF。适用于明确要操作 AutoCAD 的任务，兼容简体中文界面及 Codex、Antigravity 等各类 Agent。
---

# AutoCAD for Mac 控制

## 找到目标图纸

- 通过当前环境的 macOS 桌面操作工具取得并聚焦 AutoCAD 窗口。AutoCAD 2027 的 bundle ID 为 `com.autodesk.AutoCAD2027`，其他版本先列出运行中应用确认实际 bundle ID。开始页先打开目标文件或为新图选择与单位相符的样板（公制优先 `acadiso.dwt`）。
- 核对活动标签、窗口路径和模型空间或布局。涉及同名图纸、多个窗口或改图时，用 `(list (getvar "DWGPREFIX") (getvar "DWGNAME") (getvar "CTAB") (getvar "INSUNITS"))` 回读。路径冲突或弹窗遮挡时先解决实际问题，再发命令。
- 按用户要求操作当前图纸。需要保留原件或用户指定另存时，用 AutoCAD 建立副本并确认切换到了该副本。用户要求保存回当前图纸时，核对原路径后按要求保存。

## 执行和验证

1. 在可访问性树中找 `cmdInput`（位于 `commandPane`），点击输入区并确认命令提示符空闲。若 AutoCAD 正在执行命令或等待选择，先判断其状态，避免盲发 Esc 或 Enter。
2. 短查询或单步修改：通过剪贴板粘贴（`paste` 或 `pbcopy` + `Cmd+V`）原样贴入一条命令或完整单行 AutoLISP 表达式，核对 `cmdInput` 文字和焦点后再按一次 `Return`。空输入框按 `Return` 会重复上一条命令；禁止依赖中文输入法逐字键入，以免改写 ASCII 引号和括号。
3. 复杂或多实体成图：不要逐行粘贴，改为写入本地 `.lsp` 脚本，在脚本内临时归零并最终恢复 `OSMODE`（避免对象捕捉吸偏坐标），再通过 `(load "/绝对路径/task.lsp")` 一次执行。
4. 从 `cmdHistory` 或可见提示符读取结果。遇到安全加载（`SECURELOAD`）或文件对话框则在当前窗口内处理。若输出不明，先用只读表达式判断动作是否已生效，再决定是否重试；面板/菜单切换后需重新定位 UI 元素。
5. 按图纸单位、空间和图层执行要求：几何实体优先用 Mac 支持的 `entmake` 或带 `_` 前缀的全局英文命令；修改特定对象前先核对句柄、类型和图层；发现异常时先排查已生成的对象，避免重跑造成重复实体。
6. 保存与视觉闭环：保存后核对实际路径和格式；导出 PDF 或截图后必须看图核对——确认几何修剪准确、中文无乱码、虚线/中心线与粗细线宽层次清晰、尺寸标注不与中心线或轮廓线重叠；需提交 DWG 时重开回读关键实体后再汇报验证范围。

读取图层与实体、编写防踩坑 AutoLISP 脚本（`OSMODE`、公制线型、中文字体）或打印/另存文件时，按需参考 [AutoLISP 与文件操作](references/autocad-operations.md)。
