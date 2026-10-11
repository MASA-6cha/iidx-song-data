import contextlib
import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from html import escape
from pathlib import Path
from unittest.mock import patch
from lxml import html
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_bemaniwiki import (
    PAGE, chart, grid, parse_page, csv_bytes, main, validate_song_update,
)

OLD_TITLE = '恋する☆宇宙戦争っ！！(恋する★ハードコアRemix)'
NEW_TITLE = '恋する☆宇宙戦争っ!! (恋する★ハードコアRemix)'


def song(title=OLD_TITLE, **overrides):
    return {'title': title, 'series': 34, 'artist': 'Prim/Remixed by RoughSketch',
            'genre': 'Hi-リミックスコア', **overrides}


def sample_page(title=NEW_TITLE, notes_title=None):
    """Synthetic valid page, including the observed 2026-10-11 source row."""
    def row(cells):
        return '<tr>' + ''.join('<td>' + escape(v) + '</td>' for v in cells) + '</tr>'

    levels = ['<tr><th colspan="5">SP</th><th colspan="4">DP</th>'
              '<th rowspan="2">BPM</th><th rowspan="2">GENRE</th>'
              '<th rowspan="2">TITLE</th><th rowspan="2">ARTIST</th></tr>',
              row(['B', 'N', 'H', 'A', 'L', 'N', 'H', 'A', 'L']),
              '<tr><td colspan="13">後日登場予定</td></tr>']
    notes = ['<tr><th rowspan="2">TITLE</th><th colspan="5">NOTE(SP)</th>'
             '<th colspan="4">NOTE(DP)</th><th rowspan="2">TIME</th>'
             '<th rowspan="2">MOVIE</th><th rowspan="2">LAYER</th></tr>',
             row(['B', 'N', 'H', 'A', 'L', 'N', 'H', 'A', 'L'])]
    for name in [title] + [f'Test song {i:02d}' for i in range(29)]:
        levels.append(row(['-', '', '', '12', '-', '', '', '', '-', '',
                           'Hi-リミックスコア', name, 'Prim/Remixed by RoughSketch']))
        note_name = notes_title if name == title and notes_title is not None else name
        notes.append(row([note_name, '-', '', '', '', '-', '', '', '', '-', ':', '公式MV', '']))
    return ('<html><head><meta charset="utf-8"><title>' + PAGE + '</title></head>'
            '<body><div id="body"><table>' + ''.join(levels) + '</table><table>'
            + ''.join(notes) + '</table></div></body></html>').encode('utf-8')

class ParserTests(unittest.TestCase):
    def test_missing_and_unknown_are_distinct(self):
        self.assertIs(chart('-')['exists'], False)
        self.assertIsNone(chart('')['exists'])
        self.assertEqual(chart('[CN?] 12')['flags'], ['CN?'])
        self.assertEqual(chart('[CN?] 12')['level'], 12)

    def test_expand_spans(self):
        table = html.fromstring('<table><tr><th rowspan="2">TITLE</th><th colspan="2">SP</th></tr><tr><th>N</th><th>H</th></tr></table>')
        self.assertEqual(grid(table), [['TITLE', 'SP', 'SP'], ['TITLE', 'N', 'H']])

    def test_wrong_page_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_page(b'<html><title>BEMANIWiki 2nd</title></html>')

    def test_invalid_level_is_rejected(self):
        with self.assertRaises(ValueError):
            chart('13')
        with self.assertRaises(ValueError):
            chart('unexpected')


    def test_source_title_is_preserved(self):
        songs = parse_page(sample_page())
        self.assertEqual(len(songs), 30)
        target = next(s for s in songs if s['title'] == NEW_TITLE)
        self.assertEqual(target['artist'], 'Prim/Remixed by RoughSketch')
        self.assertEqual(target['charts']['SP']['A']['level'], 12)
        self.assertIsNone(target['charts']['SP']['A']['notes'])
        self.assertEqual(target['availability'], 'planned')

    def test_title_mismatch_between_source_tables_still_fails(self):
        with self.assertRaisesRegex(ValueError, 'Notes/song table title mismatch'):
            parse_page(sample_page(notes_title=OLD_TITLE))


