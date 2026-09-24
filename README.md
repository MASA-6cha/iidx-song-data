# IIDX 曲・譜面データ

メモアプリなどで利用できる、IIDXの曲情報・譜面情報・レーダー値をまとめたJSONデータです。
`songs.json` のデータ形式は `iidx-info-exporter/songs/1` です。
曲IDごとに1件にまとめ、`charts` に `SPB` / `SPN` / `SPH` / `SPA` / `SPL` / `DPB` / `DPN` / `DPH` / `DPA` / `DPL` のうち存在する譜面を格納します。

## メモアプリでの読み込み

データ取得用URL：

```text
https://raw.githubusercontent.com/MASA-6cha/iidx-song-data/main/songs.json
```

更新情報：<https://raw.githubusercontent.com/MASA-6cha/iidx-song-data/main/manifest.json>

公開リポジトリの `songs.json` の **Raw URL** を設定し、JSONとして読み込みます。
GitHubのファイル表示画面（`github.com/.../blob/...`）はHTMLなので、データ取得用URLとして使わないでください。
URLから読み込む最小の実装は `load-songs.js` を参照してください。

曲の識別には `music_id`、譜面の識別には `charts` のキーを使います。
既存メモやスコアを保持したまま、同じID・譜面種類の曲情報だけ更新してください。
初回や手動更新時に取得してIndexedDBなどに保存すれば、画面表示のたびに全件を再取得する必要はありません。

## フィールド

| 場所 | フィールド | 意味 |
| --- | --- | --- |
| 曲 | `music_id`, `title`, `artist`, `genre` | 曲ID、曲名、アーティスト、ジャンル |
| 譜面 | `chart_type`, `level` | 譜面種類、レベル |
| 譜面 | `bpm.min`, `bpm.max` | BPM範囲（小数を含む） |
| 譜面 | `bpm_display.min`, `bpm_display.max`, `bpm_display.text` | 表示用BPM（整数に丸めた値） |
| 譜面 | `note_count` | ノーツ数 |
| 譜面 | `CN`, `HCN`, `BSS`, `MSS` | 各要素の有無（booleanまたはnull） |
| 譜面 | `radar` | `NOTES`, `PEAK`, `SCRATCH`, `SOF-LAN`, `CHARGE`, `CHORD` |
| 譜面 | `status`, `status_label` | データの状態 |

`null` は未収録・不明です。0やfalseに置き換えないでください。
`status: "calculated"` は算出済み、`"captured"` は取得済み、`"unavailable"` は未取得を表します。
レーダーの各値はすでに表示用の数値（例：157.37）なので、100で割る必要はありません。
`SOF-LAN` はハイフンを含むため、JavaScriptでは `chart.radar["SOF-LAN"]` で参照します。

## データと更新

曲数・譜面数・状態別件数、データ作成日時、SHA-256は `manifest.json` に記録しています。
配信ファイルはUTF-8のJSONで、ファイルサイズを抑えるため余分な空白を省いています。
曲名などの情報がnullの曲や、値が未収録の譜面も、状態を保持して含めています。

一部の譜面でレーダー値の照合を行っていますが、全曲・全譜面の値を個別に照合したものではありません。

データ更新時は `songs.json` と `manifest.json` を一緒に更新します。
アプリ側では `manifest.json` の日時やSHA-256を使って更新の有無を確認できます。
