(function(){"use strict";
const review=globalThis.MRIReview,labels={physics:"MRI物理",sequences:"撮像シーケンス",artifacts:"Artifact",parameters:"パラメータ",coils:"装置・コイル",anatomy:"撮像部位",positioning:"Positioning",questions:"問題集"};
const el={};let materials=[],progress=review.loadProgress(localStorage),today=review.todayInJapan();
const node=(tag,cls,text)=>{const value=document.createElement(tag);if(cls)value.className=cls;if(text!==undefined)value.textContent=text;return value};
const displayDate=value=>String(value||"").replaceAll("-",".");

function makeCard(material,stage,completed=false){
  const card=node("article","card review-card"),top=node("div","card-top"),footer=node("div","review-actions"),open=node("a","","教材を開く"),button=node("button",completed?"secondary":"",completed?"完了を取り消す":"復習済みにする");
  top.append(node("span","badge",labels[material.category]||material.category),node("span","type",stage.label));
  open.href=material.path;open.setAttribute("aria-label",`${material.title}を開く`);
  button.type="button";button.onclick=()=>{review.setComplete(progress,review.materialKey(material),stage.id,!completed);review.saveProgress(localStorage,progress);render()};
  const due=review.dueDate(material,stage),meta=node("p","review-meta",`追加 ${displayDate(material.addedAt)} ・ 復習予定 ${displayDate(due)}`);
  if(!completed&&due<today)meta.append(node("strong","overdue"," 期限超過"));
  footer.append(open,button);card.append(top,node("h2","",material.title),node("p","",material.description),meta,footer);return card;
}

function render(){
  today=review.todayInJapan();
  const pending=review.pendingByStage(materials,progress,today),completed=review.completedReviews(materials,progress);
  for(const stage of review.STAGES){
    const items=pending[stage.id],grid=el[`${stage.id}Grid`],empty=el[`${stage.id}Empty`];
    grid.replaceChildren(...items.map(material=>makeCard(material,stage)));grid.hidden=!items.length;empty.hidden=Boolean(items.length);el[`${stage.id}Count`].textContent=`${items.length}件`;
  }
  el.completedGrid.replaceChildren(...completed.map(record=>makeCard(record.material,record.stage,true)));
  el.completedGrid.hidden=!completed.length;el.completedEmpty.hidden=Boolean(completed.length);el.total.textContent=`未完了 ${pending.day0.length+pending.day1.length+pending.day7.length}件`;
}

async function load(){
  el.error.hidden=true;
  try{const response=await fetch("materials.json",{cache:"no-cache"});if(!response.ok)throw Error(response.status);const data=await response.json();materials=data.materials||[];render()}
  catch(error){console.error(error);el.content.hidden=true;el.error.hidden=false;el.total.textContent="読み込みエラー"}
}

function init(){
  for(const id of ["content","error","total","day0Grid","day0Empty","day0Count","day1Grid","day1Empty","day1Count","day7Grid","day7Empty","day7Count","completedGrid","completedEmpty"])el[id]=document.querySelector(`#${id}`);
  const theme=document.querySelector("#theme"),saved=localStorage.getItem("mri-learning-theme")||"system";if(saved!=="system")document.documentElement.dataset.theme=saved;theme.value=saved;theme.onchange=()=>{localStorage.setItem("mri-learning-theme",theme.value);if(theme.value==="system")document.documentElement.removeAttribute("data-theme");else document.documentElement.dataset.theme=theme.value};
  document.querySelector("#retry").onclick=()=>{el.content.hidden=false;load()};load();if("serviceWorker"in navigator)addEventListener("load",()=>navigator.serviceWorker.register("sw.js"));
}
document.addEventListener("DOMContentLoaded",init);
})();
