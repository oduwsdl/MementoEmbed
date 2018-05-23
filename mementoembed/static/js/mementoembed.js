
function generate_cards() {

    var me_cards = [].slice.call(document.querySelectorAll('[class^=mementoembed]'));

    for (var i = 0; i < me_cards.length; i++) {

        element = me_cards[i];

        if (element.dataset["processed"] == "true") {
            console.log("alredy processed element for " + element.dataset["urim"]);
        } else {

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

            for (var j = 0; j < me_titles.length; j++) {

                belowtitleHTML = '<div class="me-belowtitle">';

                if (archiveFavicon != null) {
                    belowtitleHTML += '<img src="' + archiveFavicon + '" alt="' + archiveName + '" width="16">&nbsp;&nbsp;';
                }

                if ((collectionName != null) && (collectionURI != null)) {
                    console.log("collection URI is " + collectionURI);
                    console.log("collection name is " + collectionName);
                    belowtitleHTML += 'Member of <a class="me-archive-link" style="text-decoration:none" href="' + collectionURI + '">' + archiveName + 
                        ' Collection '  + collectionName + '</a>';
                } else {
                    if ((archiveName) != null) {
                        console.log("archive name is " + archiveName);
                        belowtitleHTML += 'Preserved by <a class="me-archive-link" href="' + archiveURI + '">' + archiveName + '</a>';
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
                            belowtitleHTML += '<a style="text-decoration:none" href="' + urir + '">' + linkstatusmsg + '</a>';
                        }

                    }

                    belowtitleHTML += "<br /><br />";

                }

                belowtitleHTML += '</div>';

                me_titles[j].insertAdjacentHTML("afterend", belowtitleHTML);

                me_titles[j].style.textAlign = "left";
                me_titles[j].style.color = "rgb(9, 116, 283)";
                me_titles[j].style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
                me_titles[j].style.fontSize = "14px";
                me_titles[j].style.fontWeight = "700";
                me_titles[j].style.lineHeight = "19.6px";
                // me_titles[j].style.textDecorationColor = "rgb(9, 116, 183)";
                // me_titles[j].style.textDecorationLine = "none";
                // me_titles[j].style.textDecoration = "none";
                me_titles[j].style.padding = "0px";
                me_titles[j].style.margin = "0px";
                me_titles[j].style.marginBottom = "1px";
                
            }

            me_textright = element.getElementsByClassName("me-textright");

            for (var j = 0; j < me_textright.length; j++) {

                belowTextRight = '<div class="me-footer">';

                if (originalFavicon != null) {
                    belowTextRight += '&nbsp;&nbsp;<img src="' + originalFavicon + '" width="16" />&nbsp;&nbsp;'
                }

                if ((pubDate != null) && (domain != null)) {
                    uPubDate = pubDate.toUpperCase();
                    uDomain = domain.toUpperCase();
                    belowTextRight += '<a class="me-pubdate" href="' + urim + '">' + uDomain + '&nbsp;&nbsp;@&nbsp;&nbsp;' + uPubDate + '</a>';                
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

    var me_title_links = [].slice.call(document.querySelectorAll('[class~=me-title-link]'));

    me_title_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
    })

    var me_pubdate_links = [].slice.call(document.querySelectorAll('[class~=me-pubdate]'));

    me_pubdate_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
    })

    var me_archive_links = [].slice.call(document.querySelectorAll('[class~=me-archive-link]'));
    
    me_archive_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
    })

    // me_title_links = element.getElementsByClassName("me-title-link");

    // for (var j = 0; i < me.me_title_links; j++) {
    //     me_title_links[j].style.textDecoration = "none";
    //     me_title_links[j].style.textAlign = "left";
    //     me_title_links[j].style.color = "rgb(9, 116, 283)";
    //     me_title_links[j].style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
    //     me_title_links[j].style.fontSize = "14px";
    //     me_title_links[j].style.fontWeight = "700";
    //     me_title_links[j].style.lineHeight = "19.6px";
    //     me_title_links[j].style.padding = "0px";
    //     me_title_links[j].style.margin = "0px";
    //     me_title_links[j].style.marginBottom = "1px";
    // }

    // var links = document.getElementsByTagName("a");

    // for (var j = 0; links.length; j++) {
    //     console.log("working on link " + links[j]);
    //     links[j].style.textDecoration = "none";
    // }

    console.log("all MementoEmbed social cards generated...");
}

generate_cards();