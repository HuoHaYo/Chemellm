import http from 'node:http'
import https from 'node:https'

const ROUTES = [
  ['/chemellm/api/', '/v1/'],
  ['/chemellm/files/', '/v1/artifacts/'],
  ['/chemellm/bundles/', '/v1/bundles/'],
]
const HOP_HEADERS = ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailer', 'transfer-encoding', 'upgrade']

function cleanHeaders(headers) {
  const result = { ...headers }
  for (const name of String(headers.connection || '').split(',')) delete result[name.trim().toLowerCase()]
  for (const name of HOP_HEADERS) delete result[name]
  delete result.host
  return result
}

/** Stream API responses and downloads through the Host; tokens stay here. */
export function createProxy(kernel) {
  return async function proxy(req, res) {
    const url = new URL(req.url || '/', 'http://127.0.0.1')
    const route = ROUTES.find(([prefix]) => url.pathname.startsWith(prefix))
    if (!route) {
      res.writeHead(404, { 'content-type': 'application/json' })
      res.end(JSON.stringify({ error: 'unknown chemellm route' }))
      return
    }
    const fail = (error) => {
      if (res.destroyed) return
      if (res.headersSent) { res.destroy(error); return }
      res.writeHead(502, { 'content-type': 'application/json' })
      res.end(JSON.stringify({ error: '化工内核不可达', detail: error.message }))
    }
    let request
    try {
      await kernel.ensure()
      if (res.destroyed) return
      const target = new URL(kernel.endpoint + route[1] + url.pathname.slice(route[0].length) + url.search)
      request = (target.protocol === 'https:' ? https : http).request(target, {
        method: req.method,
        headers: Object.fromEntries(kernel.headers(cleanHeaders(req.headers))),
        timeout: 120000,
      }, (response) => {
        res.writeHead(response.statusCode || 502, cleanHeaders(response.headers))
        response.on('error', fail)
        response.pipe(res)
      })
      request.on('timeout', () => request.destroy(new Error('内核请求超时')))
      request.on('error', fail)
      req.on('aborted', () => request.destroy())
      res.on('close', () => { if (!res.writableFinished) request.destroy() })
      req.pipe(request)
    } catch (error) {
      fail(error)
    }
  }
}
