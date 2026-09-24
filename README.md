# IIDX 曲・譜面データ

`songs.json` は `iidx-info-exporter/songs/1` 形式の曲データです。
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
| 譜面 | `bpm.min`, `bpm.max` | 譜面中の実際のBPM範囲 |
| 譜面 | `bpm_display.min`, `bpm_display.max`, `bpm_display.text` | ゲームに合わせて丸めた表示用BPM |
| 譜面 | `note_count` | ノーツ数 |
| 譜面 | `CN`, `HCN`, `BSS`, `MSS` | 各要素の有無（booleanまたはnull） |
| 譜面 | `radar` | `NOTES`, `PEAK`, `SCRATCH`, `SOF-LAN`, `CHARGE`, `CHORD` |
| 譜面 | `status`, `status_label` | 取得・計算状態 |

`null` は未取得・不明です。0やfalseに置き換えないでください。
`status: "calculated"` は譜面からの独立計算、`"captured"` はゲームからの取得、`"unavailable"` は未取得です。
レーダーの各値はすでに表示用の数値（例：157.37）なので、100で割る必要はありません。
`SOF-LAN` はハイフンを含むため、JavaScriptでは `chart.radar["SOF-LAN"]` で参照します。

## データと更新

曲数・譜面数・状態別件数、データ生成日時、SHA-256は `manifest.json` に記録しています。
元の出力からPC内のパス（`chart_sources`, `chart_source`）と診断文（`warnings`）を省き、空白を詰めています。曲・譜面の値は変更していません。
曲名などのメタデータがnullの曲、取得できていない譜面も、状態を保持して含めています。

複数のsoundフォルダの優先順位は出力元ですでに解決済みです。入力順で後のフォルダが曲ID単位で優先されます。
レーダー計算は `quaver♪` SPA のゲーム表示6軸との一致を確認しています。全曲についてゲーム画面との一致を確認したデータではありません。

更新時は元プロジェクトで次を実行し、このフォルダの `songs.json` と `manifest.json` を一緒に更新します。

```powershell
python iidx-info-exporter/prepare-github-data.py "新しい出力フォルダ/songs.json" iidx-github-data
```
