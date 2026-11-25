# AutoLISP 与文件操作

## 读取和写入实体

Mac 版 AutoCAD 支持 `getvar`、`ssget`、`entget`、`handent`、`entmake` 和 `entmod`。本地化界面可执行 `_.SAVEAS`、`_.PLOT` 等全局英文命令。`command-s` 适用于参数齐全、可一次完成的命令。交互命令按实际提示输入。COM 和 ActiveX 自动化适用于 Windows。

```lisp
(mapcar 'getvar '("DWGPREFIX" "DWGNAME" "CTAB" "TILEMODE" "CVPORT" "INSUNITS"))
((lambda (/ row names) (setq row (tblnext "LAYER" T)) (while row (setq names (cons (cdr (assoc 2 row)) names) row (tblnext "LAYER"))) (reverse names)))
((lambda (/ ss) (if (setq ss (ssget "_X" '((410 . "Model")))) (sslength ss) 0)))
((lambda (/ entity) (if (setq entity (handent "2A")) (entget entity))))
```

替换示例句柄。`ssget` 查询模型空间顶层实体，嵌套块、属性和外参按所需范围单独检查。`INSUNITS` 的 `0`、`1`、`4` 分别表示未指定、英寸和毫米。插入单位要结合实际图面或已知尺寸核对。创建对象时明确图层、坐标系和空间。先用 `tblsearch` 核对现有图层，避免拼错图层名后被 `entmake` 自动建层。写入后记下新对象的句柄，用于独立回读。

新建规则二维图且本机已有 `ezdxf` 时，可以程序化生成并审计 DXF。优先使用原生圆、多段线、文字和标注，随后**优先用无界面脚本 [dxf_to_dwg.py](../scripts/dxf_to_dwg.py)**（通过 `AcCoreConsole` 原生另存并自动只读回读校验）生成 DWG；已有 DWG 的局部修改优先保留原有图层、布局、块、外参和编辑语义。

## 图层、线型和中文标注

- 公制图缺少所需线型时，先检查 `(findfile "acadiso.lin")`，并用 `tblsearch` 查重后再加载（避免对已加载线型或重名文字/标注样式重复新增触发报错）。线宽组码 `370` 以百分之一毫米计，例如 `35` 表示 0.35 mm、`50` 表示 0.50 mm。沿用既有图纸和模板的线宽及图层标准。
- 无交互脚本中**避免盲目发送 `_AUDIT _Y`、`_PURGE _A _* _N` 或空图上的 `_ERASE _ALL`**——遇到错误时 `_AUDIT` 会追加“写审计报告文件?”提示、空图 `_ERASE` 会停在“选择对象:”提示导致命令流挂起。需审计或清理时只在交互确认提示下执行，或通过 DXF 后端 `doc.audit()` 检查。
- 线型显示异常时检查对象线型比例、`LTSCALE`，以及模型或布局相关的 `MSLTSCALE`、`PSLTSCALE` 和视口比例。只在任务需要时调整全图变量，并看实际打印效果。
- 含中文时检查实际文字样式和可用字体。将文字样式与标注样式统一绑定到同一套支持中文的 TrueType 字体（如 `Arial Unicode MS`、`PingFang SC`），避免 SHX 英文/数字与 TrueType 中文混排导致粗细不均或 PDF 数字不可检索。检查最终 PDF 的中文、尺寸符号和线型。原生半径/直径标注用系统测量值，占位符 `<>` 保留测量文字。多孔可用 `4×<>`，检查最终直径符号是否只出现一次。外置径向标注可在测试副本里核对 `DIMTOFL` 的效果。

## 另存和出图

- **DXF → DWG 优先走无界面 `AcCoreConsole`**：执行 `python3 <skill_dir>/scripts/dxf_to_dwg.py <输入.dxf> <输出.dwg> [--version 2018]`。脚本会在临时纯 ASCII 目录内中转 `_.SAVEAS` 并隔离 `LogFilePath` 日志，再以 `/readonly` 模式重开校验 `INSUNITS`、实体数与 `ACAD_LAYOUT` 列表，彻底规避中文/空格路径、覆盖确认弹窗、桌面抢焦点与跨目录 `.log` 污染。仅当本机无 `AcCoreConsole` 或已在桌面交互改图时，才在命令栏执行单行 `(command "_.SAVEAS" "2018" "/绝对路径/目标.dwg")`（AutoLISP `command` 会抑制文件对话框；目标已存在需先删或确认覆盖），完成后核对 `cmdHistory`、`file <目标.dwg>` 并关图清理 `.dwl/.dwl2` 与无关 `.log`。
- 用 `_.PLOT` 打印目标布局或模型，按用户要求核对纸张、方向、范围、比例、页面预设和 CTB/STB；打印到本轮可识别的输出路径，等待打印完成并确认新 PDF 可打开。macOS 自动化流程须能在 `BACKGROUNDPLOT` 不可写时完成打印。检查打印线宽选项与样式是否符合图纸标准。保存后打开同版 PDF，逐项查看裁切、字体一致性、线宽对比、虚线/中心线、标注重叠，以及剖视图中剖切面后方的可见轮廓线（如孔腔后壁上下口与台阶线）是否完整连通。
- 保存后重新打开目标 DWG/DXF，按要求核对关键几何、实体类型、图层、空间和布局。保留最终交付所需的外参和字体依赖。交付 DWG 时，从最终路径在 AutoCAD 中重开，先观察原始首屏，再平移或缩放。布局交付应打开约定布局，看清图框及主要视图；模型空间交付应直接看见目标主体。若只见空白或小点，核对当前空间、保存视图中心和范围，调整纸空间视图时保留布局视口的设计比例，保存后再重开检查。仅做无界面回读时，将实际首屏列为未核实。记录交付路径、实际验收结果及待核事项。

[AutoLISP 实体支持表](https://help.autodesk.com/cloudhelp/2027/ENU/AutoCAD-MAC-AutoLISP-Reference/files/GUID-1197B695-C73C-4B4D-AD5D-8F8EB64FB253.htm) · [AutoCAD for Mac PDF 出图](https://help.autodesk.com/cloudhelp/2027/ENU/AutoCAD-MAC-Core/files/GUID-310657DF-8614-4125-B2E7-1FBF8B67333F.htm)
