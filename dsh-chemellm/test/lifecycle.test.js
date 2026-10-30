import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import http from 'node:http'
import os from 'node:os'
import path from 'node:path'
import { once } from 'node:events'
import { test } from 'node:test'
import { createKernel } from '../lib/kernel.js'

test('concurrent calls share one child and pass all startup configuration', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'chemellm-lifecycle-'))
  let kernel
  t.after(async () => {
    kernel?.dispose()
    await fs.rm(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 })
  })
  await fs.mkdir(path.join(root, 'kernel'))
  await fs.mkdir(path.join(root, 'plugin'))
  // A tiny sidecar verifies real process startup without importing the heavy
  // calculation dependencies. The actual kernel has its own workflow test.
  await fs.writeFile(path.join(root, 'kernel', 'server.py'), `
import json, os, socket
from pathlib import Path
with Path('starts.txt').open('a') as output:
    output.write('started\\n')
server = socket.socket()
server.bind(('127.0.0.1', int(os.environ['CHEMELLM_KERNEL_PORT'])))
server.listen()
while True:
    connection, address = server.accept()
    request = connection.recv(65536)
    body = json.dumps({'ok': True, 'version': 'test', 'phaseGate': os.environ['CHEMELLM_PHASE_GATE'], 'env': dict(os.environ)}).encode()
    connection.sendall(b'HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\nConnection: close\\r\\nContent-Length: ' + str(len(body)).encode() + b'\\r\\n\\r\\n' + body)
    connection.close()
`)
  const reserve = http.createServer()
  reserve.listen(0, '127.0.0.1')
  await once(reserve, 'listening')
  const port = reserve.address().port
  await new Promise((resolve) => reserve.close(resolve))
  const dataDir = path.join(root, 'data')
  kernel = createKernel({ endpoint: 'http://127.0.0.1:' + port, python: 'python', token: 'test-secret', phaseGate: 'enforce', dataDir }, path.join(root, 'plugin'))
  assert.deepEqual(await Promise.all([kernel.ensure(), kernel.ensure(), kernel.ensure()]), [true, true, true])
  const { env } = await kernel.request('/env')
  assert.equal(env.CHEMELLM_KERNEL_TOKEN, 'test-secret')
  assert.equal(env.CHEMELLM_PHASE_GATE, 'enforce')
  assert.equal(env.CHEMELLM_KERNEL_HOST, '127.0.0.1')
  assert.equal(env.CHEMELLM_DATA_DIR, path.join(dataDir, 'kernel'))
  assert.equal(env.CHEMELLM_SNAPSHOT_DIR, path.join(dataDir, '.chem'))
  assert.equal(env.CHEMELLM_APP_DIR, path.join(root, 'old/app'))
  assert.deepEqual((await fs.readFile(path.join(root, 'starts.txt'), 'utf8')).trim().split(/\r?\n/), ['started'])
  kernel.dispose()
  await assert.rejects(kernel.request('/env'), /已停用/)
})

test('bad configuration fails before registering tools or starting a process', () => {
  assert.throws(() => createKernel({ endpoint: 'file:///tmp' }, '.'), /HTTP/)
  assert.throws(() => createKernel({ phaseGate: 'typo' }, '.'), /phaseGate/)
})
