#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function exists(p) {
  return fs.existsSync(path.join(__dirname, '..', p));
}

function tree(dir, prefix = '') {
  const p = path.join(__dirname, '..', dir);
  if (!fs.existsSync(p)) return `${dir} (missing)`;
  const out = [];
  const entries = fs.readdirSync(p);
  for (const e of entries) {
    out.push(prefix + e);
    const full = path.join(p, e);
    if (fs.statSync(full).isDirectory()) {
      const sub = tree(path.join(dir, e), prefix + '  ');
      out.push(sub);
    }
  }
  return out.join('\n');
}

const required = [
  'dist/main/main.js',
  'dist/renderer/index.html'
];

let ok = true;
for (const r of required) {
  if (!exists(r)) {
    console.error(`MISSING: ${r}`);
    ok = false;
  }
}

if (!ok) {
  console.error('\nContents of dist:');
  console.error(tree('dist'));
  process.exit(1);
}

console.log('dist check OK');
