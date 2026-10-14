"""Read-only timing diagnostics; never read or write collector output files."""
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))


def parse_time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Expected a timestamp with a timezone')
    return result.astimezone(timezone.utc)


def inferred_slot(cron, created):
    """Latest daily occurrence before run creation, not an original event date.

    GitHub supplies the cron expression but not the original scheduled timestamp.
    A delay of 24 hours or more cannot be resolved from this data alone.
    """
    match = re.fullmatch(r'(\d{1,2}) (\d{1,2}) \* \* \*', cron)
    if not match:
        raise ValueError('Expected a separate daily, single-hour UTC schedule')
    minute, hour = map(int, match.groups())
    if not 0 <= minute < 60 or not 0 <= hour < 24:
        raise ValueError('Invalid cron time')
    created = created.astimezone(timezone.utc)
    slot = created.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return slot if slot <= created else slot - timedelta(days=1)


def api_get(path):
    endpoint = os.environ.get('GITHUB_API_URL', 'https://api.github.com').rstrip('/')
    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'IIDX34ScheduleDiagnostics/1.0'}
    token = os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(endpoint + path, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def stamp(value):
    return value.astimezone(JST).isoformat(timespec='seconds') if value else '取得不可'


def render_report(event, cron, before_fetch, run=None, job=None, error=None):
    run, job = run or {}, job or {}
    created = parse_time(run['created_at']) if run.get('created_at') else None
    started = parse_time(job['started_at']) if job.get('started_at') else None
    rows = [('起動イベント', event), ('cron（UTC）', cron or '該当なし'),
            ('ワークフロー作成（JST）', stamp(created)),
            ('ジョブ開始（JST）', stamp(started)),
            ('取得ステップ直前（JST）', stamp(before_fetch))]
    notes = []
    if event == 'schedule' and created and cron:
        planned = inferred_slot(cron, created)
        seconds = round((created - planned).total_seconds())
        rows += [('予定起動（JST・推定）', stamp(planned)),
                 ('予定→ワークフロー作成（秒・推定）', str(seconds))]
        notes.append('予定日はcronと作成時刻から直前の枠を推定しています。'
                     'GitHubは元の予定日時を提供しないため、24時間以上の遅延は判別できません。')
        if seconds >= 1800:
            notes.append('推定起動遅延が30分以上あります。GitHubのschedule配送を確認してください。')
    else:
        notes.append('push／手動実行は定期起動の時刻精度の検証には使えません。')
    if created and started:
        rows.append(('作成→ジョブ開始（秒）', str(round((started - created).total_seconds()))))
    if started:
        rows.append(('ジョブ開始→取得直前（秒）', str(round((before_fetch - started).total_seconds()))))
    if int(run.get('run_attempt', 1)) > 1:
        notes.append('再実行です。作成→ジョブ開始には再実行までの時間が含まれます。')
    if error:
        notes.append('API時刻情報を取得できませんでした（' + error + '）。取得処理は続行します。')
    return ('## BEMANIWiki 実行時刻診断\n\n| 項目 | 値 |\n| --- | --- |\n'
            + ''.join('| ' + key + ' | ' + value + ' |\n' for key, value in rows)
            + '\n' + '\n\n'.join(notes) + '\n')


def main():
    event = os.environ.get('GITHUB_EVENT_NAME', 'local')
    cron = os.environ.get('SCHEDULE_CRON', '')
    repo, run_id = os.environ.get('GITHUB_REPOSITORY'), os.environ.get('GITHUB_RUN_ID')
    run, job, error = None, None, None
    if repo and run_id:
        try:
            run = api_get(f'/repos/{repo}/actions/runs/{run_id}')
            attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
            jobs = api_get(f'/repos/{repo}/actions/runs/{run_id}/attempts/{attempt}/jobs')
            matches = [j for j in jobs['jobs'] if j['name'] == os.environ.get('GITHUB_JOB')]
            if len(matches) == 1:
                job = matches[0]
        except (OSError, ValueError, KeyError) as exc:
            error = type(exc).__name__ # Never include headers or credentials.
    # Timestamp after diagnostic API calls, immediately before the fetch step.
    before_fetch = datetime.now(timezone.utc)
    report = render_report(event, cron, before_fetch, run, job, error)
    print(report)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a', encoding='utf-8') as stream:
            stream.write(report)


if __name__ == '__main__':
    main()
