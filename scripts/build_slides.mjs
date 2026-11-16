// Editable PowerPoint built with the bundled @oai/artifact-tool runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const project = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const skillDir = '/home/agent/.codex/skills/builtins/presentations';
const draftDir = path.join(project, '.presentation-build');
const finalPath = path.join(project, 'deliverables', 'Viva_Presentation_Team_Final.pptx');
await fs.mkdir(draftDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
let actualResults = null;
try {
  const loaded = JSON.parse(await fs.readFile(path.join(project,'output/final_100/summary.json'),'utf8'));
  if (loaded.status === 'complete' && loaded.requested_questions === 100) actualResults = loaded;
} catch (_) { /* keep a pending status slide when results are not yet available */ }
let actualMemory = null;
try {
  const loaded = JSON.parse(await fs.readFile(path.join(project,'output/memory_comparison/memory_comparison.json'),'utf8'));
  if (loaded.methods?.buffer && loaded.methods?.summary && loaded.methods?.entity) actualMemory = loaded.methods;
} catch (_) { /* preserve method-only slide when memory measurements are unavailable */ }

const ppt = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const FONT = 'Liberation Sans';
const NAVY = '#14233C';
const TEAL = '#107F86';
const MUTED = '#536579';
const PAGE = '#F8FAFC';

function box(slide, name, text, x, y, w, h, opts={}) {
  const shape = slide.shapes.add({
    geometry: 'textbox', name,
    position: { left:x, top:y, width:w, height:h },
    fill: 'none', line: { style:'solid', fill:'none', width:0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT, fontSize: `${opts.size ?? 21}pt`, color: opts.color ?? NAVY,
    bold: !!opts.bold, verticalAlignment:'middle', wrap:'square', autoFit:'shrinkText',
    alignment: opts.align ?? 'left', insets: 0,
  };
  return shape;
}
function base(title, number) {
  const slide = ppt.slides.add();
  slide.background.fill = PAGE;
  box(slide, 'slide-title', title, 72, 56, 1100, 84, {size:37, bold:true});
  box(slide, 'slide-number', String(number).padStart(2,'0'), 1175, 634, 44, 34,
      {size:15,color:MUTED,align:'right'});
  return slide;
}
function label(slide, text, x, y, w) {
  box(slide, 'label-'+x+'-'+y, text.toUpperCase(), x, y, w, 32,
      {size:15,bold:true,color:TEAL});
}

// 1. Minimal title slide
{
  const slide = ppt.slides.add();
  slide.background.fill = PAGE;
  box(slide,'cover-category','MINI-PROJECT  /  PROBLEM 5',82,110,950,38,{size:17,bold:true,color:TEAL});
  box(slide,'cover-title','Tool-Using Research\nAgent with Memory',82,178,1120,190,{size:51,bold:true});
  box(slide,'cover-subtitle','ReAct + LangGraph + HotpotQA',84,413,1010,50,{size:24,color:MUTED});
  label(slide,'Submitted by',84,515,400);
  box(slide,'student-prathyush','Prathyush Gowda\nPES1UG24AM201',84,554,505,75,{size:19,bold:true});
  box(slide,'student-pradyumn','Pradyumn Bidari\nPES1UG24AM194',674,554,505,75,{size:19,bold:true});
  box(slide,'student-prashant','Prashant Devendra Naik\nPES1UG24AM199',84,628,505,75,{size:19,bold:true});
  box(slide,'student-urs','Pradyun Urs\nPES1UG24AM195',674,628,505,75,{size:19,bold:true});
  slide.speakerNotes.text='Problem statement 5. Introduce the autonomous research agent and the exact evaluation deliverables.';
}

// 2. Problem and scope
{
  const slide=base('Problem and objectives',2);
  label(slide,'The challenge',72,183,470);
  box(slide,'problem','Single-prompt models can guess\nfacts, make calculation errors\nand lose context across turns.',72,227,525,224,{size:27});
  label(slide,'Project objectives',680,183,470);
  box(slide,'objectives','Find evidence with external tools\nCalculate numerical answers\nRetain context within a session\nRecord every action and result',680,232,525,246,{size:22});
  slide.speakerNotes.text='The required deliverables specify a ReAct loop, three tools, three memories and a 100-question benchmark.';
}

// 3. LangGraph architecture
{
  const slide=base('LangGraph agent architecture',3);
  const lines=[
    ['01','Question + selected memory','A new turn begins with session context.'],
    ['02','Reasoning node','Model outputs a public thought summary and one action.'],
    ['03','Tool node','Wikipedia, calculator or restricted Python runs.'],
    ['04','Observation + trace','Result is logged, then fed back into reasoning.'],
    ['05','Final answer','Agent responds and updates persistent memory.'],
  ];
  lines.forEach(([num,title,desc],i)=>{
    const y=166+i*92;
    box(slide,`step-${num}`,num,73,y,72,56,{size:24,bold:true,color:TEAL});
    box(slide,`step-label-${num}`,title,165,y,390,54,{size:23,bold:true});
    box(slide,`step-desc-${num}`,desc,580,y,608,54,{size:18,color:MUTED});
  });
  slide.speakerNotes.text='Code: research_agent/react_agent.py. LangGraph StateGraph creates think, act, action routing and end states.';
}

// 4. ReAct example
{
  const slide=base('ReAct cycle example',4);
  label(slide,'Illustrative research task',72,177,900);
  box(slide,'example-question','Find the difference between 1975 and 1955, after verifying the first year.',72,218,1115,84,{size:26});
  box(slide,'thought','THOUGHT SUMMARY    Look up Microsoft\'s founding year',72,340,1100,54,{size:21});
  box(slide,'action','ACTION                       wikipedia_search("Microsoft founding year")',72,418,1100,54,{size:21});
  box(slide,'observation','OBSERVATION          Wikipedia returns 1975; calculator returns 20',72,496,1100,64,{size:21});
  box(slide,'caption','Trace fields: timestamp, public summary, action, input, observation, token usage',73,595,1112,48,{size:17,color:MUTED});
  slide.speakerNotes.text='Illustrative process only. No claim of a live tool call. Public reasoning summary is different from private model chain-of-thought.';
}

// 5. Tool descriptions
{
  const slide=base('Three external tools',5);
  const cols=[
    {x:72,n:'01',title:'Wikipedia search',body:'Looks up factual claims\nReturns article excerpts\nIncludes source URLs'},
    {x:475,n:'02',title:'Calculator',body:'Evaluates arithmetic\nHandles square roots\nRejects code injection'},
    {x:875,n:'03',title:'Python execution',body:'Runs numerical scripts\nRestricts syntax and built-ins\nChild-process time limit'},
  ];
  for(const c of cols){
    box(slide,`tool-num-${c.n}`,c.n,c.x,204,320,65,{size:29,bold:true,color:TEAL});
    box(slide,`tool-title-${c.n}`,c.title,c.x,293,325,64,{size:27,bold:true});
    box(slide,`tool-body-${c.n}`,c.body,c.x,373,329,192,{size:20,color:MUTED});
  }
  box(slide,'tool-limit','Educational Python restriction is not a hardened security sandbox.',73,606,1140,35,{size:16,color:MUTED});
  slide.speakerNotes.text='Code: research_agent/tools.py and python_runner.py. Wikipedia: https://www.mediawiki.org/wiki/API:Main_page';
}

// 6. Memory comparison
{
  if(actualMemory){
    const slide=base('Measured memory comparison',6);
    const blocks=[
      {x:72,title:'BUFFER',content:'Stores all previous Q/A turns.',key:'buffer'},
      {x:475,title:'SUMMARY',content:'Maintains a rolling conversation summary.',key:'summary'},
      {x:875,title:'ENTITY',content:'Remembers named entities and facts.',key:'entity'},
    ];
    for(const block of blocks){
      const entry=actualMemory[block.key];
      label(slide,block.title,block.x,198,330);
      box(slide,'description-'+block.title,block.content,block.x,264,328,85,{size:20});
      box(slide,'accuracy-'+block.title,`${entry.correct_followups}/${entry.graded_followups} correct  (${entry.followup_accuracy_pct.toFixed(0)}%)`,block.x,363,338,65,{size:24,bold:true,color:TEAL});
      box(slide,'tokens-'+block.title,`Total tokens: ${entry.combined_tokens.toLocaleString('en-US')}\nMemory update tokens: ${entry.total_memory_update_tokens.toLocaleString('en-US')}`,block.x,452,336,104,{size:19});
    }
    box(slide,'memory-method','Illustrative four-turn conversation; two graded recall questions per memory type.',72,591,1110,56,{size:19,color:MUTED});
    slide.speakerNotes.text='Actual memory JSON: buffer 2/2, summary 2/2, entity 1/2. Combined tokens: buffer 11147, summary 10919, entity 28023. Only two graded follow-up questions per mode; this tiny test cannot establish general memory superiority.';
  } else {
    const slide=base('Three session memory strategies',6);
    const blocks=[
      {x:72,title:'BUFFER',content:'Stores all previous Q/A turns.\nDetailed recall.\nContext keeps growing.'},
      {x:475,title:'SUMMARY',content:'LLM refreshes a rolling summary.\nShorter prompt context.\nExtra tokens, possible omissions.'},
      {x:875,title:'ENTITY',content:'Stores named entities and facts.\nFocused factual retrieval.\nMay miss unnamed details.'},
    ];
    for(const block of blocks){
      label(slide,block.title,block.x,212,330);
      box(slide,'description-'+block.title,block.content,block.x,282,328,248,{size:21});
    }
    box(slide,'memory-method','Controlled test: identical four-turn dialog, two follow-up recall questions.',72,576,1150,56,{size:20,color:MUTED});
    slide.speakerNotes.text='Code: research_agent/memory.py and session.py. Summary/entity memory use model calls to update their state.';
  }
}

// 7. Benchmark
{
  const slide=base('Evaluation on 100 HotpotQA questions',7);
  label(slide,'Same 100 validation questions',72,172,1130);
  box(slide,'react-arm','ReAct agent\nWikipedia + calculator + Python\nSeveral model steps if needed',72,241,532,208,{size:23});
  box(slide,'cot-arm','Single-prompt CoT baseline\nOne model call\nNo external tools or memory',680,241,528,208,{size:23});
  label(slide,'Metrics',72,492,300);
  box(slide,'metrics','Exact match accuracy  /  Token F1  /  Tools per query  /  Input + output tokens',72,537,1120,88,{size:20});
  slide.speakerNotes.text='HotpotQA: Yang et al. (2018) https://arxiv.org/abs/1809.09600; data: https://huggingface.co/datasets/hotpotqa/hotpot_qa. Gold answers are used for grading only.';
}

// 8. Measured results, when the benchmark has genuinely completed
{
  if (actualResults) {
    const slide=base('Measured HotpotQA results',8);
    const r=actualResults.methods.react, c=actualResults.methods.cot;
    box(slide,'result-context','Qwen2.5 3B  /  HotpotQA validation  /  100 questions per method',72,153,1100,40,{size:18,color:MUTED});
    label(slide,'METRIC',72,215,490);
    label(slide,'REACT',680,215,230);
    label(slide,'COT BASELINE',975,215,260);
    const rows=[
      ['Questions evaluated',String(r.completed),String(c.completed)],
      ['Exact match accuracy',`${r.exact_match_accuracy_pct.toFixed(1)}%`,`${c.exact_match_accuracy_pct.toFixed(1)}%`],
      ['Token F1',`${r.token_f1_pct.toFixed(2)}%`,`${c.token_f1_pct.toFixed(2)}%`],
      ['Average tool calls / query',r.mean_tool_calls_per_query.toFixed(2),c.mean_tool_calls_per_query.toFixed(2)],
      ['Average tokens / query',r.mean_total_tokens_per_query.toLocaleString('en-US'),c.mean_total_tokens_per_query.toLocaleString('en-US')],
      ['Abstained',String(r.abstained),String(c.abstained)],
    ];
    rows.forEach((row,i)=>{
      const y=270+i*50;
      box(slide,`metric-${i}`,row[0],72,y,555,39,{size:21});
      box(slide,`react-${i}`,row[1],680,y,220,39,{size:21,bold:i===1,color:i===1?TEAL:NAVY});
      box(slide,`cot-${i}`,row[2],975,y,235,39,{size:21,bold:i===1,color:i===1?TEAL:NAVY});
    });
    box(slide,'result-footer',`CoT scored higher on this run. ReAct abstained on ${r.abstained} queries; results depend on this local model and retrieval setup.`,72,600,1100,53,{size:17,color:MUTED});
    slide.speakerNotes.text=`Actual 100-question measurement: ReAct ${r.exact_match_accuracy_pct}% exact match, CoT ${c.exact_match_accuracy_pct}%; ReAct ${r.abstained} abstentions. Both methods executed 100 with zero execution failures. CoT was more accurate and used fewer tokens in this specific experiment. Keep memory strategy comparison separate until its measured JSON is provided.`;
  } else {
    const slide=base('Project implementation status',8);
    box(slide,'ready-title','IMPLEMENTED',72,188,470,50,{size:23,bold:true,color:TEAL});
    box(slide,'ready-list','LangGraph ReAct loop and traces\nThree functional tool interfaces\nBuffer, summary and entity memory\n100 genuine HotpotQA questions cached\n21 automated tests passed',72,251,539,285,{size:21});
    box(slide,'pending-title','REQUIRES LOCAL MODEL RUN',690,188,525,50,{size:23,bold:true,color:TEAL});
    box(slide,'pending-list','100-question accuracy values\nTool-call averages on actual queries\nProvider-reported token usage\nMemory comparison measured values',690,251,502,260,{size:21});
    box(slide,'status-footer','No paid API needed. Run the evaluation locally with Ollama to fill the results.',72,580,1132,62,{size:19,color:MUTED});
    slide.speakerNotes.text='No verified 100-question measurements were provided. Run the evaluation before claiming accuracy results.';
  }
}

// 9. Contribution and demo
{
  const slide=base('Independent contributions and demo',9);
  label(slide,'What this project adds',72,178,650);
  box(slide,'novelty','Auditable ReAct decisions and observations\nInterchangeable persistent memory modes\nRestricted numerical execution\nReproducible benchmark with resume support',72,226,1095,215,{size:23});
  label(slide,'Demo on Windows CMD',72,474,700);
  box(slide,'commands','python -m research_agent.cli chat --memory buffer --session viva\npython -m research_agent.cli compare-memory\nstreamlit run app.py',72,527,1120,114,{size:19,color:MUTED});
  slide.speakerNotes.text='These are integration and evaluation contributions, not claims that ReAct, LangGraph or HotpotQA were invented here.';
}

// 10. Closing
{
  const slide=ppt.slides.add();
  slide.background.fill = PAGE;
  box(slide,'thanks','Thank you',75,231,1127,130,{size:60,bold:true,align:'center'});
  box(slide,'questions','Questions and live demonstration',75,380,1127,62,{size:24,color:TEAL,align:'center'});
  slide.speakerNotes.text='Offer a live ReAct question, show the trace, then switch memory modes to demonstrate remembered context.';
}

for(let i=0;i<ppt.slides.items.length;i++){
  const bytes=await ppt.export({slide:ppt.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(draftDir,`slide-${String(i+1).padStart(2,'0')}.png`),
    new Uint8Array(await bytes.arrayBuffer()));
}
const candidatePath=path.join(draftDir,'candidate.pptx');
await (await PresentationFile.exportPptx(ppt)).save(candidatePath);
const { finalizePresentation }=await import(pathToFileURL(
  path.join(skillDir,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({
  workspaceDir:project,
  candidatePath,
  finalPath,
  pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
  integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
  explicitTotalSlideCount:10,
  fontPolicy:{basis:'design',families:[FONT]},
  verifyArtifactToolImport:true,
  receiptPath:path.join(draftDir,`Viva_Presentation_Free_${Date.now()}.validation.json`),
});
console.log('Presentation finalized:',finalPath,JSON.stringify(result).slice(0,900));
