const $ = (id) => document.getElementById(id);
const stages = [
  ["PREFLIGHT","ตรวจสอบภาพ"],["CREATE_PROJECT","สร้าง Project"],["ADD_PHOTOS","เพิ่มภาพ"],
  ["ALIGN","Align Photos"],["DEPTH_MAPS","สร้าง Depth Maps"],["DEM","สร้าง DEM"],
  ["ORTHOMOSAIC","สร้าง Orthomosaic"],["EXPORT","Export GeoTIFF"],
  ["VALIDATE_OUTPUT","ตรวจสอบผลลัพธ์"],["SAVE_PROJECT","บันทึก Project"],["COMPLETE","เสร็จสิ้น"]
];
let inspection = null, currentJob = null, pollTimer = null, mockMode = false;

async function api(path, options={}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
  const type = response.headers.get("content-type") || "";
  const data = type.includes("json") ? await response.json() : await response.text();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data));
  return data;
}
function bytes(value){ if(value==null)return "—"; const units=["B","KB","MB","GB","TB"];let i=0,n=value;while(n>=1024&&i<units.length-1){n/=1024;i++;}return `${n.toFixed(i?1:0)} ${units[i]}`; }
function initTimeline(){ $("timeline").innerHTML=stages.map(([id,label])=>`<li class="stage pending" id="stage-${id}"><strong>${label}</strong><small>รอ</small></li>`).join(""); }
function showWarnings(items=[]){ $("warnings").textContent=items.join("\n"); $("warnings").classList.toggle("hidden",!items.length); }

async function inspect(path){
  inspection = await api("/api/inspect-folder",{method:"POST",body:JSON.stringify({path})});
  $("photo-dir").value=inspection.path; $("plot-code").value=inspection.plot_code||"";
  $("image-count").value=inspection.image_count; $("crs").value=inspection.crs;
  $("disk-space").value=bytes(inspection.available_disk_space);
  $("output-dir").value=inspection.output_proposal?.output_dir||"";
  showWarnings([...(inspection.warnings||[]), ...(inspection.conflicts?.length?["พบไฟล์ผลลัพธ์เดิม กรุณาเลือกวิธีจัดการ"]:[])]);
  $("start-job").disabled=!inspection.image_count;
}
async function chooseFolder(){ const result=await api("/api/select-folder",{method:"POST"}); if(!result.cancelled) await inspect(result.path); }
async function startJob(){
  const policy=$("conflict-policy").value;
  const confirmed=policy!=="overwrite"||confirm("ยืนยันเขียนทับไฟล์ผลลัพธ์เดิมหรือไม่?"); if(!confirmed)return;
  const payload={photo_dir:inspection.path,image_count:inspection.image_count,plot_code:$("plot-code").value,crs:$("crs").value,output_dir:$("output-dir").value,profile:$("profile").value,conflict_policy:policy,confirm_overwrite:confirmed,mock_scenario:$("mock-scenario").value};
  const result=await api("/api/jobs",{method:"POST",body:JSON.stringify(payload)}); currentJob=result.job_id; setActions(true); poll();
}
function setActions(active){ $("cancel-job").disabled=!active; $("show-log").disabled=!active; $("codex-help").disabled=!active; }
function render(state){
  $("job-summary").textContent=`${state.job_id} · ${state.overall_status}`;
  stages.forEach(([id])=>{const row=$(`stage-${id}`),stage=state.stages[id];row.className=`stage ${stage.status}`;row.querySelector("small").textContent=stage.elapsed_seconds==null?stage.status:`${stage.elapsed_seconds.toFixed(1)}s`;});
  const failed=state.overall_status==="failed", done=state.overall_status==="completed", stopped=failed||done||state.overall_status==="cancelled";
  $("error-box").classList.toggle("hidden",!state.error); $("error-box").textContent=state.error?`${state.error.stage}: ${state.error.message}`:"";
  $("cancel-job").disabled=stopped; $("open-output").disabled=!done; $("open-diagnostics").disabled=!failed; $("retry-job").disabled=!failed;
  if(stopped&&pollTimer){clearTimeout(pollTimer);pollTimer=null;} return !stopped;
}
async function poll(){ try{const state=await api(`/api/jobs/${currentJob}`);if(render(state))pollTimer=setTimeout(poll,2000);}catch(error){notify(error);} }
async function action(suffix){return api(`/api/jobs/${currentJob}/${suffix}`,{method:"POST"});}
async function showLog(){const text=await api(`/api/jobs/${currentJob}/log`);$("log-view").textContent=text;$("log-view").classList.remove("hidden");}
function notify(error){alert(error.message||String(error));}

async function boot(){
  initTimeline(); const health=await api("/api/health"); mockMode=health.mock_mode;
  $("mode-badge").classList.toggle("hidden",!mockMode); $("scenario-wrap").classList.toggle("hidden",!mockMode);
  const profiles=await api("/api/profiles"); $("profile").innerHTML=profiles.map(p=>`<option value="${p.name}">${p.label_th}</option>`).join("");
  $("profile").value="standard";
  const jobs=await api("/api/jobs"); if(jobs.length){currentJob=jobs[0].job_id;setActions(true);render(jobs[0]);if(["pending","running"].includes(jobs[0].overall_status))poll();}
}
$("choose-folder").onclick=()=>chooseFolder().catch(notify); $("start-job").onclick=()=>startJob().catch(notify);
$("cancel-job").onclick=()=>action("cancel").catch(notify); $("open-output").onclick=()=>action("open-output").catch(notify);
$("open-diagnostics").onclick=()=>action("open-diagnostics").catch(notify); $("show-log").onclick=()=>showLog().catch(notify);
$("retry-job").onclick=async()=>{try{const r=await action("retry");currentJob=r.job_id;poll();}catch(e){notify(e)}};
$("codex-help").onclick=async()=>{const text=`ช่วยวิเคราะห์ diagnostics ของงาน ${currentJob} โดยอ่าน job.json, state.json, processing.log และ error.txt ห้ามอ้างว่าได้ทดสอบ Metashape จริงหากไม่มีหลักฐาน`;try{await navigator.clipboard.writeText(text);alert("คัดลอกคำสั่งสำหรับ Codex แล้ว — ไม่มีการ execute code");}catch{alert(text)}};
boot().catch(notify);
