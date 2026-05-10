# iOS App Wrapper

`うどん・そば百名店MAP` のCapacitorベースiOSラッパーです。

## Commands

```bash
cd mobile
npm install
npm run sync:assets
npx cap add ios
npm run ios:sync
npm run ios:open
```

## App Settings

- Bundle ID: `jp.miitarou.hyakumeiten.udonsoba`
- Display name: `うどん・そば百名店MAP`
- Location permission: 現在地周辺の店舗検索にのみ使用

## Data Refresh Policy

iOSアプリは、Web版のHTML/CSS/JSと店舗JSONをアプリ内に同梱します。
起動時にGitHub Pages上の最新版店舗JSON取得を試み、失敗時は端末キャッシュ、さらに失敗時は同梱JSONへフォールバックします。
HTML/CSS/JSはリモート差し替えせず、機能変更はApp Storeアップデートで反映します。

## Prerequisites

- Xcode
- CocoaPods
- Node.js / npm
