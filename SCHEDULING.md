# BEMANIWiki 定期取得の時刻調査・改善

調査日：2026-10-14（日本時間）。対象：`.github/workflows/update-bemaniwiki.yml`。

## 確認できたこと

- 変更前のcronは `0 3,12 * * *`、timezone指定なし。UTC 03:00・12:00なので、日本時間12:00・21:00の変換は正しい。
- workflowファイルの変更履歴は作成コミット `667ef75072284f62952d8a3e05d758858e35c828` の1件のみ。途中で別の時刻設定になっていた証拠はない。
- 全18回の実行のうち定期実行は16回。予定からrun作成までの推定遅延は4時間55分37秒〜8時間52分20秒、平均6時間34分48秒。固定7時間のずれではない。
- 直近2件の `created_at` と `run_started_at` は同時刻。実際のジョブ開始はそれぞれ作成から2秒後・2秒後。取得ステップは各約2秒、全実行は各15秒で完了した。
- 他の実行も11〜21秒で終了し、同じconcurrencyグループの長時間実行との重なりは見られない。取得処理・pip・runner待ち・concurrency待ちでは数時間の遅延を説明できない。
- 最新の状況ファイルは `checked_at=2026-10-13T18:50:54+00:00`（10月14日03:50:54 JST）、44曲、`data_changed=false`。
- 10月8〜10日の失敗は別件の曲名変更検出。10月11日に復旧済み。その前後とも定期起動が数時間遅れている。

遅延はGitHub側でワークフロー実行が作成される前に発生していると判断できる。GitHubのscheduleイベント配送の遅延が有力。ただし、公開REST APIには元の予定日時・内部配送キュー・混雑原因がないため、「なぜこのリポジトリで数時間になるか」の根本原因は確定できない。必要ならこの16件と直近のjob API情報をGitHub Supportへ提示する。

## 実行履歴

すべて日本時間。予定枠はcronと実行順からの推定であり、GitHubが元の予定日時を返した値ではない。`created_at` はワークフロー作成、実行時間は `updated_at-created_at`。statusがsuccessでも定時起動の成功を意味しない。

