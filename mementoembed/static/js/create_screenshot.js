const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({headless:true});
  const page = await browser.newPage();
  await page.goto(process.env.URIM);
  await page.screenshot({path: process.env.THUMBNAIL_OUTPUTFILE});
  await browser.close();
})();
