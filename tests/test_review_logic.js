const test=require("node:test");
const assert=require("node:assert/strict");
const review=require("../assets/review-logic.js");

const material=(overrides={})=>({id:"lesson-1",title:"Lesson",addedAt:"2026-09-10",reviewEligible:true,...overrides});

test("JSTの日付と復習予定日を計算する",()=>{
  assert.equal(review.todayInJapan(new Date("2026-09-12T14:59:59Z")),"2026-09-12");
  assert.equal(review.todayInJapan(new Date("2026-09-12T15:00:00Z")),"2026-09-13");
  assert.equal(review.addDays("2026-12-31",1),"2027-01-01");
});

test("追加当日・翌日・7日後に独立した復習を提示する",()=>{
  const progress=review.parseProgress(null),item=material();
  let pending=review.pendingByStage([item],progress,"2026-09-10");
  assert.deepEqual(pending.day0.map(value=>value.id),["lesson-1"]);
  assert.equal(pending.day1.length,0);
  assert.equal(pending.day7.length,0);
  pending=review.pendingByStage([item],progress,"2026-09-11");
  assert.deepEqual(pending.day1.map(value=>value.id),["lesson-1"]);
  assert.equal(pending.day7.length,0);
  review.setComplete(progress,item.id,"day0",true,"2026-09-10T01:00:00Z");
  review.setComplete(progress,item.id,"day1",true,"2026-09-11T01:00:00Z");
  pending=review.pendingByStage([item],progress,"2026-09-17");
  assert.equal(pending.day0.length,0);
  assert.equal(pending.day1.length,0);
  assert.deepEqual(pending.day7.map(value=>value.id),["lesson-1"]);
});

test("未完了は期限後も残り、完了を取り消せる",()=>{
  const progress=review.parseProgress(null),item=material();
  assert.equal(review.pendingByStage([item],progress,"2026-10-01").day1.length,1);
  review.setComplete(progress,item.id,"day1",true);
  assert.equal(review.pendingByStage([item],progress,"2026-10-01").day1.length,0);
  review.setComplete(progress,item.id,"day1",false);
  assert.equal(review.pendingByStage([item],progress,"2026-10-01").day1.length,1);
});

test("基準日以前の教材と壊れた保存データを安全に扱う",()=>{
  const progress=review.parseProgress("{broken");
  assert.deepEqual(progress,{version:1,materials:{}});
  assert.equal(review.pendingByStage([material({reviewEligible:false})],progress,"2026-10-01").day1.length,0);
});
