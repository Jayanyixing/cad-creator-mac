# SKP 到 Blender 导入、实时 MCP 控制与渲染

支持两套无缝衔接的执行方式：**Live 实时操控桌面 Blender（`blender` MCP）** 与 **无界面后台出图（`blender_render.py`）**。Blender 5.x `bpy` 语法避坑与灯光/QA 门禁见 [Blender 5.x 核心规范](blender-5x-core.md)。

## 1. 本地 MCP 环境与防冲突配置

- **端口分配（关键）**：SketchUp `su_mcp` 默认监听 `127.0.0.1:9876`，`mcp-for-blender` 默认也是 `9876`。为使 SketchUp 与 Blender 同时运行不冲突，本机配置 **SketchUp 保持 `9876`，Blender MCP 固定使用 `9877`**：
  - Blender 插件：`~/Library/Application Support/Blender/5.3/scripts/addons/blender_mcp.py`（由 `uvx mcp-for-blender install-addon` 安装并已在偏好设置启用，默认端口设为 `9877`）。
  - 客户端 MCP 注册（Codex `~/.codex/config.toml`、Claude Code `~/.claude.json`、Antigravity `~/.gemini/config/mcp_config.json`）：使用 `/Users/yixing/.local/bin/uvx mcp-for-blender --port 9877`（`BLENDER_PORT=9877`），Codex 设 `tool_timeout_sec = 600`。
  - 若后续运行 `uvx mcp-for-blender update` 重置了插件默认端口，在桌面 Blender 右侧 `N` 面板 **MCP for Blender** 将 Port 改回 `9877` 即可。

## 2. 从 SKP 导出中间文件

- **优先用 `sketchup` MCP 的 `export_for_render`**：在目标目录生成米制 Y-up `<name>.obj`、`.mtl`、贴图文件夹、`<name>_cameras.json` 与 `<name>_lights.json`（临时将组/组件继承材质烘焙到面后回滚，不改原 `.skp`）。
- **未注册 `sketchup` MCP 但运行 SU MCP Bridge 时**：向 `127.0.0.1:9876` 发 `export_for_render` JSON 行请求；也可在 SketchUp 桌面端 **文件 → 导出 → 三维模型** 导出 `.obj` / `.glb` / 二进制 `.fbx`。
- **避坑要点**：
  - **不要导出 `.dae`（Collada）**：Blender 5.0 起已永久移除原生 Collada 导入器；SketchUp ASCII FBX 亦无法在 Blender 读取。
  - 数百 MB 级大模型（如 300 MB+ 建筑组团）导出 OBJ 耗时 3–5 分钟，须将 `SKETCHUP_MCP_TIMEOUT` 设至 `300–600` 秒。

## 3. 路由：Live MCP 控制 vs 无界面脚本

| 场景 | 首选路线 | 说明 |
|---|---|---|
| 需要实时看桌面 Blender 视口、交互调相机/灯光/材质 | **Live MCP**（`blender` MCP） | 先确认 Blender 已打开且监听 `9877`；用 `get_scene_info` / `execute_blender_code` / `look` 操作并看图 |
| 大体量 OBJ 初次导入、批量多机位出图、无人值守后台渲染 | **无界面 CLI**（[blender_render.py](../scripts/blender_render.py)） | 自动启用 Apple Silicon `METAL` GPU Cycles、修补 OBJ 材质、保存 `.blend` 并输出 PNG |

- **Live MCP 调用共享脚本（推荐，零重复代码）**：在 `execute_blender_code` 内可直接导入 `blender_render` 把模型拉进当前桌面窗口，或实时调当前打开的场景：
  ```python
  import sys; sys.path.insert(0, "/Users/yixing/.codex/skills/cad-creator-mac/scripts")
  import blender_render
  # 导入到当前桌面窗口并保存 .blend：
  blender_render.run("/path/to/model.obj", save_blend="/path/to/scene.blend")
  # 或直接对桌面已打开场景切换鸟瞰/调日光并渲染：
  blender_render.run(camera="birdseye", sun_elevation=24, output="/path/to/out.png")
  ```
  每次 `execute_blender_code` 都在新命名空间执行，按需 `import`；改过脚本文件后加 `importlib.reload(blender_render)`；调 `look` 检查视口结果。

## 4. 无界面控制命令（`blender_render.py`）

支持 `.obj`（自动读同目录 `*_cameras.json` / `*_lights.json`、修补 `Kd` sRGB→线性色值、修正 `Roughness=1.0` 与透明玻璃/水体 `Thin Wall`）、`.glb`/`.gltf`、`.fbx`、`.usd`/`.usdz` 与 `.blend`：

```bash
# 1) 首次导入 OBJ，保存 .blend 并用 Cycles Metal GPU 出图
python3 <skill_dir>/scripts/blender_render.py "/path/to/model.obj" \
  --save-blend "/path/to/scene.blend" -o "/path/to/render.png" --samples 64 --width 1600

# 2) 基于 .blend 快速切换机位/日光/引擎出图（免重读大 OBJ）
python3 <skill_dir>/scripts/blender_render.py "/path/to/scene.blend" \
  --camera birdseye -o "/path/to/birdseye.png" --samples 64 --width 1600

python3 <skill_dir>/scripts/blender_render.py "/path/to/scene.blend" \
  --eye "53,40,1.8" --target "25,51,5.0" --fov 46 \
  --sun-elevation 24 --sun-rotation 55 -o "/path/to/courtyard.png" --samples 64 --width 1600
```

- 常用参数：`--info`、`--camera <名称|auto|birdseye>`、`--engine CYCLES|BLENDER_EEVEE`、`--samples`、`--width` / `--height`、`--exposure`、`--sky-strength`、`--no-sky`。
- 若需桌面人工继续调整，运行 `open -a Blender /path/to/scene.blend`；Blender 打开后 MCP `9877` 会自动连上。

## 5. 验收核对

- 自检：`python3 <skill_dir>/scripts/blender_render.py --self-test` 返回 `SELF_TEST_OK`。
- 数据回读：核对 `BLENDER_OK:` JSON（网格/材质/相机/边界框/是否命中 `METAL`）或 Live `get_scene_info`。
- 视觉检查：Live 模式用 `look`，无界面出图直接看 PNG，按 [Blender 5.x 核心规范](blender-5x-core.md) 核查曝光、构图、法线、贴图与背景。
