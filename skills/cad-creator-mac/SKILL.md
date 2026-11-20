---
name: cad-creator-mac
description: 通过 macOS 桌面操作和 AutoLISP 控制 Autodesk AutoCAD。用于打开或检查 DWG、查询图层和实体、原生绘图改图、另存 DWG/DXF 或打印 PDF。适用于明确要操作 AutoCAD 的任务。
license: MIT
---

# AutoCAD for Mac 控制

## 确定目标

- 用 [桌面操作指南](references/desktop-runners.md) 聚焦 AutoCAD。2027 版 bundle ID 是 `com.autodesk.AutoCAD2027`。开始页先打开目标文件，或为新图选择符合单位的样板。
- 修改前回读完整文件路径、`CTAB`、`TILEMODE`、`CVPORT` 和 `INSUNITS`。布局标签内也可能在编辑视口中的模型。确认图面实际单位、WCS/UCS 和目标对象，再决定绘制或修改范围。
- 按用户要求原位更新、另存或建立副本。局部改图沿用原图标准，保留无关图层、布局、块、外参和样式。先从需求记下关键几何、实体类型、语义图层及输出格式作为验收依据。

## 执行和验证

1. 从可访问性树定位 `commandPane` 下的 `cmdInput`。确认目标窗口和提示符空闲，用当前工具原样输入一条命令或完整单行表达式，核对文本与焦点，再按一次 `Return`。空输入框上的 `Return` 可能重复上一条命令。
2. 简单操作可直接用 AutoLISP。多实体修改按 [批量脚本与失败恢复](references/batch-workflow.md) 先加载助手，再执行本次任务。脚本写入前核对上下文，记录返回结果，恢复临时变量，并将本次操作放入一个撤销组。
3. 用 `cmdHistory` 或可见提示符核对执行结果。发生弹窗、切换文档或命令结果不明时，刷新窗口状态并先读回已有改动，再决定是否重试。无法聚焦确切图纸时保留当前证据，暂停发送命令。
4. 按 [AutoLISP 与文件操作](references/autocad-operations.md) 保存并验证。DWG/DXF 重开后核对关键坐标、尺寸、空间、图层和原生实体类型。PDF 检查同版实际页面、图幅、比例、字体、线型、线宽和裁切。汇报实际完成的检查与交付文件。
