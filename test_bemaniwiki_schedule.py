"""Timing boundary and non-blocking API failure tests (no live requests)."""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from report_bemaniwiki_schedule import inferred_slot, main, parse_time, render_report


class ScheduleTests(unittest.TestCase):
    def test_each_daily_slot_and_jst_midnight(self):
        cases = [
            ('7 3 * * *', '2026-10-13T03:07:00Z', '2026-10-13T03:07:00Z'),
            ('7 3 * * *', '2026-10-13T10:04:04Z', '2026-10-13T03:07:00Z'),
            ('7 12 * * *', '2026-10-13T18:50:45Z', '2026-10-13T12:07:00Z'),
            ('7 12 * * *', '2026-10-14T01:00:00Z', '2026-10-13T12:07:00Z'),
        ]
        for cron, created, expected in cases:
            with self.subTest(cron=cron, created=created):
                self.assertEqual(inferred_slot(cron, parse_time(created)), parse_time(expected))

    def test_invalid_or_ambiguous_cron_fails(self):
        for cron in ('0 3,12 * * *', '60 3 * * *', '7 24 * * *', '7 3 * * 1'):
            with self.subTest(cron=cron):
                with self.assertRaises(ValueError):
                    inferred_slot(cron, parse_time('2026-10-13T10:04:04Z'))

    def test_report_separates_schedule_and_runner_wait(self):
        run = {'created_at': '2026-10-13T10:04:04Z', 'run_attempt': 1}
        job = {'started_at': '2026-10-13T10:04:06Z'}
        report = render_report('schedule', '7 3 * * *',
                               parse_time('2026-10-13T10:04:13Z'), run, job)
        self.assertIn('2026-10-13T12:07:00+09:00', report)
        self.assertIn('| 予定→ワークフロー作成（秒・推定） | 25024 |', report)
        self.assertIn('| 作成→ジョブ開始（秒） | 2 |', report)
        self.assertIn('| ジョブ開始→取得直前（秒） | 7 |', report)
        self.assertIn('24時間以上', report)
        self.assertIn('30分以上', report)

    def test_push_does_not_claim_scheduled_validation(self):
        report = render_report('push', '', parse_time('2026-10-13T10:04:13Z'))
        self.assertNotIn('予定→', report)
        self.assertIn('時刻精度の検証には使えません', report)

    def test_rerun_is_identified(self):
        report = render_report('schedule', '7 3 * * *',
                               parse_time('2026-10-14T10:04:13Z'),
                               {'created_at': '2026-10-13T10:04:04Z', 'run_attempt': 2})
        self.assertIn('再実行です', report)

    def test_api_failure_keeps_data_and_writes_summary_without_token(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'data'
            output.mkdir()
            for name in ('bemaniwiki-iidx34.json', 'bemaniwiki-iidx34.csv',
                         'bemaniwiki-iidx34-status.json'):
                (output / name).write_bytes(b'previous data')
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            summary = root / 'summary.md'
            env = {'GITHUB_REPOSITORY': 'MASA-6cha/iidx-song-data',
                   'GITHUB_RUN_ID': '123', 'GITHUB_EVENT_NAME': 'schedule',
                   'SCHEDULE_CRON': '7 3 * * *', 'GH_TOKEN': 'test-secret',
                   'GITHUB_STEP_SUMMARY': str(summary)}
            with patch.dict(os.environ, env, clear=True), \
                    patch('report_bemaniwiki_schedule.api_get', side_effect=OSError('test-secret')), \
                    contextlib.redirect_stdout(io.StringIO()) as log:
                main()
            self.assertIn('取得処理は続行します', summary.read_text('utf-8'))
            self.assertNotIn('test-secret', log.getvalue())
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_main_reads_current_attempt_job(self):
        run = {'created_at': '2026-10-13T10:04:04Z'}
        jobs = {'jobs': [{'name': 'update', 'started_at': '2026-10-13T10:04:06Z'}]}
        env = {'GITHUB_REPOSITORY': 'MASA-6cha/iidx-song-data', 'GITHUB_RUN_ID': '123',
               'GITHUB_RUN_ATTEMPT': '2', 'GITHUB_JOB': 'update',
               'GITHUB_EVENT_NAME': 'workflow_dispatch'}
        with patch.dict(os.environ, env, clear=True), \
                patch('report_bemaniwiki_schedule.api_get', side_effect=[run, jobs]) as api, \
                contextlib.redirect_stdout(io.StringIO()) as log:
            main()
        self.assertEqual(api.call_args_list[1].args[0],
                         '/repos/MASA-6cha/iidx-song-data/actions/runs/123/attempts/2/jobs')
        self.assertIn('| 作成→ジョブ開始（秒） | 2 |', log.getvalue())


if __name__ == '__main__':
    unittest.main()
