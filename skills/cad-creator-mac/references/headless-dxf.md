# 用 cad-dxf MCP 无界面处理 DXF

`cad-dxf` 是 [id0o0bi/autocad-mcp](https://github.com/id0o0bi/autocad-mcp) 在 Codex 中建议使用的注册名。其他客户端可能使用不同名称，按 `drawing_run` 和 `drawing_summary` 识别工具。这个流程通过 ezdxf 处理文件，AutoCAD 桌面可关闭。上游的 `autocad_run_lisp` 和 `autocad_accoreconsole_switches` 面向 Windows Core Console；**macOS 版 AutoCAD 同样内置 `Contents/Helpers/AcCoreConsole.app/Contents/MacOS/AcCoreConsole`**，可无界面完成 DXF→DWG 转存与只读回读校验（见 [dxf_to_dwg.py](../scripts/dxf_to_dwg.py)）。

## 按文件工作

1. 新图确认实际单位、原点、尺寸和所需版本。旧图先用 `drawing_summary(path=绝对路径)` 读取版本、单位、图层和实体摘要，再按句柄、图层或几何条件限定修改范围。
2. 用 `drawing_run` 批量执行一段 Python。作用域已有 `doc`、`msp`、`ezdxf` 和 `emit`。`path` 为空时创建新图。编辑时 `path` 指向已有 DXF，`save_as` 指向约定的结果文件。仅查询时省略 `save_as`。默认新建 R2010；写入较旧版本前核对实体支持。`drawing_run` 可以执行 Python，只传当前任务需要的受控代码。
3. 保存后用新一次 `drawing_summary` 或查询调用读回结果。关键尺寸、坐标、孔径、闭合性和原生标注从保存后的数据求值。可用 `doc.audit()` 检查结构，若有错误或内存修复，先核对再决定是否保存修复结果。需要展示效果时，再按用途检查线宽、文字、裁切和显示比例。
4. 规则 DXF 交付原生 DWG 时，直接运行 `/usr/bin/python3 <skill_dir>/scripts/dxf_to_dwg.py <输入.dxf> <输出.dwg>`（自动用临时 ASCII 目录隔离中文/空格路径与 `.log`，不启动桌面 UI、不抢焦点、默认回读源图及输出 DWG，核对单位与布局名称，返回实体计数。回读通过后在目标磁盘原子替换 .dwg 文件）。已有复杂 DWG 编辑、原生 AutoCAD 三维或交互出图时再走桌面流程。

下面的 `code` 示例对应一张 120 × 80 mm 的板和四个 Ø10 mm 的孔。调用 `drawing_run` 时另传 `save_as` 为实际输出路径。

```python
doc.units = ezdxf.units.MM
for name in ("OUTLINE", "HOLES"):
    doc.layers.new(name)
msp.add_lwpolyline([(0, 0), (120, 0), (120, 80), (0, 80)], close=True,
                   dxfattribs={"layer": "OUTLINE"})
for x, y in [(20, 20), (100, 20), (20, 60), (100, 60)]:
    msp.add_circle((x, y), 5, dxfattribs={"layer": "HOLES"})
```

## 首次配置 MCP

如果客户端已经提供上述工具，可以直接使用。否则在一个用户可持久保存的目录下按上游方式安装。以下命令假定已经安装 `git`、`uv` 和 Codex CLI。

```bash
git clone https://github.com/id0o0bi/autocad-mcp.git
cd autocad-mcp
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
codex mcp add cad-dxf -- "$PWD/.venv/bin/python" "$PWD/server.py"
```

其他客户端可注册同一个 stdio 命令，填入虚拟环境 Python 和 `server.py` 的绝对路径。保留安装目录供客户端启动服务器。可用 `codex mcp get cad-dxf` 检查登记，再运行一个无保存的 `drawing_run`，例如 `emit(ezdxf.__version__)`，确认无界面后端响应。客户端没有 MCP 但能运行已有的 `ezdxf` 解释器时，也可对同一工作文件运行本地 Python 并采用相同的回读检查。
