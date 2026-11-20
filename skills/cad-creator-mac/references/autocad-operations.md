# AutoLISP 与文件操作

## 命令行与脚本执行

macOS 完整版 AutoCAD 支持 `getvar`、`setvar`、`ssget`、`entget`、`handent`、`entmake` 和 `entmod` 等标准 AutoLISP 函数。COM、ActiveX 以及依赖它们的 `vla-*`、`vlax-*` 和 `vl-load-com` 属于 Windows 路径，不要在 macOS 上调用。

- **全局英文命令**：本地化界面可通过下划线前缀执行标准命令（如 `_.SAVEAS`、`_.PLOT`、`_.ZOOM`）。需要执行多条无交互原生命令时使用 `(command-s ...)`；若命令会触发文件或选项弹窗，先核对提示再响应。
- **单行 vs `.lsp` 脚本**：单步查询/小改直接通过剪贴板粘贴单行表达式；创建多图层、多视图、数十个实体及标注时，将代码写入工作目录的 `.lsp` 文件，再用 `(load "/abs/path/task.lsp")` 加载。受 `SECURELOAD` / `TRUSTEDPATHS` 约束时，在弹出的安全提示中按需确认或使用已信任路径。
- **`OSMODE` 捕捉防偏**：调用 `(command-s ...)` 传入坐标时，若用户开着对象捕捉（`OSMODE ≠ 0`），坐标会被吸附到邻近端点/圆心导致错位。脚本开头务必保存并临时归零 `OSMODE`（或在坐标前传 `"_non"`），结束时恢复原值；几何创建优先使用不受捕捉和当前图层影响的 `entmake`。

```lisp
(defun c:run_task (/ old_osmode)
  (setq old_osmode (getvar "OSMODE"))
  (setvar "OSMODE" 0)
  ;; ... 绘图与标注逻辑 ...
  (setvar "OSMODE" old_osmode)
  (princ)
)
```

## 读取与编辑

以下示例均可作为单行表达式粘贴。`INSUNITS` 是插入单位设置：`0` 为未指定，`1` 为英寸，`4` 为毫米。最终比例仍需核对用户尺寸或已有标注。

```lisp
(list (getvar "DWGPREFIX") (getvar "DWGNAME") (getvar "CTAB") (getvar "INSUNITS"))
(list (getvar "CLAYER") (tblsearch "LAYER" (getvar "CLAYER")))
((lambda (/ row names) (setq row (tblnext "LAYER" T)) (while row (setq names (cons (cdr (assoc 2 row)) names) row (tblnext "LAYER"))) (reverse names)))
((lambda (/ ss) (if (setq ss (ssget "_X" '((410 . "Model")))) (sslength ss) 0)))
(entget (handent "2A"))
```

将 `"2A"` 换成实际句柄。`ssget` 示例只统计模型空间顶层实体，块定义、嵌套实体与外参需单独检查。批量查询要控制命令历史输出量；需大量回读数据时，在工作目录写出本次任务专用的临时文本文件再读取核对。

在确认过的目标图上用 `entmake` 创建实体并立即按句柄回读（避免后续误把 `entlast` 当成同一对象）：

```lisp
(if (entmake '((0 . "CIRCLE") (8 . "OUTLINE") (10 24.0 18.0 0.0) (40 . 7.5))) (mapcar '(lambda (n) (assoc n (entget (entlast)))) '(0 5 8 10 40)))
```

## 图层、线型与中文字体（macOS 高频坑）

1. **公制线型加载**：公制图（`INSUNITS = 4`）加载 `DASHED`、`CENTER` 等非连续线型时应使用 `acadiso.lin`（英制 `acad.lin` 在毫米图里会密得像实线），并按图幅合理设置 `LTSCALE`（如 A3 1:1 图常用 `0.5`～`1.0`）：

```lisp
(if (not (tblsearch "LTYPE" "DASHED")) (command-s "_.-LINETYPE" "_L" "DASHED" "acadiso.lin" ""))
(if (not (tblsearch "LTYPE" "CENTER")) (command-s "_.-LINETYPE" "_L" "CENTER" "acadiso.lin" ""))
(setvar "LTSCALE" 1.0)
```

2. **图层与对象线宽**：用 `entmake` 建图层时，组码 `370` 以 **1/100 mm** 表示线宽（如 `35` = 0.35mm、`25` = 0.25mm、`18` = 0.18mm），组码 `62` 为 ACI 颜色索引（`7` 白/黑、`1` 红、`3` 绿、`4` 青、`5` 蓝）：

```lisp
(if (not (tblsearch "LAYER" "HIDDEN"))
  (entmake '((0 . "LAYER") (100 . "AcDbSymbolTableRecord") (100 . "AcDbLayerTableRecord")
             (2 . "HIDDEN") (70 . 0) (62 . 5) (6 . "DASHED") (370 . 18))))
```

3. **中文字体防乱码（`???`）**：macOS 版 AutoCAD 默认 `Standard` 文字样式使用 `txt.shx`，直接写中文标题栏或注释常显示为问号。含中文文字或标注时，新建或更新文字样式，指定 macOS 自带的中文 TrueType 字体（如 `PingFang SC`、`STHeiti` 或 `Songti SC`），并在标注样式中引用该文字样式。

## 打开、另存和打印

- **打开与样板**：打开后检查 `DWGPREFIX` 与 `DWGNAME`；开始页最近项同名时务必核对完整路径。新建公制图优先选用 `acadiso.dwt`。
- **另存 DWG/DXF**：`_.SAVEAS` 打开原生另存对话框。简体中文版的名称字段为 `saveAsNameTextField`，可通过 `setValue` 填写。确认目录（`where popup`）、文件类型（`fileType`）与文件名后再点 `OKButton`。保存 DXF 后重新核对活动图纸路径。若需命令行无弹窗保存，可临时设 `(setvar "FILEDIA" 0)` 执行 `(command-s "_.SAVEAS" ...)`，结束后**必须**立即恢复 `(setvar "FILEDIA" 1)`。
- **打印 PDF 与线宽层次**：用 `_.PLOT` 打印模型空间或指定布局。核对纸张（如 ISO A3）、横向/纵向、比例（如 1:1）、打印范围与居中；**务必勾选“打印对象线宽（Plot object lineweights）”**，并检查打印样式表（如 `monochrome.ctb`）未把线宽强制覆盖为单一粗细，确保轮廓粗实线与虚线/中心线/标注细线层次分明。
- **提交前双重复核**：
  - **视觉回检**：查看导出的 PDF 或截图，确认：① 几何修剪与相交无穿模/多余线段；② 中文无 `???` 乱码；③ 虚线/点划线和粗细线宽可见；④ 尺寸标注文字清晰，未与中心线、图框或轮廓重叠。
  - **数据回读**：以关键对象句柄或明确选择集重查几何数据；需重开验证时只关闭已保存目标文档，实体在重开后按预期读回才证明保存有效。

[Autodesk 的 AutoLISP 平台支持表](https://help.autodesk.com/cloudhelp/2027/ENU/AutoCAD-MAC-AutoLISP-Reference/files/GUID-1197B695-C73C-4B4D-AD5D-8F8EB64FB253.htm) · [AutoCAD for Mac 的 PDF 出图说明](https://help.autodesk.com/cloudhelp/2027/ENU/AutoCAD-MAC-Core/files/GUID-310657DF-8614-4125-B2E7-1FBF8B67333F.htm)
