/**
 * ChemELLM local workspace — DSH Host half.
 *
 * Registers 11 domain tools that talk to the local Python kernel
 * (default http://127.0.0.1:8765), a phase guard, a prompt section, and
 * same-origin proxy routes for the Web panel and file previews.
 */
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'

export const inject = ['tools', 'systemPrompt', 'webServer']

const PHASES = ['intake', 'requirements', 'plan', 'basis', 'execute', 'review', 'bundle', 'done']

// Domain tool -> minimum phase when phaseGate=enforce.
const MIN_PHASE = {
  chem_intake: 'intake',
  chem_requirements: 'intake',
  chem_evidence: 'intake',
  chem_plan: 'requirements',
  chem_object: 'plan',
  chem_calc: 'basis',
  chem_generate: 'basis',
  chem_review: 'execute',
  chem_bundle: 'review',
}

const MODELS = [
  'properties', 'steam', 'convert_units', 'material_balance', 'heat_exchanger', 'flash',
  'economics', 'reaction_thermo', 'mixture_reaction', 'distillation_shortcut',
  'pipe_pressure_drop', 'pinch_analysis', 'column_mesh', 'aqueous_flash', 'condenser_flash',
  'frontend_process', 'wet_column', 'wet_separation_train', 'recycle_process', 'fit_data',
  'cantera_equilibrium', 'cantera_reactor',
]

const EVIDENCE_ACTIONS = [
  'literature_search', 'open_literature_search', 'pubchem', 'project_search',
  'fulltext_import', 'source_fetch', 'document_extract', 'document_read',
  'claim_save', 'evidence_add', 'evidence_check', 'evidence_export',
]

const RULES = [
  '你在本地化工工程工作台内工作，数据与计算都在本机，不依赖云端。',
  '按阶段推进：资料(intake) → 要求(requirements) → 计划(plan) → 依据(basis) → 执行(execute) → 校核(review) → 打包(bundle)。',
  '要求逐条登记；工程数值必须说明单位、条件与来源（假设/设计选择/文档/计算）。',
  '变更依据或计算后，重新生成受影响的成果；不得把旧数据写进新报告。',
  '交付前必须调用 chem_review；未通过要如实报告 blockers，不得声称已完成。',
  '工具返回失败时修正参数或询问用户；禁止编造计算、文献、厂家数据或软件源文件。',
].join('\n')

