#!/usr/bin/env node
// Prebuild hook: mirror ../docs/screenshots/**/*.png into ./public/screenshots/
// preserving subfolder structure. Lets the Astro landing reference PNGs via
// /synology-photos-video-enhancer/screenshots/<file> without a duplicate source copy.
//
// Mirrors in sync mode: any PNG in ./public/screenshots/ that is NOT in the
// source tree gets removed, so renames/deletes in docs/screenshots/ propagate
// cleanly and stale files don't leak into the Astro build.

import { mkdirSync, readdirSync, copyFileSync, rmSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SRC  = join(__dirname, '..', '..', 'docs', 'screenshots')
const DEST = join(__dirname, '..', 'public', 'screenshots')

function listPngs(dir, prefix = '') {
  const result = new Set()
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name
    if (entry.isDirectory()) {
      for (const child of listPngs(join(dir, entry.name), rel)) result.add(child)
    } else if (entry.isFile() && entry.name.endsWith('.png')) {
      result.add(rel)
    }
  }
  return result
}

function sync(srcDir, destDir) {
  mkdirSync(destDir, { recursive: true })
  const srcFiles = listPngs(srcDir)
  let destFiles = new Set()
  try {
    destFiles = listPngs(destDir)
  } catch {
    // dest didn't exist before mkdir — nothing to delete.
  }

  let copied = 0
  for (const rel of srcFiles) {
    const destPath = join(destDir, rel)
    mkdirSync(dirname(destPath), { recursive: true })
    copyFileSync(join(srcDir, rel), destPath)
    copied += 1
  }

  let removed = 0
  for (const rel of destFiles) {
    if (srcFiles.has(rel)) continue
    rmSync(join(destDir, rel), { force: true })
    removed += 1
  }

  return { copied, removed }
}

const { copied, removed } = sync(SRC, DEST)
const suffix = removed > 0 ? ` (removed ${removed} stale)` : ''
console.log(`copy-screenshots: mirrored ${copied} PNG(s) from docs/screenshots → site/public/screenshots${suffix}`)