class UpdateValidationTests(unittest.TestCase):
    def test_reviewed_rename(self):
        self.assertEqual(validate_song_update([song()], [song(NEW_TITLE)]),
                         [{'from': OLD_TITLE, 'to': NEW_TITLE}])

    def test_rename_allows_new_chart_information(self):
        self.assertEqual(validate_song_update([song(charts={})],
                         [song(NEW_TITLE, charts={'SP': {'A': {'level': 12}}})]),
                         [{'from': OLD_TITLE, 'to': NEW_TITLE}])

    def test_rename_requires_matching_identity(self):
        for field in ('artist', 'genre', 'series'):
            for value in (None, '', 'different'):
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(ValueError, 'Songs disappeared'):
                        validate_song_update([song()], [song(NEW_TITLE, **{field: value})])
            with self.subTest(field=field, missing_in_both=True):
                with self.assertRaisesRegex(ValueError, 'Songs disappeared'):
                    validate_song_update([song(**{field: None})],
                                         [song(NEW_TITLE, **{field: None})])

    def test_unreviewed_variants_and_original_song_are_not_aliases(self):
        for title in (OLD_TITLE.replace('☆', '★'), NEW_TITLE.lower(),
                      NEW_TITLE.replace('!! ', '!!'), '恋する☆宇宙戦争っ!!'):
            with self.subTest(title=title):
                with self.assertRaisesRegex(ValueError, 'Songs disappeared'):
                    validate_song_update([song()], [song(title)])

    def test_rename_is_directional(self):
        with self.assertRaisesRegex(ValueError, 'Songs disappeared'):
            validate_song_update([song(NEW_TITLE)], [song()])

    def test_same_count_replacement_does_not_hide_deletion(self):
        with self.assertRaisesRegex(ValueError, 'Songs disappeared.*Other song'):
            validate_song_update([song(), song('Other song')],
                                 [song(NEW_TITLE), song('Unrelated addition')])

    def test_real_removal_still_fails(self):
        with self.assertRaisesRegex(ValueError, 'Songs disappeared'):
            validate_song_update([song()], [])

    def test_unchanged_titles_and_additions(self):
        self.assertEqual(validate_song_update([song(NEW_TITLE)],
                         [song(NEW_TITLE), song('New song')]), [])

    def test_ambiguous_aliases_fail_even_with_manual_override(self):
        for old, new in (([song(), song(NEW_TITLE)], [song(NEW_TITLE)]),
                         ([song()], [song(), song(NEW_TITLE)])):
            for allow in (False, True):
                with self.subTest(previous=old, current=new, allow=allow):
                    with self.assertRaisesRegex(ValueError, 'Ambiguous reviewed title rename'):
                        validate_song_update(old, new, allow_removals=allow)

    def test_duplicate_titles_fail(self):
        for old, new in (([song(), song()], [song(NEW_TITLE)]),
                         ([song()], [song(NEW_TITLE), song(NEW_TITLE)])):
            with self.subTest(previous=old, current=new):
                with self.assertRaisesRegex(ValueError, 'duplicate song title'):
                    validate_song_update(old, new)

    def test_manual_removal_override_remains_available(self):
        self.assertEqual(validate_song_update([song()], [], allow_removals=True), [])


class OutputProtectionTests(unittest.TestCase):
    def run_offline(self, source, output):
        with patch.object(sys, 'argv', ['fetch_bemaniwiki.py', '--html', str(source),
                                       '--output', str(output)]):
            with contextlib.redirect_stdout(io.StringIO()) as log:
                main()
        return log.getvalue()

    def test_rename_updates_outputs_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'source.html', root / 'data'
            source.write_bytes(sample_page(OLD_TITLE))
            self.run_offline(source, output)
            source.write_bytes(sample_page())
            self.assertIn('Reviewed title rename:', self.run_offline(source, output))
            payload = json.loads((output / 'bemaniwiki-iidx34.json').read_text('utf-8'))
            status = json.loads((output / 'bemaniwiki-iidx34-status.json').read_text('utf-8'))
            titles = {s['title'] for s in payload['songs']}
            self.assertEqual(payload['song_count'], 30)
            self.assertIn(NEW_TITLE, titles)
            self.assertNotIn(OLD_TITLE, titles)
            self.assertTrue(status['data_changed'])
            self.assertEqual(status['title_changes'], [{'from': OLD_TITLE, 'to': NEW_TITLE}])
            rows = list(csv.DictReader(io.StringIO(
                (output / 'bemaniwiki-iidx34.csv').read_text('utf-8-sig'))))
            self.assertEqual(len(rows), 30 * 9)
            self.assertEqual({r['title'] for r in rows}, titles)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            self.run_offline(source, output)
            for name in ('bemaniwiki-iidx34.json', 'bemaniwiki-iidx34.csv'):
                self.assertEqual((output / name).read_bytes(), before[name])
            status = json.loads((output / 'bemaniwiki-iidx34-status.json').read_text('utf-8'))
            self.assertFalse(status['data_changed'])
            self.assertEqual(status['title_changes'], [])

    def test_rejected_update_preserves_all_previous_files(self):
        for failure in ('removal', 'identity', 'table_mismatch'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, output = root / 'source.html', root / 'data'
                source.write_bytes(sample_page(OLD_TITLE))
                self.run_offline(source, output)
                payload = json.loads((output / 'bemaniwiki-iidx34.json').read_text('utf-8'))
                if failure == 'removal':
                    extra = copy.deepcopy(payload['songs'][0])
                    extra['title'] = 'Actually removed song'
                    payload['songs'].append(extra)
                    payload['song_count'] += 1
                elif failure == 'identity':
                    next(s for s in payload['songs'] if s['title'] == OLD_TITLE)['artist'] = 'Other artist'
                (output / 'bemaniwiki-iidx34.json').write_text(
                    json.dumps(payload, ensure_ascii=False), encoding='utf-8')
                before = {p.name: p.read_bytes() for p in output.iterdir()}
                source.write_bytes(sample_page(notes_title=OLD_TITLE if failure == 'table_mismatch' else None))
                with self.assertRaises(ValueError):
                    self.run_offline(source, output)
                self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
