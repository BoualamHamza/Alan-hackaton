#!/usr/bin/env node
// Generate PWA icons from public/logo.jpeg using sharp.
// Run once with: node scripts/generate-pwa-icons.mjs

import { mkdir, access } from 'node:fs/promises';
import { constants } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');
const source = resolve(root, 'public/logo.jpeg');
const iconsDir = resolve(root, 'public/icons');

const HIPPO_PINK_BG = { r: 0xfa, g: 0xb9, b: 0xd1, alpha: 1 };

async function ensureDir(path) {
  await mkdir(path, { recursive: true });
}

async function fileExists(path) {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function makeSquare(sizePx, outPath, { padRatio = 0 } = {}) {
  const innerSize = Math.round(sizePx * (1 - padRatio * 2));
  const logo = await sharp(source)
    .resize(innerSize, innerSize, { fit: 'cover' })
    .toBuffer();

  await sharp({
    create: {
      width: sizePx,
      height: sizePx,
      channels: 4,
      background: HIPPO_PINK_BG,
    },
  })
    .composite([{ input: logo, gravity: 'center' }])
    .png()
    .toFile(outPath);

  console.log(`✓ ${outPath}`);
}

async function main() {
  if (!(await fileExists(source))) {
    console.error(`Source image not found: ${source}`);
    process.exit(1);
  }
  await ensureDir(iconsDir);

  await makeSquare(192, resolve(iconsDir, 'icon-192.png'));
  await makeSquare(512, resolve(iconsDir, 'icon-512.png'));
  // Maskable: ~12% safe-zone padding so the logo survives aggressive masks
  await makeSquare(512, resolve(iconsDir, 'icon-maskable-512.png'), { padRatio: 0.12 });
  await makeSquare(180, resolve(iconsDir, 'apple-touch-icon.png'));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
