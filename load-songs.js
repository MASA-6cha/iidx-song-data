/** Import a public Raw JSON URL. Never put a GitHub access token in browser code. */
export async function loadSongs(url, { signal } = {}) {
  const response = await fetch(url, { signal, credentials: "omit" });
  if (!response.ok) {
    throw new Error(`曲データ取得エラー: HTTP ${response.status}`);
  }
  const document = await response.json();
  if (document?.schema !== "iidx-info-exporter/songs/1" ||
      !Array.isArray(document.songs)) {
    throw new Error("未対応の曲データ形式です");
  }
  const songsById = new Map();
  for (const song of document.songs) {
    if (!Number.isInteger(song.music_id) || !song.charts ||
        Array.isArray(song.charts) || typeof song.charts !== "object" ||
        songsById.has(song.music_id)) {
      throw new Error("曲IDまたは譜面データが不正です");
    }
    songsById.set(song.music_id, song);
  }
  return { document, songsById };
}

// Usage:
// const { songsById } = await loadSongs(config.songsJsonUrl);
// const song = songsById.get(19071);
// const chart = song?.charts.SPA;
// console.log(song?.title, chart?.bpm_display.text, chart?.radar["SOF-LAN"]);
