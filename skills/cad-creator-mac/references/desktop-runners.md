# macOS 桌面操作

AutoCAD 2027 的 bundle ID 是 `com.autodesk.AutoCAD2027`。部分工具（如 `computer-use_cua`）可能把 `AutoCAD`/`com.autodesk.AutoCAD2027` 误匹配到 `AcQuickLookThumbnailer` 插件，或因台前调度（Stage Manager）收起窗口而漏列主进程：此时用 `osascript` / `System Events` 查 `process "AutoCAD"` 的 `window 1` 标题、窗口范围及 `AXIdentifier` 为 `"cmdInput"` / `"cmdHistory"` 的坐标与值（勿硬编码坐标，也勿遍历整棵功能区 AX 树，可按中下部坐标裁剪过滤）。

- **Codex** 使用 Computer Use。点击命令输入区，用 `paste` 保留 ASCII 引号和括号。另存面板里的文件名可用 `setValue` 写入，然后读回。
- **Hermes** 先加载 `computer-use`，用 `computer_use` 获取窗口和可访问性树，必要时用 `list_apps` 确认应用。用 `type` 输入，再核对 `cmdInput`；内容正确时用 `key` 发一次 `return`。另存面板可用 `set_value` 写入并回读文件名。改图时复用已核实的目标窗口，先用只读查询验证输入通路，再在同一窗口运行批量命令。
- **Gemini / Antigravity** 使用当前客户端可用的 macOS 桌面工具（无后台 AX 权限时配合 `System Events` 读窗口与 `cmdInput` 坐标）。实测在简体中文 AutoCAD 2027 中：**直接给 `cmdInput` 写 `AXValue` 不会提交到命令缓冲**，而聚焦不稳时发 **`Cmd+V` 会触发画布 `_pasteclip`**；应先确认目标窗口未遮挡（若被台前调度收起且确认 `window 1` 为目标图纸，在同一 `batch` 内依次“点击台前调度缩略图/窗口激活 -> 点击 `cmdInput` 实心坐标 -> `type_text` 注入 Unicode 命令（绕开中文输入法）-> `press_key` `return`”），不要把“激活窗口”和“点击输入”拆到两轮工具调用之间。安装后先试读 `(list (getvar "DWGNAME") (getvar "INSUNITS"))`。文档加载和真实 AutoCAD 调用分别记录。

若无法通过标题/AX 确认目标图纸、或用户正在前台交互导致焦点反复被抢，立即停止发送按键并请用户切到目标图纸后再继续。SolidCraft MCP 操作的是 SolidCraft 的独立建模引擎。
