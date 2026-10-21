const LABEL={works:"Works",crashes:"Crashes",bricks:"Bricks",fixed:"Fixed",mixed:"Mixed reports",unknown:"Unknown"};
const ORDER={bricks:0,crashes:1,mixed:2,unknown:3,fixed:4,works:5};
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const badge=s=>`<span class="badge b-${s}">${LABEL[s]||s}</span>`;
const dt=r=>r.date_precision==="exact"?r.date:`≈${r.date}`;
function reportList(m){return `<ul class="reports">${m.reports.map(r=>`<li>${badge(r.verdict)} <b>${dt(r)}</b> · <a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a> <span class="muted">(${esc(r.source)})</span><br><span class="small">${r.quote?`“${esc(r.quote)}”`:""}${r.note?` <span class="muted">${esc(r.note)}</span>`:""}${r.verified?` <span class="vtag">✓ ${esc(r.verified)}</span>`:""}</span></li>`).join("")}</ul>`}
let DATA,sortK="status",open=new Set();
fetch("data/mods.json").then(r=>r.json()).then(d=>{DATA=d;
 d.mods.forEach(m=>m.latest=m.reports.map(r=>r.date).sort().pop());
 const p=d.current_patch;document.getElementById("patch").innerHTML=`<b>Current patch:</b> ${esc(p.label)} (${p.date}) · <a href="${p.url}">notes</a> · <a href="${p.official_url}">Bethesda Aug 20 notes</a><br><span class="small muted">${esc(p.note)}</span>`;
 const c={};d.mods.forEach(m=>c[m.status]=(c[m.status]||0)+1);
 document.getElementById("counts").innerHTML=`<b>${d.mods.length} mods tracked</b> · `+Object.keys(ORDER).filter(k=>c[k]).map(k=>`<span>${badge(k)} ${c[k]}</span>`).join("")+` <span class="muted">Updated ${d.generated}</span>`;
 const cats=[...new Set(d.mods.map(m=>m.category))].sort();document.getElementById("cat").innerHTML+=cats.map(x=>`<option>${esc(x)}</option>`).join("");
 document.getElementById("changes").innerHTML=d.changes.map(x=>`<li><b>${x.date}</b> ${esc(x.text)}${x.url?` <a href="${x.url}">source</a>`:""}</li>`).join("");
 const h=location.hash.slice(1);if(h)open.add(h);render();});
function render(){const q=document.getElementById("q").value.toLowerCase(),st=document.getElementById("status").value,ca=document.getElementById("cat").value;
 let ms=DATA.mods.filter(m=>(!q||m.name.toLowerCase().includes(q)||m.summary.toLowerCase().includes(q))&&(!st||m.status===st)&&(!ca||m.category===ca));
 ms.sort((a,b)=>sortK==="status"?(ORDER[a.status]-ORDER[b.status])||a.name.localeCompare(b.name):sortK==="latest"?b.latest.localeCompare(a.latest):String(a[sortK]).localeCompare(String(b[sortK])));
 document.getElementById("rows").innerHTML=ms.map(m=>`<tr class="row" data-id="${m.id}"><td><b>${esc(m.name)}</b></td><td>${badge(m.status)}</td><td class="small">${esc(m.category)}</td><td class="small">${m.latest}</td><td class="small">${m.reports.length}</td></tr>`+(open.has(m.id)?`<tr class="detail"><td colspan="5"><p>${esc(m.summary)}</p>${reportList(m)}<p class="small muted">Mod last updated: ${m.mod_last_updated||"not yet recorded (check the mod's Creations page)"} · <a href="${m.creations_url}">Find it on Bethesda Creations (PlayStation)</a> · <a href="mod.html?id=${m.id}">Permalink</a></p></td></tr>`:"")).join("")||`<tr><td colspan="5" class="muted">No mods match.</td></tr>`;
 document.querySelectorAll("tr.row").forEach(tr=>tr.onclick=()=>{const id=tr.dataset.id;open.has(id)?open.delete(id):open.add(id);render();});}
["q","status","cat"].forEach(id=>document.getElementById(id).addEventListener("input",render));
document.querySelectorAll("th[data-k]").forEach(th=>th.onclick=()=>{sortK=th.dataset.k;render();});
// Newsletter signup -> Kit. Works without JS via the form's action/method.
document.querySelectorAll("form.nl-form").forEach(f=>f.addEventListener("submit",ev=>{
 if(!window.fetch||!window.FormData||f.dataset.fallback)return;
 ev.preventDefault();const btn=f.querySelector("button");if(btn){btn.disabled=true;btn.textContent="Subscribing…";}
 const fallback=()=>{f.dataset.fallback="1";f.submit();};
 fetch(f.action,{method:"POST",mode:"cors",body:new FormData(f),headers:{Accept:"application/json"}})
 .then(r=>{if(!(r.ok||r.type==="opaque"||r.type==="opaqueredirect"))throw new Error("HTTP "+r.status);
  return r.text().then(t=>{let j=null;try{j=JSON.parse(t)}catch(e){}if(j&&j.status==="quarantined"&&j.url){window.location.href=j.url;throw new Error("guard");}if(j&&(j.status==="failed"||j.status==="error"))throw new Error("rejected");},()=>{});})
 .then(()=>{const p=document.createElement("p");p.className="nl-ok";p.setAttribute("role","status");p.textContent="Thanks! Check your email to confirm your subscription.";f.replaceWith(p);})
 .catch(e=>{if(e&&e.message==="guard")return;fallback();});}));
