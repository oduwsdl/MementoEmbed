
function generate_cards() {
    var me_cards = [].slice.call(document.querySelectorAll('[class^=mementoembed]'));

    console.log("me_cards length: " + me_cards.length);

    for (var i = 0; i < me_cards.length; i++) {

    // me_cards.forEach(element => {

        element = me_cards[i];

        if (element.dataset["processed"] == "true") {
            console.log("alredy processed element for " + element.dataset["urim"]);
        } else {
            console.log("working on card " + element);

            console.log("processed: " + element.me_processed);

            urim = element.dataset["urim"];
            urir = element.dataset["urir"];
            image = element.dataset["image"];
            collectionid = element.dataset["archiveCollectionId"];
            archiveFavicon = element.dataset["archiveFavicon"];
            archiveURI = element.dataset["archiveUri"];
            collectionURI = element.dataset["archiveCollectionUri"];
            collectionName = element.dataset["archiveCollectionName"];
            archiveName = element.dataset["archiveName"];
            originalFavicon = element.dataset["originalFavicon"];
            creationDate = element.dataset["surrogateCreationDate"];
            pubDate = element.dataset["date"];
            domain = element.dataset["originalDomain"];
            linkStatus = element.dataset["originalLinkStatus"];
            
            meImageHTML = '<div class="me-image"><img style="max-width: 96px; max-height: 96px;" src="'+ image + '" /></div>';

            element.insertAdjacentHTML("afterbegin", meImageHTML);

            me_titles = element.getElementsByClassName("me-title");

            console.log("me_titles length:  " + me_titles.length);

            for (var j = 0; j < me_titles.length; j++) {

                console.log("working on title " + j + ": " + me_titles[j]);

                belowtitleHTML = '<div class="me-belowtitle">';

                if ((archiveFavicon != null) && (archiveName != null)) {
                    belowtitleHTML += '<img src="' + archiveFavicon + '" alt="' + archiveName + '" width="16">&nbsp;&nbsp;';
                }

                

                if ((collectionName != null) && (collectionURI != null)) {
                    console.log("collection URI is " + collectionURI);
                    console.log("collection name is " + collectionName);
                    belowtitleHTML += 'Member of <a href="' + collectionURI + '">' + archiveName + 
                        ' Collection '  + collectionName + '</a>';
                } else {
                    if ((archiveName) != null) {
                        console.log("archive name is " + archiveName);
                        belowtitleHTML += 'Preserved by <a href="' + archiveURI + '">' + archiveName + '</a>';
                    }
                }

                if (linkStatus != null) {
                    belowtitleHTML += "<br /><br />";

                    if (linkStatus == "Rotten") {
                        
                        belowtitleHTML += '<span style="color: #a8201a;">'
                        belowtitleHTML += "Live web resource is Unavailable";
                        belowtitleHTML += '</span>';


                    } else {
                        linkstatusmsg = '<span style="color: #143642;">'
                        linkstatusmsg += "Live web resource is Available";
                        linkstatusmsg += '</span>';                    

                        if (urir != null) {
                            belowtitleHTML += '<a href="' + urir + '">' + linkstatusmsg + '</a>';
                        }

                    }

                    belowtitleHTML += "<br /><br />";

                }

                belowtitleHTML += '</div>';
                
                console.log("inserting HTML afterend: " + belowtitleHTML);

                me_titles[j].insertAdjacentHTML("afterend", belowtitleHTML);

                me_titles[j].style.textAlign = "left";
                me_titles[j].style.color = "rgb(09, 116, 283)";
                me_titles[j].style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
                me_titles[j].style.fontSize = "14px";
                me_titles[j].style.fontWeight = "700";
                me_titles[j].style.lineHeight = "19.6px";
                me_titles[j].style.textAlign = "left";
                me_titles[j].style.textDecorationColor = "rgb(0, 116, 183)";
                me_titles[j].style.textDecorationLine = "none";
                me_titles[j].style.textDecorationStyle = "solid";
                me_titles[j].style.padding = "0px";
                me_titles[j].style.margin = "0px";
                me_titles[j].style.marginBottom = "1px";
                
            }

            me_textright = element.getElementsByClassName("me-textright");

            for (var j = 0; j < me_textright.length; j++) {

                console.log("working on snippet " + j + ": " + me_textright[j]);
                console.log("really working...");

                belowTextRight = '<div class="me-footer">';

                if (originalFavicon != null) {
                    belowTextRight += '&nbsp;&nbsp;<img src="' + originalFavicon + '" width="16" />&nbsp;&nbsp;'
                }

                if ((pubDate != null) && (domain != null)) {
                    uPubDate = pubDate.toUpperCase();
                    uDomain = domain.toUpperCase();
                    belowTextRight += '<a href="' + urim + '">' + uDomain + '&nbsp;&nbsp;@&nbsp;&nbsp;' + uPubDate + '</a>';                
                }

                belowTextRight += '</div>';

                me_textright[j].insertAdjacentHTML("afterend", belowTextRight);

                console.log("done with snippet...");

            }

            element.setAttribute("data-processed", "true");
        }

    }

    var me_images = [].slice.call(document.querySelectorAll('[class^=me-image]'));

    me_images.forEach(element => {
        element.style.borderColor = "rgb(221, 221, 221)";
        element.style.borderStyle = "solid";
        element.style.borderWidth = "1px";
        element.style.color = "rgb(51, 51, 51)";
        element.style.display = "inline";
        element.style.float = "left";
        element.style.marginBottom = "5px";
        element.style.marginLeft = "0px";
        element.style.marginRight = "30px";
        element.style.marginTop = "0px";
        element.style.maxHeight = "96px";
        element.style.maxWidth = "96px";
        element.style.padding = "1px";
        element.style.width = "96px";
    });

    var me_textright = [].slice.call(document.querySelectorAll('[class^=me-textright]'));

    me_textright.forEach(element =>{
        element.style.clear = "right";
    });

    var me_belowtitle = [].slice.call(document.querySelectorAll('[class~=me-belowtitle]'));

    me_belowtitle.forEach(element =>{
        element.style.color = "rgb(153, 153, 153)";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontSize = "10px";
        element.style.textAlign = "left";
        element.style.padding = "0px";
    });

    var me_snippets = [].slice.call(document.querySelectorAll('[class^=me-snippet]'));

    me_snippets.forEach(element =>{
        element.style.color = "rgb(09, 116, 283)";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontSize = "12px";
        element.style.lineHeight = "18px";
        element.style.textAlign = "left";
        element.style.padding = "0px";
        element.style.margin = "0px";
        element.style.color = "rgb(51, 51, 51)";
    });

    var me_footer = [].slice.call(document.querySelectorAll('[class~=me-footer]'));

    me_footer.forEach(element =>{
        element.style.color = "rgb(153, 153, 153)";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontSize = "10px";
        element.style.textAlign = "left";
        element.style.marginTop = "10px";
        element.style.paddingTop = "10px";
    });

    console.log("all MementoEmbed social cards generated...");
}

generate_cards();