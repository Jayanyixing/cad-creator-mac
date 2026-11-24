# SKP 到 Blender 导入与渲染控制

将 SketchUp 模型导出并在 macOS Blender（5.3+ / Apple Silicon Metal）中自动化配置相机、物理天空与 Cycles 渲染输出。

## 1. 从 SKP 导出中间文件

- **优先用 `sketchup` MCP 的 `export_for_render`**：在目标目录生成米制 Y-up `<name>.obj`、`.mtl`、贴图文件夹、`<name>_cameras.json`（场景相机）与 `<name>_lights.json`（`LT` 灯光），导出时临时将组/组件继承材质烘焙到面并在事务结束后回滚，不改动原 `.skp`。
- **未注册 `sketchup` MCP 但本机运行 SU MCP Bridge 时**：可向 `127.0.0.1:9876` 发送一行 JSON 请求（`{"id":1,"cmd":"export_for_render","params":{"folder":"...","name":"...","current_view":true}}`）；或直接在 SketchUp 桌面端 **文件 → 导出 → 三维模型** 导出 `.obj` / `.glb` / 二进制 `.fbx`。
- **避坑要点**：
  - **不要导出 `.dae`（Collada）**：Blender 5.0 起已永久移除原生 Collada 导入器。
  - SketchUp 导出 ASCII FBX 时 Blender 无法读取，手动导出优先选 `.obj`（勾选贴图、米制、三角化）或 `.glb`。
  - 大体量 `.skp`（如 300 MB+ 建筑组团）执行 `export_for_render` 可能耗时 3–5 分钟；使用 `sketchup` MCP 时需将 `SKETCHUP_MCP_TIMEOUT` 设至 `300–600` 秒。

## 2. 用 `blender_render.py` 控制 Blender 渲染

[blender_render.py](../scripts/blender_render.py) 自动定位 `/Applications/Blender.app/Contents/MacOS/Blender`（可用 `BLENDER_BIN` 覆盖）并无界面运行，支持 `.obj`、`.glb`/`.gltf`、`.fbx`、`.usd`/`.usdz` 与 `.blend`。

```bash
# 1) 首次导入 OBJ（自动读取 *_cameras.json / *_lights.json），保存 .blend 并用 Cycles Metal 出图
python3 <skill_dir>/scripts/blender_render.py "/path/to/model.obj" \
  --save-blend "/path/to/scene.blend" \
  -o "/path/to/render.png" \
  --samples 64 --width 1600

# 2) 基于已保存的 .blend 快速切换机位/日光重新渲染（免重读大 OBJ）
python3 <skill_dir>/scripts/blender_render.py "/path/to/scene.blend" \
  --camera birdseye -o "/path/to/birdseye.png" --samples 64 --width 1600

# 3) 自定义相机位置与朝向（单位：米）+ 太阳高度角/方位角
python3 <skill_dir>/scripts/blender_render.py "/path/to/scene.blend" \
  --eye "53,40,1.8" --target "25,51,5.0" --fov 46 \
  --sun-elevation 24 --sun-rotation 55 \
  -o "/path/to/courtyard.png" --samples 64 --width 1600
```

- **常用控制参数**：`--info`（只读统计网格/材质/相机/边界框）、`--camera <名称|auto|birdseye>`、`--engine CYCLES|BLENDER_EEVEE`、`--samples`、`--width` / `--height`、`--exposure`、`--sky-strength`、`--no-sky`。
- **内置修复与硬件适配**：自动开启 Apple Silicon `METAL` GPU 加速与降噪；将 OBJ `Kd` 从 sRGB 转为线性空间，把 SketchUp 默认 `Roughness=1.0` 调为建筑材质合理粗糙度，并为透明玻璃/水体设置低粗糙度与 `Thin Wall`；使用 Blender 5.x `ShaderNodeTexSky`（`SINGLE_SCATTERING`）并在世界着色器为地平线以下射线补中性灰背景，防止鸟瞰俯视背景全黑。
- **接力精修**：需要手动调整材质或构图时，直接用 `open -a Blender /path/to/scene.blend` 在桌面端继续编辑。

## 3. 验收核对

- 运行 `python3 <skill_dir>/scripts/blender_render.py --self-test` 校验纯 Python 解析与色彩转换逻辑。
- 核对脚本输出的 `BLENDER_OK:` JSON（对象/材质数、相机列表、`device` 是否命中 `METAL`、边界框与输出路径），并实际打开渲染 PNG 检查曝光、遮挡、材质透光与背景。
