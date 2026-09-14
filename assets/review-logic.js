(function(global,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  global.MRIReview=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const STORAGE_KEY="mri-learning-review-v1";
  const STAGES=[
    {id:"day0",days:0,label:"今日の復習"},
    {id:"day1",days:1,label:"昨日の復習"},
    {id:"day7",days:7,label:"先週の復習"}
  ];

  function addDays(value,days){
    const [year,month,day]=String(value).split("-").map(Number);
    if(!year||!month||!day)return "";
    const date=new Date(Date.UTC(year,month-1,day+days));
    return date.toISOString().slice(0,10);
  }

  function todayInJapan(now=new Date()){
    const parts=new Intl.DateTimeFormat("en-CA",{
      timeZone:"Asia/Tokyo",year:"numeric",month:"2-digit",day:"2-digit"
    }).formatToParts(now);
    const values=Object.fromEntries(parts.map(part=>[part.type,part.value]));
    return `${values.year}-${values.month}-${values.day}`;
  }

  function emptyProgress(){return {version:1,materials:{}}}

  function parseProgress(value){
    try{
      const parsed=typeof value==="string"?JSON.parse(value):value;
      if(!parsed||parsed.version!==1||!parsed.materials||typeof parsed.materials!=="object"||Array.isArray(parsed.materials))return emptyProgress();
      return parsed;
    }catch(_error){return emptyProgress()}
  }

  function loadProgress(storage){
    try{return parseProgress(storage.getItem(STORAGE_KEY))}
    catch(_error){return emptyProgress()}
  }

  function saveProgress(storage,progress){
    try{storage.setItem(STORAGE_KEY,JSON.stringify(progress));return true}
    catch(_error){return false}
  }

  function isComplete(progress,materialId,stageId){
    return Boolean(progress.materials?.[materialId]?.[stageId]);
  }

  function materialKey(material){return material.reviewKey||material.id}

  function setComplete(progress,materialId,stageId,complete,completedAt=new Date().toISOString()){
    if(!progress.materials[materialId])progress.materials[materialId]={};
    if(complete)progress.materials[materialId][stageId]=completedAt;
    else delete progress.materials[materialId][stageId];
    if(!Object.keys(progress.materials[materialId]).length)delete progress.materials[materialId];
    return progress;
  }

  function dueDate(material,stage){return addDays(material.addedAt,stage.days)}

  function pendingByStage(materials,progress,today=todayInJapan()){
    return Object.fromEntries(STAGES.map(stage=>[
      stage.id,
      materials.filter(material=>material.reviewEligible===true&&dueDate(material,stage)<=today&&!isComplete(progress,materialKey(material),stage.id))
        .sort((a,b)=>dueDate(a,stage).localeCompare(dueDate(b,stage))||a.title.localeCompare(b.title,"ja"))
    ]));
  }

  function completedReviews(materials,progress){
    const records=[];
    for(const material of materials){
      if(material.reviewEligible!==true)continue;
      for(const stage of STAGES){
        const completedAt=progress.materials?.[materialKey(material)]?.[stage.id];
        if(completedAt)records.push({material,stage,completedAt,dueDate:dueDate(material,stage)});
      }
    }
    return records.sort((a,b)=>b.completedAt.localeCompare(a.completedAt));
  }

  return {STORAGE_KEY,STAGES,addDays,todayInJapan,parseProgress,loadProgress,saveProgress,isComplete,setComplete,materialKey,dueDate,pendingByStage,completedReviews};
});
