const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const statusNames={needs_review:'待人工审核',supported:'人工判断：支持',contradicted:'人工判断：反驳',insufficient:'人工判断：证据不足'};
const relationNames={supports:'支持标注',refutes:'反驳标注',context:'背景资料'};
const location=b=>b.page?'第 '+b.page+' 页':(b.section||'段落')+(b.anchor?' · '+b.anchor:'');

export async function renderEvidence(state,{intro,api,post}){
 const prefix='/api/projects/'+state.project.id,projectId=state.project.id;
 const files=state.files.filter(f=>['pdf','xml','txt','md','docx','pptx','png','jpg','jpeg'].includes(f.kind));
 document.querySelector('#content').innerHTML=intro('让每个论断，都能回到原文。','保存全文快照、定位引句、记录相反证据，分别检查引用完整性与科学支持程度。','FULL TEXT / EVIDENCE')+
 '<div id="evidence-workspace"><div class="toolbar"><button class="button" data-action="upload">＋ 上传原文 / 扫描件</button><button class="button secondary" id="evidence-export">导出证据记录 ↓</button></div><div id="evidence-notice" role="status"></div><div class="evidence-grid"><section class="panel"><h2>全文来源</h2><form id="fulltext-import-form" class="section-gap"><label class="field">Europe PMC 开放全文 PMCID<input name="pmcid" required pattern="PMC[1-9][0-9]+" placeholder="例如 PMC10110988"></label><button class="button secondary small">获取开放全文</button></form><form id="document-extract-form" class="section-gap"><label class="field">项目原文件<select name="artifact_id" required>'+files.map(f=>'<option value="'+f.id+'">'+esc(f.name)+'</option>').join('')+'</select></label><div class="parameter-grid"><label class="field">起始页<input name="first_page" type="number" value="1" min="1" max="600"></label><label class="field">结束页（可选）<input name="last_page" type="number" min="1" max="600"></label></div><label class="field">扫描件文字识别<select name="ocr"><option value="never">优先原有文本（默认）</option><option value="auto">自动：缺少文本时辅助识别</option><option value="force">强制 OCR</option></select></label><button class="button small">建立全文快照 →</button><p class="source-note">PDF每次最多50页，默认最多20页。OCR、表格和公式候选均需对照原版。</p></form><hr><h3>待研究的论断</h3><form id="claim-create-form"><label class="field">研究论断<textarea name="text" rows="3" minlength="8" maxlength="5000" required placeholder="写下需要证据支持或反驳的具体论断"></textarea></label><button class="button secondary small">登记论断</button></form><form id="quote-form" class="section-gap"><h3>关联原文引句</h3><label class="field">选择论断<select name="claim_id" required></select></label><input type="hidden" name="snapshot_id"><input type="hidden" name="block_id"><p id="quote-locator" class="source-note">在右侧全文中点击“引用这段”。</p><label class="field">原文引句<textarea name="quote" rows="5" minlength="8" maxlength="2500" required></textarea></label><label class="field">录入者的关系判断<select name="relation"><option value="context">背景资料</option><option value="supports">支持</option><option value="refutes">反驳</option></select></label><label class="field">体系、条件及方法<textarea name="conditions" rows="2" maxlength="1500" placeholder="例如：H₂—水、温度范围、常数定义、单位"></textarea></label><button class="button small">核对引句并保存 →</button><p class="source-note">程序只核对引句是否存在；支持/反驳标注不是科学审核结论。</p></form></section><section class="panel"><div class="panel-heading"><h2>全文阅读</h2></div><label class="field">已建立的全文快照<select id="snapshot-picker"></select></label><div id="document-reader" class="empty">先建立快照或导入开放全文。</div><div id="reader-pages" class="toolbar"></div></section></div><section class="panel section-gap"><div class="panel-heading"><h2>论断与证据</h2><span>修改论断或新增证据会使旧审核过期</span></div><div id="claim-list"></div></section></div>';
 const root=document.querySelector('#evidence-workspace');
 const $=selector=>root.querySelector(selector);
 const imageMode=$('#document-extract-form [name="ocr"]');
 imageMode.name='image_mode';
 imageMode.closest('label').firstChild.textContent='图像文字识读';
 imageMode.innerHTML='<option value="native">仅原生文本（默认）</option><option value="ai">AI视觉转录（待核验）</option>';
 let claims=[],snapshots=[],reader=null,offset=0;
 function notice(text,error=false){if(root.isConnected)$('#evidence-notice').innerHTML='<p class="'+(error?'inline-error':'source-note')+'">'+esc(text)+'</p>';}
 async function run(button,operation){if(button)button.disabled=true;try{await operation();}catch(error){notice(error.message,true);}finally{if(button)button.disabled=false;}}
 async function loadSnapshots(selected){
  snapshots=await api(prefix+'/documents');if(!root.isConnected)return;
  $('#snapshot-picker').innerHTML=snapshots.map(s=>'<option value="'+s.id+'">'+esc(s.name)+' · '+esc(s.created_at)+'</option>').join('');
  if(selected)$('#snapshot-picker').value=selected;
 }
 async function loadClaims(selected){
  const data=await api(prefix+'/claims');if(!root.isConnected)return;claims=data.claims;
  const previous=selected||$('#quote-form').elements.claim_id.value;
  $('#quote-form').elements.claim_id.innerHTML=claims.map(c=>'<option value="'+c.id+'">'+esc(c.text.slice(0,65))+' · v'+c.revision+'</option>').join('');
  if(claims.some(c=>c.id===previous))$('#quote-form').elements.claim_id.value=previous;
  let replacement=$('#quote-form select[name="supersedes_evidence_id"]');
  if(!replacement){
   const label=document.createElement('label');label.className='field';
   label.innerHTML='替换已有证据（保留历史）<select name="supersedes_evidence_id"></select>';
   $('#quote-form button').before(label);replacement=label.querySelector('select');
  }
  const refreshReplacement=()=>{
   const current=claims.find(c=>c.id===$('#quote-form').elements.claim_id.value);
   replacement.innerHTML='<option value="">新增证据</option>'+(current?.evidence||[]).filter(e=>!e.superseded).map(e=>'<option value="'+e.id+'">'+esc(e.data.quote.slice(0,70))+(e.transcription_outdated?' · 转录已纠正':'')+'</option>').join('');
  };
  $('#quote-form').elements.claim_id.onchange=refreshReplacement;refreshReplacement();
  $('#claim-list').innerHTML=claims.length?claims.map(c=>'<article class="evidence-claim"><div class="panel-heading"><h3>'+esc(c.text)+'</h3><span class="pill">v'+c.revision+' · '+esc(statusNames[c.review_status])+'</span></div><p class="source-note">'+(c.integrity_passed?'关联引句及文件完整性检查通过。':'尚无完整有效证据，或来源已变化。')+'</p>'+(c.conflict.opposing_annotations?'<div class="note">存在相反关系标注，请比较条件与方法。'+esc(c.conflict.interpretation)+'</div>':'')+c.evidence.map(e=>'<blockquote class="evidence-quote"><p>'+esc(e.data.quote)+'</p><small>'+esc(e.data.source_name)+' · '+esc(location(e.data.locator))+' · '+esc(relationNames[e.data.relation])+(e.data.ocr?' · OCR转录':'')+'</small><p class="source-note">'+esc(e.data.conditions)+'</p><p class="source-note evidence-hash">SHA256 '+esc(e.data.source_sha256)+'</p></blockquote>').join('')+'<details><summary>人工审核当前版本</summary><form class="claim-review-form" data-claim="'+c.id+'" data-revision="'+c.revision+'"><div class="parameter-grid"><label class="field">审核者<input name="reviewer" minlength="2" maxlength="100" required></label><label class="field">结论<select name="decision"><option value="insufficient">证据不足</option><option value="supported">支持</option><option value="contradicted">反驳</option></select></label></div><label class="field">审核说明<textarea name="notes" minlength="10" maxlength="3000" required></textarea></label><label class="dataset-choice"><input type="checkbox" name="ocr_transcription_checked">涉及OCR时，我已对照原图核对转录</label><button class="button secondary small">保存人工审核</button></form></details><details class="section-gap"><summary>版本与完整性记录</summary><pre class="result">'+esc(JSON.stringify({reviews:c.reviews,history:c.history,evidence:c.evidence},null,2))+'</pre></details></article>').join(''):'<div class="empty">登记一个具体论断，再关联原文引句。</div>';
  root.querySelectorAll('.evidence-quote small').forEach(node=>{node.textContent=node.textContent.replace('OCR转录','AI或历史机器转录');});
  for(const claim of claims){
   const review=$('.claim-review-form[data-claim="'+claim.id+'"]');
   const article=review.closest('.evidence-claim');
   const check=review.querySelector('.dataset-choice');
   const needsTranscriptionCheck=claim.evidence.some(e=>!e.superseded&&e.data.ocr);
   if(needsTranscriptionCheck){const checkbox=check.querySelector('input');check.textContent='机器视觉转录已逐字对照原图';check.prepend(checkbox);}else check.remove();
   if(claim.transcription_recheck_required){const warning=document.createElement('p');warning.className='note';warning.textContent='关联机器视觉转录已有纠正。请从新快照引用并替换旧证据，再审核。';article.querySelector('.panel-heading').after(warning);}
   article.querySelectorAll('.evidence-quote').forEach((node,i)=>{
    const evidence=claim.evidence[i],badge=document.createElement('p');badge.className='source-note';
   badge.textContent=evidence.superseded?'历史证据 · 已替换':evidence.transcription_outdated?'当前证据 · 转录已纠正，待替换':evidence.data.ocr?'当前证据 · 机器视觉转录，待原图核验':'当前证据';node.prepend(badge);
   });
   const editor=document.createElement('details');editor.className='section-gap';
   editor.innerHTML='<summary>修改论断 · 旧审核将过期</summary><form class="claim-edit-form" data-claim="'+claim.id+'" data-revision="'+claim.revision+'"><label class="field">论断正文<textarea name="text" rows="3" minlength="8" maxlength="5000" required>'+esc(claim.text)+'</textarea></label><button class="button secondary small">保存新版本</button></form>';
   review.closest('details').before(editor);
  }
 }
 async function read(id,start=0){
  const result=await api(prefix+'/documents/'+id+'?offset='+start+'&limit=20');if(!root.isConnected)return;
  reader=result;offset=start;$('#document-reader').className='';
  $('#quote-form').elements.snapshot_id.value='';$('#quote-form').elements.block_id.value='';
  $('#quote-locator').textContent='在全文中点击“引用这段”。';
  $('#document-reader').innerHTML='<p class="source-note evidence-hash">原文 SHA256 '+esc(result.source_sha256)+'</p>'+result.blocks.map(b=>'<article class="document-block"><div class="panel-heading"><strong>'+esc(location(b.locator))+' · '+esc(b.kind)+'</strong><button class="text-button" data-cite-block="'+b.id+'">引用这段 ↙</button></div><pre>'+esc(b.text)+'</pre>'+(b.ocr?'<p class="source-note">机器视觉转录 · '+esc(b.transcription_model||'历史转录')+'；内容须逐字核验，不能作为专业审核。</p>':'')+'</article>').join('')+'<p class="source-note">'+esc(result.warnings.join(' '))+'</p>';
  $('#reader-pages').innerHTML='<button class="button secondary small" data-reader-step="-1" '+(start===0?'disabled':'')+'>上一组</button><span class="source-note">'+(start+1)+'–'+Math.min(start+20,result.total_blocks)+' / '+result.total_blocks+' 段</span><button class="button secondary small" data-reader-step="1" '+(start+20>=result.total_blocks?'disabled':'')+'>下一组</button>';
  result.blocks.forEach((block,i)=>{
   if(!block.ocr)return;
   const node=$('#document-reader').querySelectorAll('.document-block')[i],details=document.createElement('details');
   details.innerHTML='<summary>对照原图纠正机器视觉转录</summary><button class="text-button" type="button" data-preview="'+result.artifact_id+'">打开原文件 ↗</button><form class="transcription-form" data-snapshot="'+result.snapshot_id+'" data-block="'+block.id+'"><label class="field">核对后的文字<textarea name="text" rows="5" maxlength="30000" required>'+esc(block.text)+'</textarea></label><label class="field">核对者<input name="reviewer" minlength="2" maxlength="100" required></label><label class="field">修改依据<textarea name="notes" minlength="10" maxlength="3000" required></textarea></label><button class="button secondary small">保存为新快照</button></form><p class="source-note">纠正后仍需审核引用。原始转录和旧证据会保留。</p>';
   node.append(details);
   if(block.transcription_history?.length){const history=document.createElement('p');history.className='source-note';history.textContent='此段保留历史人工转录纠正；原始转录与旧快照仍可追溯。';node.append(history);}
  });
 }
 root.addEventListener('submit',event=>{
  event.preventDefault();event.stopPropagation();const form=event.target;
  run(form.querySelector('button'),async()=>{
   if(form.id==='document-extract-form'){
    notice('正在建立全文快照…');const args={artifact_id:form.elements.artifact_id.value,first_page:Number(form.elements.first_page.value),last_page:form.elements.last_page.value?Number(form.elements.last_page.value):null,image_mode:form.elements.image_mode.value,tables:true};
    const result=await post(prefix+'/tools/document_extract',{arguments:args});await loadSnapshots(result.snapshot_id);await read(result.snapshot_id);notice('已保存 '+result.blocks+' 段全文。'+result.warnings.join(' '));
   }else if(form.id==='fulltext-import-form'){
    notice('正在获取开放全文并保存来源…');const result=await post(prefix+'/tools/fulltext_import',{arguments:{pmcid:form.elements.pmcid.value.trim()}});
    const currentFiles=await api(prefix+'/artifacts');if(state.project.id===projectId)state.files=currentFiles;
    if(root.isConnected)$('#document-extract-form').elements.artifact_id.innerHTML=currentFiles.filter(f=>['pdf','xml','txt','md','docx','pptx','png','jpg','jpeg'].includes(f.kind)).map(f=>'<option value="'+f.id+'">'+esc(f.name)+'</option>').join('');
    await loadSnapshots(result.extraction.snapshot_id);await read(result.extraction.snapshot_id);notice('开放全文已导入，DOI与许可见原文件来源记录。');
   }else if(form.id==='claim-create-form'){
    const claim=await post(prefix+'/tools/claim_save',{arguments:{text:form.elements.text.value}});form.reset();await loadClaims(claim.id);notice('论断已登记，等待原文证据。');
   }else if(form.id==='quote-form'){
    const claim=claims.find(c=>c.id===form.elements.claim_id.value);if(!claim)throw Error('先登记或选择论断');
    if(!form.elements.snapshot_id.value)throw Error('先在全文中选择段落');
    await post(prefix+'/tools/evidence_add',{arguments:{claim_id:claim.id,expected_revision:claim.revision,snapshot_id:form.elements.snapshot_id.value,block_id:form.elements.block_id.value,quote:form.elements.quote.value,relation:form.elements.relation.value,conditions:form.elements.conditions.value,supersedes_evidence_id:form.elements.supersedes_evidence_id.value||null}});
    await loadClaims(claim.id);notice('引句已匹配原文；论断仍需人工审核。');
   }else if(form.classList.contains('transcription-form')){
    const result=await post(prefix+'/documents/'+form.dataset.snapshot+'/transcription',{reviewer:form.elements.reviewer.value,notes:form.elements.notes.value,corrections:[{block_id:form.dataset.block,text:form.elements.text.value}]});
    await loadSnapshots(result.snapshot_id);await read(result.snapshot_id,offset);await loadClaims();notice('已保存新快照和纠正依据；引用旧转录的审核须复核。');
   }else if(form.classList.contains('claim-edit-form')){
    await post(prefix+'/tools/claim_save',{arguments:{claim_id:form.dataset.claim,expected_revision:Number(form.dataset.revision),text:form.elements.text.value}});await loadClaims(form.dataset.claim);notice('论断已更新；旧审核保留在历史中，新版本需重新审核。');
   }else if(form.classList.contains('claim-review-form')){
    await post(prefix+'/claims/'+form.dataset.claim+'/review',{expected_revision:Number(form.dataset.revision),reviewer:form.elements.reviewer.value,decision:form.elements.decision.value,notes:form.elements.notes.value,ocr_transcription_checked:form.elements.ocr_transcription_checked?.checked||false});await loadClaims();notice('已保存当前版本的人工审核。');
   }
  });
 });
 root.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.dataset.citeBlock){const block=reader.blocks.find(b=>b.id===button.dataset.citeBlock);const form=$('#quote-form');form.elements.snapshot_id.value=reader.snapshot_id;form.elements.block_id.value=block.id;form.elements.quote.value=block.text.slice(0,2500);$('#quote-locator').textContent=location(block.locator)+' · '+block.id;form.elements.quote.focus();}
  if(button.dataset.readerStep)run(button,()=>read(reader.snapshot_id,offset+Number(button.dataset.readerStep)*20));
  if(button.id==='evidence-export')run(button,async()=>{const result=await post(prefix+'/tools/evidence_export',{arguments:{}});const currentFiles=await api(prefix+'/artifacts');if(state.project.id===projectId)state.files=currentFiles;if(root.isConnected)$('#evidence-notice').innerHTML='<div class="toolbar">'+result.artifacts.map(f=>'<a class="button secondary small" href="'+f.download_url+'" download>下载 '+esc(f.kind.toUpperCase())+' ↓</a>').join('')+'</div>';});
 });
 $('#snapshot-picker').onchange=()=>run(null,()=>read($('#snapshot-picker').value));
 await Promise.all([loadSnapshots(),loadClaims()]);if(root.isConnected&&snapshots.length)await read(snapshots[0].id);
}