export function apply(ctx, config) {
  const cfg = config && typeof config === 'object' ? config : {}
  const endpoint = String(cfg.endpoint || 'http://127.0.0.1:8765').replace(/\/+$/, '')
  const token = String(cfg.token || '')
  const gateMode = String(cfg.phaseGate || 'advisory').toLowerCase()
  const phaseCache = new Map()

  // Bundled runtime: <plugin>/runtime/{python,site-packages,kernel,app}. When the
  // kernel is not already running, the Host starts it from this runtime so the
  // plugin works on another DSH without a pre-installed Python environment.
  const pluginDir = path.dirname(fileURLToPath(import.meta.url))
  const runtimeDir = path.join(pluginDir, 'runtime')
  const runtimePython = process.platform === 'win32'
    ? path.join(runtimeDir, 'python', 'python.exe')
    : path.join(runtimeDir, 'python', 'bin', 'python3')
  const hasRuntime = fs.existsSync(runtimePython) && fs.existsSync(path.join(runtimeDir, 'kernel', 'server.py'))
  let kernelChild = null
  let starting = null

  async function kernelHealthy(timeoutMs) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs || 1500)
    try {
      const response = await fetch(endpoint + '/v1/health', { signal: controller.signal })
      return response.ok
    } catch {
      return false
    } finally {
      clearTimeout(timer)
    }
  }

  async function ensureKernel() {
    if (await kernelHealthy()) return true
    if (cfg.autostart === false) return false
    if (starting) return starting
    const python = String(cfg.python || '') || (hasRuntime ? runtimePython : (process.platform === 'win32' ? 'python' : 'python3'))
    const server = hasRuntime
      ? path.join(runtimeDir, 'kernel', 'server.py')
      : path.resolve(pluginDir, '..', 'kernel', 'server.py')
    if (!fs.existsSync(server)) return false
    const dataRoot = String(cfg.dataDir || '') ||
      path.join(process.env.DSH_PROFILE_DIR || pluginDir, 'chemellm-data')
    const port = new URL(endpoint).port || '8765'
    const env = {
      ...process.env,
      CHEMELLM_KERNEL_PORT: port,
      CHEMELLM_DATA_ROOT: dataRoot,
      CHEMELLM_DATA_DIR: path.join(dataRoot, 'kernel'),
      CHEMELLM_APP_DIR: path.join(runtimeDir, 'app'),
      PYTHONPATH: [path.join(runtimeDir, 'site-packages'), path.join(runtimeDir, 'app')].join(path.delimiter),
      PYTHONUTF8: '1',
      PYTHONIOENCODING: 'utf-8',
    }
    starting = (async () => {
      try {
        kernelChild = spawn(python, ['-X', 'utf8', server], {
          cwd: runtimeDir, env, stdio: 'ignore', windowsHide: true,
        })
        kernelChild.on('exit', () => { kernelChild = null })
        kernelChild.on('error', () => { kernelChild = null })
      } catch {
        kernelChild = null
        return false
      }
      for (let attempt = 0; attempt < 40; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 500))
        if (await kernelHealthy(1000)) return true
        if (!kernelChild) return false
      }
      return false
    })()
    try {
      return await starting
    } finally {
      starting = null
    }
  }

  ctx.effect(() => () => {
    if (kernelChild) {
      try { kernelChild.kill() } catch { /* already gone */ }
      kernelChild = null
    }
  })
  void ensureKernel()

  function headers(extra) {
    const result = { ...(extra || {}) }
    if (token) result['x-kernel-token'] = token
    return result
  }

  async function kernel(path, init) {
    await ensureKernel()
    const request = { ...(init || {}) }
    request.headers = headers(request.headers)
    if (request.body !== undefined && typeof request.body !== 'string') {
      request.body = JSON.stringify(request.body)
      request.headers['content-type'] = 'application/json'
    }
    let response
    try {
      response = await fetch(endpoint + path, request)
    } catch (error) {
      throw new Error(
        '本地化工内核不可达（' + endpoint + '）。请先运行 scripts/start-kernel.ps1。原始错误：' +
        String(error && error.message ? error.message : error),
      )
    }
    const text = await response.text()
    let data
    try {
      data = text ? JSON.parse(text) : {}
    } catch {
      throw new Error('内核返回了非 JSON 响应（HTTP ' + response.status + '）：' + text.slice(0, 300))
    }
    if (!response.ok) {
      const detail = data && (data.detail || data.error) ? (data.detail || data.error) : text.slice(0, 500)
      throw new Error('内核 HTTP ' + response.status + '：' + (typeof detail === 'string' ? detail : JSON.stringify(detail)))
    }
    return data
  }

  function remember(projectId, data) {
    if (projectId && data && typeof data.phase === 'string' && PHASES.includes(data.phase)) {
      phaseCache.set(projectId, data.phase)
    }
    return data
  }

  function projectArgs(args) {
    const value = args && typeof args === 'object' ? args : {}
    return value
  }

  function textRender(_args, value) {
    let text
    try {
      text = JSON.stringify(value)
    } catch {
      text = String(value)
    }
    if (typeof text === 'string' && text.length > 12000) text = text.slice(0, 12000) + '…（已截断，见面板）'
    return [{ type: 'text', text }]
  }

  function define(def) {
    return {
      name: def.name,
      description: def.description,
      parameters: def.parameters,
      output: { schema: { type: 'object' }, render: textRender },
      async execute(args) {
        const data = await def.execute(projectArgs(args))
        return remember(projectArgs(args).projectId, data)
      },
    }
  }

  // --------------------------------------------------------------------- //
  // tools
  // --------------------------------------------------------------------- //
  const projectIdProp = { type: 'string', description: '项目 ID（chem_project 返回）' }

  const tools = [
    define({
      name: 'chem_project',
      description: '列出、创建或读取本地化工项目。开始任何工程任务前先调用。',
      parameters: {
        type: 'object',
        properties: {
          action: { type: 'string', enum: ['list', 'create', 'get'], description: 'list 列出；create 新建；get 读取项目详情' },
          name: { type: 'string', description: 'create 时的项目名称' },
          projectId: projectIdProp,
        },
        required: ['action'],
      },
      async execute(args) {
        if (args.action === 'create') {
          if (!args.name || !String(args.name).trim()) throw new Error('create 需要 name')
          return kernel('/v1/projects', { method: 'POST', body: { name: String(args.name).trim() } })
        }
        if (args.action === 'get') {
          if (!args.projectId) throw new Error('get 需要 projectId')
          return kernel('/v1/projects/' + encodeURIComponent(args.projectId))
        }
        return kernel('/v1/projects')
      },
    }),

    define({
      name: 'chem_intake',
      description: '把工作区内的资料（赛题 PDF、文献、数据表）登记进当前项目，生成带哈希与页数的文件记录。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          path: { type: 'string', description: '工作区内的文件路径（绝对路径或相对仓库根目录）' },
          name: { type: 'string', description: '可选：登记名称' },
        },
        required: ['projectId', 'path'],
      },
      async execute(args) {
        return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/intake', {
          method: 'POST',
          body: { path: args.path, name: args.name },
        })
      },
    }),

    define({
      name: 'chem_requirements',
      description: '登记或查看项目要求清单。要求逐条编码，可带原文引句与适用性说明；不能把“不适用”当作通过。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          action: { type: 'string', enum: ['list', 'save'], description: 'list 查看；save 保存/更新' },
          items: {
            type: 'array',
            description: 'save 时的要求条目',
            items: {
              type: 'object',
              properties: {
                code: { type: 'string', description: '稳定编码，如 B01' },
                title: { type: 'string' },
                mandatory: { type: 'boolean', description: '默认 true' },
                applicability: { type: 'string', description: '原文适用条件或说明' },
                quote: { type: 'string', description: '原文逐字引句（可选）' },
                source: { type: 'string', description: '来源文件或页码（可选）' },
              },
              required: ['code', 'title'],
            },
          },
        },
        required: ['projectId', 'action'],
      },
      async execute(args) {
        if (args.action === 'save') {
          if (!Array.isArray(args.items) || args.items.length === 0) throw new Error('save 需要非空 items')
          return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/requirements', {
            method: 'POST',
            body: { items: args.items },
          })
        }
        const data = await kernel('/v1/projects/' + encodeURIComponent(args.projectId))
        return { ok: true, phase: data.phase, requirements: data.project.requirements }
      },
    }),

    define({
      name: 'chem_plan',
      description: '登记或查看成果计划：要求→成果映射、对象计划、格式与依赖。要求零遗漏。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          action: { type: 'string', enum: ['list', 'save'] },
          objects: {
            type: 'array',
            description: '计划中的工程对象',
            items: {
              type: 'object',
              properties: {
                key: { type: 'string' },
                kind: { type: 'string', description: 'basis/stream/equipment/utility/hazard/cost…' },
                title: { type: 'string' },
                note: { type: 'string' },
              },
              required: ['key'],
            },
          },
          deliverables: {
            type: 'array',
            description: '计划中的交付成果',
            items: {
              type: 'object',
              properties: {
                key: { type: 'string' },
                title: { type: 'string' },
                requirementCodes: { type: 'array', items: { type: 'string' } },
                formats: { type: 'array', items: { type: 'string' } },
              },
              required: ['key', 'title'],
            },
          },
        },
        required: ['projectId', 'action'],
      },
      async execute(args) {
        if (args.action === 'save') {
          return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/plan', {
            method: 'POST',
            body: { objects: args.objects || [], deliverables: args.deliverables || [] },
          })
        }
        const data = await kernel('/v1/projects/' + encodeURIComponent(args.projectId))
        return { ok: true, phase: data.phase, plan: data.project.plan }
      },
    }),

    define({
      name: 'chem_object',
      description: '保存或查看工程对象（设计依据、物流、设备、公用工程、安全、成本等）。数值必须带单位、条件与来源。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          action: { type: 'string', enum: ['list', 'save'] },
          kind: { type: 'string', description: '对象类型：basis/component/stream/unit_operation/equipment/utility/cost/site/control/pipe/hazard/method' },
          key: { type: 'string', description: '对象稳定键名' },
          title: { type: 'string' },
          quantities: {
            type: 'array',
            description: '数值项：{key, value, unit, origin, conditions, rationale}',
            items: {
              type: 'object',
              properties: {
                key: { type: 'string' },
                value: { type: ['number', 'null'] },
                unit: { type: 'string' },
                origin: { type: 'string', enum: ['assumption', 'design_choice', 'document', 'calculation'] },
                conditions: { type: 'string' },
                rationale: { type: 'string' },
                calculationId: { type: 'string' },
                resultPath: { type: 'string' },
              },
              required: ['key', 'unit', 'origin'],
            },
          },
          attributes: { type: 'object', description: '非数值属性（方法、规格、说明等）' },
          dependsOn: { type: 'array', items: { type: 'string' }, description: '上游对象键' },
        },
        required: ['projectId', 'action'],
      },
      async execute(args) {
        if (args.action === 'save') {
          if (!args.kind || !args.key) throw new Error('save 需要 kind 与 key')
          return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/objects', {
            method: 'POST',
            body: {
              kind: args.kind,
              key: args.key,
              title: args.title || args.key,
              quantities: args.quantities || [],
              attributes: args.attributes || {},
              dependsOn: args.dependsOn || [],
            },
          })
        }
        const data = await kernel('/v1/projects/' + encodeURIComponent(args.projectId))
        return { ok: true, phase: data.phase, objects: data.project.objects }
      },
    }),

    define({
      name: 'chem_calc',
      description: '调用本地化工计算模型（物性/衡算/反应/精馏/分相/循环/换热/压降/夹点/经济/Cantera/回归等），返回计算 ID、校验与关键结果。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          model: { type: 'string', enum: MODELS, description: '计算模型 ID' },
          input: { type: 'object', description: '按模型输入 schema 的参数对象；缺参时返回错误而不是编造默认值' },
        },
        required: ['projectId', 'model', 'input'],
      },
      async execute(args) {
        if (!MODELS.includes(args.model)) throw new Error('未知模型：' + args.model)
        return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/execute', {
          method: 'POST',
          body: { tool: args.model, args: args.input || {} },
        })
      },
    }),

    define({
      name: 'chem_evidence',
      description: '文献检索、全文导入、引句证据与论断管理；也可查询项目内文件内容。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          action: { type: 'string', enum: EVIDENCE_ACTIONS, description: '要调用的证据/检索工具' },
          arguments: { type: 'object', description: '透传给该工具的输入参数' },
        },
        required: ['projectId', 'action'],
      },
      async execute(args) {
        if (!EVIDENCE_ACTIONS.includes(args.action)) throw new Error('未知证据动作：' + args.action)
        return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/execute', {
          method: 'POST',
          body: { tool: args.action, args: args.arguments || {} },
        })
      },
    }),

    define({
      name: 'chem_generate',
      description: '生成成果文件：DOCX/PPTX/PDF/MD 报告，或 PFD/P&ID 草图（SVG/DXF）。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          kind: { type: 'string', enum: ['report', 'pfd'], description: 'report 生成文档；pfd 生成流程图' },
          title: { type: 'string' },
          body: { type: 'string', description: 'report 正文（纯文本，按行分页/分段）' },
          formats: { type: 'array', items: { type: 'string', enum: ['docx', 'pdf', 'pptx', 'md'] }, description: 'report 输出格式，默认 docx+pdf' },
          drawingType: { type: 'string', enum: ['PFD', 'P&ID'], description: 'pfd 图类型' },
          nodes: { type: 'array', description: 'pfd 设备节点 {id,label,kind,x,y}', items: { type: 'object' } },
          edges: { type: 'array', description: 'pfd 物流连线 {source,target,label}', items: { type: 'object' } },
        },
        required: ['projectId', 'kind'],
      },
      async execute(args) {
        if (args.kind === 'report') {
          if (!args.body || !String(args.body).trim()) throw new Error('report 需要非空 body')
          return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/execute', {
            method: 'POST',
            body: {
              tool: 'export_report',
              args: {
                title: args.title || '工程报告',
                body: args.body,
                formats: args.formats || ['docx', 'pdf'],
              },
            },
          })
        }
        if (args.kind === 'pfd') {
          return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/execute', {
            method: 'POST',
            body: {
              tool: 'pfd',
              args: {
                title: args.title || '工艺流程草图',
                drawing_type: args.drawingType || 'PFD',
                nodes: args.nodes || [],
                edges: args.edges || [],
              },
            },
          })
        }
        throw new Error('未知成果类型：' + args.kind)
      },
    }),

    define({
      name: 'chem_review',
      description: '工程自检：要求覆盖、依据、计算校验、成果文件与缺口。自动校核不等于专业审核。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          note: { type: 'string', description: '可选：本次校核说明' },
        },
        required: ['projectId'],
      },
      async execute(args) {
        return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/review', {
          method: 'POST',
          body: { note: args.note || '' },
        })
      },
    }),

    define({
      name: 'chem_bundle',
      description: '打包本地项目成果：项目数据、计算记录、成果文件与哈希清单，生成可下载 zip。',
      parameters: {
        type: 'object',
        properties: { projectId: projectIdProp },
        required: ['projectId'],
      },
      async execute(args) {
        return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/bundle', { method: 'POST', body: {} })
      },
    }),

    define({
      name: 'chem_artifact',
      description: '列出项目文件，或取得某个成果文件的预览/下载链接（同源 /chemellm/files/…）。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          artifactId: { type: 'string', description: '可选：指定文件 ID' },
          mode: { type: 'string', enum: ['download', 'preview'], description: '默认 download' },
        },
        required: ['projectId'],
      },
      async execute(args) {
        const data = await kernel('/v1/projects/' + encodeURIComponent(args.projectId))
        const files = data.project.files || []
        if (!args.artifactId) return { ok: true, files }
        const file = files.find((item) => item.artifactId === args.artifactId)
        if (!file) throw new Error('项目中没有该文件：' + args.artifactId)
        const mode = args.mode === 'preview' ? 'preview' : 'download'
        return {
          ok: true,
          artifact: file,
          url: '/chemellm/files/' + encodeURIComponent(file.artifactId) + '/' + mode,
        }
      },
    }),

    define({
      name: 'chem_tool',
      description: '通用透传：调用旧版 ChemELLM 的任意已注册工具（设备登记/查询、图纸识读、数据集检查与分析、证据等），补足域工具未覆盖的能力。不传 tool 时返回全部可用工具名。',
      parameters: {
        type: 'object',
        properties: {
          projectId: projectIdProp,
          tool: {
            type: 'string',
            description: '旧版工具 ID，如 equipment_save / equipment_query / drawing_read / dataset_inspect / analyze_dataset / project_search',
          },
          arguments: { type: 'object', description: '透传给该工具的输入参数' },
        },
        required: ['projectId'],
      },
      async execute(args) {
        if (!args.tool) {
          const catalog = await kernel('/v1/tools')
          return { ok: true, tools: (catalog.tools || []).map((tool) => tool.id) }
        }
        if (args.tool === 'ask_user') throw new Error('需要追问时请使用内建 ask_user_question 工具')
        return kernel('/v1/projects/' + encodeURIComponent(args.projectId) + '/execute', {
          method: 'POST',
          body: { tool: args.tool, args: args.arguments || {} },
        })
      },
    }),
  ]

  for (const tool of tools) {
    ctx.effect(() => ctx.tools.register(tool))
  }

  // --------------------------------------------------------------------- //
  // phase guard
  // --------------------------------------------------------------------- //
  ctx.effect(() => ctx.tools.guard((exec) => {
    if (gateMode !== 'enforce') return undefined
    const name = String(exec.name || '')
    const minimum = MIN_PHASE[name]
    if (!minimum) return undefined
    const args = exec.arguments && typeof exec.arguments === 'object' ? exec.arguments : {}
    const projectId = args.projectId
    if (!projectId) return undefined
    const phase = phaseCache.get(projectId)
    if (!phase) return undefined
    if (PHASES.indexOf(phase) >= PHASES.indexOf(minimum)) return undefined
    return '当前项目阶段为 ' + phase + '，' + name + ' 需要至少 ' + minimum + '；先完成阶段前置条件'
  }))

  // --------------------------------------------------------------------- //
  // prompt
  // --------------------------------------------------------------------- //
  ctx.effect(() => ctx.systemPrompt.section({
    name: 'chemellm/local-workspace',
    order: 45,
    text: RULES,
  }))

  // --------------------------------------------------------------------- //
  // same-origin proxy for the Web panel and file previews
  // --------------------------------------------------------------------- //
  function targetPath(pathname, search) {
    if (pathname.startsWith('/chemellm/api/')) {
      return '/v1/' + pathname.slice('/chemellm/api/'.length) + (search || '')
    }
    if (pathname.startsWith('/chemellm/files/')) {
      return '/v1/artifacts/' + pathname.slice('/chemellm/files/'.length) + (search || '')
    }
    if (pathname.startsWith('/chemellm/bundles/')) {
      return '/v1/bundles/' + pathname.slice('/chemellm/bundles/'.length) + (search || '')
    }
    return null
  }

  function proxy(req, res) {
    const url = new URL(String(req.url || '/'), 'http://127.0.0.1')
    const path = targetPath(url.pathname, url.search)
    if (!path) {
      res.writeHead(404, { 'content-type': 'application/json' })
      res.end(JSON.stringify({ error: 'unknown chemellm route' }))
      return
    }
    let target
    try {
      target = new URL(endpoint)
    } catch {
      res.writeHead(502, { 'content-type': 'application/json' })
      res.end(JSON.stringify({ error: 'invalid kernel endpoint in plugin config' }))
      return
    }
    const headers = { ...req.headers }
    delete headers.host
    delete headers.connection
    if (token) headers['x-kernel-token'] = token
    const request = http.request({
      hostname: target.hostname,
      port: target.port || 80,
      method: req.method,
      path,
      headers,
      timeout: 120000,
    }, (response) => {
      const outgoing = { ...response.headers }
      delete outgoing['transfer-encoding']
      delete outgoing.connection
      res.writeHead(response.statusCode || 502, outgoing)
      response.pipe(res)
    })
    request.on('timeout', () => request.destroy(new Error('kernel request timeout')))
    request.on('error', (error) => {
      if (!res.headersSent) {
        res.writeHead(502, { 'content-type': 'application/json' })
        res.end(JSON.stringify({ error: 'kernel unreachable', detail: String(error && error.message ? error.message : error) }))
      } else {
        res.end()
      }
    })
    req.pipe(request)
  }

  ctx.effect(() => ctx.webServer.register({
    kind: 'prefix',
    // 注意：注册路径不要带尾斜杠——WebServer.match 会把 prefix 拼成 `${prefix}/`
    // 再比较，'/chemellm/' 只能匹配 '/chemellm/' 本身或 '/chemellm//…'。
    path: '/chemellm',
    handler: proxy,
  }))
}
