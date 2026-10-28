export function createWorkspaceChrome(state, h) {
 const {api,post,esc,icon,render,loadProject,saveDraft,modal,previewFile,toast,closeMobileSidebar}=h;
 const $=s=>document.querySelector(s);
 const url=s=>'/api/projects/'+state.project.id+s;
 const curl=s=>url('/conversations/'+state.conversation.id+s);
 let revision=0,scope='conversation',previewId=null;
 const remember=()=>{try{localStorage.setItem('chemellm-conversation-'+state.project.id,state.conversation.id);}catch{}};
 function updateLocation(){if(state.page==='workspace'&&state.conversation){$('#page-name').textContent=state.conversation.title;document.title=state.conversation.title+' · ChemELLM';}}
 function conversationButton(c){
  const count=c.calculation_count?c.calculation_count+' 次计算':c.message_count?c.message_count+' 条消息':c.history_cutoff?'文件记录':'空会话';
  return '<button class="conversation-entry '+(c.id===state.conversation?.id?'selected':'')+'" data-conversation="'+c.id+'" '+(c.id===state.conversation?.id?'aria-current="true"':'')+' title="'+esc(c.title)+' · '+count+'">'+icon(c.history_cutoff?'workflow':'message')+'<span>'+esc(c.title)+'</span><small class="conversation-count">'+count+'</small>'+(['running','queued'].includes(c.latest_status)?'<i class="conversation-running" aria-label="执行中"></i>':'')+'</button>';
 }
 function renderProjects(){
  $('#project-list').innerHTML=state.projects.map(p=>{
   const current=p.id===state.project.id,conversations=current?state.conversations:[];
   const keys=[...new Set(conversations.map(c=>c.task_key||''))];
   return '<section class="project-branch '+(current?'current':'')+'"><div class="project-row"><button class="project-entry" data-project="'+p.id+'" aria-expanded="'+current+'" title="'+esc(p.name)+'">'+icon('folder')+'<span>'+esc(p.name)+'</span></button><button class="icon-button project-add" data-new-conversation="'+p.id+'" aria-label="在 '+esc(p.name)+' 中新建会话" title="新建会话">'+icon('plus')+'</button></div>'+(current?'<div class="project-conversations">'+keys.map(key=>'<div class="conversation-group">'+(key?'<div class="conversation-group-label">'+icon('workflow')+'<span>'+esc(state.studyTasks.find(t=>t.key===key)?.config.title||key)+'</span><button class="icon-button" data-task-conversation="'+esc(key)+'" aria-label="为此任务新建会话" title="为此任务新建会话">'+icon('plus')+'</button></div>':'')+conversations.filter(c=>(c.task_key||'')===key).map(conversationButton).join('')+'</div>').join('')+'</div>':'')+'</section>';
  }).join('');
 }
 async function refreshConversations(){
  const id=state.project.id,items=await api(url('/conversations'));if(state.project.id!==id)return;
  state.conversations=items;state.conversation=items.find(c=>c.id===state.conversation?.id)||items[0];renderProjects();updateLocation();
 }
 async function loadContext(){
  const id=state.project.id,[items,study]=await Promise.all([api(url('/conversations')),api(url('/study'))]);if(state.project.id!==id)return;
  state.conversations=items;state.studyTasks=study.tasks;let remembered;try{remembered=localStorage.getItem('chemellm-conversation-'+id);}catch{}
  state.conversation=items.find(c=>c.id===state.conversation?.id)||items.find(c=>c.id===remembered)||items[0];
  const history=items.find(c=>c.history_cutoff),known=state.conversation;
  try{
   const key='chemellm-history-discovered-'+id;
   if(history&&!localStorage.getItem(key)){
    if(!known||known.title==='新会话'&&!known.message_count&&!known.calculation_count)state.conversation=history;
    localStorage.setItem(key,'true');
   }
  }catch{}
  if(!state.conversation){const c=await post(url('/conversations'),{title:'新会话'});if(state.project.id!==id)return;state.conversations=[c];state.conversation=c;}
  remember();renderProjects();updateLocation();
 }
 async function selectProject(id){
  saveDraft();clearTimeout(state.poll);if(id!==state.project.id){state.project=state.projects.find(p=>p.id===id);state.conversation=null;}
  state.page='workspace';localStorage.setItem('chemellm-project',id);$('#project-select').value=id;closeMobileSidebar();clearPreview();await loadProject();
 }
 async function selectConversation(id){
  saveDraft();clearTimeout(state.poll);state.run=null;state.chatLocked=false;state.conversation=state.conversations.find(c=>c.id===id);state.page='workspace';remember();renderProjects();closeMobileSidebar();clearPreview();await render();await renderResources();
 }
 async function newConversation(projectId=state.project.id,taskKey=null){
  if(projectId!==state.project.id)await selectProject(projectId);
  const id=state.project.id,c=await post(url('/conversations'),{title:'新会话',task_key:taskKey});if(state.project.id!==id)return;state.conversations.unshift(c);await selectConversation(c.id);
 }
 function editConversation(){
  const pid=state.project.id,c=state.conversation;if(!c)return;
  modal('会话设置','<form id="conversation-settings-form"><label class="field">会话名称<input name="title" required maxlength="150" value="'+esc(c.title)+'"></label><label class="field">关联研究任务<select name="task_key"><option value="">项目会话 · 未关联具体任务</option>'+state.studyTasks.map(t=>'<option value="'+esc(t.key)+'" '+(t.key===c.task_key?'selected':'')+'>'+esc(t.config.title)+'</option>').join('')+'</select></label><p class="source-note">同一个研究任务可以关联多个会话，每个会话保留独立的对话与草稿。</p><button class="button" type="submit">保存设置</button></form>');
  $('#conversation-settings-form').onsubmit=async e=>{e.preventDefault();e.stopPropagation();const f=e.target,b=f.querySelector('button');b.disabled=true;try{const value=Object.fromEntries(new FormData(f));value.task_key=value.task_key||null;await api('/api/projects/'+pid+'/conversations/'+c.id,{method:'PATCH',body:JSON.stringify(value)});$('#form-dialog').close();if(state.project.id===pid){await refreshConversations();await renderResources();}}catch(error){toast(error.message);}finally{b.disabled=false;}};
 }
 function clearPreview(){previewId=null;$('#resource-preview').hidden=true;$('#resource-preview-frame').src='about:blank';}
 function closeResources(){revision++;$('#project-dialog').hidden=true;document.body.classList.remove('resources-open');$('#project-overview-button').setAttribute('aria-expanded','false');clearPreview();}
 async function openResources(){if(!state.conversation)return;$('#project-dialog').hidden=false;document.body.classList.add('resources-open');$('#project-overview-button').setAttribute('aria-expanded','true');await renderResources();}
 async function renderResources(){
  if($('#project-dialog').hidden||!state.conversation)return;
  const n=++revision,pid=state.project.id,cid=state.conversation.id;
  $('#project-overview').innerHTML='<div class="loading">加载当前任务资源…</div>';
  try{
   const [data,files]=await Promise.all([api(curl('/resources')),api(url('/artifacts'))]);if(n!==revision||state.project.id!==pid||state.conversation.id!==cid)return;state.files=files;
   const resources=scope==='project'?files:data.artifacts,a=state.acceptance;
   $('#project-overview').innerHTML='<div class="resource-context"><span class="nav-label">'+(data.task?'当前研究任务':'当前会话')+'</span><h2>'+esc(data.task?.config.title||data.conversation.title)+'</h2><p>'+esc(state.project.name)+(data.task?' · '+esc(data.conversation.title):'')+'</p></div>'+(data.task?'<div class="resource-task-status"><span class="pill">'+esc(({pending:'未执行',running:'执行中',succeeded:'结果已保存',stale:'上游已变化',failed:'执行失败'})[data.task.status]||data.task.status)+'</span><button class="text-button" data-navigate="study">查看任务</button></div>':'')+'<div class="resource-tabs" role="group" aria-label="资源范围"><button data-resource-scope="conversation" class="'+(scope==='conversation'?'active':'')+'">任务相关 <span>'+data.artifacts.length+'</span></button><button data-resource-scope="project" class="'+(scope==='project'?'active':'')+'">项目全部 <span>'+files.length+'</span></button></div><div class="resource-toolbar"><span>'+resources.length+' 份资源</span><button class="text-button" data-add-resource>关联文件</button><button class="icon-button" data-action="upload" aria-label="上传任务资料" title="上传任务资料">'+icon('upload')+'</button><button class="icon-button" data-refresh-resources aria-label="刷新任务资源" title="刷新任务资源">'+icon('refresh')+'</button></div><div class="resource-list">'+(resources.length?resources.map(f=>'<article class="resource-card"><button class="resource-open" data-resource-preview="'+f.id+'"><span class="resource-file-icon">'+icon('files')+'<small>'+esc(f.kind.toUpperCase())+'</small></span><span class="resource-file-info"><strong>'+esc(f.name)+'</strong><small>'+esc((f.relations||[]).join(' · ')||'项目文件')+' · '+(f.has_visual_preview?'可视预览':'文本预览 / 下载')+'</small></span></button><div class="resource-file-actions"><button class="text-button" data-resource-preview="'+f.id+'">预览</button><a href="'+esc(f.download_url)+'" download aria-label="下载 '+esc(f.name)+'">下载</a>'+(scope==='project'&&!data.artifacts.some(a=>a.id===f.id)?'<button class="text-button" data-link-resource="'+f.id+'">关联到会话</button>':'')+'</div></article>').join(''):'<div class="resource-empty">'+icon('files')+'<strong>还没有关联资源</strong><p>上传资料、关联项目文件，或在对话中生成成果。</p><button class="button secondary small" data-resource-scope="project">浏览项目文件</button></div>')+'</div><details class="resource-project-actions"><summary>项目操作</summary><div class="overview-tools"><button class="button secondary small" data-action="import">导入赛题</button><button class="button secondary small" data-navigate="files">文件与图纸</button><button class="button secondary small" data-navigate="acceptance">验收 '+(a.verified||0)+' / '+(a.mandatory||0)+'</button></div></details>';
   if(previewId&&!resources.some(f=>f.id===previewId))clearPreview();
  }catch(error){if(n===revision)$('#project-overview').innerHTML='<p class="inline-error">'+esc(error.message)+'</p>';}
 }
 function previewResource(id){const f=state.files.find(f=>f.id===id);if(!f)return;previewId=id;$('#resource-preview').hidden=false;$('#resource-preview-title').textContent=f.name;$('#resource-preview-title').title=f.name;$('#resource-preview-frame').src=f.preview_url;}
 async function linkResource(id){await post(curl('/resources/'+id));await renderResources();}
 function addResourceDialog(){
  const pid=state.project.id,cid=state.conversation.id;
  modal('关联项目资料','<form id="link-resource-form"><label class="field">选择项目文件<select name="artifact_id" required>'+state.files.map(f=>'<option value="'+f.id+'">'+esc(f.name)+'</option>').join('')+'</select></label><p class="source-note">文件保留在项目中，同时出现在当前会话的任务资源列表。</p><button class="button" type="submit" '+(!state.files.length?'disabled':'')+'>关联资料</button></form>');
  $('#link-resource-form').onsubmit=async e=>{e.preventDefault();e.stopPropagation();try{await post('/api/projects/'+pid+'/conversations/'+cid+'/resources/'+e.target.elements.artifact_id.value);$('#form-dialog').close();await renderResources();}catch(error){toast(error.message);}};
 }
 $('#project-list').onclick=async e=>{const b=e.target.closest('button');if(!b)return;try{if(b.dataset.newConversation)await newConversation(b.dataset.newConversation);else if(b.dataset.taskConversation)await newConversation(state.project.id,b.dataset.taskConversation);else if(b.dataset.conversation)await selectConversation(b.dataset.conversation);else if(b.dataset.project)await selectProject(b.dataset.project);}catch(error){toast(error.message);}};
 $('#project-dialog').addEventListener('click',async e=>{const b=e.target.closest('button');if(!b)return;try{if(b.hasAttribute('data-close-resources')){closeResources();$('#project-overview-button').focus();}else if(b.dataset.resourceScope){scope=b.dataset.resourceScope;clearPreview();await renderResources();}else if(b.dataset.resourcePreview)previewResource(b.dataset.resourcePreview);else if(b.hasAttribute('data-close-resource-preview'))clearPreview();else if(b.hasAttribute('data-expand-resource'))previewFile(previewId);else if(b.dataset.linkResource)await linkResource(b.dataset.linkResource);else if(b.hasAttribute('data-add-resource'))addResourceDialog();else if(b.hasAttribute('data-refresh-resources'))await renderResources();}catch(error){toast(error.message);}});
 $('#new-conversation').onclick=()=>newConversation().catch(e=>toast(e.message));$('#conversation-settings').onclick=editConversation;
 $('#project-overview-button').onclick=()=>{if($('#project-dialog').hidden)openResources().catch(e=>toast(e.message));else closeResources();};
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('#project-dialog').hidden&&!document.querySelector('dialog[open]')){closeResources();$('#project-overview-button').focus();}});
 return {loadContext,refreshConversations,renderProjects,updateLocation,selectProject,selectConversation,newConversation,renderResources,openResources,closeResources,clearPreview};
}
