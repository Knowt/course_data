// Solves the AWS WAF JS challenge that Acalog (Modern Campus) catalogs sit behind and prints the cookies.
// usage: NODE_PATH=<goliath>/node_modules node waf_token.js <url>
const { chromium } = require("playwright");

const UA =
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

(async () => {
    const url = process.argv[2];
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ userAgent: UA });
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: "networkidle", timeout: 90000 });
    for (let i = 0; i < 20; i++) {
        const cookies = await ctx.cookies();
        if (cookies.some(c => c.name === "aws-waf-token")) break;
        await page.waitForTimeout(1000);
    }
    const cookies = await ctx.cookies();
    const html = await page.content();
    console.log(JSON.stringify({ cookie: cookies.map(c => `${c.name}=${c.value}`).join("; "), coids: (html.match(/coid=\d+/g) || []).length }));
    await browser.close();
})();
