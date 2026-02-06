#!/usr/bin/env node
import { renderMermaid, THEMES } from 'beautiful-mermaid';
import { readFileSync, writeFileSync } from 'fs';

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node render-svg.mjs <input.mmd> <output.svg> [theme]');
  console.error('Themes:', Object.keys(THEMES).join(', '));
  process.exit(1);
}

const [input, output, themeName] = args;
const diagram = readFileSync(input, 'utf-8');
const options = themeName && THEMES[themeName] ? THEMES[themeName] : {};

const svg = await renderMermaid(diagram, options);
writeFileSync(output, svg);
console.log(`Rendered ${output}${themeName ? ` (theme: ${themeName})` : ''}`);
