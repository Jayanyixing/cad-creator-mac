# Blender 5.2+ / 5.3 核心 `bpy` 规范与避坑

用于编写或调试 Blender 实时 MCP（`execute_blender_code`）与后台脚本的核心规则（精炼自 `EL4CTEO/blender-skills` 并在 Blender 5.3.0 验证）。

## 1. 编写铁律（Headless 与中文界面兼容）

- **Data API 优先**：优先用 `bpy.data`、`bmesh`、`mesh.attributes` 与 `foreach_get/foreach_set`（NumPy）；避免依赖 3D 视口和选区的 `bpy.ops`。
- **无法绕开算子时用上下文覆盖**：
  ```python
  with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
      assert bpy.ops.object.modifier_apply(modifier="Weld") == {"FINISHED"}
  ```
- **Edit 模式隔离**：读 `ob.data` 或用 Data API 修改前先切回 `OBJECT` 模式；Edit 模式下需用 `bmesh.from_edit_mesh` + `bmesh.update_edit_mesh`。
- **按 `type` 查节点（防中文界面崩溃）**：永远用 `next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")`，**禁止用本地化 `n.name`（如 `"原理化 BSDF"`）**。插座用英文名或 `identifier`。
- **用 RNA 发现枚举**：遇到未知枚举值先查 `[i.identifier for i in obj.bl_rna.properties[prop].enum_items]`。

## 2. Blender 5.0–5.3 关键 API 变更速查

| 旧写法（4.x 及以前） | 5.2 / 5.3 正确写法 |
|---|---|
| `Collada (.dae)` 导入导出 | **5.0 已永久移除**；改用 `.obj` / `.glb` / 二进制 `.fbx` / `.usd` |
| `ShaderNodeTexSky.sky_type = "NISHITA"` | 改用 `"SINGLE_SCATTERING"` 或 `"MULTIPLE_SCATTERING"`；5.3 起 `sun_disc=True` 会发光（另加 Sun 灯需设 `sun_disc=False`） |
| `BLENDER_EEVEE_NEXT` | 改回 `BLENDER_EEVEE`；开光追设 `scene.eevee.use_raytracing = True` |
| `Principled BSDF` 的 `Specular` / `Transmission` | 5.x 为 `Specular IOR Level`、`Transmission Weight`、`Thin Wall`（单面建筑玻璃必开）、`Coat Weight`、`Subsurface Weight` |
| `mesh.use_auto_smooth` / `calc_normals_split()` | 已移除；用 `bpy.ops.object.shade_smooth_by_angle(angle=...)` 或 `mesh.corner_normals` |
| `World.use_nodes` / `Material.use_nodes` 无条件读取 | 新建后自带 `node_tree`；先判 `if obj.node_tree is None: obj.use_nodes = True` 避开 6.0 废弃警告 |
| `CompositorNodeComposite` | 5.0+ 无此节点；改用 `scene.compositing_node_group` + `NodeGroupOutput`（5.3 支持 `scene.compositor_effects`） |
| `scene["cycles"]` 字典下标访问 RNA 属性 | 5.0 起禁止，一律用点号属性（`scene.cycles`） |
| 数据贴图未改色彩空间 | 法线 / 粗糙度 / 金属度 / AO 贴图必须设 `image.colorspace_settings.name = "Non-Color"`；基色/自发光用 `"sRGB"` |

## 3. 常用核心片段与交付 QA 门禁

- **灯光与曝光准则**：
  - 建筑日景：物理天空（`SINGLE_SCATTERING`）+ 地平线下方中性背景填充（防止鸟瞰俯视全黑）；若另加 `SUN` 灯则关掉天空 `sun_disc`，Sun 强度通常 `3–10 W/m²` 配合 `AgX`；整体明暗优先调 `view_settings.exposure`。
  - 室内：主光 + 窗洞入口光（`light.cycles.is_portal = True`），`cycles.diffuse_bounces >= 4`；产品展示用大面积柔和面光（3 点布光）配 `Khronos PBR Neutral` 核对本色。
  - 焦距：建筑/室内 `24–35 mm`（保持竖直线垂直），自然视角 `50 mm`，产品特写 `85–135 mm`；按包围盒对角线收紧 `clip_start` / `clip_end`。
- **交付前 QA 核验（数值 + 视觉）**：
  1. 查缩放与法线：避免负缩放导致反面，必要时 `transform_apply(rotation=True, scale=True)` 与 `normals_make_consistent(inside=False)`；
  2. 查材质与贴图：无空材质槽/丢图，数据贴图色彩空间为 `Non-Color`；检查重面闪烁（z-fighting）；
  3. 视觉复核：Live 模式调 `look` 截图，Headless 模式用图片读取工具检查输出 PNG（构图、曝光、玻璃水体透光、阴影接触）。
