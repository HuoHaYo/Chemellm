import {renderDatasets,datasetArguments,datasetResult} from './datasets.js';
import {renderEvidence} from './evidence.js';
import {simulationResult} from './simulation.js';
import {renderStudy} from './study.js';
import {recoveryCards,bindRecovery} from './run-recovery.js';
import {createWorkspaceChrome} from './workspace-chrome.js';
import {createModelSettings} from './model-settings.js';
import {historyMarkup,bindHistory} from './conversation-history.js';
const $=s=>document.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pretty=v=>JSON.stringify(v,null,2);
const icon=name=>'<svg class="icon" aria-hidden="true"><use href="/icons.svg#'+name+'"></use></svg>';
const pageNames={workspace:'设计对话',tools:'工具与计算',research:'文献检索',evidence:'全文证据',datasets:'实验数据',study:'研究任务',files:'文件与图纸',database:'工程数据库',acceptance:'赛题验收'};
const state={project:null,conversation:null,conversations:[],studyTasks:[],page:"workspace",projects:[],tools:[],schemas:{},files:[],acceptance:{requirements:[]},config:{},run:null,poll:null,tool:"properties"};
const statusNames={queued:"排队中",running:"执行中",completed:"执行结束 · 待工程校核",needs_review:"仍有工具失败",awaiting_user:"等待补充参数",iteration_limit:"达到本轮上限",budget_exhausted:"达到累计预算",failed:"执行失败",cancelled:"已取消",interrupted:"服务重启后中断"};
const toolStatus={integrated:"已接入",planned:"待接入",reference:"技术参考"};
const equipmentTypes={reactor:"反应器",column:"塔器",exchanger:"换热器",pump:"泵",tank:"储罐",pipe:"管路",other:"其他"};
const provenanceNames={assumption:"假设值",calculated:"计算结果",datasheet:"设备手册",literature:"文献数据"};
const labels={compound:"化合物名称 / CAS",temperature_K:"温度 / K",pressure_Pa:"绝对压力 / Pa",quality:"蒸汽干度（指定温度时设为 null）",value:"数值",from_unit:"原单位",to_unit:"目标单位",product_t_per_year:"苯乙烯产量 / t·a⁻¹",operating_hours:"年操作时间 / h",conversion:"单程转化率",ethylbenzene_recovery:"乙苯回收率",recycle_purge:"循环排放比例",duty_kW:"换热负荷 / kW",hot_in_C:"热流入口 / °C",hot_out_C:"热流出口 / °C",cold_in_C:"冷流入口 / °C",cold_out_C:"冷流出口 / °C",U_W_m2_K:"总传热系数 / W·m⁻²·K⁻¹",correction_factor:"温差修正因子",compounds:"组分名称（JSON 数组）",mole_fractions:"摩尔分数（JSON 数组）",capital_CNY:"建设投资 / CNY",annual_revenue_CNY:"年收入 / CNY",annual_cost_CNY:"年成本 / CNY",years:"评价期 / 年",discount_rate:"折现率",query:"检索词",limit:"结果数量",title:"标题",body:"正文",formats:"导出格式（JSON 数组）"};
Object.assign(labels,{ethylbenzene_kmol_h:"乙苯进料 / kmol·h⁻¹",steam_to_ethylbenzene:"蒸汽/乙苯摩尔比",inlet_temperature_K:"气相进料温度 / K",reactor_temperature_K:"反应温度 / K",feed_kmol_h:"进料量 / kmol·h⁻¹",feed_light_fraction:"进料轻组分摩尔分数",distillate_light_fraction:"塔顶轻组分摩尔分数",bottoms_light_fraction:"塔底轻组分摩尔分数",relative_volatility:"轻/重组分相对挥发度",feed_liquid_fraction:"进料液相分率 q",reflux_multiple:"回流比 / 最小回流比",overall_tray_efficiency:"全塔板效率",volume_flow_m3_h:"体积流量 / m³·h⁻¹",inner_diameter_m:"管道内径 / m",length_m:"管长 / m",roughness_m:"绝对粗糙度 / m",density_kg_m3:"密度 / kg·m⁻³",viscosity_Pa_s:"动力黏度 / Pa·s",minor_loss_K:"局部阻力系数 ΣK",elevation_rise_m:"出口高差 / m",terminal_pressure_rise_Pa:"出口-入口指定静压差 / Pa",pump_efficiency:"泵效率",delta_T_min_K:"最小换热温差 / K",streams:"热/冷物流（JSON 数组）",record:"设备记录（JSON）",expected_revision:"预期旧版本（新建时 null）"});
Object.assign(labels,{column_stages:"湿塔平衡级数",column_feed_stage:"湿塔进料级",column_pressure_Pa:"湿塔绝对压力 / Pa",column_reflux_ratio:"湿塔有机液回流比",column_organic_distillate_fraction:"湿塔有机馏出 / 进料",organic_distillate_fraction:"有机液馏出 / 进料",feed_molar_enthalpy_J_mol:"实际进料摩尔焓 / J·mol⁻¹（含生成焓参考）",light_component:"轻组分（苯、甲苯、乙苯或苯乙烯）",heavy_component:"重组分",equilibrium_stages:"平衡级数（含部分再沸器）",feed_stage:"进料级（从塔顶第1级起）",distillate_fraction:"馏出量 / 进料量",reflux_ratio:"操作回流比",artifact_id:"选择本项目图纸文件"});
Object.assign(labels,{feed_component_kmol_h:"实际气相进料：水/乙苯/苯乙烯/H₂ / kmol·h⁻¹",recycle_purge_fraction:"有机馏出排放比例",recycle_pump_efficiency:"循环泵效率",recycle_molar_volume_m3_kmol:"循环液平均摩尔体积 / m³·kmol⁻¹（设计假设）",fresh_temperature_K:"新鲜液态乙苯温度 / K",target_styrene_mass_fraction:"苯乙烯质量纯度研究目标"});
Object.assign(labels,{condenser_temperature_K:"冷凝分相温度 / K",organic_henry_multiplier:"有机溶剂H₂亨利常数预测倍率（敏感性）"});
function toast(message){const box=$("#toast");box.textContent=message;box.style.display="block";clearTimeout(toast.timer);toast.timer=setTimeout(()=>box.style.display="none",6000);}
async function api(path,options={}){
 const headers={...(options.body instanceof FormData?{}:{"Content-Type":"application/json"}),...options.headers};
 const response=await fetch(path,{...options,headers});
 const data=await response.json().catch(()=>({detail:"服务响应无法解析"}));
 if(!response.ok){if(response.status===401)showLogin();throw Error(typeof data.detail==="string"?data.detail:pretty(data.detail));}
 return data;
}
const post=(path,data={})=>api(path,{method:"POST",body:JSON.stringify(data)});
const projectURL=suffix=>"/api/projects/"+state.project.id+suffix;
const scopedURL=suffix=>projectURL(suffix)+'?conversation_id='+encodeURIComponent(state.conversation.id);
function modal(title,body){$("#form-title").textContent=title;$("#form-body").innerHTML=body;const d=$("#form-dialog");if(!d.open)d.showModal();}
function showLogin(){modal("访问工作台",'<form id="login-form"><label class="field">工作台访问口令<input name="token" type="password" autocomplete="current-password" required></label><button class="button">登录</button><p class="inline-error" id="login-error"></p></form>');}
function intro(title,subtitle){return '<div class="intro"><h1>'+title+'</h1><p>'+subtitle+'</p></div>';}
async function loadProject(){
 clearTimeout(state.poll);state.run=null;state.chatLocked=false;
 const id=state.project.id;
 const [files,acceptance]=await Promise.all([api(projectURL("/artifacts")),api(projectURL("/acceptance"))]);
 if(state.project.id!==id)return;
 state.files=files;state.acceptance=acceptance;
 $("#project-name").textContent=state.project.name;
 $("#project-name").title=state.project.name;
 try{await chrome.loadContext();}catch(error){showLoadError(error);return;}
 if(state.project.id!==id)return;
 await render();
 await chrome.renderResources();
}
async function boot(){
 const health=await api('/api/health');
 if(!health.capabilities?.includes('conversations'))throw Error('当前后端仍是旧版本，缺少会话接口。请重启本地服务后重新加载页面。');
 const [projects,config,toolData]=await Promise.all([api("/api/projects"),api("/api/config"),api("/api/tools")]);
 state.config=config;state.tools=toolData.tools;state.schemas=toolData.schemas;state.examples=toolData.examples||{};state.diagram=toolData.diagram_example;state.projects=projects;
 if(!projects.length){state.projects=[await post("/api/projects",{name:"苯乙烯清洁生产 · 2026"})];}
 const remembered=localStorage.getItem("chemellm-project");
 state.project=state.projects.find(p=>p.id===remembered)||state.projects[0];
 $("#project-select").innerHTML=state.projects.map(p=>'<option value="'+p.id+'">'+esc(p.name)+'</option>').join("");
 $("#project-select").value=state.project.id;
 modelSettings.applyConfig(config);
 await loadProject();
}
async function render(){
 saveDraft();
 document.querySelectorAll("[data-page]").forEach(n=>{const active=n.dataset.page===state.page;n.classList.toggle("active",active);if(active)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
 $("#page-name").textContent=pageNames[state.page];
 $("#content").classList.toggle('chat-page',state.page==='workspace');
 document.title=pageNames[state.page]+' · ChemELLM';
 chrome.updateLocation();
 const functions={workspace:renderWorkspace,tools:renderTools,research:renderResearch,evidence:()=>renderEvidence(state,{intro,api,post}),datasets:()=>renderDatasets(state,{intro,api}),study:()=>renderStudy(state,{intro,api,post,toast,modal,refreshNavigation:chrome.renderProjects,openConversation:key=>chrome.newConversation(state.project.id,key)}),files:renderFiles,database:renderDatabase,acceptance:renderAcceptance};
 await functions[state.page]();
}
async function renderWorkspace(){
 const projectId=state.project.id,conversationId=state.conversation.id,draft=readDraft();
 $("#content").innerHTML='<section class="chat-workspace is-empty" aria-label="设计对话"><div class="conversation-scroll" id="conversation-scroll"><div class="conversation-inner"><div id="messages"><div class="loading">加载项目对话…</div></div><div id="run-panel" aria-label="执行状态"></div></div></div>'+
 '<div class="composer-wrap"><form id="chat-form" class="composer"><textarea name="message" rows="2" placeholder="描述你的设计目标，或从一个问题开始…" required maxlength="20000" aria-label="设计需求">'+esc(draft)+'</textarea><div class="composer-bar"><div class="composer-settings"><button class="icon-button attach-button" type="button" data-action="upload" title="添加项目资料" aria-label="添加项目资料">'+icon('plus')+'</button><span class="composer-divider"></span><select name="speed" aria-label="模型速度"><option value="fast">快速模型</option><option value="balanced" selected>均衡模型</option><option value="deep">深度模型</option></select><select name="reasoning" aria-label="思考能力" '+(!state.config.reasoning_supported?'disabled title="当前接口未启用 reasoning_effort"':'')+'><option value="low">轻量思考</option><option value="medium" selected>标准思考</option><option value="high">深度思考</option></select></div><button type="submit" class="send-button" id="send-button" aria-label="发送设计需求" title="发送（Enter），换行（Shift + Enter）">'+icon('arrow-up')+'</button></div><div id="chat-attachments" class="chat-attachments" hidden></div></form>'+
 '<div class="suggestions" aria-label="试试这些问题"><button data-prompt="请先检索项目赛题原文，梳理苯乙烯清洁生产设计所需依据，并追问缺失的关键参数。">'+icon('checklist')+'拆解赛题</button><button data-prompt="比较乙苯脱氢与其他苯乙烯生产路线，先检索文献并列出证据和待核实数据。">'+icon('workflow')+'比较工艺</button><button data-prompt="请核对项目现有计算的假设和适用范围，指出下一步必须补充的数据。">'+icon('book')+'核对依据</button><button data-tool="material_balance">'+icon('calculator')+'物料衡算</button></div><p class="composer-hint"><span>工具调用与研究记录自动保存至当前项目</span><span class="keyboard-hint">Enter 发送 · Shift + Enter 换行</span></p></div></section>';
 $('#chat-form .composer-settings').insertAdjacentHTML('beforeend','<select name="mode" aria-label="任务方式"><option value="chat">对话任务</option><option value="engineering">整包工程交付</option></select>');
 updateComposer();
 await refreshMessages();
 if(state.project.id!==projectId||state.conversation.id!==conversationId||state.page!=='workspace')return;
 const runs=await api(scopedURL("/runs"));
 if(state.project.id!==projectId||state.conversation.id!==conversationId||state.page!=="workspace")return;
 if(runs.length){state.run=(runs.find(r=>r.needs_reconciliation)||runs[0]).id;await pollRun();}
}
function draftKey(){return 'chemellm-draft-'+state.project.id+'-'+state.conversation.id;}
function readDraft(){try{return sessionStorage.getItem(draftKey())||(state.conversation.id.startsWith('legacy-')?sessionStorage.getItem('chemellm-draft-'+state.project.id):'')||'';}catch{return '';}}
function saveDraft(){
 const field=$('#chat-form textarea');if(!field||!state.draftKey)return;
 try{if(field.value)sessionStorage.setItem(state.draftKey,field.value);else sessionStorage.removeItem(state.draftKey);}catch{}
}
function updateComposer(){
 const field=$('#chat-form textarea');if(!field)return;
 state.draftKey=draftKey();
 field.style.height='auto';field.style.height=Math.min(200,Math.max(76,field.scrollHeight))+'px';
 $('#send-button').disabled=!field.value.trim()||state.chatLocked||state.sendingProject===state.project.id;
}
async function refreshMessages(){
 const projectId=state.project.id,conversationId=state.conversation.id;
 const offset=state.historyOffsets?.[conversationId]||0;
 const [messages,history]=await Promise.all([api(scopedURL("/messages")),api(projectURL('/conversations/'+conversationId+'/history?offset='+offset))]);
 if(state.project.id!==projectId||state.conversation.id!==conversationId||!$("#messages"))return;
 const scroll=$("#conversation-scroll"),nearBottom=scroll.scrollHeight-scroll.scrollTop-scroll.clientHeight<100;
 const signature=JSON.stringify([messages,history]);
 if($("#messages").dataset.signature===signature)return;
 $("#messages").dataset.signature=signature;
 const saved=historyMarkup(history,{esc,icon,tools:state.tools});
 $('.chat-workspace').classList.toggle('is-empty',!messages.length&&!saved);
 const existing=state.conversations.find(c=>c.history_cutoff)||state.conversations.find(c=>c.id!==conversationId&&c.message_count);
 $("#messages").innerHTML=saved+(messages.length?messages.map(m=>'<article class="message '+(m.role==='user'?'message-user':'message-assistant')+'"><div class="message-heading">'+(m.role==='user'?'<span class="message-avatar user-avatar">你</span><span>你</span>':'<span class="message-avatar">'+icon('brand')+'</span><span>ChemELLM</span>')+'</div><div class="message-content">'+esc(m.content)+'</div></article>').join(""):saved?'<p class="history-chat-note">此记录尚无 AI 聊天消息，可以在下方继续研究。</p>':'<div class="chat-welcome"><span class="welcome-mark">'+icon('brand')+'</span><span class="welcome-eyebrow">'+esc(state.conversation.title==='新会话'?'新的独立会话':state.conversation.title)+'</span><h1>从一个问题，推进你的研究。</h1><p>此会话暂无消息。发送问题后，会在这里保留完整对话。</p>'+(existing?'<button class="history-empty-link" data-open-conversation="'+existing.id+'">查看'+esc(existing.title)+' →</button>':'')+'</div>');
 bindHistory($("#messages"),history,displayResult);
 if(nearBottom)scroll.scrollTop=messages.length?scroll.scrollHeight:0;
}
async function pollRun(){
 clearTimeout(state.poll);
 if(!state.run||state.page!=="workspace")return;
 const ident=state.run;
 const run=await api("/api/runs/"+ident);
 if(state.run!==ident||!$("#run-panel"))return;
 const busy=["queued","running"].includes(run.status);
 const uncertain=(run.unknown_calls||[]).length>0;
 state.chatLocked=busy||uncertain;updateComposer();
 const resumable=!uncertain&&["awaiting_user","iteration_limit","failed","needs_review","interrupted","cancelled"].includes(run.status);
 $("#run-panel").innerHTML='<div class="run-bar"><span class="pill '+(busy?"good":"warn")+'">'+esc(statusNames[run.status]||run.status)+'</span><span class="muted">第 '+(run.result.iterations||0)+' 轮</span>'+(busy?'<button class="text-button" data-action="cancel-run">取消任务</button>':resumable?'<button class="text-button" data-action="resume-run">继续此任务 →</button>':"")+'</div>'+(run.result.error?'<p class="inline-error">'+esc(run.result.error)+'</p>':"")+(run.status==="awaiting_user"?'<div class="note">'+esc(run.result.answer)+'<br>在下方输入回答后点击“继续此任务”。</div>':"")+'<details><summary class="source-note">查看执行轨迹 · '+run.events.length+' 条记录</summary>'+run.events.map(e=>'<details class="event"><summary>'+esc(e.type)+(e.payload.name?" · "+esc(e.payload.name):"")+'</summary><pre>'+esc(pretty(e.payload))+'</pre></details>').join("")+'</details>';
 $("#run-panel").insertAdjacentHTML('beforeend',recoveryCards(run));
 bindRecovery(run,{modal,post,refresh:pollRun,toast});
 if(busy)state.poll=setTimeout(()=>pollRun().catch(e=>toast(e.message)),1800);
 else {await refreshMessages();await chrome.refreshConversations();await chrome.renderResources();}
}
Object.assign(labels,{mechanism:"反应机理 / 物种集合",constraint:"计算约束",composition:"物种相对摩尔量（JSON）",energy:"能量边界",end_time_s:"积分终止时间 / s",samples:"对数采样点数（另含初始点）"});
const optionLabels={TP:"定温定压",HP:"定焓定压",constant_pressure:"定压",constant_volume:"定容",adiabatic:"绝热",isothermal:"恒温",h2o2:"h2o2 · 氢氧气相机理",gri30:"gri30 · GRI-Mech 3.0",wgs4:"wgs4 · 四物种平衡，无动力学"};
function toolFields(name){
 const schema=state.schemas[name];
 if(name==="pfd")return '<label class="field">设备与物流拓扑（JSON）<textarea name="_json" class="json-input" rows="24">'+esc(pretty(state.diagram))+'</textarea></label>';
 if(name==="drawing_read")return '<label class="field">选择图纸文件<select name="artifact_id" required>'+state.files.filter(f=>["svg","dxf","json","pdf"].includes(f.kind)).map(f=>'<option value="'+f.id+'">'+esc(f.name)+'</option>').join("")+'</select></label><p class="source-note">从矢量文字、图元和内置拓扑中提取可核实信息。扫描图片尚需视觉模型。</p>';
 return Object.entries(schema.properties||{}).map(([key,original])=>{
   const s=original.$ref?{...schema.$defs[original.$ref.split("/").pop()],...original}:original;
   let value=state.examples[name]?.[key]??s.default??(key==="compound"?"苯乙烯":key==="from_unit"?"bar":key==="to_unit"?"Pa":key==="value"?1:"");
   const complex=s.type==="array"||s.type==="object";
   if(complex)value=pretty(value|| (s.type==="array"?[]:{}));
   const textarea=complex||["body"].includes(key);
   const optional=s.anyOf?.some(t=>t.type==="null");
   if(optional&&s.default===null)value="null";
   return '<label class="field">'+esc(labels[key]||key)+(optional?"（允许 null）":"")+(s.enum?'<select name="'+key+'">'+s.enum.map(v=>'<option value="'+esc(v)+'" '+(v===value?'selected':'')+'>'+esc(optionLabels[v]||v)+'</option>').join('')+'</select>':textarea?'<textarea name="'+key+'" rows="'+(key==="body"?10:3)+'">'+esc(value)+'</textarea>':'<input name="'+key+'" value="'+esc(value)+'" '+(schema.required?.includes(key)?"required":"")+'>')+'<small>'+esc(key)+(s.minimum!==undefined?" · ≥ "+s.minimum:"")+(s.exclusiveMinimum!==undefined?" · > "+s.exclusiveMinimum:"")+(s.description?" · "+esc(s.description):"")+'</small></label>';
 }).join("");
}
function readTool(form,name){
 if(name==="pfd")return JSON.parse(form.elements._json.value);
 const args={};
 for(const [key,s] of Object.entries(state.schemas[name].properties||{})){
  const value=form.elements[key].value;
  if(value==="null"&&s.anyOf?.some(t=>t.type==="null")){args[key]=null;continue;}
  const type=s.type||(s.$ref?"object":s.anyOf?.find(t=>t.type!=="null")?.type);
  args[key]=["number","integer"].includes(type)?Number(value):["array","object","boolean"].includes(type)?JSON.parse(value):value;
  if(["number","integer"].includes(type)&&(!value.trim()||!Number.isFinite(args[key])))throw Error("请输入有效数值："+(labels[key]||key));
 }
 return args;
}
async function renderTools(){
 const t=state.tools.find(t=>t.id===state.tool)||state.tools[0];state.tool=t.id;
 $("#content").innerHTML=intro("工具与工程计算","显式输入、确定性计算、适用范围和校验记录。","TOOLS / COMPUTATION")+
 '<div class="toolbar"><select id="tool-picker" aria-label="选择计算工具">'+state.tools.filter(t=>t.status==="integrated"&&state.schemas[t.id]).map(t=>'<option value="'+t.id+'" '+(t.id===state.tool?"selected":"")+'>'+esc(t.name)+'</option>').join("")+'</select><span class="muted">默认参数为演示假设，运行前请核实。</span></div><div class="calculation-grid"><form class="panel" id="tool-form"><h3>'+esc(t.name)+'</h3><p class="source-note">'+esc(t.description)+'</p>'+toolFields(state.tool)+'<button class="button" id="calculate-button">执行工具 →</button></form><section class="panel"><div class="panel-heading"><h2>计算与校验结果</h2><span>保存至项目记录</span></div><div id="tool-result" class="empty">选择输入参数并执行工具</div></section></div><details class="tool-directory"><summary>浏览工具与技术目录<span>'+state.tools.length+' 项 · 已接入 / 待接入 / 技术参考</span></summary><div class="catalog">'+state.tools.map(t=>'<article class="tool-card"><span class="category">'+esc(t.category)+'</span><h3>'+esc(t.name)+'</h3><span class="pill '+(t.status==="integrated"?"good":"")+'">'+toolStatus[t.status]+'</span><p>'+esc(t.description)+'</p><div class="card-footer"><a href="'+esc(t.url)+'" target="_blank" rel="noopener noreferrer">官方资料 ↗</a>'+(state.schemas[t.id]?'<button class="text-button" data-tool="'+t.id+'">使用工具 →</button>':esc(t.engine))+'</div></article>').join("")+'</div></details>';
}
function wetColumnTable(column){
 const names={organic_distillate:"塔顶有机馏出",aqueous_distillate:"塔顶水相",vent:"塔顶尾气",bottoms:"富苯乙烯塔底"};
 const compositions=x=>x.map(v=>'<td>'+Number(v).toPrecision(5)+'</td>').join('');
 return '<div class="metrics"><div class="metric"><span>湿塔再沸器供热</span><strong>'+column.reboiler_duty_kW.toFixed(1)+'</strong><small>kW</small></div><div class="metric"><span>湿塔冷凝移热</span><strong>'+column.condenser_duty_removed_kW.toFixed(1)+'</strong><small>kW</small></div></div>'+
 '<p class="source-note">四元湿有机相研究塔。塔顶有机液回流，水相和尾气单独排出；各组分均保留。极微量尾数不代表可靠脱除率；出口未按产品规格验收。</p>'+
 '<div class="table-wrap"><table data-wet-outlets><thead><tr><th>出口</th><th>kmol/h</th><th>水 x</th><th>乙苯 x</th><th>苯乙烯 x</th><th>H₂ x</th></tr></thead><tbody>'+column.outlets.map(s=>'<tr><td>'+esc(names[s.outlet])+'</td><td>'+s.flow_kmol_h.toFixed(4)+'</td>'+compositions(s.mole_fractions)+'</tr>').join('')+'</tbody></table></div>'+
 '<details class="section-gap"><summary>查看四组分逐级剖面</summary><div class="table-wrap"><table data-wet-stages><thead><tr><th>级</th><th>温度 / °C</th><th>L / kmol·h⁻¹</th><th>V / kmol·h⁻¹</th><th>液水 x</th><th>液乙苯 x</th><th>液苯乙烯 x</th><th>液H₂ x</th><th>气水 y</th><th>气乙苯 y</th><th>气苯乙烯 y</th><th>气H₂ y</th></tr></thead><tbody>'+column.stages.map(s=>'<tr><td>'+s.stage+(s.feed?' · 进料':'')+(s.role==='partial_reboiler'?' · 再沸器':'')+'</td><td>'+(s.temperature_K-273.15).toFixed(2)+'</td><td>'+s.liquid_kmol_h.toFixed(3)+'</td><td>'+s.vapor_kmol_h.toFixed(3)+'</td>'+compositions(s.liquid_mole_fractions)+compositions(s.vapor_mole_fractions)+'</tr>').join('')+'</tbody></table></div></details>';
}
function processStreamTable(result){
 if(!result.streams?.[0]?.component_flows_kmol_h)return '';
 const limits={feed:'外部进料',outlet:'外部出口',internal:'内部物流'};
 const metrics=[['反应器供热',result.reactor_heat_input_kW,'kW'],['前端冷凝移热',result.condenser_heat_removed_kW,'kW']];
 if(result.feed_conditioning_heat_kW!==undefined)metrics.push(['进料汽化与预热',result.feed_conditioning_heat_kW,'kW'],['循环泵轴功',result.recycle_pump_work_kW,'kW']);
 const quality=result.product_specification;
 return '<div class="metrics">'+metrics.map(([name,value,unit])=>'<div class="metric"><span>'+name+'</span><strong>'+Number(value).toFixed(1)+'</strong><small>'+unit+'</small></div>').join('')+'</div>'+
 (quality?'<div class="note" data-product-quality>塔底预测苯乙烯质量分数 '+(quality.predicted_styrene_mass_fraction*100).toFixed(4)+'%；指定研究目标 '+(quality.target_styrene_mass_fraction*100).toFixed(4)+'%。'+(quality.meets_assumed_purity_target?'达到该纯度数值目标。':'未达到该纯度数值目标。')+' 此比较不代表满足完整产品标准或工程验收。</div>':'')+
 '<div class="table-wrap"><table data-streams><thead><tr><th>物流</th><th>流程边界</th><th>温度 / °C</th><th>压力 / kPa</th><th>水</th><th>乙苯</th><th>苯乙烯</th><th>H₂</th><th>焓流 / kW</th></tr></thead><tbody>'+result.streams.map(s=>'<tr><td>'+esc(s.id)+' · '+esc(s.name)+'</td><td>'+limits[s.boundary||(s.id==='S01'?'feed':s.id==='S02'?'internal':'outlet')]+'</td><td>'+(s.temperature_K-273.15).toFixed(2)+'</td><td>'+(s.pressure_Pa/1000).toFixed(2)+'</td>'+['water','ethylbenzene','styrene','hydrogen'].map(k=>'<td>'+Number(s.component_flows_kmol_h[k]).toPrecision(6)+'</td>').join('')+'<td>'+s.enthalpy_flow_kW.toFixed(2)+'</td></tr>').join('')+'</tbody></table></div><p class="source-note">组分流量：kmol/h。外部进料与外部出口用于整体衡算，内部物流不重复计入。焓流含生成焓参考；出口须继续按实际产品标准和工程要求校核。</p>';
}
function displayResult(result){
 if(result.backend==='Cantera')return simulationResult(result);
 const files=result.artifacts||[];
 const binaryStageTable=result.stages?.[0]?.liquid_light_fraction!==undefined?'<div class="metrics"><div class="metric"><span>塔顶轻组分</span><strong>'+Number(result.distillate_light_fraction).toFixed(4)+'</strong><small>摩尔分数</small></div><div class="metric"><span>再沸器供热</span><strong>'+Number(result.reboiler_duty_kW).toFixed(1)+'</strong><small>kW</small></div><div class="metric"><span>冷凝器移热</span><strong>'+Number(result.condenser_duty_removed_kW).toFixed(1)+'</strong><small>kW</small></div></div><div class="table-wrap"><table><thead><tr><th>级</th><th>温度 / °C</th><th>液相轻组分</th><th>气相轻组分</th><th>L / kmol·h⁻¹</th><th>V / kmol·h⁻¹</th></tr></thead><tbody>'+result.stages.map(s=>'<tr><td>'+s.stage+(s.feed?" · 进料":"")+(s.role==="partial_reboiler"?" · 再沸器":"")+'</td><td>'+(s.temperature_K-273.15).toFixed(2)+'</td><td>'+s.liquid_light_fraction.toFixed(6)+'</td><td>'+s.vapor_light_fraction.toFixed(6)+'</td><td>'+s.liquid_kmol_h.toFixed(3)+'</td><td>'+s.vapor_kmol_h.toFixed(3)+'</td></tr>').join("")+'</tbody></table></div>':"";
 const wet=result.column?.stages?result.column:result.stages?.[0]?.liquid_mole_fractions?result:null;
 const stageTable=wet?wetColumnTable(wet):binaryStageTable;
 const topology=result.encoded_topology?'<div class="note">文件声明了 '+result.encoded_topology.nodes.length+' 个设备、'+result.encoded_topology.edges.length+' 条连接；尚未核对其与图形一致。</div><button class="button secondary small" data-edit-topology="'+esc(result.artifact_id)+'">编辑内置流程拓扑 →</button>':"";
 const streamTable=processStreamTable(result);
 const structured=Boolean(stageTable||streamTable);
 return (result.validation?'<div class="note">'+(result.validation.passed===false?"校验未通过":"校验字段已返回；仅代表该模型检查范围")+'</div>':"")+files.map(f=>'<button class="button secondary small" data-preview="'+f.id+'">'+esc(f.kind.toUpperCase())+' 预览 ↗</button> ').join("")+stageTable+streamTable+topology+(structured?'<details class="section-gap"><summary>完整数值、求解残差与数据来源</summary>':"")+'<pre class="result">'+esc(pretty(result))+'</pre>'+(structured?"</details>":"");
}
function renderResearch(){
 $("#content").innerHTML=intro("从可靠来源，寻找设计依据。","检索真实文献题录，保留 DOI 和来源；定量结论仍需读取原文。","RESEARCH / EVIDENCE")+'<form id="research-form" class="toolbar"><input class="search-input" name="query" placeholder="例如：ethylbenzene dehydrogenation styrene catalyst energy" required minlength="2" maxlength="300" aria-label="文献检索词"><select name="source" aria-label="检索来源"><option value="literature_search">Crossref / OpenAlex</option><option value="open_literature_search">Europe PMC 开放文献</option><option value="project_search">本项目文档</option><option value="pubchem">PubChem 化学数据</option></select><button class="button">检索 →</button></form><div id="research-results" class="empty">输入主题或化合物名称开始查询。</div>';
}
function renderFiles(){
 $("#content").innerHTML=intro("文件、图纸与交付成果","在线预览 PDF、流程图和 Office 文档，原始文件与生成成果统一管理。","DOCUMENTS / DRAWINGS")+'<div class="toolbar"><button class="button" data-action="upload">＋ 上传资料</button><button class="button secondary" data-tool="export_report">生成报告 / PPT</button><button class="button secondary" data-action="diagram">生成 PFD 示例</button><button class="button secondary" data-action="bundle">打包项目成果 ↓</button></div>'+(!state.config.office_preview?'<div class="note">当前主机未安装 LibreOffice：DOCX/PPTX 提供文本预览和原文件下载。Linux 容器配置包含 PDF 转换组件。</div>':"")+(state.files.length?'<div class="files-grid">'+state.files.map(f=>'<article class="file-card"><div class="file-art">'+esc(f.kind.toUpperCase())+'</div><div class="file-info"><strong>'+esc(f.name)+'</strong><small>'+new Date(f.created_at).toLocaleString("zh-CN")+' · '+(f.metadata.status==="draft"?"草稿":f.has_visual_preview?"可视预览":"文本/下载")+'</small><div class="file-actions"><button class="button secondary small" data-preview="'+f.id+'">打开预览 ↗</button><a class="button secondary small" href="'+f.download_url+'" download>下载 ↓</a>'+(['svg','dxf','json','pdf'].includes(f.kind)?'<button class="text-button" data-read-drawing="'+f.id+'">识读</button>':"")+'</div></div></article>').join("")+'</div>':'<div class="empty">项目还没有文件。上传赛题或生成第一份计算报告。</div>');
}
async function renderDatabase(){
 $("#content").innerHTML=intro("工程数据，保留使用条件。","物性来源、设备参数需求、计算模型和竞赛参考费用。","DATABASE / KNOWLEDGE")+'<div class="loading">加载数据库…</div>';
 const [db,records,calculations]=await Promise.all([api("/api/database"),api(projectURL("/equipment")),api(projectURL("/calculations"))]);if(state.page!=="database")return;
 state.equipment=records;state.calculations=calculations;
 $("#content").innerHTML=intro("工程数据，保留使用条件。","物性来源、设备参数需求、计算模型和竞赛参考费用。","DATABASE / KNOWLEDGE")+
 '<div class="panel"><div class="panel-heading"><h2>化学物性</h2><span>已保存 '+db.property_cache_count+' 条查询记录</span></div><p class="source-note">使用 thermo / Chemicals 的物性库及关联式，水蒸汽使用 CoolProp。查询返回 CAS、单位、条件与方法；不以模型生成的数值代替物性数据。</p><button class="button small" data-tool="properties">查询物性 →</button></div>'+
 equipmentPanel()+
 '<div class="panel"><div class="panel-heading"><h2>计算模型与公式</h2></div><div class="table-wrap"><table><thead><tr><th>模型</th><th>公式</th><th>适用范围</th></tr></thead><tbody>'+db.formulas.map(f=>'<tr><td>'+esc(f.name)+'</td><td>'+esc(f.formula)+'</td><td>'+esc(f.scope)+'</td></tr>').join("")+'</tbody></table></div></div>'+
 '<div class="panel"><div class="panel-heading"><h2>设备参数准备</h2><span>当前为设计参数清单，未含厂家性能曲线</span></div>'+db.equipment.map(e=>'<div class="task-item"><div><strong>'+esc(e.type)+'</strong><p class="source-note">'+esc(e.required.join(" · "))+'</p><span class="badge">'+esc(e.status)+'</span></div></div>').join("")+'</div>'+
 '<div class="panel"><div class="panel-heading"><h2>2026 赛题费用基准</h2><span>来源：任务书第4页</span></div><div class="table-wrap"><table><thead><tr><th>项目</th><th>费用</th><th>单位</th><th>条件与范围</th></tr></thead><tbody>'+db.prices.map(p=>'<tr><td>'+esc(p.name)+'</td><td>'+p.value+'</td><td>'+esc(p.unit)+'</td><td>'+esc(p.scope)+'</td></tr>').join("")+'</tbody></table></div></div>';
}
function equipmentPanel(){
 const records=state.equipment||[];
 return '<section class="panel" id="equipment-panel"><div class="panel-heading"><h2>本项目设备参数</h2><button class="button small" data-action="equipment-new">＋ 登记设备</button></div><p class="source-note">按位号保存参数、单位、原始文件页码或计算记录。每次修改保留版本，并恢复为草稿。</p>'+
 (records.length?'<div class="table-wrap"><table><thead><tr><th>位号 / 名称</th><th>类型</th><th>版本 / 状态</th><th>参数及来源</th><th>操作</th></tr></thead><tbody>'+records.map(r=>'<tr><td><strong>'+esc(r.tag)+'</strong><br>'+esc(r.data.name)+'</td><td>'+equipmentTypes[r.data.equipment_type]+'</td><td>v'+r.revision+'<br><span class="pill '+(r.status==="reviewed"?"good":"warn")+'">'+(r.status==="reviewed"?"人工审核":"草稿")+'</span></td><td>'+r.data.parameters.map(p=>esc(p.label)+': '+esc(p.value)+' '+esc(p.unit)+' <small>('+provenanceNames[p.provenance]+')</small>').join("<br>")+'</td><td><button class="text-button" data-equipment-edit="'+r.id+'">编辑</button> · <button class="text-button" data-equipment-review="'+r.id+'">校核</button><br><button class="text-button" data-equipment-history="'+r.id+'">版本历史</button></td></tr>').join("")+'</tbody></table></div>':'<div class="empty">尚未登记设备。可先录入设计参数，再关联手册或计算依据。</div>')+'</section>';
}
function parameterRow(p={}){
 return '<fieldset class="parameter-row"><legend>'+esc(p.label||"设备参数")+'</legend><div class="parameter-grid">'+
 '<label class="field">参数名称<input data-param="label" value="'+esc(p.label||"")+'" required placeholder="如 换热面积"></label>'+
 '<label class="field">参数标识<input data-param="name" value="'+esc(p.name||"")+'" required pattern="[a-zA-Z][a-zA-Z0-9_]{0,59}" placeholder="如 area"></label>'+
 '<label class="field">数值<input data-param="value" type="number" step="any" value="'+esc(p.value??"")+'" required></label>'+
 '<label class="field">单位<input data-param="unit" value="'+esc(p.unit||"")+'" required placeholder="如 m^2、Pa、degC"></label>'+
 '<label class="field">依据类型<select data-param="provenance">'+Object.entries(provenanceNames).map(([value,label])=>'<option value="'+value+'" '+(value===(p.provenance||"assumption")?"selected":"")+'>'+label+'</option>').join("")+'</select></label>'+
 '<label class="field">原始文件<select data-param="artifact_id"><option value="">未关联</option>'+state.files.map(f=>'<option value="'+f.id+'" '+(f.id===p.artifact_id?"selected":"")+'>'+esc(f.name)+'</option>').join("")+'</select></label>'+
 '<label class="field">来源页码<input data-param="source_page" type="number" min="1" step="1" value="'+esc(p.source_page??"")+'" placeholder="PDF/PPTX 页码"></label>'+
 '<label class="field">来源计算<select data-param="calculation_id"><option value="">未关联</option>'+(state.calculations||[]).map(c=>'<option value="'+c.id+'" '+(c.id===p.calculation_id?"selected":"")+'>'+esc(state.tools.find(t=>t.id===c.tool)?.name||c.tool)+' · '+esc(new Date(c.created_at).toLocaleString("zh-CN"))+'</option>').join("")+((p.calculation_id&&!(state.calculations||[]).some(c=>c.id===p.calculation_id))?'<option value="'+esc(p.calculation_id)+'" selected>'+esc(p.calculation_id)+'</option>':"")+'</select></label></div>'+
 '<label class="field">适用条件 / 说明<textarea data-param="note" rows="2">'+esc(p.note||"")+'</textarea></label><button type="button" class="text-button" data-action="parameter-remove">移除此参数</button></fieldset>';
}
async function equipmentDialog(ident=null){
 await refreshFiles();
 const record=(state.equipment||[]).find(r=>r.id===ident);
 const d=record?.data||{tag:"",name:"",equipment_type:"exchanger",material:"",description:"",parameters:[{}]};
 state.editingEquipment=record||null;
 modal(record?"编辑 "+record.tag+" · v"+record.revision:"登记设备参数",'<form id="equipment-form"><div class="parameter-grid"><label class="field">设备位号<input name="tag" required pattern="[A-Za-z][A-Za-z0-9_\\-]{0,29}" value="'+esc(d.tag)+'" '+(record?"readonly":"")+' placeholder="如 E-101"></label><label class="field">设备名称<input name="name" required maxlength="100" value="'+esc(d.name)+'"></label><label class="field">设备类型<select name="equipment_type">'+Object.entries(equipmentTypes).map(([key,label])=>'<option value="'+key+'" '+(key===d.equipment_type?"selected":"")+'>'+label+'</option>').join("")+'</select></label><label class="field">材质<input name="material" maxlength="100" value="'+esc(d.material)+'" placeholder="待确定可留空"></label></div><label class="field">设计说明<textarea name="description" rows="2">'+esc(d.description)+'</textarea></label><div id="parameter-rows">'+d.parameters.map(parameterRow).join("")+'</div><button type="button" class="button secondary small" data-action="parameter-add">＋ 添加参数</button><div class="note">手册/文献参数需关联原始文件；计算参数需关联计算记录。填写来源不代表已校核原文。</div><button type="submit" class="button">保存设备版本</button></form>');
}
function readEquipment(form){
 const record={};
 for(const key of ["tag","name","equipment_type","material","description"])record[key]=form.elements[key].value;
 record.parameters=[...form.querySelectorAll(".parameter-row")].map(row=>{
   const p={};for(const input of row.querySelectorAll("[data-param]"))p[input.dataset.param]=input.value;
   p.value=Number(p.value);p.source_page=p.source_page?Number(p.source_page):null;
   p.artifact_id=p.artifact_id||null;p.calculation_id=p.calculation_id||null;
   return p;
 });
 return {record,expected_revision:state.editingEquipment?.revision??null};
}
function reviewEquipmentDialog(ident){
 const r=state.equipment.find(r=>r.id===ident);
 state.reviewingEquipment=r;
 modal("校核 "+r.tag+" · v"+r.revision,'<form id="equipment-review-form"><p class="source-note">当前记录含 '+r.data.parameters.length+' 个参数。含假设参数时只能保留草稿；来源与数值适用性须由审核人核实。</p><label class="field">结论<select name="status"><option value="draft">保留草稿</option><option value="reviewed">人工审核通过</option></select></label><label class="field">校核依据与结论<textarea name="notes" rows="5" minlength="10" required>'+esc(r.review_notes)+'</textarea></label><button class="button">保存校核记录</button></form>');
 $("#equipment-review-form select").value=r.status;
}
function renderAcceptance(){
 const a=state.acceptance;
 $("#content").innerHTML=intro("把赛题要求，逐项落实。","关联交付文件，记录校核依据。模型生成内容不会自动获得审核通过。","ACCEPTANCE / TRACEABILITY")+
 '<div class="panel"><div class="panel-heading"><h2>必需交付项</h2><span>'+(a.verified||0)+' / '+(a.mandatory||0)+' 已人工审核</span></div><div class="progress"><i style="width:'+((a.verified||0)/Math.max(1,a.mandatory||0)*100)+'%"></i></div><p class="source-note section-gap">DOCX/PDF 报告、AutoCAD 2004 兼容图纸、模拟和计算源文件，以及现场可运行验证均需独立检查。</p></div>'+
 (a.requirements.length?'<div class="panel table-wrap"><table><thead><tr><th>编号</th><th>赛题要求</th><th>原文</th><th>状态</th><th>证据</th><th>操作</th></tr></thead><tbody>'+a.requirements.map(r=>'<tr><td>'+r.code+'</td><td>'+esc(r.title)+'<br><small>'+(r.mandatory?"必需":"计分材料")+'</small></td><td>第 '+r.page+' 页</td><td><span class="pill '+(r.status==="verified"?"good":"warn")+'">'+({missing:"缺少成果",draft:"已有草稿",verified:"人工审核"}[r.status])+'</span></td><td>'+r.evidence.length+' 份</td><td><button class="text-button" data-requirement="'+r.code+'">关联 / 校核</button></td></tr>').join("")+'</tbody></table></div>':'<div class="empty"><p>导入项目中的比赛 PDF，建立逐项验收清单。</p><button class="button" data-action="import">导入赛题 →</button></div>');
}
function previewFile(id){
 const f=state.files.find(f=>f.id===id);if(!f)throw Error("文件尚未刷新，请重新打开文件列表");
 $("#preview-title").textContent=f.name;$("#preview-download").href=f.download_url;$("#preview-frame").src=f.preview_url;$("#preview-dialog").showModal();
}
async function refreshFiles(){const id=state.project.id,files=await api(projectURL("/artifacts"));if(state.project.id!==id)return;state.files=files;await chrome.renderResources();}
async function action(name){
 if(name==="upload")return $("#upload").click();
 if(name==="import"){const f=await post(projectURL("/import-competition"));await post(projectURL('/conversations/'+state.conversation.id+'/resources/'+f.id));toast("赛题已导入，验收清单已建立");await loadProject();}
 if(name==="diagram"){closeProjectOverview();toast("正在生成流程图与可编辑源文件…");const result=await post(projectURL("/tools/pfd"),{arguments:state.diagram});await refreshFiles();state.page="files";await render();previewFile(result.artifacts[0].id);}
 if(name==="bundle"){closeProjectOverview();const f=await post(projectURL("/bundle"));await refreshFiles();state.page="files";await render();const a=document.createElement("a");a.href=f.download_url;a.download="";a.click();toast("项目成果包已生成，内含验收清单与计算记录");}
 if(name==="cancel-run"){await post("/api/runs/"+state.run+"/cancel");await pollRun();}
 if(name==="resume-run"){const textarea=$("#chat-form textarea");await post("/api/runs/"+state.run+"/resume",{answer:textarea.value});textarea.value="";saveDraft();await pollRun();}
 if(name==="equipment-new")await equipmentDialog();
 if(name==="parameter-add")$("#parameter-rows").insertAdjacentHTML("beforeend",parameterRow());
}
function requirementDialog(code){
 const r=state.acceptance.requirements.find(r=>r.code===code);
 modal(code+" · "+r.title,'<form id="requirement-form" data-code="'+code+'"><label class="field">审核状态<select name="status"><option value="missing">缺少成果</option><option value="draft">已有草稿</option><option value="verified">人工审核通过</option></select></label><label class="field">关联证据（可多选）<select name="evidence" multiple size="6">'+state.files.map(f=>'<option value="'+f.id+'" '+(r.evidence.includes(f.id)?"selected":"")+'>'+esc(f.name)+'</option>').join("")+'</select></label><label class="field">校核依据与结论<textarea name="notes" rows="5">'+esc(r.notes)+'</textarea></label><p class="source-note">审核通过至少需要一份本项目证据及10字校核说明。该记录由当前工作台使用者负责。</p><button class="button">保存审核记录</button></form>');
 $("#requirement-form select[name=status]").value=r.status;
}
document.addEventListener("click",async event=>{
 const button=event.target.closest("button,[data-preview]");if(!button)return;
 try{
  if(button.dataset.close){$("#"+button.dataset.close).close();if(button.dataset.close==="preview-dialog")$("#preview-frame").src="about:blank";}
  else if(button.dataset.openConversation){await chrome.selectConversation(button.dataset.openConversation);}
  else if(button.hasAttribute('data-history-offset')){state.historyOffsets??={};state.historyOffsets[state.conversation.id]=Number(button.dataset.historyOffset);await refreshMessages();$('#conversation-scroll').scrollTop=0;}
  else if(button.dataset.page||button.dataset.navigate){state.page=button.dataset.page||button.dataset.navigate;clearTimeout(state.poll);closeMobileSidebar();await render();$('#content').focus({preventScroll:true});}
  else if(button.dataset.datasetExample){button.disabled=true;const projectId=state.project.id;try{const prefix='/api/projects/'+projectId;await post(prefix+'/datasets/example',{name:button.dataset.datasetExample});const files=await api(prefix+'/artifacts');if(state.project.id===projectId){state.files=files;await render();}}finally{button.disabled=false;}}
  else if(button.dataset.tool){state.tool=button.dataset.tool;state.page="tools";closeMobileSidebar();await render();$('#content').focus({preventScroll:true});}
  else if(button.dataset.action==="parameter-remove")button.closest(".parameter-row").remove();
  else if(button.dataset.action){button.disabled=true;try{await action(button.dataset.action);}finally{button.disabled=false;}}
  else if(button.dataset.preview)previewFile(button.dataset.preview);
  else if(button.dataset.prompt){$("#chat-form textarea").value=button.dataset.prompt;updateComposer();saveDraft();$("#chat-form textarea").focus();}
  else if(button.dataset.requirement)requirementDialog(button.dataset.requirement);
  else if(button.dataset.equipmentEdit)await equipmentDialog(button.dataset.equipmentEdit);
  else if(button.dataset.equipmentReview)reviewEquipmentDialog(button.dataset.equipmentReview);
  else if(button.dataset.equipmentHistory){const history=await api(projectURL("/equipment/"+button.dataset.equipmentHistory+"/history"));modal("设备版本历史",history.map(h=>'<details class="event"><summary>v'+h.revision+' · '+esc(new Date(h.created_at).toLocaleString("zh-CN"))+'</summary><pre>'+esc(pretty(h.data))+'</pre></details>').join(""));}
  else if(button.dataset.readDrawing){state.tool="drawing_read";state.page="tools";await render();$("#tool-form select[name=artifact_id]").value=button.dataset.readDrawing;$("#tool-form").requestSubmit();}
  else if(button.dataset.editTopology){const result=await post(projectURL("/tools/drawing_read"),{arguments:{artifact_id:button.dataset.editTopology}});if(!result.encoded_topology)throw Error("该文件没有可编辑的结构化拓扑");state.diagram=result.encoded_topology;state.tool="pfd";state.page="tools";await render();}
  else if(button.dataset.importPmc){state.page="evidence";await render();$("#fulltext-import-form input[name=pmcid]").value=button.dataset.importPmc;$("#fulltext-import-form input[name=pmcid]").focus();}
 }catch(e){toast(e.message);}
});
document.addEventListener("submit",async event=>{
 event.preventDefault();const form=event.target;const submit=form.querySelector('button[type="submit"],button:not([type])');if(submit)submit.disabled=true;
 try{
  if(form.id==="login-form"){await post("/api/login",{token:form.elements.token.value});$("#form-dialog").close();await boot();}
  if(form.id==="new-project-form"){const p=await post("/api/projects",{name:form.elements.name.value});localStorage.setItem("chemellm-project",p.id);state.page='workspace';await boot();$("#form-dialog").close();}
  if(form.id==="chat-form"){
   const projectId=state.project.id,conversationId=state.conversation.id,key=draftKey();if(state.chatLocked||state.sendingProject===projectId)return;
   const data=Object.fromEntries(new FormData(form));data.message=data.message.trim();if(!data.message)return;
   if(data.mode==='engineering'){data.max_tools=300;data.max_seconds=7200;data.max_model_requests=120;}
   data.conversation_id=conversationId;data.reasoning=data.reasoning||"medium";state.sendingProject=projectId;updateComposer();
   try{
    const r=await post('/api/projects/'+projectId+'/runs',data);
    try{sessionStorage.removeItem(key);}catch{}
    if(state.project.id!==projectId||state.conversation.id!==conversationId)return;
    state.run=r.id;if(form.isConnected){form.elements.message.value='';saveDraft();updateComposer();}
    await refreshMessages();await pollRun();
   }finally{state.sendingProject=null;updateComposer();}
  }
  if(form.id==="tool-form"){const name=state.tool;$("#tool-result").className="";$("#tool-result").innerHTML='<div class="loading">正在执行与校验…</div>';const result=await post(projectURL("/tools/"+name),{arguments:readTool(form,name),conversation_id:state.conversation.id});await refreshFiles();await chrome.refreshConversations();$("#tool-result").innerHTML=displayResult(result);}
  if(form.id==="dataset-form"){
   const arguments_=datasetArguments(form),url=projectURL('/tools/analyze_dataset');
   const target=$('#dataset-result');target.className='';target.innerHTML='<div class="loading">正在拟合、比较并保存成果…</div>';
   try{const result=await post(url,{arguments:arguments_,conversation_id:state.conversation.id});await refreshFiles();await chrome.refreshConversations();if(form.isConnected)target.innerHTML=datasetResult(result);}
   catch(error){if(form.isConnected)target.innerHTML='<p class="inline-error">'+esc(error.message)+'</p>';throw error;}
  }
  if(form.id==="research-form"){
   const source=form.elements.source.value;$("#research-results").className="";$("#research-results").innerHTML='<div class="loading">正在检索真实来源…</div>';
   const result=await post(projectURL("/tools/"+source),{arguments:source==="pubchem"?{compound:form.elements.query.value}:{query:form.elements.query.value,limit:6}});
   if(["literature_search","open_literature_search"].includes(source))$("#research-results").innerHTML=(result.results.length?result.results.map(p=>'<article class="paper-result"><div class="eyebrow">'+esc(p.source)+' · '+esc(p.year||"年份未提供")+'</div><h3>'+esc(p.title)+'</h3><p>'+esc(p.authors.join(", "))+'</p>'+(p.url?'<a target="_blank" rel="noopener noreferrer" href="'+esc(p.url)+'">'+esc(p.DOI||"原始记录")+' ↗</a>':"")+' <span class="pill">题录 · 未读取全文</span>'+(p.pmcid&&p.open_access?' <button class="button secondary small" data-import-pmc="'+esc(p.pmcid)+'">导入开放全文 '+esc(p.pmcid)+' →</button>':"")+'</article>').join(""):'<div class="empty">没有获得可用检索结果。</div>')+(result.errors.length?'<div class="note">'+esc(pretty(result.errors))+'</div>':"");
   else $("#research-results").innerHTML=displayResult(result);
  }
  if(form.id==="requirement-form"){await api(projectURL("/requirements/"+form.dataset.code),{method:"PUT",body:JSON.stringify({status:form.elements.status.value,evidence:[...form.elements.evidence.selectedOptions].map(o=>o.value),notes:form.elements.notes.value})});$("#form-dialog").close();state.acceptance=await api(projectURL("/acceptance"));renderAcceptance();}
  if(form.id==="equipment-form"){await post(projectURL("/equipment"),readEquipment(form));$("#form-dialog").close();await renderDatabase();toast("设备参数版本已保存");}
  if(form.id==="equipment-review-form"){const r=state.reviewingEquipment;await post(projectURL("/equipment/"+r.id+"/review"),{expected_revision:r.revision,status:form.elements.status.value,notes:form.elements.notes.value});$("#form-dialog").close();await renderDatabase();toast("校核记录已保存");}
 }catch(e){toast(e.message);if(form.id==="tool-form"&&$("#tool-result"))$("#tool-result").innerHTML='<p class="inline-error">'+esc(e.message)+'</p>';}
 finally{if(form.id==='chat-form')updateComposer();else if(submit)submit.disabled=false;}
});
$("#project-select").addEventListener("change",e=>chrome.selectProject(e.target.value).catch(e=>toast(e.message)));
document.addEventListener("change",e=>{if(e.target.id==="tool-picker"){state.tool=e.target.value;renderTools();}});
$("#new-project").onclick=()=>{closeMobileSidebar();modal("新建项目",'<form id="new-project-form"><label class="field">项目名称<input name="name" required maxlength="150" placeholder="例如：苯乙烯清洁生产方案比选" autofocus></label><button class="button">创建项目</button></form>');};
$("#upload-button").onclick=()=>$("#upload").click();
$("#upload").onchange=async e=>{const f=e.target.files[0];if(!f)return;const projectId=state.project.id,conversationId=state.conversation.id;try{if(f.size>25*1024*1024)throw Error("文件不得超过25 MiB");toast("正在导入并解析 "+f.name);const data=new FormData();data.append("file",f);await api('/api/projects/'+projectId+'/upload?conversation_id='+encodeURIComponent(conversationId),{method:"POST",body:data});toast("文件已导入");if(state.project.id===projectId)await loadProject();}catch(error){toast(error.message);}finally{e.target.value="";}};

const mobileSidebar=window.matchMedia('(max-width: 760px)');
let sidebarCollapsed=false;
try{sidebarCollapsed=localStorage.getItem('chemellm-sidebar-collapsed')==='true';}catch{}
function setSidebar(open,remember=false){
 document.body.classList.toggle('sidebar-open',mobileSidebar.matches&&open);
 document.body.classList.toggle('sidebar-collapsed',!mobileSidebar.matches&&!open);
 $('#sidebar').inert=!open;
 $('.shell').inert=mobileSidebar.matches&&open;
 $('#sidebar-backdrop').hidden=!(mobileSidebar.matches&&open);
 $('#sidebar-toggle').setAttribute('aria-expanded',String(open));
 if(remember&&!mobileSidebar.matches){sidebarCollapsed=!open;try{localStorage.setItem('chemellm-sidebar-collapsed',String(!open));}catch{}}
}
function closeMobileSidebar(){if(mobileSidebar.matches)setSidebar(false);}
function closeProjectOverview(){chrome.closeResources();}
$('#sidebar-toggle').onclick=()=>{setSidebar(true,true);$('#sidebar-close').focus();};
$('#sidebar-close').onclick=()=>{setSidebar(false,true);$('#sidebar-toggle').focus();};
$('#sidebar-backdrop').onclick=()=>{setSidebar(false);$('#sidebar-toggle').focus();};
mobileSidebar.addEventListener('change',()=>setSidebar(!mobileSidebar.matches&&!sidebarCollapsed));
setSidebar(!mobileSidebar.matches&&!sidebarCollapsed);
const chrome=createWorkspaceChrome(state,{api,post,esc,icon,render,loadProject,saveDraft,modal,previewFile,toast,closeMobileSidebar});
const modelSettings=createModelSettings(state,{api,esc,modal,toast,closeMobileSidebar});
$('#settings-button').onclick=modelSettings.open;
function showLoadError(error){
 const message=esc(error.message);$('#content').classList.remove('chat-page');$('#content').innerHTML='<div class="load-error"><h2>工作区暂时无法加载</h2><p>'+message+'</p><button class="button" id="retry-workspace">重新加载</button></div>';
 $('#project-list').innerHTML='<p class="inline-error">'+message+'</p>';
 $('#retry-workspace').onclick=()=>boot().catch(showLoadError);
}
document.addEventListener('input',event=>{if(event.target.matches('#chat-form textarea')){updateComposer();saveDraft();}});
document.addEventListener('keydown',event=>{
 if(event.key==='Escape'&&document.body.classList.contains('sidebar-open')){setSidebar(false);$('#sidebar-toggle').focus();}
 if(event.key==='Tab'&&document.body.classList.contains('sidebar-open')){
  const items=[...$('#sidebar').querySelectorAll('a,button,select')].filter(el=>!el.disabled),first=items[0],last=items.at(-1);
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
 }
 if(event.target.matches('#chat-form textarea')&&event.key==='Enter'&&!event.shiftKey&&!event.isComposing&&event.keyCode!==229){
  event.preventDefault();if(!$('#send-button').disabled)$('#chat-form').requestSubmit();
 }
});
window.addEventListener('pagehide',saveDraft);
boot().catch(showLoadError);
