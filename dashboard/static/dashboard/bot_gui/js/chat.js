const converter = new showdown.Converter({
    "simpleLineBreaks": true, "headerLevelStart": 3, "simplifiedAutoLink": true,
    "tables": true, "backslashEscapesHTMLTags": true, "literalMidWordUnderscores":true, "smoothLivePreview":true
})
const pRegex = /<p>(.*)<\/p>/gmi;


function formatForChat(text) {
    text = converter.makeHtml(text);
    text = text.replace(pRegex, '$1')
    text = text.replace(/(?:\r\n|\r|\n)/g, "<br>");
    text = TexToHTML(text)
    return text
}

/**
 * removes the bot typing indicator from the chat screen
 */
function hideBotTyping() {
    $("#botAvatarTyping").fadeOut("fast").remove();
    $(".botTyping").fadeOut("fast").remove();
}

/**
 * adds the bot typing indicator from the chat screen
 */
function showBotTyping() {
    scrollToBottomOfResults();
    const botTyping = `<img class="botAvatar" id="botAvatarTyping" src=${getPath("./static/img/sara_avatar.png")}/><div class="botTyping"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div>`;
    $(botTyping).appendTo(".chats");
    $(".botTyping").show();

}


/**
 * scroll to the bottom of the chats after new message has been added to chat
 */
function scrollToBottomOfResults() {
    const terminalResultsDiv = document.getElementById("chats");
    terminalResultsDiv.scrollTop = terminalResultsDiv.scrollHeight;
}


function addMessage(content, fmt=true) {
    messageHistory.push(content)
    let msg_id = content["msg_id"]
    let message = content["content"]
    if(fmt) {
        message = formatForChat(message)
    }
    if (content["role"] == "user") {
        const user_response = `<img class="userAvatar" src=${getPath('./static/img/userAvatar.jpg')}><div id="sub_id_span_${msg_id}" class="userMsg">${message}</div><div class="clearfix"></div>`;
        $(user_response).appendTo(".chats").show("slow");
        $("#userInput").val("");
        scrollToBottomOfResults();
    } else {
        let botResponse = `<img class="botAvatar" src=${getPath("./static/img/sara_avatar.png")}/><span id="sub_id_span_${msg_id}" class="botMsg">${message}</span><div class="clearfix"></div>`;
        botResponse = `<div id="sub_id_parent_${msg_id}">${botResponse}</div>`;
        $(botResponse).appendTo(".chats").hide().fadeIn(1000);
        $("#userInput").focus();
    }
}



function userWantsSend(e) {
    let text = $("#userInput").val();
    if (text === "" || $.trim(text) === "") {

        e.preventDefault();
        return false;
    }

    // text = TexToHTML(text)
    let fmt = true
    if (text.startsWith("###")) {
        text = text.substring(3, text.length)
        let toSend = {'content': text, "msg_id": lastUsedId, "role": "user"}
        addMessage(toSend)
        e.preventDefault();
        return false;
    }

    else if (text.startsWith("##")) {
        fmt=false

    }
    lastUsedId += 1


    // setUserResponse(text, lastUsedId);
    // showBotTyping()
    let toSend = {'content': text, "msg_id": lastUsedId, "role": "user"}
    addMessage(toSend, fmt)
    messageHistory.push(toSend)
    send(toSend);
    e.preventDefault();
    return false;
}

/**
 * if user hits enter or send button
 * */
$("#userInput").on("keyup keypress", (e) => {
    const keyCode = e.keyCode || e.which;
    if (keyCode === 13 && !e.originalEvent.shiftKey) {
        userWantsSend(e)
    }
    return true;
});

$("#sendButton").on("click", (e) => {
    userWantsSend(e)
});

const texPatterns = [/\$\$([^\$]*)\$\$/g, /\$([^\$]*)\$/g, /\\\(([^\\]+)\\\)/g, /\\\[(.+?)\\\]/g]

function TexToHTML(str) {
    for (let i in texPatterns) {
        str = str.replace(texPatterns[i], function (match, captured) {
            let processed = window.LatexToMathML(captured)
            return processed;
        });
    }
    return str
}
