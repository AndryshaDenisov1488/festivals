/**
 * Verifies standalone build structure after npm run build.
 * Run from web/ directory: node scripts/verify-standalone.js
 */
const fs = require('fs')
const path = require('path')

const webDir = path.join(__dirname, '..')
const standaloneDir = path.join(webDir, '.next', 'standalone')
const staticDir = path.join(standaloneDir, '.next', 'static')
const publicDir = path.join(standaloneDir, 'public')

const checks = [
  { name: 'standalone/', path: standaloneDir },
  { name: 'standalone/server.js', path: path.join(standaloneDir, 'server.js') },
  { name: 'standalone/.next/static', path: staticDir },
  { name: 'standalone/public', path: publicDir }
]

let ok = true
for (const c of checks) {
  const exists = fs.existsSync(c.path)
  if (!exists) ok = false
  console.log(exists ? '  ✓' : '  ✗', c.name)
}

if (!ok) {
  console.error('\nMissing files. Run: npm run build')
  process.exit(1)
}

const chunksDir = path.join(staticDir, 'chunks')
if (fs.existsSync(chunksDir)) {
  const files = fs.readdirSync(chunksDir)
  console.log('\n  Chunks:', files.length, 'files')
}

const absStandalone = path.resolve(standaloneDir)
console.log('\nTo run:')
console.log('  cd', absStandalone)
console.log('  node server.js')
console.log('\nOr: npm start (from web/)')
process.exit(0)