| 実行 | 予定枠（推定） | ワークフロー作成 | 推定遅延 | 実行時間 | 結果 |
| --- | --- | --- | --- | --- | --- |
| [37445121717](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37445121717) | 2026-10-06 12:00:00 | 2026-10-06 18:45:10 | 6時間45分10秒 | 14秒 | success |
| [37507017648](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37507017648) | 2026-10-06 21:00:00 | 2026-10-07 02:53:19 | 5時間53分19秒 | 14秒 | success |
| [37602838195](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37602838195) | 2026-10-07 12:00:00 | 2026-10-07 18:45:50 | 6時間45分50秒 | 15秒 | success |
| [37666499367](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37666499367) | 2026-10-07 21:00:00 | 2026-10-08 03:23:49 | 6時間23分49秒 | 18秒 | success |
| [37760104689](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37760104689) | 2026-10-08 12:00:00 | 2026-10-08 18:56:22 | 6時間56分22秒 | 21秒 | failure |
| [37823918698](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37823918698) | 2026-10-08 21:00:00 | 2026-10-09 03:23:36 | 6時間23分36秒 | 13秒 | failure |
| [37914862263](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37914862263) | 2026-10-09 12:00:00 | 2026-10-09 19:00:09 | 7時間0分9秒 | 12秒 | failure |
| [37969788216](https://github.com/MASA-6cha/iidx-song-data/actions/runs/37969788216) | 2026-10-09 21:00:00 | 2026-10-10 02:56:23 | 5時間56分23秒 | 14秒 | failure |
| [38041107360](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38041107360) | 2026-10-10 12:00:00 | 2026-10-10 18:21:35 | 6時間21分35秒 | 12秒 | failure |
| [38069637371](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38069637371) | 2026-10-10 21:00:00 | 2026-10-11 01:55:37 | 4時間55分37秒 | 11秒 | failure |
| [38129109002](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38129109002) | 2026-10-11 12:00:00 | 2026-10-11 18:38:47 | 6時間38分47秒 | 17秒 | success |
| [38159033549](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38159033549) | 2026-10-11 21:00:00 | 2026-10-12 02:17:41 | 5時間17分41秒 | 17秒 | success |
| [38234740136](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38234740136) | 2026-10-12 12:00:00 | 2026-10-12 19:11:21 | 7時間11分21秒 | 20秒 | success |
| [38307008343](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38307008343) | 2026-10-12 21:00:00 | 2026-10-13 05:52:20 | 8時間52分20秒 | 17秒 | success |
| [38380802280](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38380802280) | 2026-10-13 12:00:00 | 2026-10-13 19:04:04 | 7時間4分4秒 | 15秒 | success |
| [38450051165](https://github.com/MASA-6cha/iidx-song-data/actions/runs/38450051165) | 2026-10-13 21:00:00 | 2026-10-14 03:50:45 | 6時間50分45秒 | 15秒 | success |

直近の詳細：
- [10月13日19:04のjobs API](https://api.github.com/repos/MASA-6cha/iidx-song-data/actions/runs/38380802280/jobs)：作成19:04:04、ジョブ開始19:04:06、取得19:04:13〜19:04:15。
- [10月14日03:50のjobs API](https://api.github.com/repos/MASA-6cha/iidx-song-data/actions/runs/38450051165/jobs)：run作成03:50:45、job作成03:50:46、ジョブ開始03:50:47、取得03:50:52〜03:50:54。
- [全実行のREST API](https://api.github.com/repos/MASA-6cha/iidx-song-data/actions/runs?per_page=30)
- [workflow変更履歴](https://github.com/MASA-6cha/iidx-song-data/commits/main/.github/workflows/update-bemaniwiki.yml)

## GitHub公式情報との照合

[公式schedule仕様](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)では、毎時00分などの高負荷時に遅延する可能性、キュー内の起動が落ちる可能性、分をずらす緩和策が説明されている。時刻どおりの実行も、毎回配送されることも保証されない。

[10月12日の障害](https://www.githubstatus.com/incidents/93njd414rpbx)ではActionsの新規実行のキュー投入などに影響が報告された。この日の悪化に関係した可能性はあるが、10月6日からの継続した遅延全体を説明できない。

[10月13日のログ表示障害](https://www.githubstatus.com/incidents/6yk962mhlr3h)は、GitHub自身が実行遅延はなかったと説明している。今回の定期起動の原因とする証拠にはならない。

## 今回の変更

定期起動は以下の2枠に変更する。目標12:00・21:00に対して7分後の予約。毎時00分の集中を避けるための緩和であり、数時間の遅延が解消したとはまだ言えない。

```yaml
schedule:
  - cron: '7 3 * * *'   # JST 12:07
  - cron: '7 12 * * *'  # JST 21:07
```

別々のcronにして、日付を跨いで遅れた場合も昼／夜の枠を識別できるようにする。起動回数は1日2回のまま。調査・検証用のpush／手動実行は別途可能で、これは従来と同じ。

`report_bemaniwiki_schedule.py` を取得直前に実行し、ActionsのSummaryとログに以下を表示する。

- cron、run作成、実際のジョブ開始、取得ステップ直前の時刻（JST）。
- cronとrun作成から推定した予定枠・配送遅延、run作成→ジョブ開始、ジョブ開始→取得直前の秒数。
- 推定配送遅延が30分以上なら注意文。元の予定日が提供されないため24時間以上の遅延は判別できない旨。
- push／手動実行は定期起動精度を証明しない旨、再実行は待ち時間を区別すべき旨。

追加権限は `actions: read` のみ。API取得に失敗した場合も取得処理を続行し、診断ステップ自体も `continue-on-error: true`。外部サービス・新しいsecret・追加ライブラリは不要。

取得コード、JSON／CSV／状況ファイルの形式、robots.txt確認、削除検出、確認済み曲名変更の照合、失敗時の既存データ保持、排他実行、10分timeoutは維持する。診断コードはデータファイルを書き換えない。データ保護19件と診断7件の計26件をテストする。

## 現実的な代替案

| 方法 | 時刻精度と残る制約 | 準備・運用 |
| --- | --- | --- |
| 今回：GitHubのcronを12:07・21:07へずらす | 00分の混雑回避。定時起動・配送の保証はない | 現構成で即実装でき、PCの常時起動不要 |
| 常時稼働PC／サーバーから12:00・21:00にworkflow_dispatch | GitHubのschedule配送を通さずに起動要求を送れる。Actionsのrunner待ち・API障害は残る | Windowsタスクスケジューラ等とGitHub認証が必要。内部cronは外して二重取得を防ぐ |
| 外部のスケジューラーからworkflow_dispatch | 常時稼働PC不要。サービスの配送精度・障害、Actionsのrunner待ちは残る | 外部サービスのアカウント、GitHubトークン等の安全な保存が必要。内部cronは外す |
| 常時稼働サーバーで取得処理を直接実行してGitHubへpush | Actionsの起動待ちを避けられる。サーバー停止、時刻ずれ、取得先や通信の障害は残る | Python・Git・資格情報・排他制御・失敗監視を運用する必要がある |

常時稼働サーバーがあるなら2番目が移行の負担を抑えやすい。起動コマンド例：

```powershell
gh workflow run update-bemaniwiki.yml --repo MASA-6cha/iidx-song-data --ref main
```

これは移行用の例で、今回サーバーや外部サービスの設定は行っていない。外部起動に移す場合は、内部scheduleと併用して1日4回にしない。重複防止・再試行を導入する場合も、同じ時間枠の成功を確認してから再取得の要否を判断する。

7時間前倒しする方法は採用しない。遅延は4時間55分〜8時間52分と変動しており、早過ぎる取得になったり、引き続き大きく遅れたりするため。

## 検証と未確認事項

ローカルで26件のテストを実行し、workflowが2枠だけであること、取得・commitの対象とデータ保護コードが維持されていることを確認する。mainへの反映時にpushイベントで1回実取得を行い、Summary・テスト・44曲とデータ変更有無を確認する。

push実行が成功しても、新しいschedule配送の時刻精度は未確認。変更後の最初の12:07・21:07以降のschedule実行結果で判断する。まず数日分のSummaryを比較し、長時間の遅延が続くなら外部workflow_dispatchまたはサーバー直接取得へ移す。
