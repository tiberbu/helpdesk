/**
 * Fail the build if the gzipped widget bundle exceeds 50KB (51200 bytes).
 * Usage: node scripts/check-bundle-size.mjs
 */
import { createReadStream, statSync } from 'fs'
import { createGzip } from 'zlib'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const BUNDLE = resolve(__dirname, '../../helpdesk/public/js/helpdesk-chat.iife.js')
const MAX_GZIP_BYTES = 51200 // 50 KB

async function getGzipSize(filePath) {
  return new Promise((resolve, reject) => {
    let size = 0
    const gzip = createGzip({ level: 9 })
    const stream = createReadStream(filePath)
    stream.on('error', reject)
    gzip.on('error', reject)
    gzip.on('data', (chunk) => { size += chunk.length })
    gzip.on('end', () => resolve(size))
    stream.pipe(gzip)
  })
}

try {
  statSync(BUNDLE)
} catch {
  console.error(`Bundle not found: ${BUNDLE}`)
  console.error('Run "yarn build" first.')
  process.exit(1)
}

const gzipSize = await getGzipSize(BUNDLE)
const kb = (gzipSize / 1024).toFixed(2)

console.log(`Bundle gzip size: ${kb} KB (${gzipSize} bytes)`)

if (gzipSize > MAX_GZIP_BYTES) {
  console.error(`❌ FAIL: Bundle exceeds 50KB limit (${MAX_GZIP_BYTES} bytes). Got ${gzipSize} bytes.`)
  process.exit(1)
} else {
  console.log(`✅ PASS: Bundle is within the 50KB gzip limit.`)
}
