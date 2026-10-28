const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export function simulationResult(result){
 const files=result.artifacts||[],plot=files.find(f=>f.id===result.plot_artifact_id),archive=files.find(f=>f.id===result.native_archive_id);
 const initial=result.initial,final=result.final;
 const species=Object.keys(final.mole_fractions).filter(s=>Math.max(initial.mole_fractions[s],final.mole_fractions[s])>1e-10);
 return '<div data-cantera-summary><p class="source-note">Cantera '+esc(result.backend_version)+' · '+esc(result.mechanism)+' · '+result.species_count+' 物种 / '+result.reaction_count+' 反应</p>'+
 '<div class="note">'+(result.validation.passed?'该工况的数值一致性检查通过。':'该工况的数值检查未通过，请检查适用温区与残差。')+' '+(result.mode==='reactor'?'这是有限时间积分，不代表已达到平衡。':'这是指定约束和允许物种集合内的气相平衡。')+'</div>'+
 '<div class="metrics"><div class="metric"><span>最终温度</span><strong>'+final.temperature_K.toFixed(2)+'</strong><small>K</small></div><div class="metric"><span>最终绝对压力</span><strong>'+(final.pressure_Pa/1000).toFixed(3)+'</strong><small>kPa</small></div></div>'+
 (archive?'<a class="button secondary small" data-native-download href="'+archive.download_url+'" download>下载原生模型与复算包 ↓</a>':'')+
 (plot?'<img class="dataset-plot" src="'+plot.preview_url+'" alt="反应器温度和主要物种随时间变化">':'')+
 '<div class="table-wrap section-gap"><table data-cantera-species><thead><tr><th>物种</th><th>初始摩尔分数</th><th>最终摩尔分数</th></tr></thead><tbody>'+species.map(s=>'<tr><td>'+esc(s)+'</td><td>'+initial.mole_fractions[s].toPrecision(7)+'</td><td>'+final.mole_fractions[s].toPrecision(7)+'</td></tr>').join('')+'</tbody></table></div><p class="source-note">表中省略低于1e-10的物种，完整数值保留在JSON/CSV中。'+esc(result.warnings.join(' '))+'</p>'+
 '<div class="toolbar">'+files.filter(f=>['csv','pdf','yaml'].includes(f.kind)||f.name==='result.json').map(f=>'<a class="button secondary small" href="'+f.download_url+'" download>'+esc(f.name)+' ↓</a>').join('')+'</div>'+
 '<details><summary>完整数值、方法与校核</summary><pre class="result">'+esc(JSON.stringify(result,null,2))+'</pre></details></div>';
}
