#!/usr/bin/env node
import { renderMermaid, THEMES } from 'beautiful-mermaid';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { spawnSync } from 'child_process';

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node render-png.mjs <input.mmd> <output.png> [theme] [width] [height]');
  console.error('Themes:', Object.keys(THEMES).join(', '));
  console.error('Width/height default to the SVG\'s native size; pass values to override.');
  process.exit(1);
}

const [input, output, themeName, widthArg, heightArg] = args;

const THEME_BG = {
  'github-dark': '#0d1117', 'github-light': '#ffffff',
  'tokyo-night': '#1a1b26', 'tokyo-night-storm': '#24283b', 'tokyo-night-light': '#d5d6db',
  'catppuccin-mocha': '#1e1e2e', 'catppuccin-latte': '#eff1f5',
  'dracula': '#282a36',
  'nord': '#2e3440', 'nord-light': '#eceff4',
  'solarized-dark': '#002b36', 'solarized-light': '#fdf6e3',
  'one-dark': '#282c34',
  'zinc-dark': '#09090b', 'zinc-light': '#ffffff',
};

const CHROME_PATHS = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  process.env.CHROME_PATH,
].filter(Boolean);

const diagram = readFileSync(input, 'utf-8');
const options = themeName && THEMES[themeName] ? THEMES[themeName] : {};
const bg = (themeName && THEME_BG[themeName]) || '#ffffff';

const svg = await renderMermaid(diagram, options);

// Pull intrinsic dimensions from the root <svg> tag so the screenshot matches.
const widthMatch = svg.match(/<svg[^>]*\bwidth="([0-9.]+)"/);
const heightMatch = svg.match(/<svg[^>]*\bheight="([0-9.]+)"/);
const svgWidth = widthMatch ? Math.ceil(parseFloat(widthMatch[1])) : 1200;
const svgHeight = heightMatch ? Math.ceil(parseFloat(heightMatch[1])) : 800;

const winWidth = widthArg ? parseInt(widthArg, 10) : svgWidth + 40;
const winHeight = heightArg ? parseInt(heightArg, 10) : svgHeight + 40;

const workDir = mkdtempSync(join(tmpdir(), 'beautiful-mermaid-'));
const svgPath = join(workDir, 'diagram.svg');
const htmlPath = join(workDir, 'wrapper.html');
const userDataDir = join(workDir, 'chrome-profile');

writeFileSync(svgPath, svg);
writeFileSync(htmlPath, `<!DOCTYPE html>
<html><head><style>
  *{margin:0;padding:0}
  html,body{background:${bg}}
  img{display:block}
</style></head>
<body><img src="file://${svgPath}" /></body></html>`);

const chrome = CHROME_PATHS.find(p => {
  try { return spawnSync(p, ['--version'], { stdio: 'ignore' }).status === 0; }
  catch { return false; }
});

if (!chrome) {
  console.error('Chrome not found. Set $CHROME_PATH or install Chrome/Chromium.');
  process.exit(1);
}

const result = spawnSync(chrome, [
  '--headless=new',
  '--disable-gpu',
  '--hide-scrollbars',
  `--user-data-dir=${userDataDir}`,
  `--window-size=${winWidth},${winHeight}`,
  `--screenshot=${output}`,
  `file://${htmlPath}`,
], { stdio: 'pipe' });

rmSync(workDir, { recursive: true, force: true });

if (result.status !== 0) {
  console.error('Chrome screenshot failed:');
  console.error(result.stderr?.toString());
  process.exit(result.status ?? 1);
}

console.log(`Rendered ${output} (${winWidth}x${winHeight}${themeName ? `, theme: ${themeName}` : ''})`);
