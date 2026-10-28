#!/usr/bin/env node
/**
 * Headless render check: visits every view, fails on any console or page error,
 * and asserts the things that have actually broken before.
 *
 *   node scripts/check.mjs            # fail on error
 *   node scripts/check.mjs --shots    # also write screenshots to .shots/
 *
 * Needs a server on :8000 (make serve) and `npm i -D playwright`.
 */
import { chromium } from 'playwright';
import { mkdirSync, readFileSync } from 'fs';

// expected figures come from the checked-in baseline, never from index.json (see CLAUDE.md)
const T = JSON.parse(readFileSync(new URL('../data-baseline.json', import.meta.url))).totals;
const fmt = n => n.toLocaleString('en-US');

const BASE = process.env.CW_BASE || 'http://localhost:8000/index.html';
const SHOTS = process.argv.includes('--shots');
if (SHOTS) mkdirSync('.shots', { recursive: true });

const problems = [];
const checks = [];
function assert(cond, msg) {
  checks.push({ ok: !!cond, msg });
  if (!cond) problems.push('assert: ' + msg);
}

// CW_CHROMIUM lets a CI image or sandbox point at a browser Playwright did not install
const exe = process.env.CW_CHROMIUM;
const browser = await chromium.launch(exe ? { executablePath: exe } : {});

async function page(opts = {}) {
  const p = await browser.newPage({ viewport: opts.vp || { width: 1440, height: 940 } });
  if (opts.dark) await p.emulateMedia({ colorScheme: 'dark' });
  p.on('pageerror', e => problems.push(`pageerror: ${e.message}`));
  p.on('console', m => {
    const t = m.text();
    // a missing favicon is not our problem
    if (m.type() === 'error' && !/favicon|404 \(File not found\)/i.test(t)) {
      problems.push(`console: ${t}`);
    }
  });
  p.on('requestfailed', r => {
    if (!/favicon/.test(r.url())) problems.push(`requestfailed: ${r.url()}`);
  });
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.waitForTimeout(1500);
  return p;
}

// ---------- home ----------
{
  const p = await page();
  const figs = await p.$$eval('.fig b', e => e.map(x => x.textContent));
  assert(figs[0] === fmt(T.linked_verses), `home: verses-linked figure is "${figs[0]}", expected ${fmt(T.linked_verses)}`);
  assert(figs[1] === fmt(T.edges), `home: cross-reference figure is "${figs[1]}", expected ${fmt(T.edges)}`);
  assert(await p.isHidden('#trail'), 'home: the verse trail must not show outside the reader');
  if (SHOTS) await p.screenshot({ path: '.shots/home.png', fullPage: false });
  await p.close();
}

// ---------- reader ----------
{
  const p = await page();
  await p.click('.nav button[data-view="read"]');
  await p.waitForTimeout(1200);
  assert((await p.textContent('.ch-h')).trim().length > 0, 'reader: chapter heading is empty');
  const verses = await p.$$('.v');
  assert(verses.length === 31, `reader: Genesis 1 rendered ${verses.length} verses, expected 31`);

  // selecting a verse must populate the reference panel
  const linked = await p.$$('.v.lk');
  assert(linked.length > 0, 'reader: no verse carries cross-references');
  await linked[2].click();
  await p.waitForTimeout(900);
  const refs = await p.$$('.xr');
  assert(refs.length > 0, 'reader: selecting a verse produced no cross-references');
  const quote = await p.textContent('#rquote');
  assert(!/Ã|â€/.test(quote), `reader: mojibake in the verse quote - ${quote.slice(0, 40)}`);

  // place links must exist somewhere with dense geography
  await p.click('.bk[data-b="0"]');
  await p.waitForTimeout(300);
  await p.click('.cp[data-b="0"][data-c="10"]');
  await p.waitForTimeout(1300);
  const pl = await p.$$('.pl');
  assert(pl.length > 10, `reader: Genesis 10 has ${pl.length} place links, expected many`);
  await pl[3].click();
  await p.waitForTimeout(800);
  assert(await p.isVisible('#bub'), 'reader: clicking a place did not open the bubble');
  assert(await p.isVisible('#bgo'), 'reader: the place bubble has no Open map control');
  if (SHOTS) await p.screenshot({ path: '.shots/read.png' });
  await p.close();
}

