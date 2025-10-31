#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function copyFile(src, dest) {
  ensureDir(path.dirname(dest));
  fs.copyFileSync(src, dest);
  console.log(`copied ${src} -> ${dest}`);
}

function copyRenderer() {
  const srcDir = path.join(__dirname, '..', 'src', 'renderer');
  const outDir = path.join(__dirname, '..', 'dist', 'renderer');
  ensureDir(outDir);
  const entries = fs.readdirSync(srcDir, { withFileTypes: true });
  for (const e of entries) {
    if (e.isFile()) {
      if (e.name.endsWith('.html') || e.name.endsWith('.css')) {
        copyFile(path.join(srcDir, e.name), path.join(outDir, e.name));
      }
    } else if (e.isDirectory()) {
      // copy files directly under subdirs as well
      const subdir = path.join(srcDir, e.name);
      const files = fs.readdirSync(subdir);
      for (const f of files) {
        if (f.endsWith('.html') || f.endsWith('.css')) {
          copyFile(path.join(subdir, f), path.join(outDir, f));
        }
      }
    }
  }
}

function copyPreload() {
  const src = path.join(__dirname, '..', 'src', 'main', 'preload.js');
  const dest = path.join(__dirname, '..', 'dist', 'main', 'preload.js');
  if (fs.existsSync(src)) copyFile(src, dest);
}

function main() {
  copyRenderer();
  copyPreload();
}

main();
