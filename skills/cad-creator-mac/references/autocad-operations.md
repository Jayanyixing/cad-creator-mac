# AutoLISP 与文件操作

## 命令行

macOS 完整版 AutoCAD 支持 `getvar`、`ssget`、`entget`、`handent`、`entmake` 和 `entmod` 等 AutoLISP 函数。COM、ActiveX 以及依赖它们的 `vla-*`、`vlax-*` 和 `vl-load-com` 属于 Windows 路径。查看对应函数的 Autodesk 平台支持表。

本地化界面可通过全局英文命令名执行标准命令，例如 `_.SAVEAS`、`_.PLOT`。依次发送后续选项前查看当前提示。需要执行多条原生命令时，用 `(command-s ...)` 执行完整且无需交互的命令序列，或逐个处理实际弹出的提示。涉及 `SECURELOAD` 或 `TRUSTEDPATHS` 的文件加载受 AutoCAD 设置约束。短任务直接粘贴表达式，较长的脚本使用已授权的加载路径和 AutoCAD 的正常加载流程。

## 读取与编辑

以下示例均可作为单行表达式粘贴。`INSUNITS` 是插入单位设置，`0` 为未指定，`1` 为英寸，`4` 为毫米。最终比例还需要核对用户提供的尺寸或已有标注。

```lisp
(list (getvar "DWGPREFIX") (getvar "DWGNAME") (getvar "CTAB") (getvar "INSUNITS"))
(list (getvar "CLAYER") (tblsearch "LAYER" (getvar "CLAYER")))
((lambda (/ row names) (setq row (tblnext "LAYER" T)) (while row (setq names (cons (cdr (assoc 2 row)) names) row (tblnext "LAYER"))) (reverse names)))
((lambda (/ ss) (if (setq ss (ssget "_X" '((410 . "Model")))) (sslength ss) 0)))
(entget (handent "2A"))
```

换成实际读取的句柄。`ssget` 的示例只统计模型空间中的顶层实体。块定义、嵌套实体和外参需要单独检查。批量查询要控制命令历史的输出量。需要大量回读数据时，在授权的工作目录写入只属于本次任务的结果文件，并核对内容后再使用。

在确认过的测试图或获准编辑的目标图上，下面的例子创建一个圆并立即读回类型、句柄、圆心、半径。`entmake` 把图形实体建在当前空间，按需在 DXF 数据中指定图层。先确认图层存在、坐标系正确，并记下新对象的句柄。后续读回用该句柄，避免把当前 `entlast` 假定为同一对象。

```lisp
(if (entmake '((0 . "CIRCLE") (10 24.0 18.0 0.0) (40 . 7.5))) (mapcar '(lambda (n) (assoc n (entget (entlast)))) '(0 5 10 40)))
```

## 打开、另存和打印

- 打开文件后检查 `DWGPREFIX` 与 `DWGNAME`。开始页的最近使用项可打开同一工作文件，但同名时要看完整路径。对新任务选用和图纸单位相符的样板。
- `_.SAVEAS` 打开原生另存对话框。简体中文版的名称字段为 `saveAsNameTextField`，可通过 `setValue` 填写。检查 `where popup`、`fileType` 和名称后再点击 `OKButton`。DWG 或 DXF 的版本在文件类型处选择，保存 DXF 后重新核对活动图纸。
- PDF 用 `_.PLOT` 打印模型空间或选定布局。核对纸张、方向、比例、打印范围和样式，通过预览检查字体和裁切。需要多布局时使用原生发布流程。保存后验证实际 PDF 的页数和内容。
- 回读时以关键对象的句柄或明确的选择条件重查几何数据。有必要重开时，只关闭已保存的目标文档。文件已写入只能证明存在，实体能在重开后按预期读回才证明保存有效。

[Autodesk 的 AutoLISP 平台支持表](https://help.autodesk.com/cloudhelp/2024/ITA/AutoCAD-MAC-AutoLISP-Reference/files/GUID-1197B695-C73C-4B4D-AD5D-8F8EB64FB253.htm) · [AutoCAD for Mac 的 PDF 出图说明](https://help.autodesk.com/cloudhelp/2027/ENU/AutoCAD-MAC-Core/files/GUID-310657DF-8614-4125-B2E7-1FBF8B67333F.htm)
