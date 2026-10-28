const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty=v=>JSON.stringify(v,null,2);
const names={pending:'未执行',stale:'上游变化 · 已过期',running:'执行中',succeeded:'当前结果 · 待专业审核',failed:'执行失败',interrupted:'服务中断',cancelled:'已取消',queued:'排队中',completed:'执行结束 · 待专业审核',blocked:'需要处理',budget_exhausted:'达到预算'};
let timer;

export async function renderStudy(state,helpers){
 clearTimeout(timer);
 const {intro,api,post,toast,modal}=helpers,id=state.project.id,prefix='/api/projects/'+id;
 const current=()=>state.project.id===id&&state.page==='study';
 const data=await api(prefix+'/study');if(!current())return;
 state.studyTasks=data.tasks;helpers.refreshNavigation?.();
 const refresh=()=>renderStudy(state,helpers).catch(e=>toast(e.message));
 document.querySelector('#content').innerHTML=intro('研究任务与依赖','版本化参数、上游结果和成果一起管理。','RESEARCH / WORKFLOW')+
 '<div id="study-workspace"><div class="toolbar"><button class="button" data-study-new-parameter>＋ 研究参数</button><button class="button secondary" data-study-new-task>＋ 研究任务</button><button class="button secondary" data-study-run>执行 / 重算所选任务 →</button><button class="text-button" data-study-refresh>刷新状态</button></div>'+
 '<p class="note">'+esc(data.scope)+' 取消与时间预算在工具调用边界生效；正在执行的工具可能继续返回。未登记的依赖不自动推断。</p>'+
 '<section class="panel"><h2>研究参数</h2>'+(data.parameters.length?'<div class="table-wrap"><table data-study-parameters><thead><tr><th>参数</th><th>值与单位</th><th>版本</th><th>类别 / 条件 / 来源</th><th>操作</th></tr></thead><tbody>'+data.parameters.map(p=>'<tr><td>'+esc(p.data.label)+'<br><small>'+esc(p.key)+'</small></td><td>'+esc(p.data.value)+' '+esc(p.data.unit)+'</td><td>v'+p.revision+'</td><td>'+esc(({assumption:'假设',experimental:'实验',predicted:'预测',literature:'文献'})[p.data.provenance])+'<br><small>'+esc(p.data.conditions)+'<br>'+esc(p.data.source||'未指定外部来源')+'</small></td><td><button class="text-button" data-study-parameter="'+p.key+'">编辑版本</button></td></tr>').join('')+'</tbody></table></div>':'<p class="source-note section-gap">登记关键输入，并在任务中绑定；修改参数会使所有下游结果失效。</p>')+'</section>'+
 '<section class="panel"><h2>任务与当前结果</h2>'+(data.tasks.length?'<div class="study-task-list">'+data.tasks.map(t=>{const a=t.latest_attempt;return '<article class="study-task" data-study-task="'+t.key+'"><div class="toolbar"><label><input type="checkbox" name="study-task" value="'+t.key+'" '+(!['succeeded','running'].includes(t.status)?'checked':'')+'> '+esc(t.config.title)+'</label><span class="pill '+(t.status==='succeeded'?'good':'warn')+'" data-study-status>'+esc(names[t.status]||t.status)+'</span><button class="text-button" data-study-edit-task="'+t.key+'">编辑 v'+t.revision+'</button></div><p class="source-note">'+esc(t.key)+' · '+esc(t.config.tool)+' · 上游：'+esc([...new Set([...(t.config.depends_on||[]),...t.config.bindings.filter(b=>b.kind==='task').map(b=>b.key)])].join(', ')||'无')+'</p>'+(t.reason?'<p class="inline-error">'+esc(t.reason)+'</p>':'')+(a?'<details><summary>实际输入、来源版本和结果</summary><pre class="result">'+esc(pretty(a))+'</pre></details><div class="toolbar section-gap">'+(a.result.artifacts||[]).map(f=>'<a class="button secondary small" href="'+f.download_url+'" download>'+esc(f.name)+(t.status==='succeeded'?'':' · 旧/待确认结果')+' ↓</a>').join('')+'</div>':'')+'</article>'}).join('')+'</div>':'<p class="source-note section-gap">先登记上游计算，再登记依赖它的图纸或报告。任务参数支持JSON指针绑定；可从工具页保存当前输入。</p>')+'</section>'+
 ((data.uncertain_attempts||[]).length?'<section class="panel section-gap"><h2>中断调用待核对</h2><p class="note">以下调用在服务中断前未保存确认结果。先核对已有计算和文件，再确认重试或采用已有记录；系统不会直接重放。</p>'+data.uncertain_attempts.map(a=>'<article class="study-task" data-uncertain-attempt="'+a.id+'"><h3>'+esc(a.key)+'</h3><p class="source-note">调用 '+esc(a.id)+' · 输入版本 v'+a.task_revision+'</p><details><summary>中断时输入与候选计算</summary><pre class="result">'+esc(pretty({input:a.input,sources:a.sources,candidates:a.candidate_calculations}))+'</pre></details><button class="button secondary small" data-study-reconcile="'+a.id+'">核对并确认处置</button></article>').join('')+'</section>':'')+
 '<section class="panel"><h2>执行历史与检查点</h2><div class="section-gap">'+(data.executions.length?data.executions.map(r=>'<article class="study-task" data-study-execution="'+r.id+'"><div class="toolbar"><span class="pill '+(r.status==='completed'?'good':'warn')+'">'+esc(names[r.status]||r.status)+'</span><span class="source-note">'+new Date(r.created_at).toLocaleString('zh-CN')+' · '+r.state.tool_calls+'/'+r.request.max_tools+' 次工具 · '+Number(r.state.active_seconds||0).toFixed(1)+' s</span>'+(['queued','running'].includes(r.status)?'<button class="text-button" data-study-cancel="'+r.id+'">取消</button>':['interrupted','failed','blocked','cancelled'].includes(r.status)?'<button class="text-button" data-study-resume="'+r.id+'">恢复执行</button>':'')+'</div><p class="source-note">顺序：'+esc(r.state.order.join(' → '))+'<br>已完成：'+esc(r.state.completed.join(', ')||'无')+'</p>'+(r.state.reason?'<p class="inline-error">'+esc(r.state.reason)+'</p>':'')+'<button class="text-button" data-study-events="'+r.id+'">查看执行事件</button></article>').join(''):'<p class="source-note">尚无研究任务执行记录。</p>')+'</div></section></div>';
 const root=document.querySelector('#study-workspace');
 for(const article of root.querySelectorAll('[data-study-task]')){
  const button=document.createElement('button');button.className='text-button';button.textContent='新建任务会话';button.dataset.studyConversation=article.dataset.studyTask;article.querySelector('.toolbar').append(button);
 }
 root.onclick=async event=>{
  const b=event.target.closest('button');if(!b)return;
  try{
   if(b.dataset.studyConversation)await helpers.openConversation(b.dataset.studyConversation);
   else if(b.hasAttribute('data-study-new-parameter'))parameterDialog(null);
   else if(b.dataset.studyParameter)parameterDialog(data.parameters.find(p=>p.key===b.dataset.studyParameter));
   else if(b.hasAttribute('data-study-new-task'))taskDialog(null);
   else if(b.dataset.studyEditTask)taskDialog(data.tasks.find(t=>t.key===b.dataset.studyEditTask));
   else if(b.dataset.studyReconcile)reconcileDialog(data.uncertain_attempts.find(a=>a.id===b.dataset.studyReconcile));
   else if(b.hasAttribute('data-study-refresh'))await refresh();
   else if(b.hasAttribute('data-study-run')){
    const keys=[...root.querySelectorAll('[name="study-task"]:checked')].map(n=>n.value);if(!keys.length)throw Error('请选择需要执行的任务');
    modal('执行研究任务','<form id="study-start-form"><p class="source-note">自动包含全部上游任务；当前有效结果会复用。所选任务：'+esc(keys.join(', '))+'</p><label class="field">本次最多工具次数<input name="max_tools" type="number" min="1" max="100" value="30" required></label><label class="field">累计主动执行时间 / s<input name="max_seconds" type="number" min="1" max="3600" value="300" required></label><button class="button">开始执行</button></form>');
    document.querySelector('#study-start-form').onsubmit=async e=>{e.preventDefault();e.stopPropagation();try{const f=e.target;await post(prefix+'/study/executions',{task_keys:keys,max_tools:Number(f.elements.max_tools.value),max_seconds:Number(f.elements.max_seconds.value)});document.querySelector('#form-dialog').close();await refresh()}catch(error){toast(error.message)}};
   }
   else if(b.dataset.studyCancel){await post('/api/study-executions/'+b.dataset.studyCancel+'/cancel');await refresh()}
   else if(b.dataset.studyResume){await post('/api/study-executions/'+b.dataset.studyResume+'/resume');await refresh()}
   else if(b.dataset.studyEvents){const r=await api('/api/study-executions/'+b.dataset.studyEvents);modal('研究执行事件','<pre class="result">'+esc(pretty(r))+'</pre>')}
  }catch(error){toast(error.message)}
 };
 function reconcileDialog(a){
  modal('核对中断调用 · '+a.key,'<form id="study-reconcile-form"><p class="note">请先核对中断前实际生成的文件与计算记录。确认重试可能再次生成成果；采用已有记录会核对工具、输入及依赖版本。这是执行处置，不能替代专业审核。</p><label class="field">处置方式<select name="decision"><option value="retry">确认重新执行，保留中断历史</option><option value="adopt">采用已核对的计算记录</option></select></label><label class="field">已有计算记录<select name="calculation_id"><option value="">请选择采用的记录</option>'+a.candidate_calculations.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.tool)+' · '+esc(c.created_at)+' · '+esc(c.id)+'</option>').join('')+'</select></label><label class="field">核对者<input name="reviewer" minlength="2" maxlength="100" required></label><label class="field">核对依据与处置说明<textarea name="notes" minlength="10" maxlength="3000" required></textarea></label><button class="button">保存处置确认</button></form>');
  document.querySelector('#study-reconcile-form').onsubmit=async e=>{e.preventDefault();e.stopPropagation();const f=e.target,button=f.querySelector('button');button.disabled=true;try{const d=Object.fromEntries(new FormData(f));d.calculation_id=d.decision==='adopt'?d.calculation_id:null;await post('/api/study-attempts/'+a.id+'/reconcile',d);document.querySelector('#form-dialog').close();await refresh()}catch(error){toast(error.message)}finally{button.disabled=false}};
 }
 function parameterDialog(p){
  const d=p?.data||{label:'',value:1,unit:'dimensionless',provenance:'assumption',conditions:'',source:'',uncertainty:null};
  modal(p?'编辑研究参数 · v'+p.revision:'登记研究参数','<form id="study-parameter-form"><div class="parameter-grid"><label class="field">参数键<input name="key" pattern="[A-Za-z][A-Za-z0-9_\\-]{0,59}" value="'+esc(p?.key||'')+'" '+(p?'readonly':'')+' required></label><label class="field">名称<input name="label" value="'+esc(d.label)+'" required></label><label class="field">数值<input name="value" type="number" step="any" value="'+esc(d.value)+'" required></label><label class="field">单位<input name="unit" value="'+esc(d.unit)+'" required></label></div><label class="field">数据类别<select name="provenance">'+Object.entries({assumption:'假设',experimental:'实验',predicted:'预测',literature:'文献'}).map(([v,label])=>'<option value="'+v+'" '+(d.provenance===v?'selected':'')+'>'+label+'</option>').join('')+'</select></label><label class="field">适用条件<textarea name="conditions" required>'+esc(d.conditions)+'</textarea></label><label class="field">来源 / 定位<textarea name="source">'+esc(d.source)+'</textarea></label><label class="field">标准不确定度（同单位，可留空）<input name="uncertainty" type="number" min="0" step="any" value="'+esc(d.uncertainty??'')+'"></label><p class="note">保存新版本将使所有关联下游任务、文件和已有审核过期；不会删除历史。</p><button class="button">保存参数版本</button></form>');
  document.querySelector('#study-parameter-form').onsubmit=async e=>{e.preventDefault();e.stopPropagation();try{const f=e.target,d=Object.fromEntries(new FormData(f));d.value=Number(d.value);d.uncertainty=d.uncertainty===''?null:Number(d.uncertainty);d.expected_revision=p?.revision??null;await post(prefix+'/study/parameters',d);document.querySelector('#form-dialog').close();await refresh()}catch(error){toast(error.message)}};
 }
 function taskDialog(t){
  const config=t?.config||{title:'',tool:'convert_units',arguments:{value:1,from_unit:'bar',to_unit:'Pa'},bindings:[],depends_on:[]};
  const blocked=new Set(['ask_user','equipment_save','claim_save','evidence_add']);
  const tools=Object.keys(state.schemas).filter(name=>!blocked.has(name));
  const labels=Object.fromEntries(state.tools.map(tool=>[tool.id,tool.name]));
  modal(t?'编辑研究任务 · v'+t.revision:'登记研究任务','<form id="study-task-form"><div class="parameter-grid"><label class="field">任务标识<input name="key" pattern="[A-Za-z][A-Za-z0-9_\\-]{0,59}" value="'+esc(t?.key||'')+'" '+(t?'readonly':'')+' required></label><label class="field">任务名称<input name="title" value="'+esc(config.title)+'" required maxlength="150"></label></div><label class="field">执行工具<select name="tool">'+tools.map(name=>'<option value="'+name+'" '+(name===config.tool?'selected':'')+'>'+esc(labels[name]||name)+'</option>').join('')+'</select></label><h3>工具输入</h3><div id="study-tool-inputs"></div><h3>参数与上游结果</h3><p class="source-note">把输入字段连接到研究参数或上游计算。未连接的字段使用上方填写的值；改变来源会使本任务及后续成果过期。</p><div id="study-bindings"></div><button class="button secondary small" type="button" data-add-binding>＋ 关联一个输入</button><fieldset class="dataset-models"><legend>等待这些任务完成</legend>'+data.tasks.filter(other=>other.key!==t?.key).map(other=>'<label class="dataset-choice"><input type="checkbox" name="dependency" value="'+esc(other.key)+'" '+(config.depends_on.includes(other.key)?'checked':'')+'> '+esc(other.config.title)+'</label>').join('')+'</fieldset><button class="button" type="submit">保存任务版本</button></form>');
  const form=document.querySelector('#study-task-form');
  const sourceOptions=data.parameters.map(p=>['parameter:'+p.key,p.data.label+'（研究参数）']).concat(data.tasks.filter(other=>other.key!==t?.key).map(other=>['task:'+other.key,other.config.title+'（计算结果）']));
  function drawInputs(values){
   const properties=state.schemas[form.elements.tool.value].properties||{};
   document.querySelector('#study-tool-inputs').innerHTML=Object.entries(properties).map(([key,schema])=>{
    const value=values[key]??schema.default??'',label=schema.description||schema.title||key;
    const complex=schema.type==='array'||schema.type==='object'||schema.$ref||Array.isArray(value)||(value!==null&&typeof value==='object');
    const kind=complex?'json':schema.type==='number'||schema.type==='integer'?'number':schema.type==='boolean'?'boolean':'text';
    return '<label class="field">'+esc(label)+'<small> · '+esc(key)+'</small>'+(kind==='json'?'<textarea data-study-input="'+key+'" data-kind="json" rows="4">'+esc(pretty(value))+'</textarea>':kind==='boolean'?'<select data-study-input="'+key+'" data-kind="boolean"><option value="true" '+(value?'selected':'')+'>是</option><option value="false" '+(!value?'selected':'')+'>否</option></select>':'<input data-study-input="'+key+'" data-kind="'+kind+'" type="'+(kind==='number'?'number':'text')+'" step="any" value="'+esc(value)+'">')+'</label>';
   }).join('');
  }
  function addBinding(binding={target:'',kind:'parameter',key:'',path:'',unit:'',render_as:'value',prefix:'',suffix:''}){
   const row=document.createElement('fieldset');row.className='parameter-row study-binding';
   row.innerHTML='<legend>关联输入</legend><div class="parameter-grid"><label class="field">输入字段<input data-binding="target" value="'+esc(binding.target.replace(/^\//,''))+'" placeholder="例如 value 或 body" required></label><label class="field">数据来源<select data-binding="source" required><option value="">请选择</option>'+sourceOptions.map(([value,label])=>'<option value="'+esc(value)+'" '+(value===binding.kind+':'+binding.key?'selected':'')+'>'+esc(label)+'</option>').join('')+'</select></label><label class="field">结果字段（研究参数留空）<input data-binding="path" value="'+esc(binding.path.replace(/^\//,''))+'" placeholder="例如 value"></label><label class="field">输入单位（可选）<input data-binding="unit" value="'+esc(binding.unit)+'" placeholder="例如 Pa"></label></div><label class="field">填入方式<select data-binding="render_as"><option value="value" '+(binding.render_as==='value'?'selected':'')+'>数值或原始内容</option><option value="text" '+(binding.render_as==='text'?'selected':'')+'>拼接为报告文字</option></select></label><div class="parameter-grid"><label class="field">前置文字<input data-binding="prefix" value="'+esc(binding.prefix)+'"></label><label class="field">后置文字<input data-binding="suffix" value="'+esc(binding.suffix)+'"></label></div><button class="text-button" type="button" data-remove-binding>移除此关联</button>';
   row.querySelector('[data-remove-binding]').onclick=()=>row.remove();
   document.querySelector('#study-bindings').append(row);
  }
  drawInputs(config.arguments);config.bindings.forEach(addBinding);
  form.elements.tool.onchange=()=>{drawInputs(state.examples[form.elements.tool.value]||{});document.querySelector('#study-bindings').replaceChildren()};
  form.querySelector('[data-add-binding]').onclick=()=>addBinding();
  form.onsubmit=async e=>{e.preventDefault();e.stopPropagation();const submit=form.querySelector('[type="submit"]');submit.disabled=true;try{
   const arguments_={};
   form.querySelectorAll('[data-study-input]').forEach(input=>{if(input.value==='')return;arguments_[input.dataset.studyInput]=input.dataset.kind==='number'?Number(input.value):input.dataset.kind==='json'?JSON.parse(input.value):input.dataset.kind==='boolean'?input.value==='true':input.value});
   const bindings=[...form.querySelectorAll('.study-binding')].map(row=>{const value=key=>row.querySelector('[data-binding="'+key+'"]').value;const [kind,key]=value('source').split(':');const pointer=path=>path?(path.startsWith('/')?path:'/'+path):'';return {target:pointer(value('target')),kind,key,path:pointer(value('path')),unit:value('unit'),render_as:value('render_as'),prefix:value('prefix'),suffix:value('suffix')}});
   await post(prefix+'/study/tasks',{key:form.elements.key.value,title:form.elements.title.value,tool:form.elements.tool.value,arguments:arguments_,bindings,depends_on:[...form.querySelectorAll('[name="dependency"]:checked')].map(n=>n.value),expected_revision:t?.revision??null});document.querySelector('#form-dialog').close();await refresh();
  }catch(error){toast(error.message)}finally{submit.disabled=false}};
 }
 if(data.executions.some(r=>['queued','running'].includes(r.status)))timer=setTimeout(()=>{if(current())refresh()},1600);
}
