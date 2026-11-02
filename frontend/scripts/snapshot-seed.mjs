#!/usr/bin/env node
// Builds frontend/data/seed-opportunities.json from a verified research dataset.
// Usage: node scripts/snapshot-seed.mjs <dir-with-hackathons.json-and-internships.json> [YYYY-MM-DD]
// Only public listing fields are copied. Personal notes in the source dataset
// (fit, chance, resume variant, priority, override reasons) are dropped on purpose.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const [, , srcDir, snapshotDate = new Date().toISOString().slice(0, 10)] = process.argv
if (!srcDir) {
  console.error('usage: node scripts/snapshot-seed.mjs <dataset-dir> [YYYY-MM-DD]')
  process.exit(2)
}
const read = (f) => JSON.parse(fs.readFileSync(path.join(srcDir, f), 'utf8'))
const clean = (s) => (typeof s === 'string' ? s.trim() : s ?? null)

const hackathons = read('hackathons.json').map((h) => ({
  kind: 'hackathon',
  title: clean(h.name),
  organizer: clean(h.organizer),
  url: clean(h.url),
  mode: clean(h.mode),
  city: clean(h.city),
  fee: clean(h.fee),
  deadline: clean(h.reg_deadline),
  event_dates: clean(h.event_dates),
  team: clean(h.team),
  reward: clean(h.prize),
  eligibility: clean(h.eligibility),
  topics: clean(h.themes),
  verified: Boolean(h.verified),
}))

const internships = read('internships.json').map((i) => ({
  kind: 'internship',
  title: clean(i.name),
  organizer: clean(i.organizer),
  url: clean(i.url),
  mode: clean(i.mode),
  city: clean(i.city),
  fee: 'free',
  deadline: clean(i.apply_deadline),
  event_dates: [clean(i.duration), clean(i.start)].filter(Boolean).join('; '),
  team: 'solo (1)',
  reward: clean(i.stipend),
  eligibility: clean(i.eligibility),
  topics: clean(i.skills),
  verified: Boolean(i.verified),
}))

const out = {
  snapshot_date: snapshotDate,
  note:
    'Demo seed. Public listing fields copied from a hand-verified research run on ' +
    snapshotDate +
    '. Deadlines and details can change; always confirm on the organiser page.',
  items: [...hackathons, ...internships],
}
const here = path.dirname(fileURLToPath(import.meta.url))
const dest = path.join(here, '..', 'data', 'seed-opportunities.json')
fs.writeFileSync(dest, JSON.stringify(out, null, 1) + '\n')
console.log(`wrote ${out.items.length} items to ${dest}`)
