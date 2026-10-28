const $=s=>document.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const number=v=>v==null?"—":Number(v).toPrecision(6);
const percent=v=>Number(v*100).toLocaleString('zh-CN',{maximumFractionDigits:2});
const modelNames={linear:"线性",first_order_uptake:"一级趋近",first_order_decay:"一级衰减",power_law:"幂律",arrhenius:"Arrhenius"};

export async function renderDatasets(state,{intro,api}){
 const files=state.files.filter(f=>["csv","xlsx"].includes(f.kind));
 const projectId=state.project.id;
 $("#content").innerHTML=intro("把实验数据，变成可复核的模型。","从原始表格出发，检查数据、比较拟合，并保留不确定度与残差。","EXPERIMENT / DATA")+
 '<div class="toolbar"><button class="button" data-action="upload">＋ 上传 CSV / Excel</button><button class="button secondary" data-dataset-example="BoxBOD">试用 NIST 耗氧量数据</button></div>'+
 '<div class="calculation-grid"><section class="panel"><label class="field">项目数据文件<select id="dataset-picker">'+files.map(f=>'<option value="'+f.id+'">'+esc(f.name)+'</option>').join('')+'</select></label><label class="field" id="dataset-sheet-field" hidden>工作表<select id="dataset-sheet"></select></label><div id="dataset-source" class="source-note"></div><form id="dataset-form" hidden><div class="parameter-grid"><label class="field">自变量列<select name="x_column"></select></label><label class="field">因变量列<select name="y_column"></select></label><label class="field">自变量单位<input name="x_unit" value="dimensionless" required placeholder="例如 day、K"></label><label class="field">因变量单位<input name="y_unit" value="dimensionless" required placeholder="例如 mg/liter"></label></div><label class="field">观测标准差列（可选）<select name="sigma_column"></select></label><label class="dataset-choice"><input type="checkbox" name="absolute_sigma">标准差为已知绝对误差</label><fieldset class="dataset-models"><legend>候选模型</legend>'+Object.entries(modelNames).map(([key,label])=>'<label class="dataset-choice"><input type="checkbox" name="models" value="'+key+'" '+(["linear","first_order_uptake"].includes(key)?'checked':'')+'>'+label+'</label>').join('')+'</fieldset><p class="source-note">默认95%局部置信区间；Arrhenius须提供温度单位。不会自动填补缺失值或执行公式。</p><button class="button">分析并保存结果 →</button></form></section><section class="panel"><h2>数据与分析结果</h2><div id="dataset-preview"></div><div id="dataset-result" class="empty">'+(files.length?'选择列、单位与候选模型后开始。':'先上传带列名的 CSV/XLSX，或试用公开数据。')+'</div></section></div>';
 if(!files.length)return;
 const root=$("#dataset-form");
 const picker=$("#dataset-picker"),sheetPicker=$("#dataset-sheet");
 let revision=0;
 async function inspect(sheet=null){
  const current=++revision;
  root.hidden=true;
  $("#dataset-source").textContent="读取表格与来源…";
  try{
   const data=await api('/api/projects/'+projectId+'/datasets/'+picker.value+(sheet?'?sheet='+encodeURIComponent(sheet):''));
   if(!root.isConnected||current!==revision)return;
   root.dataset.artifact=data.artifact_id;root.dataset.sheet=data.sheet||'';
   const reference=files.find(f=>f.id===data.artifact_id)?.metadata.reference;
   root.elements.x_unit.value=reference?.x_unit||'dimensionless';root.elements.y_unit.value=reference?.y_unit||'dimensionless';
   $("#dataset-sheet-field").hidden=!data.sheets.length;
   sheetPicker.innerHTML=data.sheets.map(s=>'<option '+(s===data.sheet?'selected':'')+'>'+esc(s)+'</option>').join('');
   $("#dataset-source").textContent=data.rows+' 行 · SHA256 '+data.sha256+' · '+data.policy+(data.blank_rows.length?' 已跳过全空行：'+data.blank_rows.join(', '):'');
   const options=data.columns.map(c=>'<option>'+esc(c)+'</option>').join('');
   root.elements.x_column.innerHTML=options;root.elements.y_column.innerHTML=options;
   root.elements.y_column.selectedIndex=Math.min(1,data.columns.length-1);
   root.elements.sigma_column.innerHTML='<option value="">未指定：从残差估计误差尺度</option>'+options;
   $("#dataset-preview").innerHTML='<details open><summary>原始数据预览 · 前 '+data.preview.length+' 行</summary><div class="table-wrap"><table><thead><tr>'+data.columns.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+data.preview.map(r=>'<tr>'+r.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div></details>';
   $("#dataset-result").innerHTML='选择列、单位与候选模型后开始。';
   root.hidden=false;
  }catch(error){if(root.isConnected&&current===revision)$("#dataset-source").textContent=error.message;}
 }
 picker.onchange=()=>inspect();sheetPicker.onchange=()=>inspect(sheetPicker.value);
 await inspect();
}

export function datasetArguments(form){
 const selected=[...form.querySelectorAll('input[name="models"]:checked')].map(e=>e.value);
 if(!selected.length)throw Error("至少选择一个候选模型");
 return {artifact_id:form.dataset.artifact,sheet:form.dataset.sheet||null,x_column:form.elements.x_column.value,y_column:form.elements.y_column.value,x_unit:form.elements.x_unit.value,y_unit:form.elements.y_unit.value,sigma_column:form.elements.sigma_column.value||null,absolute_sigma:form.elements.absolute_sigma.checked,models:selected};
}

export function datasetResult(result){
 const ranking=result.comparison.ranking;
 const plot=result.artifacts.find(f=>f.kind==='svg');
 return '<p class="source-note dataset-hash">数据版本 SHA256 '+esc(result.source.sha256)+'</p>'+
 (plot?'<img class="dataset-plot" src="'+plot.preview_url+'" alt="数据拟合曲线、模型均值置信区间与残差图">':'')+
 '<div class="table-wrap"><table data-model-comparison><thead><tr><th>模型</th><th>'+esc(result.comparison.criterion)+'</th><th>Δ</th></tr></thead><tbody>'+ranking.map(r=>'<tr><td>'+esc(modelNames[r.model])+'</td><td>'+number(r.criterion_value)+'</td><td>'+number(r.delta)+'</td></tr>').join('')+'</tbody></table></div><p class="source-note">'+esc(result.comparison.interpretation)+'</p>'+
 result.fits.map(f=>'<article class="dataset-fit"><h3>'+esc(modelNames[f.model])+' · RMSE '+number(f.metrics.RMSE)+'</h3><p class="source-note">'+esc(f.equation)+'</p><div class="table-wrap"><table data-fit-parameters><thead><tr><th>参数</th><th>数值</th><th>单位</th><th>'+percent(f.confidence)+'%局部置信区间</th></tr></thead><tbody>'+f.parameters.map(p=>'<tr><td>'+esc(p.name)+'</td><td>'+number(p.value)+'</td><td>'+esc(p.unit)+'</td><td>'+(p.confidence_interval?p.confidence_interval.map(number).join(' ～ '):'不适用')+'</td></tr>').join('')+'</tbody></table></div>'+f.warnings.map(w=>'<p class="source-note">'+esc(w)+'</p>').join('')+'</article>').join('')+
 (result.failures.length?'<div class="note">未成功的候选模型：'+esc(JSON.stringify(result.failures))+'</div>':'')+
 '<div class="toolbar">'+result.artifacts.map(f=>'<a class="button secondary small" href="'+f.download_url+'" download>下载 '+esc(f.kind.toUpperCase())+' ↓</a>').join('')+'</div><p class="source-note">'+esc(result.warnings.join(' '))+'</p><details><summary>完整计算、来源与诊断</summary><pre class="result">'+esc(JSON.stringify(result,null,2))+'</pre></details>';
}
