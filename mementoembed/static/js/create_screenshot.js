const puppeteer = require('puppeteer');


(async () => {

  const browser = await puppeteer.launch({
    headless: true, 
    ignoreHTTPSErrors: true,
    args:['--no-sandbox']}
    );

  const page = await browser.newPage();

  await page.setUserAgent(process.env.USER_AGENT);

  await page.setViewport({
      width: parseInt(process.env.VIEWPORT_WIDTH), 
      height: parseInt(process.env.VIEWPORT_HEIGHT)
    });

  await page.goto(
    process.env.URIM, {
      waitUntil: 'domcontentloaded',
      timeout: 5000000
    });

  //Set wait time before screenshotURI - equivalent to 'networkidle0'
  await Promise.all([
    waitForNetworkIdle(page, 60000, 0), 
  ]);

  await page.screenshot({path: process.env.THUMBNAIL_OUTPUTFILE});

  await browser.close();
})();

//Functions required to control the network idle time 

function waitForNetworkIdle(page, timeout, maxInflightRequests = 0) {
  page.on('request', onRequestStarted);
  page.on('requestfinished', onRequestFinished);
  page.on('requestfailed', onRequestFinished);

  let inflight = 0;
  let fulfill;
  let promise = new Promise(x => fulfill = x);
  let timeoutId = setTimeout(onTimeoutDone, timeout);
  return promise;

  function onTimeoutDone() {
    page.removeListener('request', onRequestStarted);
    page.removeListener('requestfinished', onRequestFinished);
    page.removeListener('requestfailed', onRequestFinished);
    fulfill();
  }

  function onRequestStarted() {
    ++inflight;
    if (inflight > maxInflightRequests)
      clearTimeout(timeoutId);
  }
  
  function onRequestFinished() {
    if (inflight === 0)
      return;
    --inflight;
    if (inflight === maxInflightRequests)
      timeoutId = setTimeout(onTimeoutDone, timeout);
  }
}
