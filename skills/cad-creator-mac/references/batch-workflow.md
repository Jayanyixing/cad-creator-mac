# 批量脚本与失败恢复

1. 确定目标和工作范围，从需求写下要新增或修改的对象、坐标、尺寸、图层及输出格式。对已有实体，进脚本前后按句柄回读。尺寸标注同时核对测量值和显示文字。
2. 在命令行查询 `(mapcar 'getvar '("DWGPREFIX" "DWGNAME" "CTAB" "TILEMODE" "CVPORT" "INSUNITS"))`，把前五项按实际值写入任务。`TILEMODE=1` 是模型标签。`TILEMODE=0` 时，`CVPORT=1` 是纸空间，其他有效视口编号表示在布局视口内编辑模型。单位依据图纸和已知尺寸核对。
3. 用 `(load "/实际绝对路径/batch-task.lsp")` 加载 [批量助手](../scripts/batch-task.lsp)。看到 `CADMAC helpers loaded.` 后再运行任务。自动化优先用当前已信任的脚本目录，AutoCAD 的安全加载提示按实际路径和来源核对。保持 `SECURELOAD` 与 `TRUSTEDPATHS` 原有设置。
4. 用 `cadmac:run` 执行一个本图纸、本空间内的非交互式修改。第三个参数只传实际需要临时改变的系统变量，例 `(("OSMODE" . 0) ("CMDECHO" . 0))`，无需更改则传 `nil`。`entmake` 不经过对象捕捉。命令方式可用 `"_non"` 对单个坐标关闭捕捉。任务代码对 `entmake` 返回 `nil` 等情况显式报失败，返回非空回执时包含已核对的句柄或测量结果。打开、切换空间、另存和打印在批量助手之外办理。

下面的示例只在确认的独立测试图里加一个圆。依现场回读填入上下文，确认 `OUTLINE` 图层存在。假定圆在世界 XY 平面，法向为 `(0 0 1)`。

```lisp
(cadmac:run
  '("/example/work/" "test.dwg" "Model" 1 2)
  '(lambda ()
     (if (and (tblsearch "LAYER" "OUTLINE")
              (entmake '((0 . "CIRCLE") (8 . "OUTLINE")
                         (10 24.0 18.0 0.0) (40 . 7.5))))
       (cdr (assoc 5 (entget (entlast))))))
  nil)
```

单行粘贴可直接执行。长任务另写 `.lsp`，其中定义自己的 `c:` 命令，加载文件后从空闲提示符显式调用该命令。经脚本输入中文时先读回一个已知汉字；若有转码问题，可用 ASCII 表达式配合 `chr` 和 `strcat` 构造文字，再查实体和最终 PDF。

- `CADMAC-OK` 带有任务回执。先核对预期对象再保存。
- `CADMAC-REFUSED` 表示上下文、命令空闲状态或撤销状态未满足。先核对现场再运行。
- `CADMAC-FAILED` 或 `CADMAC-ABORTED` 说明失败或取消，可能有部分几何已写入。先回读受影响的对象。只有确认本次已产生修改，而且助手建立的组仍是最近一次可撤销操作时，才用一次 `_.U` 恢复，并回读验证。空撤销组之后的 `_.U` 可能撤销之前的工作。
- `CADMAC-CLEANUP-FAILED` 会列出未恢复的变量、撤销组或已变化的文档上下文。先恢复正确上下文并检查现场。
- **熔断纪律**：同类失败连续发生 3 次，或出现坐标系/文档上下文错乱时停止盲目重跑，先检查根因再决定下一步。

坐标来自命令时按当前 UCS 解释。用 `(trans pt 0 1)` 把 WCS 点传给原生命令；直接读写实体时按实体类型使用对应的 WCS 或 OCS，遇到倾斜法向时先转换。已有布局、缩放和视图按任务需要保留。

[Autodesk 坐标转换说明](https://help.autodesk.com/cloudhelp/2027/ENU/AutoCAD-MAC-AutoLISP-Reference/files/GUID-1A316343-0B68-4DBE-8F49-B4D601CB8FCC.htm) · [Autodesk 撤销组说明](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-4481039B-77DA-4500-AE8B-3D2AD6951115.htm)
