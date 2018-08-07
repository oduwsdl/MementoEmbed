
function generate_cards() {

    var me_cards = [].slice.call(document.querySelectorAll('[class^=mementoembed]'));

    for (var i = 0; i < me_cards.length; i++) {

        element = me_cards[i];
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
        element.style.width = "445px";
        element.style.height = "200px";
        element.style.lineHeight = "19.6px";

        if (element.dataset["processed"] == "true") {
            console.log("alredy processed element for " + element.dataset["urim"]);
        } else {

            urim = element.dataset["versionurl"];
            urir = element.dataset["originalurl"];
            image = element.dataset["image"];
            collectionid = element.dataset["archiveCollectionId"];
            archiveFavicon = element.dataset["archiveFavicon"];
            archiveURI = element.dataset["archiveUri"];
            collectionURI = element.dataset["archiveCollectionUri"];
            collectionName = element.dataset["archiveCollectionName"];
            archiveName = element.dataset["archiveName"];
            originalFavicon = element.dataset["originalFavicon"];
            creationDate = element.dataset["surrogateCreationDate"];
            pubDate = element.dataset["versiondate"];
            domain = element.dataset["originalDomain"];
            linkStatus = element.dataset["originalLinkStatus"];

            console.log("pubDate is " + pubDate);
            console.log("versionurl is " + urim);
            console.log("originalurl is " + urir);
            
            meImageHTML = '';

            if ( (image != null) && (image != "null" ) ) {
                meImageHTML += '<div class="me-image"><img style="max-width: 96px; max-height: 96px;" src="'+ image + '" /></div>';
            }            

            element.insertAdjacentHTML("afterbegin", meImageHTML);

            me_titles = element.getElementsByClassName("me-title");

            for (var j = 0; j < me_titles.length; j++) {

                belowtitleHTML = '<div class="me-belowtitle">';

                if (archiveFavicon != null) {
                    belowtitleHTML += '<img class="me-favicon" src="' + archiveFavicon + '" alt="' + archiveName + '" width="16">&nbsp;&nbsp;';
                }

                if ((archiveName) != null) {

                    console.log("archive name is " + archiveName);
                    belowtitleHTML += 'Preserved by <a class="me-archive-link" href="' + archiveURI + '">' + archiveName + '</a>';

                    console.log("collection URI is " + collectionURI);
                    console.log("collection name is " + collectionName);
                    

                    if ( (collectionName != null) && (collectionURI != null) 
                        && (collectionURI != "None") && (collectionName != "None")
                        && (collectionName != "null") && (collectionURI != "null") ) {
                        belowtitleHTML += '<br />Member of the Collection <a class="me-archive-link" style="text-decoration:none" href="' +
                             collectionURI + '">' + collectionName + '</a>';
                    }        

                }

                belowtitleHTML += '</div><br />';

                me_titles[j].insertAdjacentHTML("afterend", belowtitleHTML);

                me_titles[j].style.textAlign = "left";
                me_titles[j].style.color = "rgb(9, 116, 283)";
                me_titles[j].style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
                me_titles[j].style.fontSize = "14px";
                me_titles[j].style.fontWeight = "700";
                me_titles[j].style.lineHeight = "19.6px";
                me_titles[j].style.padding = "0px";
                me_titles[j].style.margin = "0px";
                me_titles[j].style.marginBottom = "1px";
                me_titles[j].style.background = "#ffffff no-repeat fixed center";
                
            }

            me_textright = element.getElementsByClassName("me-textright");

            for (var j = 0; j < me_textright.length; j++) {

                belowTextRight = '<div class="me-footer">';

                if (originalFavicon != null) {
                    belowTextRight += '&nbsp;&nbsp;<img class="me-favicon" src="' + originalFavicon + '" width="16" />&nbsp;&nbsp;'
                }

                if ((pubDate != null) && (domain != null)) {
                    uPubDate = pubDate.toUpperCase();
                    uDomain = domain.toUpperCase();
                    belowTextRight += '<a class="me-pubdate" ' +
                        'data-originalurl="' + urir + '" data-versiondate="' + pubDate +'"' +
                        'href="' + urim + '">' 
                        + uDomain + '&nbsp;&nbsp;@&nbsp;&nbsp;' + uPubDate + '</a>';                
                }

                // urldate, urltime, tzone = pubdate.split(" ");
                datetime_components = pubDate.split("T");
                date_components = datetime_components[0].split("-");
                time_components = datetime_components[1].split(":");
                
                datestring = date_components[0] + date_components[1] + date_components[2] + time_components[0] + time_components[1] + time_components[2];
                belowTextRight += '<br > &nbsp; <a class="me-allversions" href="http://timetravel.mementoweb.org/list/' + datestring + '/' + urir + '">Other Versions</a>';

                if (linkStatus != null) {
                    belowTextRight += "&nbsp;";

                    if (linkStatus == "Rotten") {
                        
                        belowTextRight += ' || <span style="color: #a8201a;">'
                        belowTextRight += "Current version unavailable";
                        belowTextRight += '</span>';

                    } else {

                        if (urir != null) {
                            belowTextRight += ' || <a class="me-livestatus" data-versionurl="' + 
                                urim + '" data-versiondate="' + pubDate + '" href="' + 
                                urir + '">Current version</a>';
                        }

                    }

                    me_textright[j].insertAdjacentHTML("afterend", belowTextRight);

                }

                belowTextRight += '</div>';

                console.log("done with snippet...");

            }

            element.setAttribute("data-processed", "true");
        }

    }

    var me_images = [].slice.call(document.querySelectorAll('[class^=me-image]'));

    me_images.forEach(element => {
        element.style.color = "rgb(51, 51, 51)";
        element.style.display = "inline";
        element.style.float = "left";
        element.style.margin = "0";
        element.style.padding = "0";
        element.style.marginBottom = "5px";
        element.style.marginLeft = "0px";
        element.style.marginRight = "30px";
        element.style.maxHeight = "96px";
        element.style.maxWidth = "96px";
        element.style.padding = "1px";
        element.style.width = "96px";
        element.style.background = "#ffffff no-repeat fixed center";
    });

    var me_textright = [].slice.call(document.querySelectorAll('[class^=me-textright]'));

    // me_textright.forEach(element =>{
    //     element.style.clear = "right";
    //     element.style.overflow = "auto";
    // });

    var me_belowtitle = [].slice.call(document.querySelectorAll('[class~=me-belowtitle]'));

    me_belowtitle.forEach(element =>{
        element.style.color = "rgb(153, 153, 153)";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontSize = "10px";
        element.style.textAlign = "left";
        element.style.margin = "0";
        element.style.padding = "0";
        element.style.background = "#ffffff no-repeat fixed center";
    });

    var me_snippets = [].slice.call(document.querySelectorAll('[class^=me-snippet]'));

    me_snippets.forEach(element =>{
        element.style.color = "rgb(09, 116, 283)";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontSize = "12px";
        element.style.lineHeight = "18px";
        element.style.textAlign = "left";
        element.style.margin = "0";
        element.style.padding = "0";
        element.style.color = "rgb(51, 51, 51)";
        element.style.background = "#ffffff no-repeat fixed center";
    });

    var me_footer = [].slice.call(document.querySelectorAll('[class~=me-footer]'));

    me_footer.forEach(element =>{
        element.style.color = "rgb(153, 153, 153)";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontSize = "10px";
        element.style.textAlign = "left";
        element.style.margin = "0";
        element.style.padding = "0";
        element.style.marginTop = "10px";
        element.style.paddingTop = "10px";
        element.style.background = "#ffffff no-repeat fixed center";
    });

    var me_title_links = [].slice.call(document.querySelectorAll('[class~=me-title-link]'));

    // data-originalurl="{{ urir }}"
    // data-versiondate="{{ memento_datetime }}"


    me_title_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
        element.setAttribute("data-originalurl", urir);
        element.setAttribute("data-versiondate", pubDate);
    });

    var me_pubdate_links = [].slice.call(document.querySelectorAll('[class~=me-pubdate]'));

    me_pubdate_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
    });

    var me_allversions = [].slice.call(document.querySelectorAll('[class~=me-allversions]'));

    me_allversions.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
    });

    var me_livestatus_links = [].slice.call(document.querySelectorAll('[class~=me-livestatus]'));

    me_livestatus_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
    });

    var me_archive_links = [].slice.call(document.querySelectorAll('[class~=me-archive-link]'));
    
    me_archive_links.forEach(element =>{
        element.style.textDecoration = "none";
        element.style.color = "rgb(9, 116, 283)";
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
    });

    var me_favicon_links = [].slice.call(document.querySelectorAll('[class~=me-favicon]'));

    me_favicon_links.forEach(element =>{
        element.style.background = "#ffffff no-repeat fixed center";
        element.style.margin = "0";
        element.style.padding = "0";
        element.style.fontSize = "10px";
        element.style.borderWidth = "0";
        element.style.borderStyle = "none";
        element.style.lineHeight = "15px";
        element.style.borderImageRepeat = "initial";
        element.style.borderImageWidth = "0";
        element.style.fontFamily = '"Museo Sans", "Helvetica Neue", sans-serif';
        element.style.fontStretch = "initial";
        element.style.fontWeight = "400";
        element.style.verticalAlign = "middle";
    });

    console.log("all MementoEmbed social cards generated...");
}

generate_cards();
