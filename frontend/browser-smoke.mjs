import { chromium } from '@playwright/test';
import fs from 'node:fs';
const accounts=JSON.parse(fs.readFileSync('../.runtime/demo-accounts.json','utf8'));
const browser=await chromium.launch();const errors=[];
for (const [role,creds] of Object.entries(accounts)) {
 const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8000');await page.getByLabel('Email address').fill(creds.email);await page.getByLabel('Password',{exact:true}).fill(creds.password);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('navigation').waitFor();
 await page.screenshot({path:`../docs/evidence/${role.toLowerCase()}-dark.png`,fullPage:true});
 if(role==='TRADER'){
  await page.getByRole('button',{name:'Market',exact:true}).click();await page.getByRole('heading',{name:'Place an order',exact:true}).waitFor();await page.screenshot({path:'../docs/evidence/market-dark.png',fullPage:true});
  await page.getByRole('button',{name:'Switch to light theme'}).click();await page.waitForTimeout(250);await page.screenshot({path:'../docs/evidence/market-light.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'../docs/evidence/market-mobile.png',fullPage:true});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile page overflows');
 }
 await context.close();
}
await browser.close();fs.writeFileSync('../docs/evidence/browser-smoke.json',JSON.stringify({roles:3,themes:2,mobileWidth:390,errors},null,2));if(errors.length)throw Error(errors.join('\n'));