// ---------- web ----------
{
  const p = await page();
  await p.click('.nav button[data-view="web"]');
  await p.waitForTimeout(8000);
  const n = await p.$$eval('#v-web .fig b', e => e.map(x => x.textContent));
  assert(n[0] === '1,189', `web: chapter count is "${n[0]}", expected 1,189`);
  const drawn = await p.evaluate(() => {
    const c = document.getElementById('arc');
    return c && c.width > 0 && c.height > 0;
  });
  assert(drawn, 'web: the arc canvas has no dimensions');
  if (SHOTS) await p.screenshot({ path: '.shots/web.png' });
  await p.close();
}

// ---------- atlas ----------
{
  const p = await page();
  await p.click('.nav button[data-view="atlas"]');
  await p.waitForTimeout(3500);
  const stops = await p.$$('.stp');
  assert(stops.length > 0, 'atlas: opened with no journey selected');
  const sized = await p.evaluate(() => {
    const c = document.getElementById('mapc');
    return c && c.width > 0 && c.height > 0;
  });
  assert(sized, 'atlas: the map canvas has no dimensions (sized before the view was visible?)');
  if (SHOTS) await p.screenshot({ path: '.shots/atlas.png' });
  await p.close();
}

// ---------- journey markers: one per map point ----------
// A revisit (Bethel, 4 and 8), places openBible puts on one coordinate (Rameses and
// Pi-hahiroth), or places that overlap at this zoom (Bethel and Ai) must share one marker
// carrying their ordinals, never stack. So: every waypoint's ordinal is on exactly one
// marker (counted from the data, not the render code), no marker overlaps another, and
// waypoints at an identical coordinate always share a marker.
{
  const p = await page();
  await p.click('.nav button[data-view="atlas"]');
  await p.waitForTimeout(2500);
  const js = await p.evaluate(() => fetch('data/geo/journeys.json').then(r => r.json()));
  for (let i = 0; i < js.length; i++) {
    await p.selectOption('#jsel', String(i));
    await p.waitForTimeout(700);
    const m = await p.evaluate(() => window.__cwAtlas.markers);
    const ords = m.flatMap(x => x.ords).sort((a, b) => a - b);
    const allOnce = ords.length === js[i].w.length && ords.every((o, k) => o === k + 1);
    const points = new Set(js[i].w.map(w => w.c.join(','))).size;
    let overlap = null;
    for (let a = 0; a < m.length && !overlap; a++)
      for (let b = a + 1; b < m.length; b++)
        if (Math.abs(m[a].x - m[b].x) < m[a].hw + m[b].hw && Math.abs(m[a].y - m[b].y) < 13) {
          overlap = [m[a].txt, m[b].txt]; break;
        }
    assert(allOnce && !overlap && m.length <= points,
      `journey "${js[i].n}": ${m.length} markers for ${points} distinct points, ` +
      `ordinals ${allOnce ? 'each once' : JSON.stringify(ords)}` +
      (overlap ? `, markers ${overlap[0]} and ${overlap[1]} overlap` : ''));
  }
  if (SHOTS) await p.screenshot({ path: '.shots/journey.png' });
  await p.close();
}

// ---------- atlas geometry, at two viewports ----------
// Paul's second journey is the densest overlap of route and kingdom labels. Each viewport
// asserts once, so the count stays fixed however many labels are placed.
for (const vp of [{ width: 1440, height: 940 }, { width: 1400, height: 920 }]) {
  const p = await page({ vp });
  const tag = `atlas ${vp.width}x${vp.height}`;
  await p.click('.nav button[data-view="atlas"]');
  await p.waitForTimeout(2500);
  const opt = await p.$$eval('#jsel option', o => (o.find(x => /second journey/i.test(x.textContent)) || {}).value);
  await p.selectOption('#jsel', opt);
  await p.waitForTimeout(1200);
  const g = await p.evaluate(() => {
    const c = document.getElementById('mapc'), A = window.__cwAtlas;
    const crossed = A.kingdomLabels.filter(k => A.routeSegs.some(s => A.segHitsRect(s[0], s[1], k.r)))
      .map(k => k.n);
    return { bitmapH: c.height / devicePixelRatio, shownH: c.clientHeight,
             labels: A.kingdomLabels.length, segs: A.routeSegs.length, crossed };
  });
  // the map box shrinks when the stop strip appears; a stale bitmap renders squashed
  assert(Math.abs(g.bitmapH - g.shownH) <= 1 && g.segs > 0 && g.labels > 0 && !g.crossed.length,
    `${tag}: bitmap ${g.bitmapH}px shown at ${g.shownH}px, ${g.segs} route segments, ` +
    `${g.labels} kingdom labels, crossed by the route: ${JSON.stringify(g.crossed)}`);
  await p.close();
}

