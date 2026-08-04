import fs from 'fs';
import path from 'path';
import { emojiSections } from '../docs/.vitepress/theme/components/emojiData.ts';

// ── Auto-detect emojis from interface.json task names ──
function extractEmoji(taskName) {
  const m = taskName.match(/^[\p{Emoji}️‍]+/u);
  return m ? m[0].trim() : null;
}

function collectTaskNames(interfacePath) {
  const root = path.dirname(interfacePath);
  const iface = JSON.parse(fs.readFileSync(interfacePath, 'utf-8'));
  const names = new Set();

  // 1. From inline presets
  for (const preset of (iface.preset || [])) {
    for (const t of (preset.task || [])) {
      if (t.name) names.add(t.name);
    }
  }

  // 2. From imported task JSON files
  for (const imp of (iface.import || [])) {
    try {
      const taskPath = path.resolve(root, imp);
      if (!fs.existsSync(taskPath)) continue;
      const taskFile = JSON.parse(fs.readFileSync(taskPath, 'utf-8'));
      for (const t of (taskFile.task || [])) {
        if (t.name) names.add(t.name);
      }
    } catch { /* skip unreadable import */ }
  }

  return [...names];
}

const taskNames = collectTaskNames('assets/interface.json');
console.log('Task names found:', taskNames.length);

// Extract unique emojis
const usedEmojis = new Set();
for (const name of taskNames) {
  const emoji = extractEmoji(name);
  if (emoji) usedEmojis.add(emoji);
}
console.log('Unique emojis detected:', usedEmojis.size);

// ── Match against emojiData ──
function key(si, ci, ei) {
  return `${si}-${ci}-${ei}`;
}

const used = [];
const matchedEmojis = new Set();

for (let si = 0; si < emojiSections.length; si++) {
  for (let ci = 0; ci < emojiSections[si].categories.length; ci++) {
    for (let ei = 0; ei < emojiSections[si].categories[ci].items.length; ei++) {
      const item = emojiSections[si].categories[ci].items[ei];
      const norm = item.e.replace(/️/g, '');
      for (const ue of usedEmojis) {
        if (norm === ue.replace(/️/g, '')) {
          used.push(key(si, ci, ei));
          matchedEmojis.add(ue);
        }
      }
    }
  }
}

const unmatched = [...usedEmojis].filter(e => !matchedEmojis.has(e));
console.log('Matched:', used.length, '| Unmatched:', unmatched.length, unmatched.join(' '));

const payload = {
  version: 1,
  used,
  lastSaved: new Date().toISOString(),
};

const outPath = 'docs/public/zh_cn/develop/2.2-emoji-usage.json';
fs.writeFileSync(outPath, JSON.stringify(payload, null, 2), 'utf-8');
console.log('Done:', outPath);
