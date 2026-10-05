"""BEMANIWiki IIDX 34 collector. Fail closed before replacing previous data."""
import argparse
import csv
import io
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from lxml import html

PAGE = 'beatmania IIDX 34 ZINRAI/新曲リスト'
SOURCE = 'https://bemaniwiki.com/index.php?' + urllib.parse.urlencode({'cmd': 'read', 'page': PAGE}, quote_via=urllib.parse.quote)
AGENT = 'IIDX34SongCollector/1.0'
DIFFICULTIES = [('SP', d) for d in ['B', 'N', 'H', 'A', 'L']] + [('DP', d) for d in ['N', 'H', 'A', 'L']]


def text(cell):
    clone = html.fromstring(html.tostring(cell))
    for node in clone.xpath('.//a[contains(@class,"anchor_super")]|.//sup'):
        node.drop_tree()
    for node in clone.xpath('.//br'):
        node.tail = ' ' + (node.tail or '')
    return re.sub(r'\s+', ' ', clone.text_content()).strip()


def grid(table):
    """Expand HTML row/column spans; preserve section separators."""
    slots = {}
    result = []
    for ri, row in enumerate(table.xpath('./tr|./thead/tr|./tbody/tr|./tfoot/tr')):
        ci = 0
        for cell in row.xpath('./th|./td'):
            while (ri, ci) in slots:
                ci += 1
            rs, cs = int(cell.get('rowspan', '1')), int(cell.get('colspan', '1'))
            if not 1 <= rs <= 1000 or not 1 <= cs <= 100:
                raise ValueError('Invalid table span')
            value = text(cell)
            for dr in range(rs):
                for dc in range(cs):
                    key = (ri + dr, ci + dc)
                    if key in slots:
                        raise ValueError('Overlapping table cells')
                    slots[key] = value
            ci += cs
        cols = [c for r, c in slots if r == ri]
        result.append([slots.get((ri, c), '') for c in range(max(cols, default=-1) + 1)])
    return result


def number(value):
    compact = value.replace(',', '').strip()
    if compact in ['', '-', '－', '—', '?', '？']:
        return None
    if not compact.isdigit():
        raise ValueError('Unrecognized numeric cell: ' + value)
    return int(compact)


def chart(value):
    flags = re.findall(r'\[([^\]]+)\]', value)
    remaining = re.sub(r'\[[^\]]+\]', '', value).strip()
    level = number(remaining)
    if level is not None and not 1 <= level <= 12:
        raise ValueError('Invalid level: ' + value)
    return {'exists': False if remaining in ['-', '－', '—'] else (True if level is not None else None),
            'level': level, 'notes': None, 'flags': flags, 'raw_level': value, 'raw_notes': None}


def parse_page(raw):
    doc = html.fromstring(raw)
    title = doc.find('.//title')
    if title is None or PAGE not in title.text_content():
        raise ValueError('Expected song page; received another page')
    tables = doc.xpath('//*[@id="body"]//table')
    level_tables = [t for t in tables if grid(t) and grid(t)[0] == ['SP'] * 5 + ['DP'] * 4 + ['BPM', 'GENRE', 'TITLE', 'ARTIST']]
    notes_tables = [t for t in tables if grid(t) and grid(t)[0] == ['TITLE'] + ['NOTE(SP)'] * 5 + ['NOTE(DP)'] * 4 + ['TIME', 'MOVIE', 'LAYER']]
    if len(level_tables) != 1 or len(notes_tables) != 1:
        raise ValueError('Song/notes table headers changed')
    expected_levels = ['SP'] * 5 + ['DP'] * 4
    def check_second(rows, prefix, suffix):
        wanted = prefix + [d for _, d in DIFFICULTIES] + suffix
        if rows[1] != wanted:
            raise ValueError('Difficulty column order changed')
    rows = grid(level_tables[0])
    check_second(rows, [], ['BPM', 'GENRE', 'TITLE', 'ARTIST'])
    songs = {}
    group, section, release_date, planned = '', '', None, False
    for row in rows[2:]:
        if len(row) != 13:
            raise ValueError('Unexpected song column count')
        if len(set(row)) == 1:
            label = row[0]
            date = re.search(r'(\d{4}/\d{2}/\d{2})', label)
            if date:
                release_date, section, planned = date.group(1).replace('/', '-'), label, False
            elif '予定' in label:
                release_date, section, planned = None, label, True
            else:
                group, section, release_date, planned = label, '', None, False
            continue
        name = row[11]
        if not name or name in songs:
            raise ValueError('Empty or duplicate song title')
        songs[name] = {'title': name, 'artist': row[12], 'genre': row[10], 'bpm': row[9] or None,
                       'series': 34, 'series_name': 'ZINRAI', 'song_id': None, 'group': group,
                       'section': section, 'release_date': release_date,
                       'availability': 'planned' if planned else 'listed',
                       'time': None, 'duration_seconds': None, 'movie': None, 'layer': None,
                       'charts': {'SP': {}, 'DP': {}}}
        for value, (mode, difficulty) in zip(row[:9], DIFFICULTIES):
            songs[name]['charts'][mode][difficulty] = chart(value)
    if len(songs) < 30:
        raise ValueError('Too few songs; refusing to replace data')
    rows = grid(notes_tables[0])
    check_second(rows, ['TITLE'], ['TIME', 'MOVIE', 'LAYER'])
    seen = set()
    for row in rows[2:]:
        if len(row) != 13:
            raise ValueError('Unexpected notes column count')
        if len(set(row)) == 1:
            continue
        name = row[0]
        if name not in songs or name in seen:
            raise ValueError('Notes/song table title mismatch: ' + name)
        seen.add(name)
        song = songs[name]
        for value, (mode, difficulty) in zip(row[1:10], DIFFICULTIES):
            c = song['charts'][mode][difficulty]
            c['notes'], c['raw_notes'] = number(value), value
            if c['exists'] is False and c['notes'] is not None:
                raise ValueError('Absent chart has notes')
        time = row[10]
        if re.fullmatch(r'\d+:\d{2}', time):
            minutes, seconds = map(int, time.split(':'))
            if seconds >= 60:
                raise ValueError('Invalid song duration')
            song['time'], song['duration_seconds'] = time, minutes * 60 + seconds
        elif time not in ['', ':', '-', '?', '？']:
            raise ValueError('Unrecognized song time: ' + time)
        song['movie'], song['layer'] = row[11] or None, row[12] or None
    if set(songs) != seen:
        raise ValueError('Some songs have no notes row')
    return sorted(songs.values(), key=lambda s: s['title'])


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,text/plain', 'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(request, timeout=45) as response:
        if urllib.parse.urlsplit(response.url).hostname != 'bemaniwiki.com':
            raise ValueError('Unexpected redirect host')
        raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ValueError('Response too large')
        return raw


