const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export function recoveryCards(run){
 const calls=run.unknown_calls||[];
 const decisions=(run.result.tool_attempts||[]).filter(a=>a.resolution);
 const history=decisions.length?'<p class="note section-gap" data-recovery-history>中断处置记录：'+esc(decisions.map(a=>a.tool+' · '+(a.resolution.decision==='adopt'?'采用已有记录':'确认重试')).join('；'))+'。累计工具尝试 '+Number(run.result.tool_calls||0)+' 次，含中断调用；完整依据保存在执行轨迹中。</p>':'';
 if(!calls.length)return history;
 return history+'<section class="section-gap" aria-label="对话中断调用"><h3>中断调用待核对</h3><p class="note">以下工具没有保存确认结果。先核对已有计算和文件，再确认重试或采用已有记录；处置后可继续本任务。原调用和累计预算保留。</p>'+calls.map(a=>'<article class="study-task" data-run-unknown="'+esc(a.id)+'"><strong>'+esc(a.tool)+'</strong><p class="source-note">子任务：'+esc(a.task_key||'未指定')+' · 调用 '+esc(a.call_id)+'</p><details><summary>实际输入与候选计算</summary><pre class="result">'+esc(JSON.stringify({input:a.input,candidates:a.candidate_calculations},null,2))+'</pre></details><button class="button secondary small" type="button" data-run-reconcile="'+esc(a.id)+'">核对并确认处置</button></article>').join('')+'</section>';
}

export function bindRecovery(run,{modal,post,refresh,toast}){
 document.querySelectorAll('[data-run-reconcile]').forEach(button=>button.onclick=()=>{
  const attempt=run.unknown_calls.find(a=>a.id===button.dataset.runReconcile);
  modal('核对对话工具调用 · '+attempt.tool,'<form id="run-reconcile-form"><p class="note">核对原调用的实际输入及已生成文件。确认重试会再次执行已保存的输入；采用记录会检查项目、工具、输入和文件。这里的处置不能替代科学或工程审核。</p><label class="field">处置方式<select name="decision"><option value="retry">确认重新执行</option><option value="adopt">采用已核对的计算记录</option></select></label><label class="field">已有计算记录<select name="calculation_id"><option value="">请选择要采用的记录</option>'+attempt.candidate_calculations.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.tool)+' · '+esc(c.created_at)+' · '+esc(c.id)+'</option>').join('')+'</select></label><label class="field">核对者<input name="reviewer" minlength="2" maxlength="100" required></label><label class="field">核对依据与处置说明<textarea name="notes" minlength="10" maxlength="3000" required></textarea></label><button class="button" type="submit">保存处置确认</button></form>');
  document.querySelector('#run-reconcile-form').onsubmit=async event=>{
   event.preventDefault();event.stopPropagation();const form=event.target,submit=form.querySelector('[type="submit"]');submit.disabled=true;
   try{
    const value=Object.fromEntries(new FormData(form));value.calculation_id=value.decision==='adopt'?value.calculation_id:null;
    await post('/api/runs/'+run.id+'/tool-attempts/'+attempt.id+'/reconcile',value);
    document.querySelector('#form-dialog').close();await refresh();
   }catch(error){toast(error.message)}finally{submit.disabled=false}
  };
 });
}
