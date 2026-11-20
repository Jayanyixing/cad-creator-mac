# cad-creator-mac

在 macOS 上优先使用 `cad-dxf` MCP 和 ezdxf 无界面生成、编辑和回读 DXF。需要原生 DWG、AutoCAD 三维或原生打印时，通过桌面工具和 AutoLISP 操作 AutoCAD。

## 安装

从 GitHub 复制 [skills/cad-creator-mac](skills/cad-creator-mac) 到对应技能目录。

| 客户端 | 用户级目录 |
| --- | --- |
| Codex | `~/.codex/skills/` |
| Google Antigravity | `~/.gemini/config/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| Hermes | `~/.hermes/skills/` |

也可以在 Codex 里发出这条安装请求。

> 安装这个 Skill https://github.com/Jayanyixing/cad-creator-mac/tree/main/skills/cad-creator-mac

## 使用

在 Codex 中调用 `$cad-creator-mac`，或在支持 Agent Skills 的客户端指定本技能。常规 DXF 使用 [cad-dxf MCP 操作与安装指南](skills/cad-creator-mac/references/headless-dxf.md)。原生操作需要安装 AutoCAD 桌面版，并提供可用的 macOS 桌面操作工具。

> 用 cad-creator-mac 无界面画一块 120 × 80 mm 的板，四角各一个 Ø10 mm 孔，生成 DXF 后回读。

[批量脚本](skills/cad-creator-mac/references/batch-workflow.md) · [桌面操作](skills/cad-creator-mac/references/desktop-runners.md) · [可复现用例与验证记录](tests/smoke-test.md)

## 许可证

[MIT](LICENSE)
