---
name: autocad-mac-control
description: 通过 Codex 电脑操作和 AutoLISP 控制 macOS 上的 Autodesk AutoCAD 桌面版。用于打开和检查当前 DWG、读取图层与实体、原生绘图和改图、另存 DWG/DXF 或从指定布局打印 PDF。适用于明确要操作 AutoCAD 的任务，兼容简体中文界面。
---

# AutoCAD for Mac 控制

## 找到目标图纸

- 用 Codex 的电脑操作工具取得 AutoCAD 窗口。AutoCAD 2027 的 bundle ID 为 `com.autodesk.AutoCAD2027`。其他版本用电脑操作工具发现实际应用。开始页先打开目标文件或为新图选择样板。
- 核对活动标签、窗口路径和模型空间或布局。涉及同名图纸、多个窗口或改图时，用 `(list (getvar "DWGPREFIX") (getvar "DWGNAME") (getvar "CTAB") (getvar "INSUNITS"))` 回读。路径冲突或弹窗遮挡时先解决实际问题，再发命令。
- 按用户要求操作当前图纸。需要保留原件或用户指定另存时，用 AutoCAD 建立副本并确认切换到了该副本。用户要求保存回当前图纸时，核对原路径后按要求保存。

## 执行和验证

1. 在当前可访问性树中找 `cmdInput`，位于 `commandPane`。点击输入区并确认命令提示符可用。若 AutoCAD 正在执行用户的命令或等待选择，先判断其状态，避免盲发 Esc 或 Enter。
2. 用电脑操作的 `paste` 原样贴入一条命令或一个完整的单行 AutoLISP 表达式。核对 `cmdInput` 中的文字和焦点，再按一次 `Return`。空输入框上的 `Return` 可能重复上一条命令。原样粘贴能保留 ASCII 引号和括号，避免中文输入法改写表达式。
3. 从 `cmdHistory` 或可见的提示符读取结果。遇到文件对话框则在当前窗口内操作。若输出不明，先用只读表达式判断动作是否已经生效，再决定是否重试。面板和菜单发生切换后重新定位元素，元素编号会变化。
4. 按图纸现有单位、空间和图层执行用户要求。原生实体优先用 Mac 支持的 AutoLISP 函数或 AutoCAD 自带命令。修改具体对象前核对句柄、实体类型和图层。发现异常时检查已经完成的改动，避免重跑造成重复实体。
5. 保存后核对实际路径和格式。需要提交文件时，重新打开成果检查受影响的实体、尺寸或布局，并以读到的结果报告验证范围。

读取图层与实体、构造安全的 AutoLISP 表达式或输出文件时，按需参考 [AutoLISP 与文件操作](references/autocad-operations.md)。
