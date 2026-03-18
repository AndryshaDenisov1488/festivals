const fs = require('fs')
const path = require('path')

const standalone = path.join(__dirname, '..', '.next', 'standalone')
const publicDir = path.join(__dirname, '..', 'public')
const staticDir = path.join(__dirname, '..', '.next', 'static')
const standaloneStatic = path.join(standalone, '.next', 'static')

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return
  fs.mkdirSync(dest, { recursive: true })
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name)
    const destPath = path.join(dest, entry.name)
    if (entry.isDirectory()) {
      copyRecursive(srcPath, destPath)
    } else {
      fs.copyFileSync(srcPath, destPath)
    }
  }
}

try {
  if (fs.existsSync(publicDir)) {
    copyRecursive(publicDir, path.join(standalone, 'public'))
  }
  if (fs.existsSync(staticDir)) {
    fs.mkdirSync(path.dirname(standaloneStatic), { recursive: true })
    copyRecursive(staticDir, standaloneStatic)
  }
} catch (e) {
  console.warn('Postbuild copy warning:', e.message)
}
