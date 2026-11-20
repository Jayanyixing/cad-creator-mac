# cad-creator-mac

通过 macOS 桌面工具和 AutoLISP 控制 Autodesk AutoCAD。可检查当前 DWG、读取实体、批量绘图修改、另存 DWG/DXF 和打印 PDF。

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

在 Codex 中调用 `$cad-creator-mac`，或在支持 Agent Skills 的客户端指定本技能。需要 macOS、AutoCAD 桌面版和可用的 macOS 桌面工具。先用下面的指令验证读取能力。

> 用 cad-creator-mac 检查当前 AutoCAD 图纸的文件名、单位和图层。

[批量脚本](skills/cad-creator-mac/references/batch-workflow.md) · [桌面操作](skills/cad-creator-mac/references/desktop-runners.md) · [可复现用例与验证记录](tests/smoke-test.md)

## 许可证

[MIT](LICENSE)
