const $ = id => document.getElementById(id);
let match = null, busy = false, autoplay = false, error = '';
const names = {human:'我',jev:'Jev',qwen:'Qwen3.7 Flash',draw:'平局'};

async function request(path, data) {
  const reply = await fetch(path, data === undefined ? {cache:'no-store'} : {
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),cache:'no-store'
  });
  const payload = await reply.json();
  if (!reply.ok) {
    if (payload.state) match = payload.state;
    throw new Error(payload.error || '请求失败');
  }
  return payload;
}

function render() {
  $('modelOrder').hidden = $('mode').value !== 'jev_qwen';
  $('humanOrder').hidden = $('mode').value === 'jev_qwen';
  if (!match) return;
  names.qwen = match.platform_model || 'qwen3.7-flash-non-thinking';
  $('mode').options[1].textContent = `我 vs ${names.qwen}`;
  $('mode').options[2].textContent = `Jev vs ${names.qwen}`;
  $('jevFirst').options[1].textContent = `${names.qwen} 执黑`;
  const {board, history, next_actor: next, actors, winner} = match;
  const configChanged = match.mode !== $('mode').value ||
    actors[1] !== ($('mode').value === 'jev_qwen'
      ? ($('jevFirst').value === 'true' ? 'jev' : 'qwen')
      : ($('humanFirst').value === 'true' ? 'human' : $('mode').value.slice(6)));
  $('counter').textContent = `第 ${history.length} 手`;
  $('turn').textContent = winner ? (winner === 'draw' ? '平局' : names[winner]+' 获胜') :
    configChanged ? '配置已改变，请点击开始新局' : `轮到 ${names[next]} · ${match.next_color===1?'黑':'白'}棋`;
  const grid=$('board');grid.replaceChildren();
  const last=history.at(-1);
  for(let r=0;r<15;r++)for(let c=0;c<15;c++){
    const cell=document.createElement('button');cell.type='button';cell.className='cell';
    cell.dataset.row=r;cell.dataset.col=c;
    cell.setAttribute('role','gridcell');cell.setAttribute('aria-label',`第${r+1}行第${c+1}列${board[r][c]?'已落子':'空位'}`);
    cell.disabled=busy||configChanged||next!=='human'||board[r][c]!==0;
    if(last?.row===r&&last?.col===c)cell.classList.add('last');
    if(board[r][c]){const stone=document.createElement('span');stone.className='stone '+(board[r][c]===1?'black':'white');cell.append(stone);}
    grid.append(cell);
  }
  $('mode').disabled=busy;$('humanFirst').disabled=busy;$('jevFirst').disabled=busy;
  $('start').disabled=busy;
  $('step').disabled=busy||configChanged||!!winner||!next||next==='human';
  $('auto').disabled=!autoplay&&(busy||configChanged||!!winner||!next||next==='human');
  $('auto').textContent=autoplay?'暂停自动对战':'自动对战';
  const ready=match.available?.[next];
  $('notice').textContent=error||(busy ? (next==='human'?'正在提交操作…':`正在等待 ${names[next]} 返回；模型响应可能需要约 60 秒…`) :
    configChanged?'选择已更新，请点击开始新局。':
    next&&next!=='human'&&!ready?`${names[next]} 的 Key 未配置；请在启动服务前设环境变量。`:
    winner?$('turn').textContent:'已连接本地对战服务。一次 AI 落子对应一次模型调用（规则必胜/必防除外）。');
  $('notice').classList.toggle('error',!!error||!!(next&&next!=='human'&&!ready));
  $('decision').textContent=last?`${names[last.actor]} · (${last.row+1}, ${last.col+1}) · ${last.source==='rule_win'||last.source==='rule_block'?'代码必胜/必防（未调用模型）':last.model||'真人落子'}`:'等待开局';
  $('usage').textContent=last?.usage?`Token: ${last.usage.input_tokens??last.usage.prompt_tokens??'?'} 输入 / ${last.usage.output_tokens??last.usage.completion_tokens??'?'} 输出 · ${last.confidence===null?'模型无概率置信度':'置信度 '+last.confidence}`:'';
  const log=$('history');log.replaceChildren();
  if(!history.length){const li=document.createElement('li');li.textContent='暂无落子';log.append(li);}
  history.forEach((h,i)=>{const li=document.createElement('li');li.textContent=`#${i+1} ${names[h.actor]} ${h.color===1?'黑':'白'} → (${h.row+1},${h.col+1}) [${h.source}]`;log.append(li);});
}

async function action(path,data){if(busy)return;busy=true;render();try{match=await request(path,data);error='';}catch(e){error=e.message;autoplay=false;}finally{busy=false;render();}}
async function step(){if(!match||match.winner||match.next_actor==='human')return;await action('/api/step',{});}
$('board').addEventListener('click',async e=>{const el=e.target.closest('.cell');if(!el||el.disabled)return;await action('/api/move',{row:Number(el.dataset.row),col:Number(el.dataset.col)});if(match?.next_actor!=='human'&&!match?.winner)await step();});
$('start').addEventListener('click',async()=>{
  autoplay=false;await action('/api/reset',{mode:$('mode').value,human_first:$('humanFirst').value==='true',jev_first:$('jevFirst').value==='true'});
  if(match?.next_actor!=='human'&&!match?.winner)await step();
});
$('step').addEventListener('click',step);
$('auto').addEventListener('click',async()=>{
  autoplay=!autoplay;render();
  while(autoplay&&match?.next_actor!=='human'&&!match?.winner&&!error){await step();if(autoplay)await new Promise(resolve=>setTimeout(resolve,250));}
  autoplay=false;render();
});
for(const id of ['mode','humanFirst','jevFirst'])$(id).addEventListener('change',()=>{autoplay=false;render();});
if(location.protocol==='file:'){
  match={board:Array.from({length:15},()=>Array(15).fill(0)),history:[],mode:'human_jev',
    actors:{1:'human',2:'jev'},next_actor:'human',next_color:1,winner:null,
    available:{jev:false,qwen:false}};
  render();
  $('notice').textContent='静态预览不能调用模型。请先启动 enhanced_server.py，再打开 http://127.0.0.1:8767/';
  $('notice').classList.add('error');$('start').disabled=true;
}else request('/api/state').then(s=>{match=s;render();}).catch(()=>{$('notice').textContent='本地服务不可用，请按运行文档启动。';$('notice').classList.add('error');});