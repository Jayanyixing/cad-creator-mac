# 可选：DXF 交付前验收与改动比对

需要可重复的二维验收或核对局部改图范围时启用。用已有、安装了 `ezdxf` 的 Python 运行 [dxf_qa.py](../scripts/dxf_qa.py)。脚本只读文本 DXF，在标准输出生成 JSON，不改图纸，不启动 AutoCAD。先用副本；报告不要覆盖输入文件。

## 1. 验收规则

先从已确认的底图、尺寸或任务书整理独立验收依据，不要从待验收结果反推期望值。用 CAD 查询取得稳定句柄（图元编号）；以下句柄是示例，需替换：

```json
{
  "units": 4,
  "checks": [
    {"kind":"count","type":"LINE","layer":"AXIS","expected":4},
    {"kind":"length","handle":"2F","expected":6000,"tolerance":0.1},
    {"kind":"closed","handle":"31","expected":true},
    {"kind":"dimension","handle":"30","expected":3000,"tolerance":0.1}
  ]
}
```

```sh
python3 /path/to/scripts/dxf_qa.py check delivery.dxf --rules rules.json > check-report.json
```

- `units` 是 DXF 的 INSUNITS（4 = 毫米）；长度和测量值使用模型单位。数值规则要求明确的正容差。若标注有正的比例系数（DIMLFAC），手填数字与换算后的尺寸比对，阈值在显示单位中使用同一个容差数字；需要分别设置两种容差时，请手动核验。
- 规则查模型空间：`count` 按类型与图层，`length` 查 LINE，`closed` 查多段线的闭合标志，`dimension` 查普通十进制线性/对齐标注的测量值与手填数字。原生测量占位符不算手填；复杂标注格式报待验收。闭合标志不证明边界无自交。

## 2. 同源改图比对

从同版基线保留改前 DXF，使用保持原图句柄和指纹的另存副本。事先确认允许变动的图元；新增图元的句柄从结果回读后再与批准范围核对，不要为了让报告通过而照抄所有差异。

```json
{"allow":[{"handle":"2F","operation":"modified"}]}
```

```sh
python3 /path/to/scripts/dxf_qa.py diff before.dxf after.dxf --policy allowed.json > diff-report.json
```

`allow` 可为空；支持 `added`、`removed`、`modified`。比对覆盖模型空间、布局内图元和块定义内的记录；不覆盖图层表、标注样式表、布局打印设置、外参文件及任意扩展对象。版本或文件指纹不一致时不猜测对应关系，报待验收。重新导出、重新编号或重建匿名标注块可能产生额外差异，须单独复核。

## 读报告

退出码：0 为所列检查通过，1 为发现不符，2 为输入有误或无法验证。报告含 DXF 与规则/范围文件的 SHA-256；图纸更新后重新跑，不能沿用旧报告。报告只覆盖已填写的规则和注明的比较范围，不替代 DWG 重开、最终 PDF 量测和视觉审查，也不证明建筑规范合规。
