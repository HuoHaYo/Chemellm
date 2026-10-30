import assert from 'node:assert/strict'
import http from 'node:http'
import { once } from 'node:events'
import { test } from 'node:test'
import { createKernel } from '../lib/kernel.js'
import { createProxy } from '../lib/proxy.js'
import { createTools } from '../lib/tools.js'
import { apply } from '../index.js'

async function serve(t, handler) {
  const server = http.createServer(handler)
  server.listen(0, '127.0.0.1')
  await once(server, 'listening')
  t.after(() => new Promise((resolve) => { server.close(resolve); server.closeAllConnections() }))
  return 'http://127.0.0.1:' + server.address().port
}

test('configured endpoint and Host token cover API, preview, and bundle streams', async (t) => {
  const seen = []
  const binary = Buffer.from([0, 1, 2, 127, 255])
  const endpoint = await serve(t, async (req, res) => {
    seen.push({ url: req.url, token: req.headers['x-kernel-token'] })
    if (req.headers['x-kernel-token'] !== 'host-secret') { res.writeHead(401); res.end('{}'); return }
    if (req.url === '/v1/health') {
      res.end(JSON.stringify({ ok: true, version: '0.1.0', phaseGate: 'advisory' }))
    } else if (req.url.startsWith('/v1/artifacts/') || req.url.startsWith('/v1/bundles/')) {
      res.writeHead(200, { 'content-type': 'application/octet-stream', 'content-disposition': 'attachment; filename="result.zip"' })
      res.end(binary)
    } else {
      let body = ''
      for await (const chunk of req) body += chunk
      res.end(JSON.stringify({ url: req.url, body: body ? JSON.parse(body) : null }))
    }
  })
  const kernel = createKernel({ endpoint, token: 'host-secret', autostart: false }, process.cwd())
  t.after(() => kernel.dispose())
  assert.equal(await kernel.ensure(), true)
  assert.deepEqual(await kernel.request('/v1/projects', { method: 'POST', body: { name: '工程' } }), {
    url: '/v1/projects', body: { name: '工程' },
  })
  const panel = await serve(t, createProxy(kernel))
  const response = await fetch(panel + '/chemellm/api/projects?limit=2', {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-kernel-token': 'browser-value' },
    body: JSON.stringify({ name: '面板工程' }),
  })
  assert.deepEqual(await response.json(), { url: '/v1/projects?limit=2', body: { name: '面板工程' } })
  for (const route of ['/chemellm/files/a/preview', '/chemellm/files/a/download', '/chemellm/bundles/result.zip?download=1']) {
    const download = await fetch(panel + route)
    assert.deepEqual(Buffer.from(await download.arrayBuffer()), binary)
    assert.match(download.headers.get('content-disposition'), /result.zip/)
  }
  assert.equal((await fetch(panel + '/chemellm/unknown')).status, 404)
  assert.ok(seen.every((entry) => entry.token === 'host-secret'))
})

test('proxy reports kernel failures as JSON and preserves upstream HTTP errors', async (t) => {
  const endpoint = await serve(t, (_req, res) => { res.writeHead(401); res.end('{"detail":"invalid token"}') })
  const kernel = createKernel({ endpoint, autostart: false }, process.cwd())
  t.after(() => kernel.dispose())
  assert.equal(await kernel.ensure(), false)
  await assert.rejects(kernel.request('/v1/projects'), /HTTP 401.*invalid token/)
  const panel = await serve(t, createProxy(kernel))
  assert.equal((await fetch(panel + '/chemellm/api/projects')).status, 401)
  const broken = await serve(t, createProxy({
    ensure: async () => { throw new Error('startup failed') },
  }))
  const response = await fetch(broken + '/chemellm/api/health')
  assert.equal(response.status, 502)
  assert.equal((await response.json()).detail, 'startup failed')
})

test('phase enforcement follows current project state, including generic tools', async () => {
  let phase = 'intake'
  const executed = []
  const tools = Object.fromEntries(createTools(async (route, init) => {
    if (route === '/v1/tools') return { tools: [{ id: 'ask_user' }], executable: ['pid', 'export_xlsx'] }
    if (!init) return { project: { phase, plan: {}, objects: {}, files: [], requirements: [] } }
    executed.push(init.body)
    return { ok: true }
  }, 'enforce').map((tool) => [tool.name, tool]))
  assert.equal(Object.keys(tools).length, 12)
  const args = { projectId: 'p1', model: 'properties', input: { compound: 'water' } }
  await assert.rejects(tools.chem_calc.execute(args), /intake.*basis/)
  await assert.rejects(tools.chem_calc.execute({ ...args, action: 'list' }), /intake.*basis/)
  await assert.doesNotReject(tools.chem_plan.execute({ projectId: 'p1', action: 'list' }))
  await assert.rejects(tools.chem_tool.execute({ projectId: 'p1', tool: 'pid' }), /basis/)
  assert.deepEqual((await tools.chem_tool.execute({ projectId: 'p1' })).tools, ['pid', 'export_xlsx'])
  phase = 'basis' // Changed through the panel, with no preceding Host tool call.
  await tools.chem_calc.execute(args)
  assert.deepEqual(executed[0], { tool: 'properties', args: { compound: 'water' } })
  phase = 'intake'
  await assert.rejects(tools.chem_tool.execute({ projectId: 'p1', tool: 'export_xlsx' }), /basis/)
  await assert.rejects(tools.chem_calc.execute({ ...args, model: 'typo' }), /无效的 model/)
  await assert.rejects(tools.chem_project.execute({ action: 'typo' }), /无效的 action/)
  await assert.rejects(tools.chem_tool.execute({ projectId: 'p1', tool: 'acceptance' }), /不在内核执行入口/)
})

test('Host registration exposes one plugin and disposes all owned resources', async (t) => {
  const endpoint = await serve(t, (_req, res) => res.end('{"ok":true,"version":"0.1.0","phaseGate":"advisory"}'))
  const cleanups = []
  const names = []
  let proxy
  let prompt
  const ctx = {
    effect(fn) { cleanups.push(fn()) },
    tools: { register(tool) { names.push(tool.name); return () => {} } },
    systemPrompt: { section(value) { prompt = value; return () => {} } },
    webServer: { register(value) { proxy = value; return () => {} } },
  }
  apply(ctx, { endpoint, autostart: false })
  assert.equal(new Set(names).size, 12)
  assert.equal(proxy.path, '/chemellm')
  assert.match(prompt.text, /chem_review/)
  for (const cleanup of cleanups.reverse()) cleanup()
  const service = createKernel({ endpoint, autostart: false }, process.cwd())
  service.dispose()
  assert.equal(await service.ensure(), false)
  await assert.rejects(service.request('/v1/projects'), /已停用/)
})
