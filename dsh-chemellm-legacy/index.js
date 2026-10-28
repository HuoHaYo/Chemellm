/**
 * ChemELLM legacy passthrough — DSH Host half.
 *
 * Registers one tool, `chem_legacy`, that forwards any named ChemELLM kernel
 * tool call. It exists so the local workspace can reach every archived tool
 * (equipment, drawings, datasets, evidence) without waiting for a Host restart
 * of the main plugin generation. Equivalent to `chem_tool` in the main bundle.
 */
export const inject = ['tools']

export function apply(ctx, config) {
  const cfg = config && typeof config === 'object' ? config : {}
  const endpoint = String(cfg.endpoint || 'http://127.0.0.1:8765').replace(/\/+$/, '')
  const token = String(cfg.token || '')

  async function kernel(path, init) {
    const request = { ...(init || {}) }
    const headers = { ...(request.headers || {}) }
    if (token) headers['x-kernel-token'] = token
    if (request.body !== undefined && typeof request.body !== 'string') {
      request.body = JSON.stringify(request.body)
      headers['content-type'] = 'application/json'
    }
    request.headers = headers
    let response
    try {
      response = await fetch(endpoint + path, request)
    } catch (error) {
      throw new Error(
        '本地化工内核不可达（' + endpoint + '）。请先运行 scripts/start-kernel.cmd。原始错误：' +
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

  const tool = {
    name: 'chem_legacy',
    description: '通用透传：调用本地内核中任意已注册工具（equipment_save/equipment_query、drawing_read、dataset_inspect、analyze_dataset、project_search、evidence_* 等）。不传 tool 时返回全部可用工具名。',
    parameters: {
      type: 'object',
      properties: {
        projectId: { type: 'string', description: '项目 ID（chem_project 返回）' },
        tool: { type: 'string', description: '内核工具 ID；省略时列出全部工具名' },
        arguments: { type: 'object', description: '透传给该工具的输入参数' },
      },
      required: ['projectId'],
    },
    output: {
      schema: { type: 'object' },
      render(_args, value) {
        let text
        try {
          text = JSON.stringify(value)
        } catch {
          text = String(value)
        }
        if (typeof text === 'string' && text.length > 12000) text = text.slice(0, 12000) + '…（已截断）'
        return [{ type: 'text', text }]
      },
    },
    async execute(args) {
      const payload = args && typeof args === 'object' ? args : {}
      if (!payload.projectId) throw new Error('需要 projectId')
      if (!payload.tool) {
        const catalog = await kernel('/v1/tools')
        return { ok: true, tools: (catalog.tools || []).map((entry) => entry.id) }
      }
      if (payload.tool === 'ask_user') throw new Error('需要追问时请使用内建 ask_user_question 工具')
      return kernel('/v1/projects/' + encodeURIComponent(payload.projectId) + '/execute', {
        method: 'POST',
        body: { tool: payload.tool, args: payload.arguments || {} },
      })
    },
  }

  ctx.effect(() => ctx.tools.register(tool))
}
