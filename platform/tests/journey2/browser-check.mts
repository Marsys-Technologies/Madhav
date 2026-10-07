import { chromium } from '@playwright/test'
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
const { assembleAcharyaReadingReceipt } = createRequire(import.meta.url)('../../src/lib/pariprashna/receipt/assemble') as typeof import('../../src/lib/pariprashna/receipt/assemble')
const { AiConsoleError } = createRequire(import.meta.url)('../../src/lib/ai-console/errors') as typeof import('../../src/lib/ai-console/errors')
import { mkdir, writeFile } from 'node:fs/promises'
const out=process.env.JOURNEY2_BROWSER_OUTPUT ?? '../verification_artifacts/journey2-audit/browser'
await mkdir(out,{recursive:true})
const browser=await chromium.launch({headless:true})
const results: unknown[]=[]
const errors:string[]=[]
const chart='22222222-2222-4222-8222-222222222222',thread='11111111-1111-4111-8111-111111111111',answer='44444444-4444-4444-8444-444444444444'
const receipt=assembleAcharyaReadingReceipt({turnId:answer,conversationId:thread,chartId:chart,now:new Date('2026-10-01T00:00:01Z'),plan:{domains:[]},committedBlocks:[],accumulatedText:'Saved canonical answer',citationsFound:[],citationRewriteEnabled:false,resolvedCitations:[],citationHallucinationCount:0,completenessReceipt:null,safetyDecision:undefined,validToolResults:[],provenanceStamp:{build_id:null,priors_version:'synthetic',formula_versions:{salience_formula_ver:null},ranking_config:{mode:'synthetic'},now_context_date:'2026-10-01',computed_at:'2026-10-01T00:00:01Z'}})

