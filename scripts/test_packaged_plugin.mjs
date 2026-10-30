/** Run the staged plugin with its actual portable runtime and isolated data. */
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import http from 'node:http'
import path from 'node:path'
import { once } from 'node:events'
import { pathToFileURL } from 'node:url'
import { createHash, randomUUID } from 'node:crypto'

const pluginDir = path.resolve(process.argv[2] || 'dist/dsh-chemellm')
const manifest = JSON.parse(await fs.readFile(path.join(pluginDir, 'package.json'), 'utf8'))
assert.equal(manifest.name, '@local/dsh-chemellm')
const checksums = await fs.readFile(path.join(pluginDir, 'SHA256SUMS.txt'), 'utf8')
for (const entry of ['package.json', 'index.js', 'client.js', 'lib/kernel.js', 'lib/tools.js', 'lib/proxy.js', 'runtime/kernel/server.py']) {
  const line = checksums.split(/\r?\n/).find((item) => item.endsWith('  ' + entry))
  assert.ok(line, 'missing checksum: ' + entry)
  const hash = createHash('sha256').update(await fs.readFile(path.join(pluginDir, entry))).digest('hex')
  assert.equal(hash, line.trim().split(/\s+/)[0], 'checksum mismatch: ' + entry)
}
for (const entry of ['data', '.chem', 'work_absorption']) {
  assert.equal(await fs.stat(path.join(pluginDir, 'runtime', entry)).then(() => true, () => false), false)
}
const { createKernel } = await import(pathToFileURL(path.join(pluginDir, 'lib/kernel.js')))
const { createTools } = await import(pathToFileURL(path.join(pluginDir, 'lib/tools.js')))
const { createProxy } = await import(pathToFileURL(path.join(pluginDir, 'lib/proxy.js')))
// Use an ordinary workspace directory: Windows temp ACLs can prevent a
// portable child interpreter from creating subdirectories in Node's mkdtemp.
const temporary = path.resolve('data/qa/package-test-' + randomUUID())
await fs.mkdir(temporary, { recursive: true })
const reserve = http.createServer()
reserve.listen(0, '127.0.0.1')
await once(reserve, 'listening')
const port = reserve.address().port
await new Promise((resolve) => reserve.close(resolve))
const kernel = createKernel({ endpoint: 'http://127.0.0.1:' + port, token: 'package-test', phaseGate: 'enforce', dataDir: temporary }, pluginDir)
const panel = http.createServer(createProxy(kernel))
try {
  if (!await kernel.ensure()) {
    // Include the child's import/startup diagnostics in a failed smoke test.
    await kernel.request('/v1/health')
    throw new Error('portable kernel failed to start')
  }
  const health = await kernel.request('/v1/health')
  assert.equal(health.phaseGate, 'enforce')
  assert.equal(health.projectCount, 0)
  assert.equal(health.dataDir, temporary)
  const tools = Object.fromEntries(createTools(kernel.request, 'enforce').map((tool) => [tool.name, tool]))
  const created = await tools.chem_project.execute({ action: 'create', name: '分发包验证' })
  const projectId = created.project.projectId
  await assert.rejects(tools.chem_tool.execute({ projectId, tool: 'export_xlsx' }), /basis/)
  await tools.chem_requirements.execute({ projectId, action: 'save', items: [{ code: 'R01', title: '物性报告' }] })
  await tools.chem_plan.execute({ projectId, action: 'save', deliverables: [{ key: 'report', title: '报告', requirementCodes: ['R01'], formats: ['md'] }] })
  await tools.chem_object.execute({ projectId, action: 'save', kind: 'basis', key: 'feed', quantities: [{
    key: 'flow', value: 100, unit: 'kmol/h', origin: 'assumption', conditions: '298 K, 1 atm', rationale: '分发包回归验证',
  }] })
  const calc = await tools.chem_calc.execute({ projectId, model: 'properties', input: { compound: 'water' } })
  assert.ok(calc.calculationId)
  const report = await tools.chem_generate.execute({ projectId, kind: 'report', body: '分发包回归验证报告', formats: ['md'] })
  assert.ok((await tools.chem_review.execute({ projectId })).review.ready)
  const bundle = await tools.chem_bundle.execute({ projectId })
  panel.listen(0, '127.0.0.1')
  await once(panel, 'listening')
  const base = 'http://127.0.0.1:' + panel.address().port
  const artifact = report.artifacts[0]
  const link = await tools.chem_artifact.execute({ projectId, artifactId: artifact.artifactId })
  assert.equal((await fetch(base + link.url)).status, 200)
  assert.equal((await fetch(base + '/chemellm/bundles/' + encodeURIComponent(bundle.bundle.name))).status, 200)
  const project = await tools.chem_project.execute({ action: 'get', projectId })
  assert.ok(project.project.bundle)
  console.log('PACKAGED PLUGIN OK: portable autostart, token, enforce gate, 12 tools, report, review, bundle, proxy downloads')
} finally {
  panel.closeAllConnections()
  if (panel.listening) await new Promise((resolve) => panel.close(resolve))
  kernel.dispose()
  await fs.rm(temporary, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 })
}
