# 🍜🥢 Udon & Soba Hyakumeiten Map 2017-2025

🌐 **Language:** [日本語](README.md) | **English** | [中文](README.zh.md)

An unofficial reference map personally organized from publicly available information related to "Udon and Soba Hyakumeiten" lists.
The app lets you browse udon and soba restaurants on a map, switch genres, filter by year, area, prefecture, selection count, distance, and visit status, and discover related restaurants using static recommendation tags.
This project is not affiliated with, sponsored by, or endorsed by Tabelog, Kakaku.com, or Tabelog Hyakumeiten.

🔗 **Live App**: [https://miitarou.github.io/udon-hyakumeiten-map/](https://miitarou.github.io/udon-hyakumeiten-map/)

![Udon](https://img.shields.io/badge/Udon-428-D4A853)
![Soba](https://img.shields.io/badge/Soba-266-7B9E6B)
![Total](https://img.shields.io/badge/Total-694-555555)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ Features

### 🗂️ Genre Switching
- **ALL / 🍜 Udon / 🥢 Soba**: Quickly switch the visible genre from the header.
- **Category markers**: Marker color is used to distinguish udon and soba, while selection strength is shown with size and hall-of-fame effects.
- **Custom icons**: Udon and soba markers use separate in-app icons.

### 🗺️ Map
- **694 restaurants** rendered with Leaflet.js and MarkerCluster.
- **Selection count emphasis**: Frequently selected restaurants, including category top 10% "hall-of-fame" entries, are visually emphasized.
- **Automatic labels**: Restaurant labels appear when markers are shown individually.
- **Current location**: Search around your current location without sending or storing location data on a server.

### 🔍 Search and Filters
- **EAST / WEST / KAGAWA** area filters. KAGAWA is available for udon.
- **Restaurant, address, and station search** with lightweight normalization for kana variants and minor typos.
- **Prefecture, year, and selection-count filters**.
- **Radius search** from your current location or a clicked point on the map.
- **Visit status**: Save "Want to go" and "Visited" locally in your browser, with JSON export/import.
- **If you like this restaurant**: Show similar or nearby candidates using static AI-inferred recommendation tags.

Saved visit status is stored only in browser `localStorage` and is not sent to a server.
It may be lost when switching browsers/devices or clearing site data, so use the export feature when needed.

### 🎨 Design
- Dark glassmorphism UI.
- Responsive desktop side panel and mobile bottom sheet.
- Resizable desktop panel.
- PWA support with Service Worker caching for app assets and restaurant JSON, update notices, and offline guidance.

## 🚀 Local Use

```bash
python3 -m http.server 8080
open http://localhost:8080
```

## 📁 Project Structure

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

## 🛠️ Technology

| Category | Technology |
| --- | --- |
| Map | [Leaflet.js](https://leafletjs.com/) |
| Clustering | [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) |
| Map Tiles | [GSI Tiles](https://maps.gsi.go.jp/development/ichiran.html), attribution: Geospatial Information Authority of Japan |
| Fonts | Noto Sans JP, Outfit |
| Hosting | GitHub Pages |

Leaflet and Leaflet.markercluster CDN resources use Subresource Integrity (SRI).

## 📊 Data

This is an unofficial reference map based on publicly available "Udon and Soba Hyakumeiten" related information.
Coordinates are estimated from addresses and restaurant pages and may contain errors.

"Hall of fame" is not an official title. In this app, it means restaurants in approximately the top 10% of selection counts within each category.

### Udon
- Years: 2017-2024
- Records: 428 restaurants
- Areas: EAST 212 / WEST 111 / KAGAWA 105

### Soba
- Years: 2017-2025
- Records: 266 restaurants
- Areas: EAST 157 / WEST 109

### Recommendation Tags

`data/recommendation_tags.json` is static data used by the "If you like this restaurant" feature.
It separates factual tags, such as genre and region, from conservative AI-inferred exploratory tags.
The inferred tags are not factual descriptions of restaurants; they are auxiliary signals for restaurant-to-restaurant similarity.

See [docs/recommendation-tags.md](docs/recommendation-tags.md) and [docs/external-signals.md](docs/external-signals.md) for the scoring design and external signal policy.

## 🧪 Data Validation

```bash
python3 scripts/generate_data_version.py
python3 scripts/generate_external_signal_backlog.py
python3 scripts/generate_external_signals.py
python3 scripts/generate_recommendation_tags.py
python3 scripts/check_data_quality.py
python3 scripts/evaluate_recommendations.py
```

See [docs/update-guide.md](docs/update-guide.md) for the full update workflow.

## 📱 iPhone App

The `mobile/` directory contains a Capacitor-based iOS wrapper.
The web app is the source of truth. HTML/CSS/JS changes are shipped through App Store updates, while restaurant JSON can be refreshed from GitHub Pages at app launch and falls back to cached or bundled data.

Bundle ID: `jp.miitarou.hyakumeiten.udonsoba`

## ⚖️ License

Source code is released under the MIT License. See [LICENSE](LICENSE).

Restaurant data under `data/` is not covered by the MIT License. See [DATA_LICENSE.md](DATA_LICENSE.md).

## ⚠️ Disclaimer

This is a personal, unofficial fan tool.
It is not affiliated with, sponsored by, or endorsed by Tabelog, Kakaku.com, or Tabelog Hyakumeiten.

Location data is used only in the browser or on the device and is not sent to or stored on a server.
Before visiting a restaurant, please confirm the latest official information.

## 🙏 Credits

- [Tabelog](https://tabelog.com/) for publicly available reference information
- [Geospatial Information Authority of Japan](https://www.gsi.go.jp/) for map tiles
- [OpenStreetMap](https://www.openstreetmap.org/) and [Nominatim](https://nominatim.org/)
- [Leaflet](https://leafletjs.com/)
