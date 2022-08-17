$(window).on('load', function() {
    // let doc2 = $('#lesson-topic-0').html();
    
    // $('#lesson-topic-0').html(doc2.replaceAll("&lt;", "<").replaceAll('&gt;', '>'))
    let docs = document.getElementsByClassName("p-topic-card-body");
    for (let i = 0; i < docs.length; i++) {
        let item_id = docs[i].id;
        let text_replaced = docs[i].innerHTML.replaceAll("&lt;", "<").replaceAll('&gt;', '>');
        text_replaced = text_replaced.replace(/<script/ig , "").replace(/script>/ig, "");
        $('#'+item_id).html(text_replaced);
    }
});

