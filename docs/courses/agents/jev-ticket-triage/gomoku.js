const $ = id => document.getElementById(id);
let game = null;
let busy = false;
let error = '';

async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? {cache:'no-store'} : {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload), cache:'no-store'
  });
  const result = await response.json();
  if (!response.ok) {
    if (result.state) game = result.state;
    throw new Error(result.error || '请求失败');
  }
  return result;
}

function render() {
  if (!game) return;
  const {board, status, turns} = game;
  const humanIsBlack = game.human_color === 1;
  const chosenFirst = $('first').value;
  const needsStart = chosenFirst !== game.first;
  $('moveCount').textContent = `第 ${board.flat().filter(Boolean).length} 手`;
  const last = turns.at(-1);
  const cells = $('board');
  cells.replaceChildren();
  for (let r=0; r<15; r++) for (let c=0; c<15; c++) {
    const cell = document.createElement('button');
    cell.type = 'button'; cell.className = 'cell'; cell.setAttribute('role','gridcell');
    cell.setAttribute('aria-label',`第 ${r+1} 行第 ${c+1} 列${board[r][c] ? (board[r][c]===1 ? '黑子' : '白子') + (board[r][c]===game.ai_color ? ' Jev' : ' 我') : '空位'}`);
    cell.dataset.row = r; cell.dataset.col = c;
    cell.disabled = busy || needsStart || status !== 'PLAYING' || !game.key_configured || board[r][c] !== 0;
    if (last && last.row===r && last.col===c) cell.classList.add('last');
    if (board[r][c]) {
      const stone = document.createElement('span');
      stone.className = 'stone ' + (board[r][c]===1 ? 'black':'white');
      cell.append(stone);
    }
    cells.append(cell);
  }
  $('turn').textContent = needsStart ? '先点击“按所选先手开局”' : {
    PLAYING:`轮到你 · 执${humanIsBlack?'黑':'白'}落子`,
    AI_PENDING:`轮到 Jev · 执${humanIsBlack?'白':'黑'}落子（失败可重试）`,
    HUMAN_WON:'你赢了！',JEV_WON:'Jev 连成五子',DRAW:'平局'}[status] || status;
  $('retry').hidden = status !== 'AI_PENDING'; $('retry').disabled = busy || needsStart;
  $('first').disabled = busy;
  $('reset').disabled = busy;
  const notice = $('notice');
  notice.classList.toggle('error', Boolean(error) || !game.key_configured);
  notice.textContent = error || (!game.key_configured ? '需要 API Key：请在本地服务终端设置轮换后的 TYPESAFE_API_KEY 后重启。' :
    needsStart ? '先手已切换：请点“按所选先手开局”，再落子。' :
    status === 'PLAYING' ? `实时模式已连接：你执${humanIsBlack?'黑':'白'}，轮到你落子。` : $('turn').textContent);
  $('decision').textContent = last ?
    `${last.source==='jev' ? 'Jev 真正选择' : '确定性规则保底（未调用 Jev）'} · 第 ${last.row+1} 行第 ${last.col+1} 列。${last.reason} ${last.model || ''}` :
    '选择先手；若 Jev 先手，点击“按所选先手开局”即可看到它的第一步。';
  const choices = $('choices'); choices.replaceChildren();
  const top = Object.entries(last?.probabilities || {}).sort((a,b)=>b[1]-a[1]).slice(0,6);
  for (const [id,p] of top) {
    const item=document.createElement('div'); item.className='choice'+(id===`r${String(last.row).padStart(2,'0')}c${String(last.col).padStart(2,'0')}`?' selected':'');
    const label=document.createElement('span'); label.textContent=`第 ${Number(id.slice(1,3))+1} 行 · 第 ${Number(id.slice(4,6))+1} 列`;
    const value=document.createElement('strong'); value.textContent=(p*100).toFixed(0)+'%';
    const bar=document.createElement('div'); bar.className='bar'; const fill=document.createElement('span');fill.style.width=p*100+'%';bar.append(fill);
    item.append(label,value,bar);choices.append(item);
  }
  $('usage').textContent = last?.source==='jev' ?
    `候选 ${last.candidates.length} 点 · 置信度 ${(last.confidence*100).toFixed(0)}% · 输入 ${last.usage?.input_tokens ?? '?'} token / 输出 ${last.usage?.output_tokens ?? '?'} token` :
    last ? '此手由胜负规则直接处理：不计 Jev 调用与模型置信度。' : '';
  const history=$('history');history.replaceChildren();
  if (!turns.length) {const li=document.createElement('li');li.textContent='对局尚未开始。';history.append(li);}
  for (const [i,turn] of turns.entries()) {
    const li=document.createElement('li');
    const id=`r${String(turn.row).padStart(2,'0')}c${String(turn.col).padStart(2,'0')}`;
    li.textContent=`第 ${i+1} 回合：${turn.color===1?'黑':'白'}子 → (${turn.row+1}, ${turn.col+1}) · ${turn.source==='jev'?'Jev Choice':'代码必胜/必防'}${turn.source==='jev' ? ` · P=${turn.probabilities[id].toFixed(2)}` : ''}`;
    history.append(li);
  }
}

async function act(path, data) {
  if (busy) return;
  busy=true;render();
  try { game=await api(path,data);error=''; if (path==='/api/reset') $('first').value=game.first; }
  catch(e) { error=e.message; }
  finally {busy=false;render();}
}

$('board').addEventListener('click',event=>{
  const cell=event.target.closest('.cell');
  if (!cell || cell.disabled) return;
  act('/api/move',{row:Number(cell.dataset.row),col:Number(cell.dataset.col)});
});
$('retry').addEventListener('click',()=>act('/api/retry',{}));
$('reset').addEventListener('click',()=>act('/api/reset',{first:$('first').value}));
$('first').addEventListener('change',render);
if (location.protocol==='file:') {
  game={board:Array.from({length:15},()=>Array(15).fill(0)),status:'PLAYING',turns:[],first:'human',human_color:1,ai_color:2,key_configured:false};
  render();
  $('notice').textContent='预览模式：需要先启动本地 Python 服务，再访问 http://127.0.0.1:8766/ 才能对战。';
  $('notice').classList.add('error');
} else {
  api('/api/state').then(s=>{game=s;$('first').value=s.first;render();}).catch(()=>{
    $('notice').textContent='无法连接服务：请按玩法文档启动 gomoku_server.py 后重新打开本地地址。';
    $('notice').classList.add('error');
  });
}