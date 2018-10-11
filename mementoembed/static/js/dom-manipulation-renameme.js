const jsdom = require('jsdom');
var fs = require('fs');

const { JSDOM } = jsdom;

const dom = new JSDOM( process.env.CARD_DATA );

// intentionally global, do not set with var
document = dom.window.document;

require('./mementoembed-v20180806.js');

var output = document.getElementsByTagName('body')[0].innerHTML;

// console.log("==== OUTPUT STARTS HERE ====");

// console.log(output);

// console.log("==== OUTPUT ENDS HERE ====");

fs.writeFile(process.env.OUTPUT_FILE, output, function(err) {

    if (err) {
        return console.log(err);
    }

    console.log("output written to " + process.env.OUTPUT_FILE);
});
