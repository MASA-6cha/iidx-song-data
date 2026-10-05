# BEMANIWiki IIDX 34 新曲データ取得

1日2回（日本時間12:00・21:00）、新曲リスト1ページとrobots.txtを取得してJSON・CSVを更新します。PCを起動しておく必要はありません。GitHub Actions側の遅延はあります。

## 既存リポジトリへの追加

このフォルダの中身を既存リポジトリのルートへ追加してください。`.github/workflows/update-bemaniwiki.yml` も必要です。同名ファイルが既にある場合は内容を確認して統合してください。
デフォルトブランチに配置し、Actionsから「Update BEMANIWiki IIDX 34」→「Run workflow」で最初の実行を確認します。
ブランチ保護で直接pushが禁止されている場合は保存用ブランチやPR運用への調整が必要です。パッケージを置いただけでは定期実行は始まりません。

## 出力

- `data/bemaniwiki-iidx34.json`：曲単位。SPのB/N/H/A/L、DPのN/H/A/Lの難易度、ノーツ数、特殊ノーツ表記を保持。
- `data/bemaniwiki-iidx34.csv`：譜面単位、UTF-8 BOM付き。未収録枠・未確認枠も出力。外部テキストの数式解釈を防ぐため、先頭が = + - @ の文字列にはアポストロフィを付けます。
- `data/bemaniwiki-iidx34-status.json`：成功した確認時刻、曲数、変更有無。実際の確認履歴として毎回更新されます。
- `bemaniwiki-iidx34-list.html`：今回の取得結果を埋め込んだ静的スナップショット。自動更新されません。

曲名・アーティスト・ジャンル・BPM・配信日・後日登場予定・ノーツ数・演奏時間・ムービー・レイヤーを取得します。BPMは範囲も扱えるよう文字列です。CN?等の未確認表記はそのまま保持します。
`exists=false`は「-」（譜面なし）、`exists=null`は空欄等（存在未確認）です。数値の空欄はnullで、0にしません。
`availability=planned`は後日登場予定、`listed`はその他の掲載区分であり、実機への収録を独立に確認した意味ではありません。
公式楽曲IDはこのページから得られないため` song_id `はnullです。レーダー6項目もこのページからは取得しません。既存アプリ向けJSONへの変換は別途必要です。

## 失敗時

ページタイトル、表の見出し、列順、行数、難易度範囲、曲名とノーツ表の対応を検査してから保存します。取得・解析エラーでは前回データを変更せず、Actionsを失敗終了します。曲の消失も自動保存を止めます。正当な削除・表記変更の場合は内容を確認して`--allow-removals`で手動実行してください。
robots.txtを確認し、取得不可の指定があると停止します。404以外の取得エラーも停止します。現在確認できたrobots.txtにはSitemapの案内のみでしたが、これは転載許諾の意味ではありません。出典情報をJSONとHTMLに含めています。

## ローカル確認（任意）

```
python -m pip install -r requirements-bemaniwiki.txt
python -m unittest discover -s . -p 'test_bemaniwiki.py'
python fetch_bemaniwiki.py
```

作成日：2026-10-05。バージョン：1.0.0。
