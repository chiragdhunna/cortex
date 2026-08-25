import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Job = {id:string;status:string;stage:string;error?:string;category:string;formats:string[]};
const api = import.meta.env.VITE_API_URL || "http://localhost:8000";

function Notes({notes}:{notes:any}) {
  return <section><h2>{notes.source_title}</h2>{notes.topics?.map((topic:any) => <article key={topic.title}><h3>{topic.title}</h3>{topic.content.qa_pairs && <>{topic.content.qa_pairs.map((x:any)=><p key={x.q}><b>Q:</b> {x.q}<br/><b>A:</b> {x.a} ({x.difficulty})</p>)}<p>{topic.content.talking_points?.join(" · ")}</p></>}{topic.content.definitions && <><p>{topic.content.summary}</p><ul>{topic.content.definitions.map((x:any)=><li key={x.term}><b>{x.term}:</b> {x.definition}</li>)}</ul>{topic.content.self_test.map((x:any)=><p key={x.q}><b>{x.q}</b> — {x.a}</p>)}</>}{topic.content.explanation && <><p>{topic.content.explanation}</p><p><b>Analogies:</b> {topic.content.analogies.join("; ")}</p><p><b>Concept map:</b> {topic.content.concept_map.edges.map((x:string[])=>x.join(" → ")).join(", ")}</p></>}</article>)}</section>;
}
function App() {
 const [jobs,setJobs]=useState<Job[]>([]), [selected,setSelected]=useState<Job|null>(null), [notes,setNotes]=useState<any>(null);
 const refresh=()=>fetch(`${api}/jobs`).then(r=>r.json()).then(setJobs).catch(()=>{});
 useEffect(()=>{refresh();const timer=setInterval(refresh,2500);return()=>clearInterval(timer)},[]);
 const submit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();const form=new FormData(e.currentTarget);const file=form.get("file") as File; let response; if(file?.size){response=await fetch(`${api}/jobs/upload`,{method:"POST",body:form});}else{response=await fetch(`${api}/jobs`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:form.get("url"),source_type:form.get("source_type"),category:form.get("category"),formats:form.getAll("formats")})});}if(!response.ok) alert(await response.text());refresh();};
 const choose=async(job:Job)=>{setSelected(job);if(job.status==="done"){setNotes(await (await fetch(`${api}/jobs/${job.id}/result`)).json())}};
 return <main><h1>Cortex</h1><form onSubmit={submit}><input name="file" type="file" accept=".pdf,.mp3,.wav,.m4a,.mp4,.mov"/><input name="url" placeholder="Or paste audio/video link"/><select name="source_type"><option value="video_link">Video link</option><option value="audio_link">Audio link</option></select><select name="category"><option value="interview">Interview prep</option><option value="exam">Exam prep</option><option value="understanding">Understanding</option></select><fieldset><legend>Formats</legend>{["markdown","pdf","anki_csv","json"].map(x=><label key={x}><input type="checkbox" name="formats" value={x} defaultChecked={x==="markdown"}/>{x}</label>)}</fieldset><button>Submit</button></form><section><h2>Job history</h2>{jobs.map(job=><button className="job" key={job.id} onClick={()=>choose(job)}>{job.category}: {job.status} / {job.stage}</button>)}</section>{selected&&<section><h2>Selected job</h2><p>{selected.error||selected.status}</p>{selected.status==="done"&&<p>{selected.formats.map(f=><a key={f} href={`${api}/jobs/${selected.id}/download?format=${f}`}>Download {f} </a>)}</p>}</section>}{notes&&<Notes notes={notes}/>}</main>;
}
createRoot(document.getElementById("root")!).render(<App/>);
