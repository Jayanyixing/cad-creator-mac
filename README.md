# cad-creator-mac

通过 Codex 的电脑操作和 AutoLISP 命令行控制 macOS 版 Autodesk AutoCAD。适合检查当前 DWG、读取图层与实体、绘图改图和另存图纸。

## 安装

在 Codex 中发送下面这条安装请求。

> 安装这个 Skill https://github.com/Jayanyixing/cad-creator-mac/tree/main/skills/cad-creator-mac

也可以把 [skills/cad-creator-mac](skills/cad-creator-mac) 整个目录复制到个人技能目录 `~/.codex/skills/`。

## 使用

打开 AutoCAD 后，在 Codex 中调用 `$cad-creator-mac`。可以先用下面这条指令读图。

> 用 $cad-creator-mac 检查当前 AutoCAD 图纸的文件名、单位和图层。

需要 macOS、AutoCAD 桌面版以及可用的 Codex 电脑操作工具。已在简体中文版 AutoCAD 2027 验证读取图纸、创建圆、另存 DWG 与重开回读。

## 许可证

[MIT](LICENSE)
