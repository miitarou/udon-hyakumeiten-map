# App Store Submission Checklist

初回申請時にApp Store Connectへ入力・確認する項目です。

## 1. 新規アプリ作成

- Platform: iOS
- Name: `百名店MAP`
- Primary Language: Japanese
- Bundle ID: `jp.miitarou.hyakumeiten.udonsoba`
- SKU: `hyakumeiten-udonsoba-ios`
- User Access: Full Access

## 2. 価格と配信

- Price: Free
- Availability: Japan only or all regions
  - 初回は日本のみでもよい
  - 海外配信する場合も、アプリ文言は日本語中心

## 3. App Information

- Subtitle: `うどん・そば名店探索マップ`
- Category: Food & Drink
- Secondary Category: Travel
- Content Rights: このアプリは第三者コンテンツを含む可能性がある
  - 店舗名、住所、URL等の公開情報を参考データとして整理しているため

## 4. URLs

- Privacy Policy URL: `https://miitarou.github.io/udon-hyakumeiten-map/privacy.html`
- Support URL: `https://github.com/miitarou/udon-hyakumeiten-map/issues`

## 5. App Privacy

方針: Data Not Collected

- Location: 収集しない
  - 現在地検索時のみ端末内で使用
  - サーバー送信・保存なし
- User Content: 収集しない
  - 行きたい / 訪問済みは端末内保存
- Diagnostics / Analytics: 収集しない
- Tracking: No

App Store Connectで「データを収集しない」を選べる場合はそれを選択する。
位置情報は利用するが、開発者が収集しないため、収集データとしては申告しない。

## 6. Review Notes

`mobile/APP_STORE_NOTES.md` の Review Notes を貼り付ける。

特に以下を明記する。

- 非公式の参考マップである
- 食べログ、株式会社カカクコム、食べログ百名店とは非提携
- 位置情報は端末内利用のみ
- 訪問状況は端末内保存のみ
- 店舗データは同梱JSONから起動し、オンライン時に公開JSONを取得する
- 外部リンクはSafariまたはプラットフォームブラウザで開く

## 7. Build Upload

Xcode Organizerで実施する。

1. Xcode > Product > Archive
2. OrganizerでArchiveを選択
3. Distribute App
4. App Store Connect
5. Upload
6. Automatically manage signing
7. Upload

アップロード後、App Store Connect側でビルド処理が完了するまで待つ。

CLIでアップロードする場合は、`mobile/ExportOptions-app-store.plist` を使う。
ただし初回はエラー時の確認がしやすいので、Xcode Organizerから進める方が安全。

## 8. Screenshots

最低限、iPhone用スクリーンショットを登録する。

推奨構成:

1. 地図全体とクラスタ表示
2. 検索・フィルタのボトムシート
3. 店舗ポップアップと外部リンク
4. この店が好きなら推薦
5. 訪問状況と距離検索

## 9. Final Checks Before Submit

- アプリ名・アイコンが意図通り
- 現在地許可文言が自然
- 非公式・免責・出典・プライバシー導線が見える
- 食べログ / Googleリンクが外部ブラウザで開く
- App Privacyが実装と矛盾しない
- 価格が無料になっている
- 最終提出前にスクリーンショット内にブラウザUIが写っていない