def check_robots():
    try:
        raw = fetch('https://bemaniwiki.com/robots.txt')
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise
    rules = urllib.robotparser.RobotFileParser()
    rules.parse(raw.decode('utf-8-sig').splitlines())
    if not rules.can_fetch(AGENT, SOURCE):
        raise ValueError('robots.txt disallows retrieval')


def csv_bytes(songs):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(['series', 'title', 'artist', 'genre', 'bpm', 'availability', 'release_date', 'mode', 'difficulty', 'exists', 'level', 'notes', 'flags', 'duration_seconds'])
    for s in songs:
        for mode, difficulty in DIFFICULTIES:
            c = s['charts'][mode][difficulty]
            row = [34, s['title'], s['artist'], s['genre'], s['bpm'], s['availability'], s['release_date'], mode, difficulty,
                   c['exists'], c['level'], c['notes'], '|'.join(c['flags']), s['duration_seconds']]
            # Prevent spreadsheet formula interpretation of external text.
            writer.writerow([("'" + v if v.lstrip().startswith(('=', '+', '-', '@')) else v) if isinstance(v, str) else v for v in row])
    return stream.getvalue().encode('utf-8-sig')


def atomic_write(path, raw):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
        temporary = file.name
        file.write(raw)
    try:
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path, help='Use local HTML for offline validation')
    parser.add_argument('--output', type=Path, default=Path('data'))
    parser.add_argument('--allow-removals', action='store_true')
    args = parser.parse_args()
    if args.html:
        raw = args.html.read_bytes()
    else:
        check_robots()
        raw = fetch(SOURCE)
    songs = parse_page(raw)
    target = args.output / 'bemaniwiki-iidx34.json'
    previous = json.loads(target.read_text('utf-8')) if target.exists() else None
    if previous and not args.allow_removals:
        missing = {s['title'] for s in previous['songs']} - {s['title'] for s in songs}
        if missing:
            raise ValueError('Songs disappeared; review manually: ' + ', '.join(sorted(missing)))
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    changed = not previous or previous['songs'] != songs
    payload = {'schema_version': 1, 'source': {'name': 'BEMANIWiki 2nd', 'url': SOURCE, 'page': PAGE},
               'updated_at': now if changed else previous['updated_at'], 'song_count': len(songs), 'songs': songs}
    # Prepare all serialized outputs before any replacement. GitHub commits them together.
    json_raw = (json.dumps(payload, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    csv_raw = csv_bytes(songs)
    status_raw = (json.dumps({'checked_at': now, 'mode': 'offline' if args.html else 'live', 'song_count': len(songs), 'data_changed': changed}, indent=2) + '\n').encode()
    args.output.mkdir(parents=True, exist_ok=True)
    atomic_write(target, json_raw)
    atomic_write(args.output / 'bemaniwiki-iidx34.csv', csv_raw)
    atomic_write(args.output / 'bemaniwiki-iidx34-status.json', status_raw)
    print(f'OK: {len(songs)} songs; changed={changed}; mode={"offline" if args.html else "live"}')


if __name__ == '__main__':
    main()
