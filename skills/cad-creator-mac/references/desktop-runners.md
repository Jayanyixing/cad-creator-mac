# macOS 桌面操作

AutoCAD 2027 的 bundle ID 是 `com.autodesk.AutoCAD2027`。其他版本从工具的应用列表确认实际应用。先确认活动标签或窗口路径，再面向该窗口发送事件。`cmdInput`、`cmdHistory`、`saveAsNameTextField` 和 `OKButton` 是简体中文 AutoCAD 2027 上观察到的 AX 标识，具体元素编号以当前捕获为准。

- **Codex** 使用 Computer Use。点击命令输入区，用 `paste` 保留 ASCII 引号和括号。另存面板里的文件名可用 `setValue` 写入，然后读回。
- **Hermes** 先加载 `computer-use`，用 `computer_use` 获取窗口和可访问性树，必要时用 `list_apps` 确认应用。用 `type` 输入，再核对 `cmdInput`；内容正确时用 `key` 发一次 `return`。另存面板可用 `set_value` 写入并回读文件名。
- **Gemini / Antigravity** 使用当前客户端可用的 macOS 桌面工具。最小能力包括定位窗口、获取状态、原样输入、按键和读取结果。安装后先试读 `(list (getvar "DWGNAME") (getvar "INSUNITS"))`。文档加载和真实 AutoCAD 调用分别记录。

如果截图只有舞台管理的倾斜缩略图，或窗口状态无法确认焦点，停止发键并请用户切到目标图纸。SolidCraft MCP 操作的是 SolidCraft 的独立建模引擎。
