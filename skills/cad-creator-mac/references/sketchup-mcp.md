# SketchUp MCP

在 macOS 上用 [2ez4gcx/sketchup-mcp](https://github.com/2ez4gcx/sketchup-mcp) 连接本机 SketchUp 桌面版。Codex 通过 stdio 启动 Node.js 服务，服务连接 `127.0.0.1:9876` 上的 SU MCP Bridge，由 SketchUp Ruby API 操作活动模型。桥的 TCP 接口没有身份验证，保持仅监听本机。

## 配置与连接

1. 先运行 `codex mcp get sketchup` 检查现有注册。需要新装时，从 [上游 Releases](https://github.com/2ez4gcx/sketchup-mcp/releases) 下载并解包 `.mcpb`，用 Node.js 18 或以上版本启动解包后的 `server/index.mjs`。注册时将下列路径替换为实际绝对路径。

   ```bash
   codex mcp add sketchup -- /path/to/node /path/to/sketchup-mcp/server/index.mjs
   ```

2. 在 SketchUp 中安装与服务同版的 SU MCP Bridge。可以在 MCP 中调用 `install_sketchup_bridge` 并用 `versions` 限定要接入的年份，也可以通过 SketchUp 扩展管理器安装发布包中的 `su_mcp-*.rbz`。安装后重启对应版本的 SketchUp。Codex 当前会话若还看不到新注册的工具，重新加载 MCP 配置或开启新会话。
3. 打开目标文件或按任务新建模型，再调用 `ping` 和 `model_info`。欢迎页出现时桥接端口可能还未监听。如果进入建模窗口后仍连不上，检查 **Extensions → SU MCP Bridge → Status**，按需启动桥。若同时打开多个 SketchUp 实例，以 `model_info` 返回的完整路径识别实际连接的模型。

## 建模与验收

1. 修改前通过 `model_info` 核对模型路径和修改状态；用户指定选择集时加查 `selection_info`。新建任务使用独立空白模型。开工时记下约定的可编辑交付格式及已知的目标 SketchUp 版本；涉及 Blender 时，先确定哪些模型改动也要写入 SKP。工具的长度输入为 mm，即使模型界面显示的单位不同。
2. 基本几何用 `create_box`、`create_shape` 或 `create_lines`。`create_room` 可根据室内边界生成墙板与地面，并按墙边位置、宽高和窗台标高切门窗洞与建门窗。用 `make_group` 组织对象，`set_material` 赋材质，`create_scenes` 建平面、立面或透视场景。引用对象时使用工具本次返回的 ID。专用工具无法表达的编辑可通过 `run_ruby` 调用原生 API，建模过程使用 MCP 或 Ruby API。
3. 新文件或副本使用 `save_model` 并传入尚不存在的 `.skp` 绝对路径。用户要求原位保存时，先核对活动模型的完整路径。保存后核对返回路径和实际文件，按任务回读场景、对象、尺寸或洞口，必要时用 `screenshot` 检查结果。
   - 交付分层平面场景时，按楼层组织墙、柱、家具群组或组件并设置标签，楼梯等跨层构件按设计决定在哪些场景可见。保存场景的标签可见性，从最终路径重开 SKP，逐层切换，核对本层构件和上下层遮挡，特别检查家具与结构。
   - 交付可编辑 SKP 时，在重开文件中选取一个本轮修改的构件，进入编辑上下文，核对尺寸、材质与贴图。涉及旧版交付时核对实际文件版本，记录用于回读的 SketchUp 版本及兼容性验证范围。
4. **交付 Blender 渲染**：调用 `export_for_render` 导出 OBJ/贴图与相机灯光 JSON 后，使用 [Blender 渲染指南](blender-render.md) 中的 `blender_render.py` 启用 Metal GPU 渲染；数百 MB 级大模型建议先设 `SKETCHUP_MCP_TIMEOUT=600`。

已用 SketchUp 2026（26.0.428）和 SU MCP Bridge 1.6.0 附带的 Node.js 服务实测房间墙板、门窗、实体方块、群组、材质、场景、视图截图及原生 SKP 保存与回读。
