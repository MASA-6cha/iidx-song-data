import sys
import unittest
from pathlib import Path
from lxml import html
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_bemaniwiki import chart, grid, parse_page, csv_bytes

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

if __name__ == '__main__':
    unittest.main()
