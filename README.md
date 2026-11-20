# cad-creator-mac

通过 macOS 桌面操作工具和 AutoLISP 命令行控制 macOS 版 Autodesk AutoCAD。适合检查当前 DWG、读取图层与实体、批量绘图改图、另存 DWG/DXF 和打印 PDF，兼容 Codex、Antigravity 等支持 macOS 电脑操作的 Agent。

## 安装

- **Codex**：发送安装请求，或将 [skills/cad-creator-mac](skills/cad-creator-mac) 复制到 `~/.codex/skills/cad-creator-mac`：

> 安装这个 Skill https://github.com/Jayanyixing/cad-creator-mac/tree/main/skills/cad-creator-mac

- **Antigravity**：将 [skills/cad-creator-mac](skills/cad-creator-mac) 复制到 `~/.gemini/config/skills/cad-creator-mac`。

## 使用

打开 AutoCAD 后调用 `$cad-creator-mac`（或在对话中明确要求操作 AutoCAD）。可以先用下面这条指令读图：

> 用 $cad-creator-mac 检查当前 AutoCAD 图纸的文件名、单位和图层。

需要 macOS、AutoCAD 桌面版以及可用的桌面操作工具（如 Codex Computer Use 或 Antigravity `computer-use` MCP）。已在简体中文版 AutoCAD 2027 验证读取图纸、脚本化建模、另存 DWG、PDF 出图与重开回读。

## 许可证

[MIT](LICENSE)
