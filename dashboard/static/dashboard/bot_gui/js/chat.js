
let lastMessage = "##help()#"


const converter = new showdown.Converter({
    "simpleLineBreaks": true, "headerLevelStart": 3, "simplifiedAutoLink": true,
    "tables": true, "backslashEscapesHTMLTags": true, "literalMidWordUnderscores":true, "smoothLivePreview":true
})
const pRegex = /<p>(.*)<\/p>/gmi;


function formatForChat(text) {
    text = converter.makeHtml(text);
    text = TexToHTML(text)

    // text = text.replace(pRegex, '$1')
    // text = text.replace(/(?:\r\n|\r|\n)/g, "<br>");
    return text
}

/**
 * removes the bot typing indicator from the chat screen
 */
function hideBotTyping() {
    // $("#botAvatarTyping").fadeOut("fast").remove();
    // $(".botTyping").fadeOut("fast").remove();
    $('#spinner_overlay').css('display', 'none');
}

let botTyping;

/**
 * adds the bot typing indicator from the chat screen
 */
function showBotTyping() {
    scrollToBottomOfResults();
    botTyping = `<!--<img class="botAvatar" id="botAvatarTyping" src=${getPath("./static/img/botAvatar.png")}/><div class="botTyping"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div>-->`;
    $("#userInput").prop("disabled",true)
    // $(botTyping).appendTo(".chats");
    // $(".botTyping").show();
    chat_enabled = false
     $('#spinner_overlay').css('display', 'inline-flex');
}

/**
 * scroll to the bottom of the chats after new message has been added to chat
 */
function scrollToBottomOfResults() {
    const terminalResultsDiv = document.getElementById("chats");
    terminalResultsDiv.scrollTop = terminalResultsDiv.scrollHeight;
}
let updateableMessage = false
let partialID = 0
function addPartialMessage(content, fmt=true) {
    let msg_id =-100
    let message = content["content"]
    if(fmt) {
        message = formatForChat(message)
    }
    let botResponse = `<img class="botAvatar" src=${getPath("./static/img/botAvatar.png")}><span id="sub_id_span_${msg_id}" class="botMsg">${message}</span><div class="clearfix"></div>`;
    botResponse = `<div id="sub_id_parent_${msg_id}">${botResponse}</div>`;
    $(botResponse).appendTo(".chats").hide().fadeIn(1000);
    $("#userInput").focus();
    scrollToBottomOfResults()
    updateableMessage = true
}



function addMessage(content, fmt=true) {
    messageHistory.push(content)
    lastUsedId = content["index"]
    let msg_id = content["index"]
    let message = content["content"]
    if("translated_content" in content){
        message = content["translated_content"]
    }
    if(fmt) {
        message = formatForChat(message)
    }
    if (content["role"] == "user") {
        const user_response = `<img class="userAvatar" src=${getPath('./static/img/userAvatar.jpg')}><div id="sub_id_span_${msg_id}" class="userMsg">${message}</div><div class="clearfix"></div>`;
        $(user_response).appendTo(".chats").show("slow");
        $("#userInput").val("");
        scrollToBottomOfResults();
    } else {
        if(updateableMessage){
            //remove partial
            $("#sub_id_parent_-100").remove()
        }
        let botResponse = `<img class="botAvatar" src=${getPath("./static/img/botAvatar.png")}><span id="sub_id_span_${msg_id}" class="botMsg">${message}</span><div class="clearfix"></div>`;
        botResponse = `<div id="sub_id_parent_${msg_id}">${botResponse}</div>`;
        $(botResponse).appendTo(".chats").hide().fadeIn(1000);
        $("#userInput").focus();
        scrollToBottomOfResults()
    }
}



function userWantsSend(e) {
    let text = $("#userInput").val();

    if (text === "" || $.trim(text) === "") {

        e.preventDefault();
        return false;
    }
    lastMessage = text
    // text = TexToHTML(text)
    let fmt = true
    if (text.startsWith("###")) {
        text = text.substring(3, text.length)
        let toSend = {"type":"usr_msg", 'content': text, "msg_id": lastUsedId, "role": "user"}
        addMessage(toSend)
        e.preventDefault();
        return false;
    }

    else if (text.startsWith("##")) {
        // text = text.substring(2, text.length)
        // text = text.substring(0, text.length - 1)
        let toSend = {"type":"execute_plugin_code",'content': text, "msg_id": lastUsedId, "role": "user"}
        addMessage(toSend, fmt=false)
        send(toSend);
        e.preventDefault();
        return false;

    }
    lastUsedId += 1

    let toSend = {"type":"usr_msg", 'content': text, "index": lastUsedId, "role": "user"}
    // let toSend = {'content': text, "msg_id": lastUsedId, "role": "user"}
    addMessage(toSend, fmt)
    messageHistory.push(toSend)
    send(toSend);
    showBotTyping()
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
    //get up key
    if (e.originalEvent.code==="ArrowUp") {
        $("#userInput").val(lastMessage)
    }
    if (e.originalEvent.code==="ArrowDown") {
        $("#userInput").val("")
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
