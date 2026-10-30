import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'

/** A single owner for kernel startup, authenticated requests, and shutdown. */
export function createKernel(config, pluginDir) {
  const endpoint = new URL(String(config.endpoint || 'http://127.0.0.1:8765').replace(/\/+$/, ''))
  if (!['http:', 'https:'].includes(endpoint.protocol) || endpoint.search || endpoint.hash) {
    throw new Error('endpoint 必须是 HTTP(S) 地址，不能包含查询参数或片段')
  }
  const base = endpoint.href.replace(/\/+$/, '')
  const token = String(config.token || '')
  const phaseGate = String(config.phaseGate || 'advisory').toLowerCase()
  if (!['advisory', 'enforce'].includes(phaseGate)) throw new Error('phaseGate 必须为 advisory 或 enforce')
  const runtime = path.join(pluginDir, 'runtime')
  const bundled = !fs.existsSync(path.resolve(pluginDir, '../kernel/server.py')) &&
    fs.existsSync(path.join(runtime, 'kernel', 'server.py'))
  const root = bundled ? runtime : path.resolve(pluginDir, '..')
  const runtimePython = process.platform === 'win32'
    ? path.join(runtime, 'python', 'python.exe')
    : path.join(runtime, 'python', 'bin', 'python3')
  const workspacePython = process.platform === 'win32'
    ? path.join(root, '.venv', 'Scripts', 'python.exe')
    : path.join(root, '.venv', 'bin', 'python')
  const python = String(config.python || '') || (bundled ? [runtimePython] : [workspacePython, runtimePython]).find((file) => fs.existsSync(file)) ||
    (process.platform === 'win32' ? 'python' : 'python3')
  const dataRoot = path.resolve(String(config.dataDir || '') ||
    path.join(process.env.DSH_PROFILE_DIR || pluginDir, 'chemellm-data'))
  const local = endpoint.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(endpoint.hostname) && endpoint.pathname === '/'
  let child = null
  let starting = null
  let disposed = false
  let startupError = ''
  let reachable = false

  function headers(extra) {
    const result = new Headers(extra)
    result.delete('x-kernel-token')
    if (token) result.set('x-kernel-token', token)
    return result
  }

  async function healthy() {
    reachable = false
    try {
      const response = await fetch(base + '/v1/health', { headers: headers(), signal: AbortSignal.timeout(1000) })
      reachable = true
      if (!response.ok) { startupError = '内核健康检查 HTTP ' + response.status; return false }
      const data = await response.json()
      return data.ok === true && typeof data.version === 'string' && typeof data.phaseGate === 'string'
    } catch {
      return false
    }
  }

  async function start() {
    if (await healthy()) return !disposed
    if (disposed || reachable || config.autostart === false || !local) return false
    const server = path.join(root, 'kernel', 'server.py')
    if (!fs.existsSync(server)) return false
    // A startup timeout must not allow a second child to compete for the port.
    if (!child) {
      startupError = ''
      const env = {
        ...process.env,
        CHEMELLM_KERNEL_HOST: '127.0.0.1',
        CHEMELLM_KERNEL_PORT: endpoint.port || '80',
        CHEMELLM_KERNEL_TOKEN: token,
        CHEMELLM_PHASE_GATE: phaseGate,
        CHEMELLM_DATA_ROOT: dataRoot,
        CHEMELLM_KERNEL_DATA: path.join(dataRoot, 'kernel'),
        CHEMELLM_DATA_DIR: path.join(dataRoot, 'kernel'),
        CHEMELLM_SNAPSHOT_DIR: path.join(dataRoot, '.chem'),
        CHEMELLM_APP_DIR: path.join(root, bundled ? 'app' : 'old/app'),
        PYTHONPATH: [bundled ? path.join(root, 'site-packages') : '', process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
      }
      const processChild = spawn(python, ['-X', 'utf8', server], {
        cwd: root, env, stdio: ['ignore', 'ignore', 'pipe'], windowsHide: true,
      })
      child = processChild
      processChild.stderr.on('data', (chunk) => { startupError = (startupError + chunk.toString()).slice(-2000) })
      processChild.once('error', (error) => {
        startupError = error.message
        if (child === processChild) child = null
      })
      processChild.once('exit', () => { if (child === processChild) child = null })
    }
    const deadline = Date.now() + 20000
    while (!disposed && child && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 250))
      if (!disposed && await healthy()) return true
    }
    return false
  }

  function ensure() {
    if (disposed) return Promise.resolve(false)
    if (!starting) starting = start().finally(() => { starting = null })
    return starting
  }

  async function request(route, init = {}) {
    if (disposed) throw new Error('化工插件已停用')
    await ensure()
    if (disposed) throw new Error('化工插件已停用')
    const options = { ...init, headers: headers(init.headers), signal: init.signal || AbortSignal.timeout(120000) }
    if (options.body !== undefined && typeof options.body !== 'string') {
      options.body = JSON.stringify(options.body)
      options.headers.set('content-type', 'application/json')
    }
    let response
    try {
      response = await fetch(base + route, options)
    } catch (error) {
      throw new Error('化工内核不可达（' + base + '）：' + (startupError || error.message))
    }
    const text = await response.text()
    let data
    try {
      data = text ? JSON.parse(text) : {}
    } catch {
      throw new Error('内核返回非 JSON（HTTP ' + response.status + '）：' + text.slice(0, 300))
    }
    if (!response.ok) {
      const detail = data.detail || data.error || text.slice(0, 500)
      throw new Error('内核 HTTP ' + response.status + '：' + (typeof detail === 'string' ? detail : JSON.stringify(detail)))
    }
    return data
  }

  function dispose() {
    disposed = true
    if (child) child.kill()
    child = null
  }

  return { endpoint: base, headers, phaseGate, ensure, request, dispose }
}
