export function createModelSettings(state,{api,esc,modal,toast,closeMobileSidebar}) {
 const $=s=>document.querySelector(s);
 function applyConfig(config){
  state.config=config;
  const ready=Object.values(config.models).some(Boolean);
  $('#model-status').textContent=ready?'模型已配置':'模型待配置 · 工具可用';
  $('#model-status').className=ready?'model-ready':'';
  const reasoning=$('#chat-form select[name="reasoning"]');if(reasoning){reasoning.disabled=!config.reasoning_supported;reasoning.title=config.reasoning_supported?'':'当前接口未启用 reasoning_effort';}
 }
 async function open(){
  closeMobileSidebar();
  try{
   const c=await api('/api/config');applyConfig(c);
   modal('模型连接与运行配置','<form id="model-settings-form"><p class="source-note">设置保存在本机服务中，保存后对新任务立即生效。</p><label class="field">服务类型<select name="provider"><option value="openai_compatible">兼容 OpenAI API（如 DeepSeek）</option><option value="ollama">本地 Ollama</option></select></label><label class="field">API 地址<input name="base_url" type="url" value="'+esc(c.base_url||'https://api.openai.com/v1')+'" placeholder="https://api.deepseek.com/v1" required maxlength="1000"><small>填写 API 基础地址，通常以 /v1 结尾。</small></label><label class="field">API 密钥<input name="api_key" type="password" autocomplete="new-password" maxlength="4000" placeholder="'+(c.api_key_configured?'已设置 · 留空保留当前密钥':'输入服务商提供的 API 密钥')+'"><small>'+(c.api_key_configured?'当前密钥已保存在服务端，不会回显。':'Ollama 通常不需要密钥。')+'</small></label>'+(c.api_key_configured?'<label class="dataset-choice"><input type="checkbox" name="clear_api_key">清除已保存的密钥</label>':'')+'<label class="field">均衡模型 ID<input name="balanced" value="'+esc(c.models.balanced)+'" placeholder="例如 deepseek-flash" maxlength="200"><small>填写你的服务商支持的具体模型 ID。</small></label><div class="parameter-grid"><label class="field">快速模型 ID<input name="fast" value="'+esc(c.models.fast)+'" maxlength="200" placeholder="可与均衡模型相同"></label><label class="field">深度模型 ID<input name="deep" value="'+esc(c.models.deep)+'" maxlength="200" placeholder="可与均衡模型相同"></label></div><details class="settings-advanced"><summary>高级设置</summary><label class="field section-gap">视觉模型 ID<input name="vision_model" value="'+esc(c.vision_model||'')+'" maxlength="200" placeholder="可选：支持图像输入的模型"></label><label class="dataset-choice"><input type="checkbox" name="reasoning_supported" '+(c.reasoning_supported?'checked':'')+'>接口支持 reasoning_effort 思考参数</label><div class="parameter-grid"><label class="field">请求超时 / 秒<input name="timeout" type="number" min="10" max="300" value="'+(c.timeout||120)+'" required></label><label class="field">每轮最多模型调用<input name="iterations" type="number" min="1" max="20" value="'+(c.iterations||8)+'" required></label></div></details><p id="model-settings-error" class="inline-error" role="alert"></p><div class="settings-actions"><span class="source-note">保存设置不会发起模型请求。</span><button class="button" type="submit">保存设置</button></div></form>');
   const form=$('#model-settings-form');form.elements.provider.value=c.provider;
   form.elements.provider.onchange=()=>{if(form.elements.provider.value==='ollama'&&form.elements.base_url.value==='https://api.openai.com/v1')form.elements.base_url.value='http://localhost:11434/v1';};
   form.onsubmit=async event=>{
    event.preventDefault();event.stopPropagation();const button=form.querySelector('[type="submit"]');button.disabled=true;$('#model-settings-error').textContent='';
    try{
     const f=form.elements;
     const value={provider:f.provider.value,base_url:f.base_url.value,api_key:f.api_key.value,clear_api_key:f.clear_api_key?.checked||false,models:{balanced:f.balanced.value,fast:f.fast.value,deep:f.deep.value},vision_model:f.vision_model.value,reasoning_supported:f.reasoning_supported.checked,timeout:Number(f.timeout.value),iterations:Number(f.iterations.value)};
     const saved=await api('/api/config',{method:'PUT',body:JSON.stringify(value)});f.api_key.value='';applyConfig(saved);$('#form-dialog').close();toast('模型设置已保存，新任务立即生效');
    }catch(error){$('#model-settings-error').textContent=error.message;}finally{button.disabled=false;}
   };
  }catch(error){toast(error.message);}
 }
 return {open,applyConfig};
}
