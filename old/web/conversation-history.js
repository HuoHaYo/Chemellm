export function historyMarkup(data,{esc,icon,tools}) {
 const records=data.calculations,files=data.artifacts;
 if(!records.length&&!files.length)return '';
 const name=tool=>tools.find(t=>t.id===tool)?.name||tool;
 const date=value=>esc(new Date(value).toLocaleString('zh-CN'));
 return '<section class="conversation-history" aria-label="已保存的研究记录"><header class="history-heading"><div><span class="history-label">'+icon('workflow')+(data.is_project_history?'项目历史记录':'本会话研究记录')+'</span><h2>'+data.total_calculations+' 次计算 · '+files.length+' 份文件</h2></div><span class="pill">来自已保存的项目数据</span></header>'+
 (data.is_project_history?'<p class="history-description">这里保留了会话功能上线前的计算与文件。展开记录可查看实际输入、结果和成果。</p>':'')+
 records.map(r=>'<article class="history-record" data-history-calculation="'+r.id+'"><div class="history-record-heading"><span class="history-tool-icon">'+icon('calculator')+'</span><div><strong>'+esc(name(r.tool))+'</strong><time datetime="'+esc(r.created_at)+'">'+date(r.created_at)+'</time></div><span class="badge">工具记录</span></div><details class="history-input"><summary>查看实际输入</summary><pre class="result">'+esc(JSON.stringify(r.input,null,2))+'</pre></details><details class="history-output" data-history-output="'+r.id+'"><summary>查看计算结果与校验</summary><div class="history-result"></div></details>'+((r.result.artifacts||[]).length?'<div class="history-artifacts">'+r.result.artifacts.map(f=>'<button class="button secondary small" data-preview="'+esc(f.id)+'">'+icon('files')+esc(f.name)+'</button>').join('')+'</div>':'')+'</article>').join('')+
 (data.total_calculations>data.limit?'<div class="history-pagination"><button class="button secondary small" data-history-offset="'+Math.max(0,data.offset-data.limit)+'" '+(data.offset===0?'disabled':'')+'>上一页</button><span>第 '+(data.offset+1)+'–'+Math.min(data.offset+data.limit,data.total_calculations)+' 条 / '+data.total_calculations+'</span><button class="button secondary small" data-history-offset="'+(data.offset+data.limit)+'" '+(data.offset+data.limit>=data.total_calculations?'disabled':'')+'>下一页</button></div>':'')+
 (files.length?'<details class="history-files"><summary>项目资料与成果 · '+files.length+' 份</summary><div class="history-file-list">'+files.map(f=>'<div><button data-preview="'+esc(f.id)+'">'+icon('files')+'<span>'+esc(f.name)+'</span><small>'+esc(f.kind.toUpperCase())+'</small></button><a href="'+esc(f.download_url)+'" download aria-label="下载 '+esc(f.name)+'">下载</a></div>').join('')+'</div></details>':'')+'</section>';
}

export function bindHistory(root,data,displayResult){
 for(const details of root.querySelectorAll('[data-history-output]'))details.addEventListener('toggle',()=>{
  if(!details.open||details.dataset.loaded)return;
  const record=data.calculations.find(r=>r.id===details.dataset.historyOutput);
  details.querySelector('.history-result').innerHTML=displayResult({calculation_id:record.id,...record.result});details.dataset.loaded='true';
 });
}