try {
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
  const context=await browser.newContext({viewport})
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message))
  const response=await page.goto('http://127.0.0.1:60261/share/journey2-browser-ready')
  assert.equal(response?.status(),200)
  await page.getByText('Canonical first answer',{exact:false}).waitFor()
  const contrast=await page.locator('main').evaluate(main=>{
   const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d')!
   const values:number[]=[]
   for(const color of [getComputedStyle(main.querySelector('section .prose')!).color,getComputedStyle(main).backgroundColor]) {
    ctx.clearRect(0,0,1,1);ctx.fillStyle=color;ctx.fillRect(0,0,1,1)
    const pixel=ctx.getImageData(0,0,1,1).data,channels:number[]=[]
    for(let i=0;i<3;i++){const c=pixel[i]/255;channels.push(c<=0.04045?c/12.92:((c+0.055)/1.055)**2.4)}
    values.push(channels[0]*0.2126+channels[1]*0.7152+channels[2]*0.0722)
   }
   const [foreground,background]=values
   return (Math.max(foreground,background)+0.05)/(Math.min(foreground,background)+0.05)
  })
  assert(contrast>=4.5,`public reading contrast ${contrast}`)
  const body=await page.locator('body').innerText()
  for(const privateText of ['PRIVATE_METHOD','OPTIONAL_REASONING','PRIVATE_TOOL','Later answer','Second question','PRIVATE_FIRST_QUESTION_TOPIC']) assert(!body.includes(privateText),privateText)
  await page.getByRole('heading',{name:'Consultation answer',exact:true}).waitFor()
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'public mobile overflow')
  await page.screenshot({path:`${out}/shared-${viewport.width}.png`,fullPage:true})
  await page.getByRole('link',{name:'Open print view'}).click()
  await page.getByRole('button',{name:'Print / Save PDF'}).waitFor()
  await page.getByRole('heading',{name:'Consultation answer',exact:true}).waitFor()
  assert(!(await page.locator('body').innerText()).includes('PRIVATE_FIRST_QUESTION_TOPIC'))
  const pdf=await page.pdf({path:`${out}/selected-answer-${viewport.width}.pdf`,format:'A4',printBackground:false})
  assert(pdf.length>2000)
  await page.emulateMedia({media:'print'})
  assert.equal(await page.getByRole('button',{name:'Print / Save PDF'}).isVisible(),false)
  await page.emulateMedia({media:'screen'})
  await page.goto('http://127.0.0.1:60261/share/journey2-browser-expired')
  await page.getByRole('heading',{name:'This reading is no longer available'}).waitFor()
  assert(!(await page.locator('body').innerText()).includes('Canonical first answer'))
  assert.equal((await page.goto('http://127.0.0.1:60261/share/journey2-no-such-link'))?.status(),404)
  results.push({viewport,actualNextPublicShare:true,readingContrast:contrast,selectedExchange:true,privacy:true,printPdf:true,expired:true,missing:true})
  // The component host exercises real live transport and UI against labelled HTTP fixtures.
  const posts: {url:string;body:unknown}[]=[]
  await page.route('**/api/**',async route=>{
   const req=route.request(),url=req.url()
   if(req.method()==='POST' && url.endsWith('/api/pariprashna')) { posts.push({url,body:req.postDataJSON()}); return route.fulfill({status:400,json:new AiConsoleError('AI_DEFAULT_REQUIRED').toJSON()}) }
   if(req.method()==='PATCH') {posts.push({url,body:req.postDataJSON()});return route.fulfill({json:{ok:true}})}
   if(url.endsWith(`/api/conversations/${thread}/consultation`)) return route.fulfill({json:{conversation:{id:thread,chart_id:chart,title:'Synthetic saved consultation',tagged:false},readOnly:false,messages:[
    {id:'33333333-3333-4333-8333-333333333333',role:'user',created_at:'2026-10-01T00:00:00Z',schema_version:1,tagged:false,parts_json:[],metadata_json:{},canonical_parts:[{kind:'text',body:{text:'Original question'}}]},
    {id:answer,role:'assistant',created_at:'2026-10-01T00:00:01Z',schema_version:1,tagged:false,parts_json:[],metadata_json:{},canonical_parts:[{kind:'text',body:{text:'Saved canonical answer'}}]}]}})
   if(url.includes('/share')) {if(req.method()==='POST'){posts.push({url,body:req.postDataJSON()});return route.fulfill({json:{slug:'synthetic-selected-answer'}})}return route.fulfill({json:{share:null}})}
   return route.fulfill({json:{conversations:[],personas:[]}})
  })
  await page.goto('http://127.0.0.1:60262/tests/journey2/browser/index.html')
  await page.getByText('Saved canonical answer',{exact:true}).waitFor()
  await page.getByRole('button',{name:'Tag answer',exact:true}).click()
  await page.getByRole('button',{name:'Tagged answer',exact:true}).waitFor()
  assert(posts.some(p=>JSON.stringify(p.body).includes(answer)))
  await page.getByRole('button',{name:'Share this answer',exact:true}).click()
  await page.getByTestId('v2-share-create-btn').click()
  await page.getByText(/synthetic-selected-answer/).waitFor()
  assert(posts.some(p=>p.url.includes('/share') && (p.body as {messageId?:string}).messageId===answer))
  await page.keyboard.press('Escape')
  const ask=page.getByRole('textbox',{name:'Ask the chart'})
  await ask.fill('Follow-up question')
  await page.getByRole('button',{name:'Ask',exact:true}).click()
  await page.getByText('Choose a default in AI Console before continuing.').waitFor()
  await page.getByRole('link',{name:'Open AI Console',exact:true}).waitFor()
  assert(!(await page.locator('body').innerText()).includes('RAW_SECRET_MUST_NOT_RENDER'))
  assert(posts.some(p=>(p.body as {conversationId?:string}).conversationId===thread))
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'consultation mobile overflow')
  const box=await ask.boundingBox();assert(box && box.y+box.height<=viewport.height,'composer outside viewport')
  await page.screenshot({path:`${out}/consultation-${viewport.width}.png`,fullPage:true})
  results.push({viewport,syntheticHttpComponentHost:true,sourceThreadRestored:true,answerTagScope:true,selectedAnswerShareScope:true,followupConversationId:true,safeAiRecovery:true,noHorizontalOverflow:true,composerVisible:true})
  await context.close()
 }
 assert.deepEqual(errors,[])
 await writeFile(`${out}/results.json`,JSON.stringify({results,pageErrors:errors},null,2))
 console.log(JSON.stringify({passed:results.length,resultsPath:`${out}/results.json`}))
} finally {await browser.close()}
