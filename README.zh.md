# 🍜🥢 乌冬・荞麦百名店地图 2017-2025

🌐 **Language:** [日本語](README.md) | [English](README.en.md) | **中文**

这是一个基于公开的“乌冬・荞麦百名店”相关信息，由个人整理制作的非官方参考地图。
你可以在地图上浏览乌冬和荞麦店，按类别、年份、地区、都道府县、入选次数、距离和访问状态筛选，也可以通过静态推荐标签寻找相近的店。
本项目与 Tabelog、Kakaku.com、Tabelog 百名店没有任何合作、赞助或认可关系。

🔗 **公开地址**: [https://miitarou.github.io/udon-hyakumeiten-map/](https://miitarou.github.io/udon-hyakumeiten-map/)

![Udon](https://img.shields.io/badge/Udon-428-D4A853)
![Soba](https://img.shields.io/badge/Soba-266-7B9E6B)
![Total](https://img.shields.io/badge/Total-694-555555)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 功能

### 🗂️ 类别切换
- **ALL / 🍜 乌冬 / 🥢 荞麦**：可在页面顶部快速切换。
- **类别标记**：标记颜色用于区分乌冬和荞麦，入选次数和殿堂级显示通过尺寸与视觉效果表达。
- **自定义图标**：乌冬和荞麦使用不同的应用内图标。

### 🗺️ 地图
- **694家店铺**：使用 Leaflet.js 与 MarkerCluster 进行地图显示。
- **入选次数强调**：类别内入选次数排名前约10%的店铺以“殿堂级”视觉样式显示。
- **店名标签**：当单个标记显示时自动显示店名。
- **当前位置**：可查找当前位置附近的店铺。位置信息不会发送或保存到服务器。

### 🔍 搜索与筛选
- **EAST / WEST / KAGAWA**：乌冬支持 KAGAWA 分类。
- **店名、地址、车站搜索**：支持部分假名差异和轻微输入错误的吸收。
- **都道府县、年份、入选次数筛选**。
- **半径搜索**：可从当前位置或地图点击点开始搜索。
- **访问状态**：可在浏览器本地保存“想去”和“已访问”，并支持 JSON 设置保存/恢复。
- **如果喜欢这家店**：根据静态 AI 推定标签显示相似或附近候选。

访问状态只保存在浏览器 `localStorage` 中，不会发送到服务器。
更换浏览器/设备或删除网站数据时可能会丢失，请根据需要使用设置保存功能。

### 🎨 设计
- 深色玻璃质感 UI。
- 桌面端侧边栏与移动端底部抽屉。
- 桌面端面板宽度可调整。
- 支持 PWA、Service Worker 缓存、更新通知和离线提示。

## 🚀 本地运行

```bash
python3 -m http.server 8080
open http://localhost:8080
```

## 📁 项目结构

```text
├── index.html
├── style.css
├── app.js
├── manifest.webmanifest
├── sw.js
├── privacy.html
├── docs/
│   ├── recommendation-tags.md
│   ├── external-signals.md
│   ├── update-guide.md
│   └── app-architecture.md
├── data/
│   ├── udon.json
│   ├── soba.json
│   ├── recommendation_tags.json
│   ├── recommendation_golden_set.json
│   ├── external_source_registry.json
│   ├── external_source_review_log.json
│   ├── external_signals.json
│   └── external_signal_backlog.json
├── scripts/
│   ├── check_data_quality.py
│   ├── generate_data_version.py
│   ├── generate_external_signal_backlog.py
│   ├── generate_external_signals.py
│   ├── generate_recommendation_tags.py
│   └── evaluate_recommendations.py
├── mobile/
├── LICENSE
├── DATA_LICENSE.md
├── README.md
├── README.en.md
└── README.zh.md
```

## 🛠️ 技术栈

| 类别 | 技术 |
| --- | --- |
| 地图 | [Leaflet.js](https://leafletjs.com/) |
| 标记聚合 | [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) |
| 地图瓦片 | [日本国土地理院地理院瓦片](https://maps.gsi.go.jp/development/ichiran.html) |
| 字体 | Noto Sans JP, Outfit |
| 托管 | GitHub Pages |

Leaflet 与 Leaflet.markercluster 的 CDN 资源使用 Subresource Integrity (SRI)。

## 📊 数据

本网站是基于公开信息整理的非官方参考地图。
坐标由地址和店铺页面等推定，可能存在误差。

“殿堂级”不是官方称号。在本应用中，它表示各类别中入选次数约前10%的店铺。

### 乌冬
- 年份：2017-2024
- 店铺数：428
- 区域：EAST 212 / WEST 111 / KAGAWA 105

### 荞麦
- 年份：2017-2025
- 店铺数：266
- 区域：EAST 157 / WEST 109

### 推荐标签

`data/recommendation_tags.json` 用于“如果喜欢这家店”的推荐功能。
它将类别、地区、入选历史等事实标签，与保守推定的探索辅助标签分开保存。
推定标签不是对店铺事实的断言，而是用于计算店铺之间相似度的辅助信号。

评分设计和外部信号方针见 [docs/recommendation-tags.md](docs/recommendation-tags.md) 与 [docs/external-signals.md](docs/external-signals.md)。

## 🧪 数据验证

```bash
python3 scripts/generate_data_version.py
python3 scripts/generate_external_signal_backlog.py
python3 scripts/generate_external_signals.py
python3 scripts/generate_recommendation_tags.py
python3 scripts/check_data_quality.py
python3 scripts/evaluate_recommendations.py
```

完整更新流程见 [docs/update-guide.md](docs/update-guide.md)。

## 📱 iPhone App

`mobile/` 目录包含基于 Capacitor 的 iOS 包装项目。
Web 版是唯一的主要来源。HTML/CSS/JS 的变更通过 App Store 更新发布，店铺 JSON 会在启动时尝试从 GitHub Pages 获取最新版，并在失败时回退到缓存或应用内置数据。

Bundle ID: `jp.miitarou.hyakumeiten.udonsoba`

## ⚖️ 许可证

源代码采用 MIT License。详见 [LICENSE](LICENSE)。

`data/` 下的店铺数据不包含在 MIT License 范围内。详见 [DATA_LICENSE.md](DATA_LICENSE.md)。

## ⚠️ 免责声明

本网站是个人制作的非官方粉丝工具。
它与 Tabelog、Kakaku.com、Tabelog 百名店没有合作、赞助或认可关系。

位置信息只在浏览器或设备本地使用，不会发送或保存到服务器。
实际到访前，请务必确认店铺的最新官方信息。

## 🙏 致谢

- [Tabelog](https://tabelog.com/) 的公开参考信息
- [日本国土地理院](https://www.gsi.go.jp/) 地图瓦片
- [OpenStreetMap](https://www.openstreetmap.org/) 与 [Nominatim](https://nominatim.org/)
- [Leaflet](https://leafletjs.com/)
