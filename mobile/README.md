# iOS App Wrapper

`百名店MAP` のCapacitorベースiOSラッパーです。

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
- Display name: `百名店MAP`
- Location permission: 現在地周辺の店舗検索にのみ使用

## Data Refresh Policy

iOSアプリは、Web版のHTML/CSS/JSと店舗JSONをアプリ内に同梱します。
起動時にGitHub Pages上の最新版店舗JSON取得を試み、失敗時は端末キャッシュ、さらに失敗時は同梱JSONへフォールバックします。
HTML/CSS/JSはリモート差し替えせず、機能変更はApp Storeアップデートで反映します。

## Prerequisites

- Xcode
- CocoaPods
- Node.js / npm

## Current Local Setup

- Xcode 26.4.1 / iOS 26.4 Simulator RuntimeでSimulatorビルド確認済み。
- 実機 `mii-iPhone17` へのDebugビルド、インストール、起動確認済み。
- Signing Team: `XUQ4K2R5GP`
- 次回更新用のローカル確認: Version `1.1` / Build `3` でRelease汎用iOSビルド成功。

## App Store Preparation

申請用の説明文、レビュー用メモ、プライバシー回答の下書きは `mobile/APP_STORE_NOTES.md` を参照してください。