// ---------- places ----------
{
  const p = await page();
  await p.click('.nav button[data-view="places"]');
  await p.waitForTimeout(1500);
  const cards = await p.$$('.pcard');
  assert(cards.length > 20, `places: rendered ${cards.length} cards, expected a full first page`);
  await p.fill('#pq', 'kerak');
  await p.waitForTimeout(600);
  const hit = await p.$$eval('.pcard .pn', e => e.map(x => x.textContent));
  assert(hit.some(h => /Moab/.test(h)), 'places: searching a modern site name ("kerak") should find Moab');
  if (SHOTS) await p.screenshot({ path: '.shots/places.png' });
  await p.close();
}

// ---------- command palette ----------
{
  const p = await page();
  await p.keyboard.press('Control+k');
  await p.waitForTimeout(400);
  assert(await p.isVisible('#palscrim'), 'palette: Ctrl-K did not open search');
  await p.fill('#palq', 'john 3:16');
  await p.waitForTimeout(500);
  const first = await p.textContent('.pr .pr-n');
  assert(/John 3:16/.test(first), `palette: "john 3:16" gave "${first}"`);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(1600);
  assert(/John 3/.test(await p.textContent('.ch-h')), 'palette: Enter did not navigate to the passage');
  const sel = await p.textContent('#rref');
  assert(/John 3:16/.test(sel), `palette: landed without selecting the verse (panel shows "${sel}")`);
  // the side panel updating is not the same as the reader showing you the verse
  const inView = await p.evaluate(() => {
    const el = document.querySelector('.v.on');
    if (!el) return 'nothing selected';
    const r = el.getBoundingClientRect();
    const h = document.getElementById('read').getBoundingClientRect();
    return (r.top >= h.top - 2 && r.bottom <= h.bottom + 2)
      ? true : `verse at y=${Math.round(r.top)}, pane is ${Math.round(h.top)}..${Math.round(h.bottom)}`;
  });
  assert(inView === true, `palette: selected verse was not scrolled into view (${inView})`);
  if (SHOTS) await p.screenshot({ path: '.shots/search.png' });
  await p.close();
}

// ---------- dark + mobile ----------
{
  const p = await page({ dark: true });
  const bg = await p.evaluate(() => getComputedStyle(document.body).backgroundColor);
  assert(!/255, 255, 255/.test(bg), `dark: body background is ${bg}, expected a dark token`);
  if (SHOTS) await p.screenshot({ path: '.shots/dark.png' });
  await p.close();
}
{
  const p = await page({ vp: { width: 390, height: 780 } });
  assert(await p.isVisible('.tabs'), 'mobile: the bottom tab bar is not visible at 390px');
  const hamburgers = await p.evaluate(() =>
    [...document.querySelectorAll('.topin .ibtn svg path')]
      .filter(el => (el.getAttribute('d').match(/M2 /g) || []).length >= 3).length);
  assert(hamburgers <= 1, `mobile: ${hamburgers} hamburger-looking icons in the header, expected 1`);
  const scroll = await p.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth);
  assert(!scroll, 'mobile: the page scrolls horizontally at 390px');
  if (SHOTS) await p.screenshot({ path: '.shots/mobile.png' });
  await p.close();
}

await browser.close();

const failed = checks.filter(c => !c.ok).length;
console.log(`${checks.length - failed}/${checks.length} assertions passed`);
if (problems.length) {
  console.log('\nproblems:');
  for (const p of problems) console.log('  -', p);
  process.exit(1);
}
console.log('no console or page errors across all views');
