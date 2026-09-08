const KEY='myFarmData';
const blank={animals:[],tasks:[],records:[],activity:[]};
let data=JSON.parse(localStorage.getItem(KEY)||'null')||blank;
const $=s=>document.querySelector(s);
const save=()=>{localStorage.setItem(KEY,JSON.stringify(data));render()};
const money=n=>`R${Number(n||0).toLocaleString('en-ZA',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function render(){
 const animals=data.animals;
 const bulls=animals.filter(a=>a.type==='Bull').length;
 const females=animals.filter(a=>['Cow','Heifer'].includes(a.type)).length;
 const calves=animals.filter(a=>a.type==='Calf').length;
 $('#stats').innerHTML=[['🐄',animals.length,'Total cattle'],['🐂',bulls,'Bulls'],['🐮',females,'Cows & heifers'],['🐄',calves,'Calves']].map(x=>`<div class="stat"><div>${x[0]}</div><div class="number">${x[1]}</div><div class="label">${x[2]}</div></div>`).join('');
 $('#herdList').innerHTML=animals.length?animals.slice(-8).reverse().map(a=>`<div class="animal"><div class="animal-main"><div class="animal-icon">${a.type==='Bull'?'🐂':'🐄'}</div><div><strong>${esc(a.id)}</strong><small>${esc(a.type)} · ${esc(a.breed||'Breed unknown')} · ${a.weight?esc(a.weight)+' kg':'Weight unknown'}</small></div></div><span class="badge">${a.age?esc(a.age)+' mo':'Age ?'}</span></div>`).join(''):'<div class="empty">No cattle registered yet.<br>Start with your existing animals.</div>';
 const tasks=data.tasks;
 $('#taskList').innerHTML=tasks.length?tasks.map((t,i)=>`<div class="task ${t.done?'done':''}"><div><strong>${esc(t.task)}</strong><div class="muted">${t.due?esc(t.due):'No due date'}</div></div><button onclick="toggleTask(${i})">${t.done?'✓':'Done'}</button></div>`).join(''):'<div class="empty">No tasks yet.</div>';
 $('#activityList').innerHTML=data.activity.length?data.activity.slice(-8).reverse().map(x=>`<div class="activity"><div><strong>${esc(x.text)}</strong><div class="muted">${new Date(x.at).toLocaleString('en-ZA')}</div></div></div>`).join(''):'<div class="empty">Your activity will appear here.</div>';
 const expenses=data.records.filter(r=>r.cost).reduce((s,r)=>s+Number(r.cost),0);
 $('#finance').innerHTML=`<div class="money"><span>Recorded expenses</span><strong>${money(expenses)}</strong></div><div class="money"><span>Animals registered</span><strong>${animals.length}</strong></div><div class="money"><span>Records logged</span><strong>${data.records.length}</strong></div>`;
}
function log(text){data.activity.push({text,at:new Date().toISOString()});}
function open(d){$(d).showModal()}
function closeAll(){document.querySelectorAll('dialog').forEach(d=>d.close())}
$('#quickAdd').onclick=$('#registerBtn').onclick=()=>open('#animalDialog');
$('#addTask').onclick=()=>open('#taskDialog');
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=closeAll);
document.querySelectorAll('.action').forEach(b=>b.onclick=()=>{
 const a=b.dataset.action;
 if(a==='animal')open('#animalDialog');
 else if(a==='task')open('#taskDialog');
 else { $('#recordTitle').textContent={weight:'Record weight',health:'Health record',expense:'Add expense',caretaker:'Caretaker daily log'}[a]; $('#valueLabel').firstChild.textContent={weight:'Weight / measurement',health:'Health details',expense:'Expense details',caretaker:'Daily log'}[a]||'Details'; $('#recordForm [name=recordType]').value=a; open('#recordDialog'); }
});
$('#animalForm').onsubmit=e=>{e.preventDefault();const f=new FormData(e.target);const a=Object.fromEntries(f.entries());a.age=a.age?Number(a.age):null;a.weight=a.weight?Number(a.weight):null;data.animals.push(a);log(`Registered ${a.id}`);e.target.closest('dialog').close();e.target.reset();save()};
$('#taskForm').onsubmit=e=>{e.preventDefault();const f=new FormData(e.target);const t=Object.fromEntries(f.entries());t.done=false;data.tasks.push(t);log(`Added task: ${t.task}`);e.target.closest('dialog').close();e.target.reset();save()};
$('#recordForm').onsubmit=e=>{e.preventDefault();const f=new FormData(e.target);const r=Object.fromEntries(f.entries());data.records.push(r);log(`${r.recordType} record for ${r.animalId}`);e.target.closest('dialog').close();e.target.reset();save()};
window.toggleTask=i=>{data.tasks[i].done=!data.tasks[i].done;log(`${data.tasks[i].done?'Completed':'Reopened'} task: ${data.tasks[i].task}`);save()};
$('#exportBtn').onclick=()=>{const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='my-farm-records.json';a.click();URL.revokeObjectURL(a.href)};
$('#showAll').onclick=()=>alert(`You have ${data.animals.length} registered animal(s). Full herd management is coming next.`);
render();