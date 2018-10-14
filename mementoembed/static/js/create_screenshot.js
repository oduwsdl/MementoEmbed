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

  //Set wait time before screenshotURI
  await page.waitFor(2000);

  await page.screenshot({path: process.env.THUMBNAIL_OUTPUTFILE});

  await browser.close();
})();
