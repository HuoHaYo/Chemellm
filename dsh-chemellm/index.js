/** DSH Host entry: tools, kernel lifecycle, prompt, and panel proxy. */
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createKernel } from './lib/kernel.js'
import { createTools } from './lib/tools.js'
import { createProxy } from './lib/proxy.js'

export const inject = ['tools', 'systemPrompt', 'webServer']

const RULES = [
  '你在本地化工工程工作台内工作，数据与计算都在本机，不依赖云端。',
  '按阶段推进：资料(intake) → 要求(requirements) → 计划(plan) → 依据(basis) → 执行(execute) → 校核(review) → 打包(bundle)。',
  '要求逐条登记；工程数值必须说明单位、条件与来源（假设/设计选择/文档/计算）。',
  '变更依据或计算后，重新生成受影响的成果；不得把旧数据写进新报告。',
  '交付前必须调用 chem_review；未通过要如实报告 blockers，不得声称已完成。',
  '工具返回失败时修正参数或询问用户；禁止编造计算、文献、厂家数据或软件源文件。',
].join('\n')

export function apply(ctx, config = {}) {
  const kernel = createKernel(config || {}, path.dirname(fileURLToPath(import.meta.url)))
  ctx.effect(() => () => kernel.dispose())
  for (const tool of createTools(kernel.request, kernel.phaseGate)) {
    ctx.effect(() => ctx.tools.register(tool))
  }
  ctx.effect(() => ctx.systemPrompt.section({
    name: 'chemellm/local-workspace', order: 45, text: RULES,
  }))
  // DSH's prefix matcher appends its own slash.
  ctx.effect(() => ctx.webServer.register({
    kind: 'prefix', path: '/chemellm', handler: createProxy(kernel),
  }))
  void kernel.ensure().catch(() => {})
}
