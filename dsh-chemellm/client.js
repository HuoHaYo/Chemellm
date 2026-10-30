/**
 * ChemELLM local workspace — DSH Web Client half.
 *
 * Adds a "化工工程" entry to the sidebar and a full project panel:
 * overview / requirements / plan / basis / calculations / files / review.
 * Uses the Host's same-origin proxy for API requests and file previews.
 * The Host owns the configured endpoint and kernel token.
 */
window.__ModuleLoader__.load({
  id: '@local/dsh-chemellm',
  factory(require) {
    const React = require('react')
    const h = React.createElement
    const { useState, useEffect, useRef } = React

    const API = '/chemellm/api'

    const T = {
      bg: 'var(--dsw-alias-bg-base)',
      layer: 'var(--dsw-alias-bg-layer-1)',
      layer2: 'var(--dsw-alias-bg-layer-2)',
      border: 'var(--dsw-alias-border-l1)',
      text: 'var(--dsw-alias-label-primary)',
      muted: 'var(--dsw-alias-label-secondary)',
      brand: 'var(--dsw-alias-brand-primary)',
      ok: 'var(--dsw-alias-state-success-primary)',
      warn: 'var(--dsw-alias-state-warn-primary)',
      error: 'var(--dsw-alias-state-error-primary)',
    }

    const phaseLabels = {
      intake: '资料', requirements: '要求', plan: '计划', basis: '依据',
      execute: '执行', review: '校核', bundle: '打包', done: '完成',
    }
    const phaseOrder = ['intake', 'requirements', 'plan', 'basis', 'execute', 'review', 'bundle', 'done']
    const nextStep = {
      intake: '用 chem_intake 登记资料，再用 chem_requirements 建立要求清单',
      requirements: '用 chem_plan 建立“要求→成果”计划',
      plan: '用 chem_object 写入带来源的设计依据',
      basis: '用 chem_calc 运行计算，再用 chem_generate 生成成果',
      execute: '用 chem_review 自检并补齐缺口',
      review: '处理 blockers 后重新自检，再 chem_bundle 打包',
      bundle: '打包完成，可下载成果包',
      done: '项目已完成',
    }

    async function api(path, init) {
      const request = { headers: { 'content-type': 'application/json' } }
      if (init) {
        request.method = init.method
        request.body = init.body
      }
      const response = await fetch(API + path, { ...request, signal: AbortSignal.timeout(120000) })
      const text = await response.text()
      let data
      try {
        data = text ? JSON.parse(text) : {}
      } catch (error) {
        throw new Error('内核返回非 JSON：' + text.slice(0, 200))
      }
      if (!response.ok) {
        const detail = data && (data.detail || data.error) ? (data.detail || data.error) : 'HTTP ' + response.status
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      }
      return data
    }

    function message(error) {
      return String(error && error.message ? error.message : error)
    }

    function Pill(props) {
      return h('span', {
        style: {
          display: 'inline-block', padding: '1px 8px', borderRadius: 999,
          border: '1px solid ' + (props.color || T.border),
          color: props.color || T.muted, fontSize: 12, lineHeight: '18px', whiteSpace: 'nowrap',
        },
      }, props.children)
    }

    function Button(props) {
      return h('button', {
        type: 'button', disabled: props.disabled, onClick: props.onClick,
        style: {
          padding: '5px 12px', borderRadius: 8, border: '1px solid ' + T.border,
          background: props.primary ? T.brand : T.layer,
          color: props.primary ? '#fff' : T.text,
          cursor: props.disabled ? 'default' : 'pointer',
          opacity: props.disabled ? 0.55 : 1, fontSize: 13, whiteSpace: 'nowrap',
        },
      }, props.children)
    }

    function Card(props) {
      const heading = props.title
        ? h('h3', { style: { margin: '0 0 8px', fontSize: 13, color: T.muted, fontWeight: 600 } }, props.title)
        : null
      return h('section', {
        style: {
          background: T.layer, border: '1px solid ' + T.border,
          borderRadius: 10, padding: '12px 14px', marginBottom: 12,
        },
      }, heading, props.children)
    }

    function Table(props) {
      const columns = props.columns || []
      const header = h('tr', null, columns.map((column) =>
        h('th', {
          key: column,
          style: {
            textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid ' + T.border,
            color: T.muted, fontWeight: 600, whiteSpace: 'nowrap',
          },
        }, column)))
      const rows = props.rows.map((row, index) =>
        h('tr', { key: index }, row.map((cell, cellIndex) =>
          h('td', {
            key: cellIndex,
            style: { padding: '6px 8px', borderBottom: '1px solid ' + T.border, verticalAlign: 'top' },
          }, cell))))
      return h('div', { style: { overflowX: 'auto' } },
        h('table', { style: { width: '100%', borderCollapse: 'collapse', fontSize: 12.5 } },
          h('thead', null, header), h('tbody', null, rows)))
    }

    function Link(props) {
      return h('a', {
        href: props.href, target: props.target || '_blank', rel: 'noreferrer',
        onClick: props.onClick,
        style: { color: T.brand, textDecoration: 'none' },
      }, props.children)
    }

    function Empty(props) {
      return h('p', { style: { color: T.muted, margin: 0 } }, props.children)
    }

    function phaseOf(project) {
      return project && project.phase ? project.phase : 'intake'
    }

    function Overview(props) {
      const project = props.project
      const phase = phaseOf(project)
      const counts = [
        ['要求', (project.requirements || []).length],
        ['成果计划', ((project.plan || {}).deliverables || []).length],
        ['工程对象', Object.keys(project.objects || {}).length],
        ['计算记录', (project.calculations || []).length],
        ['文件', (project.files || []).length],
      ]
      const stats = h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 12 } },
        counts.map(([label, value]) => h('div', {
          key: label,
          style: {
            flex: '1 1 120px', background: T.layer, border: '1px solid ' + T.border,
            borderRadius: 10, padding: '10px 12px',
          },
        },
        h('div', { style: { color: T.muted, fontSize: 12 } }, label),
        h('div', { style: { fontSize: 20, marginTop: 2 } }, String(value)))))
      const index = phaseOrder.indexOf(phase)
      const progress = h('div', { style: { display: 'flex', gap: 6, flexWrap: 'wrap' } },
        phaseOrder.map((item, itemIndex) => h(Pill, {
          key: item,
          color: itemIndex <= index ? T.ok : T.border,
        }, (itemIndex < index ? '✓ ' : itemIndex === index ? '● ' : '○ ') + phaseLabels[item])))
      const progressCard = h(Card, { title: '阶段进度' }, progress,
        h('p', { style: { color: T.muted, margin: '6px 0 0', fontSize: 12.5 } },
          '下一步：' + (nextStep[phase] || '')))
      let bundleBody
      if (project.bundle) {
        bundleBody = h('div', null,
          h('div', { style: { marginBottom: 6 } },
            project.bundle.name + ' · ' + Math.round((project.bundle.bytes || 0) / 1024) + ' KB'),
          h(Link, { href: '/chemellm/bundles/' + encodeURIComponent(project.bundle.name) }, '下载成果包 ↓'))
      } else {
        bundleBody = h(Empty, null, '尚未打包；校核通过后可用 chem_bundle 打包。')
      }
      return h('div', null, stats, progressCard, h(Card, { title: '成果包' }, bundleBody))
    }

    function Requirements(props) {
      const items = props.project.requirements || []
      if (!items.length) return h(Empty, null, '暂无要求。用 chem_requirements 登记。')
      return h(Table, {
        columns: ['编码', '要求', '必需', '原文引句'],
        rows: items.map((item) => [
          item.code, item.title, item.mandatory === false ? '否' : '是',
          item.quote ? item.quote.slice(0, 80) : '—',
        ]),
      })
    }

    function Plan(props) {
      const plan = props.project.plan || {}
      const deliverables = plan.deliverables || []
      const objects = plan.objects || []
      const deliverableBody = deliverables.length
        ? h(Table, {
          columns: ['key', '标题', '要求', '格式'],
          rows: deliverables.map((item) => [
            item.key, item.title,
            (item.requirementCodes || []).join('、') || '—',
            (item.formats || []).join('、') || '—',
          ]),
        })
        : h(Empty, null, '暂无成果计划。用 chem_plan 建立。')
      const objectBody = objects.length
        ? h(Table, {
          columns: ['key', '类型', '标题'],
          rows: objects.map((item) => [item.key, item.kind || '—', item.title || '—']),
        })
        : h(Empty, null, '暂无对象计划。')
      return h('div', null,
        h(Card, { title: '成果计划（' + deliverables.length + '）' }, deliverableBody),
        h(Card, { title: '对象计划（' + objects.length + '）' }, objectBody))
    }

    function Basis(props) {
      const objects = Object.values(props.project.objects || {})
      if (!objects.length) return h(Empty, null, '暂无工程对象。用 chem_object 写入带来源的依据。')
      return h('div', null, objects.map((item) => {
        const quantities = item.quantities || []
        const body = quantities.length
          ? h(Table, {
            columns: ['数值', '值', '单位', '来源', '条件'],
            rows: quantities.map((quantity) => [
              quantity.key,
              quantity.value === null || quantity.value === undefined ? '—' : String(quantity.value),
              quantity.unit || '—',
              quantity.origin || '—',
              (quantity.conditions || '').slice(0, 60),
            ]),
          })
          : h(Empty, null, '该对象暂无数值项。')
        const title = (item.title || item.key) + ' · ' + item.kind + ' · v' + (item.revision || 1)
        return h(Card, { key: item.kind + '/' + item.key, title }, body)
      }))
    }

    function Calculations(props) {
      const items = props.project.calculations || []
      if (!items.length) return h('p', { style: { color: T.muted } }, '暂无计算。用 chem_calc 运行模型。')
      const rows = items.map((item) => {
        const validation = item.validation || {}
        const passed = validation.passed
        const color = passed === true ? T.ok : passed === false ? T.error : T.warn
        const label = passed === true ? '通过' : passed === false ? '未通过' : '无校验'
        return [
          item.tool || item.model || '—',
          h(Pill, { color }, label),
          h('code', { style: { fontSize: 11 } }, String(item.calculationId || '').slice(0, 12)),
          h(Link, { href: '#', onClick: (event) => { event.preventDefault(); props.onOpen(item) } }, '详情'),
        ]
      })
      const table = h(Table, { columns: ['工具', '校验', '计算 ID', ''], rows })
      if (!props.detail) return table
      return h('div', null, table,
        h(Card, { title: '计算详情 ' + (props.detail.tool || '') },
          h('pre', {
            style: {
              margin: 0, maxHeight: 320, overflow: 'auto', fontSize: 11.5,
              background: T.layer2, padding: 10, borderRadius: 8, whiteSpace: 'pre-wrap',
            },
          }, JSON.stringify(props.detail.result, null, 2))))
    }

    function Files(props) {
      const items = props.project.files || []
      if (!items.length) return h(Empty, null, '暂无文件。用 chem_intake 登记资料或 chem_generate 生成成果。')
      const hint = h('p', { style: { color: T.muted, margin: '0 0 10px', fontSize: 12 } },
        '三维文件（FCStd/STEP）：下载后用 FreeCAD 打开；若视图空白，点菜单“视图 → 全部适应（Fit all）”。STEP 请勿用 3D 查看器打开（不支持）。')
      return h('div', null, hint, h(Table, {
        columns: ['名称', '类型', '来源', '大小', '操作'],
        rows: items.map((item) => {
          const base = '/chemellm/files/' + encodeURIComponent(item.artifactId)
          return [
            item.name || '—',
            item.kind || '—',
            item.origin === 'intake' ? '资料' : '成果',
            item.bytes ? Math.round(item.bytes / 1024) + ' KB' : '—',
            h('span', null,
              h(Link, { href: base + '/download' }, '下载'),
              ' · ',
              h(Link, { href: base + '/preview' }, '预览')),
          ]
        }),
      }))
    }

    function Review(props) {
      const review = props.project.review || {}
      const blockers = review.blockers || []
      const status = h('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 } },
        h(Pill, { color: review.ready ? T.ok : T.warn }, review.ready ? '自动校核通过' : '存在缺口'),
        h('span', { style: { color: T.muted, fontSize: 12 } },
          '自动校核 ≠ 专业审核；专业审核状态：' + (review.professionalReview || 'not_reviewed')))
      const blockersBody = blockers.length
        ? h(Card, { title: 'Blockers（' + blockers.length + '）' },
          h('ul', { style: { margin: 0, paddingLeft: 18, lineHeight: 1.8 } },
            blockers.map((item, index) => h('li', { key: index }, item))))
        : h(Empty, null, '暂无 blockers。')
      const actions = h('div', { style: { display: 'flex', gap: 8, marginTop: 4 } },
        h(Button, { onClick: props.onReview, disabled: props.busy }, '运行自检'),
        h(Button, { onClick: props.onBundle, disabled: props.busy || !review.ready }, '打包成果'))
      return h('div', null, status, blockersBody, actions)
    }

    const tabs = [
      ['overview', '概览'], ['requirements', '要求'], ['plan', '计划'], ['basis', '依据'],
      ['calculations', '计算'], ['files', '成果'], ['review', '验收'],
    ]

    function Panel() {
      const [projects, setProjects] = useState([])
      const [activeId, setActiveId] = useState('')
      const [project, setProject] = useState(null)
      const [tab, setTab] = useState('overview')
      const [error, setError] = useState('')
      const [busy, setBusy] = useState(false)
      const [detail, setDetail] = useState(null)
      const [creating, setCreating] = useState(false)
      const [draftName, setDraftName] = useState('')

      const alive = useRef(true)
      const generation = useRef(0)

      // Every action commits only if it is still the latest request. This also
      // prevents an older project's calculation response replacing a new one.
      async function perform(load, commit) {
        const ticket = ++generation.current
        setBusy(true)
        setError('')
        try {
          const data = await load()
          if (alive.current && ticket === generation.current) commit(data)
        } catch (caught) {
          if (alive.current && ticket === generation.current) setError(message(caught))
        } finally {
          if (alive.current && ticket === generation.current) setBusy(false)
        }
      }

      function projectPath(id = activeId) {
        return '/projects/' + encodeURIComponent(id)
      }

      function refresh() {
        return perform(async () => {
          const { projects: list = [] } = await api('/projects')
          const next = list.some((item) => item.projectId === activeId)
            ? activeId : (list[0] && list[0].projectId) || ''
          const data = next ? await api(projectPath(next)) : { project: null }
          return { list, next, project: data.project }
        }, (data) => {
          setProjects(data.list)
          setActiveId(data.next)
          setProject(data.project)
          setDetail(null)
        })
      }

      useEffect(() => {
        alive.current = true
        refresh()
        return () => { alive.current = false; generation.current += 1 }
      }, [])

      function openProject(id) {
        setActiveId(id)
        setProject(null)
        setDetail(null)
        return perform(() => api(projectPath(id)), (data) => setProject(data.project))
      }

      function createProject(name) {
        if (busy) return
        const trimmed = String(name || '').trim()
        if (!trimmed) { setError('请输入项目名称'); return }
        return perform(async () => {
          const created = await api('/projects', { method: 'POST', body: JSON.stringify({ name: trimmed }) })
          const id = created.project.projectId
          const [data, listing] = await Promise.all([api(projectPath(id)), api('/projects')])
          return { id, project: data.project, projects: listing.projects || [] }
        }, (data) => {
          setActiveId(data.id)
          setProject(data.project)
          setProjects(data.projects)
          setDetail(null)
          setTab('overview')
          setCreating(false)
          setDraftName('')
        })
      }

      function mutateProject(action, payload, nextTab) {
        if (!activeId || busy) return
        return perform(async () => {
          await api(projectPath() + '/' + action, { method: 'POST', body: JSON.stringify(payload) })
          const [data, listing] = await Promise.all([api(projectPath()), api('/projects')])
          return { project: data.project, projects: listing.projects || [] }
        }, (data) => {
          setProject(data.project)
          setProjects(data.projects)
          setDetail(null)
          setTab(nextTab)
        })
      }

      function openCalculation(item) {
        if (!activeId || !item.calculationId) return
        setDetail(null)
        return perform(() => api(projectPath() + '/calculations/' + encodeURIComponent(item.calculationId)), setDetail)
      }

      const phase = phaseOf(project)
      const select = projects.length
        ? h('select', {
          value: activeId, disabled: busy,
          onChange: (event) => openProject(event.target.value),
          style: {
            padding: '5px 8px', borderRadius: 8, border: '1px solid ' + T.border,
            background: T.layer, color: T.text, maxWidth: 280,
          },
        }, projects.map((item) => h('option', { key: item.projectId, value: item.projectId },
          item.name + ' · ' + (phaseLabels[item.phase] || item.phase))))
        : null
      const header = h('header', {
        style: {
          display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
          padding: '12px 20px', borderBottom: '1px solid ' + T.border,
        },
      },
      h('strong', { style: { fontSize: 15 } }, '化工工程'),
      h(Pill, { color: T.brand }, phaseLabels[phase] || phase),
      h('span', { style: { flex: 1 } }),
      select,
      h(Button, { onClick: refresh, disabled: busy }, '刷新'),
      h(Button, {
        onClick: () => {
          setCreating(!creating)
          setDraftName('')
          setError('')
        },
        disabled: busy,
        primary: true,
      }, creating ? '取消新建' : '新建项目'))
      const createForm = creating
        ? h('div', {
          style: {
            display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
            padding: '10px 20px', borderBottom: '1px solid ' + T.border, background: T.layer,
          },
        },
        h('span', { style: { color: T.muted, fontSize: 12.5 } }, '新项目名称'),
        h('input', {
          value: draftName,
          autoFocus: true,
          placeholder: '例如：苯乙烯清洁生产设计',
          onChange: (event) => setDraftName(event.target.value),
          onKeyDown: (event) => {
            if (event.key === 'Enter') {
              event.preventDefault()
              createProject(draftName)
            }
            if (event.key === 'Escape') {
              setCreating(false)
              setDraftName('')
            }
          },
          style: {
            flex: '1 1 260px', minWidth: 220, padding: '6px 10px', borderRadius: 8,
            border: '1px solid ' + T.border, background: T.bg, color: T.text, fontSize: 13,
          },
        }),
        h(Button, { onClick: () => createProject(draftName), disabled: busy || !draftName.trim(), primary: true }, '创建'),
        h(Button, { onClick: () => { setCreating(false); setDraftName('') } }, '取消'))
        : null
      const errorBanner = error
        ? h('div', {
          style: { padding: '8px 20px', color: T.error, borderBottom: '1px solid ' + T.border, fontSize: 12.5 },
        }, error)
        : null
      const nav = h('nav', {
        style: { display: 'flex', gap: 2, padding: '8px 16px 0', borderBottom: '1px solid ' + T.border, flexWrap: 'wrap' },
      }, tabs.map(([id, label]) => h('button', {
        key: id, type: 'button', onClick: () => setTab(id),
        style: {
          padding: '6px 12px', border: 'none', background: 'transparent',
          borderBottom: tab === id ? '2px solid ' + T.brand : '2px solid transparent',
          color: tab === id ? T.text : T.muted, cursor: 'pointer', fontSize: 13,
        },
      }, label)))
      let body
      if (!project) body = h('div', { style: { color: T.muted, padding: 24 } }, '还没有本地项目。启动内核后点击“新建项目”。')
      else if (tab === 'overview') body = h(Overview, { project })
      else if (tab === 'requirements') body = h(Requirements, { project })
      else if (tab === 'plan') body = h(Plan, { project })
      else if (tab === 'basis') body = h(Basis, { project })
      else if (tab === 'calculations') body = h(Calculations, { project, detail, onOpen: openCalculation })
      else if (tab === 'files') body = h(Files, { project })
      else body = h(Review, { project, busy,
        onReview: () => mutateProject('review', { note: '面板自检' }, 'review'),
        onBundle: () => mutateProject('bundle', {}, 'overview'),
      })
      const content = h('div', { style: { flex: 1, overflow: 'auto', padding: '16px 20px', minHeight: 0 } }, body)
      return h('div', {
        style: {
          height: '100%', display: 'flex', flexDirection: 'column',
          background: T.bg, color: T.text, fontSize: 13, minHeight: 0,
        },
      }, header, createForm, errorBanner, nav, content)
    }

    function Settings() {
      const [health, setHealth] = useState(null)
      const [error, setError] = useState('')
      useEffect(() => {
        let alive = true
        api('/health')
          .then((data) => { if (alive) setHealth(data) })
          .catch(() => { if (alive) setError('本地内核未运行') })
        return () => { alive = false }
      }, [])
      let status
      if (error) status = h('p', { style: { color: T.error, margin: 0 } }, error + '；请先运行 scripts\\start-kernel.cmd')
      else if (health) {
        status = h('ul', { style: { margin: 0, paddingLeft: 18 } },
          h('li', null, '版本 ' + health.version + ' · 阶段门禁：' + health.phaseGate),
          h('li', null, '数据目录：' + health.dataDir),
          h('li', null, '项目数：' + health.projectCount))
      } else status = h('p', { style: { color: T.muted, margin: 0 } }, '检测中…')
      return h('div', { style: { fontSize: 13, lineHeight: 1.8 } },
        h('p', { style: { margin: '0 0 8px' } }, '化工工程本地内核：'),
        status,
        h('p', { style: { color: T.muted, margin: '8px 0 0' } },
          '内核地址与令牌在插件配置（cordis.patch.yml 的 chemellm 行）中设置；令牌只在 Host 侧使用，浏览器不可见。'))
    }

    function Icon(props) {
      return h('svg', {
        viewBox: '0 0 24 24', width: props.size || 20, height: props.size || 20,
        fill: 'none', stroke: 'currentColor', strokeWidth: 1.6,
        strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true,
        style: { opacity: props.active ? 1 : 0.75, display: 'block' },
      },
      h('path', { d: 'M9 3h6' }),
      h('path', { d: 'M10 3v5.2L4.8 18a2 2 0 0 0 1.7 3h11a2 2 0 0 0 1.7-3L14 8.2V3' }),
      h('path', { d: 'M7.2 14h9.6' }))
    }

    return {
      inject: ['slots'],
      apply(ctx) {
        ctx.slots.inject('sidebar.panellist', () => ctx.slots.register({
          name: 'sidebar.panellist', id: 'chemellm', order: 5, label: '化工工程',
        }, Icon))
        ctx.slots.inject('main', () => ctx.slots.register({
          name: 'main', key: 'chemellm',
        }, Panel))
        ctx.slots.inject('settings.section', () => ctx.slots.register({
          name: 'settings.section', id: 'chemellm', order: 60, label: '化工工程',
        }, Settings))
      },
    }
  },
})
