# データ利用に関する注意事項 (DATA_LICENSE)

## ソースコードのライセンス

本リポジトリのソースコード（`index.html`, `app.js`, `style.css`, `scripts/` 配下のスクリプト等）は [MIT License](LICENSE) で提供します。

## データの取り扱い

**`data/` 配下の店舗データ（店舗名、選出年度、住所、座標、URL、閉店情報等）は MIT License の対象外です。**

これらのデータは、公開情報をもとに個人が整理したものですが、各情報提供元の権利・利用条件の対象となる可能性があります。

本データの再利用・再配布・商用利用については、利用者自身の責任で各情報提供元の条件を確認してください。

### 主な情報提供元・参照元

| 情報 | 参照元 |
|------|--------|
| うどん店舗名・選出年度（EAST/WEST） | [食べログ うどん百名店 EAST/WEST](https://award.tabelog.com/hyakumeiten/udon_east) |
| うどん店舗名・選出年度（KAGAWA） | [食べログ うどん百名店 KAGAWA](https://award.tabelog.com/hyakumeiten/udon_kagawa) |
| そば店舗名・選出年度 | [食べログ そば百名店](https://award.tabelog.com/hyakumeiten/soba/) |
| 地図タイル | [国土地理院](https://maps.gsi.go.jp/)（地理院タイル） |
| 一部座標データ | [OpenStreetMap](https://www.openstreetmap.org/) / [Nominatim](https://nominatim.org/) |

### Nominatim利用について

`scripts/` 配下のジオコーディングスクリプトは、事前のデータ準備のために使用したものです。
Nominatimを利用する場合は、[OpenStreetMap Foundation の利用ポリシー](https://operations.osmfoundation.org/policies/nominatim/)に従い、一括・高頻度・反復的な問い合わせを避け、取得結果をキャッシュしてください。

## 免責事項

本サイトは個人が作成した**非公式のファンツール**です。
食べログ、株式会社カカクコム、食べログ百名店とは提携・協賛・承認関係にありません。

掲載情報の正確性、完全性、最新性は保証しません。座標は住所・店舗ページ等から推定しており、誤差が生じる場合があります。
来店前に必ず公式情報または食べログ店舗ページでご確認ください。
