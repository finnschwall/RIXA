const roomName = "room1"
let ws_scheme = window.location.protocol == "https:" ? "wss://" : "ws://";
const websocketURL = ws_scheme + window.location.host + '/ws/chat/' + roomName + '/'

// console.log(websocketURL)
let reconnectTries = 0
const maxTries = 3
let chatSocket

let lastUsedId = -1
let messageHistory = []

let lastUsedDisplay = 0

let chat_enabled = true


initializeWebSocket()
let standalone = false
let standalone_with_chat = false

try {
    $("#userInput").prop("disabled", true)
    const toastJS = bootstrap.Toast.getOrCreateInstance($("#liveToast"))
} catch (e) {

    standalone = true
if ($('#chat_container').length > 0) {
    standalone_with_chat = true
} else {
    standalone_with_chat = false
}
}

let timeout_id = -1


function initializeWebSocket() {

    if (reconnectTries >= maxTries) {

        $("#server_content_displayer").html("<img src='https://http.cat/599'style='height: 100%; display: block; margin: auto'>")
        showMessage(`Server unreachable. No further connection attempts will be made.`, -1, "danger")
        return
    }
    chatSocket = new WebSocket(websocketURL);
    chatSocket.onerror = onErrorHandler;
    chatSocket.onopen = onOpenHandler;
    chatSocket.onmessage = onMessageHandler;
    chatSocket.onclose = onCloseHandler;

}

function clearConversations() {
    resetUI()
    send({"type": "delete_current_tracker"})
    $("#chats").html("")
    messageHistory = []
    lastUsedId = -1

}

// Using a message that looks like this
// {'CMD': "function_call", "plugin_name" : "X", "function_name":"Y", "args": [A1, A2], "kwargs":{"A":"B"}}
// you can call plugin functions on the server
async function send(message) {
    chatSocket.send(JSON.stringify(message));
}


function callFunction(data) {

    let funcName = data["function"];
    let funcArgs = data["arguments"] || [];
    // var funcKWArgs = data["keywordArguments"] || {};
    // window[funcName].apply(args, [])
    console.log("Calling function", funcName, funcArgs)
    window[funcName].apply(this, [].concat(funcArgs));
}


function callPluginFunction(plugin_name, function_name, args, kwargs) {
    send({
        "type": "call_plugin_function",
        "plugin_name": plugin_name,
        "function_name": function_name,
        "args": args,
        "kwargs": kwargs
    })
}


// Call the function with args and kwargs
// this[funcName].apply(this, [].concat(funcArgs).concat([funcKWArgs]));
let firstDisplay = false

function onMessageHandler(e) {
    const data = JSON.parse(e.data);

    if (standalone) {
        try {
            if("role" in data && data["role"] === "tracker_entry" ){

            }
            else{
                messageHandler(data)
            }

        } catch (e) {
            console.error(e)
        }
        if(!standalone_with_chat){
            return
        }
        // return
    }

    if (data["type"] === "f_call") {
        callFunction(data);

    }
    if ("flags" in data) {
        for (let i in data["flags"]) {
            if (data["flags"][i] === "disable_chat") {
                chat_enabled = false
                showBotTyping()
            }
            if (data["flags"][i] === "enable_chat") {
                chat_enabled = true
                hideBotTyping()
                $("#userInput").prop("disabled", false)
            }

        }
    }


    if ("role" in data) {
        if (data["role"] === "status") {
            showMessage(data["content"], data["timeout"], data["level"])
        } else if (data["role"] === "HTML") {
            if(standalone){
                return;
            }
            if (!firstDisplay) {
                firstDisplay = true
                resetUI()
            }
            $(`#content_main_${lastUsedDisplay}`).html(data["content"])
            $(`#content_main_${lastUsedDisplay}`).show()
            lastUsedDisplay++
            lastUsedDisplay %= container_count
            // hideBotTyping();
        } else if (data["role"] === "JSON") {
            lastUsedDisplay = 1
            // $(`#content_main_1`).hide()
            $(`#content_main_0`).jsonViewer(JSON.parse(data["content"]));
        } else if (data["role"] === "flag") {
            if (data["content"] === "show_bot_loading") {
                showBotTyping()
                scrollToBottomOfResults()
            }
        } else if (data["role"] === "variable") {
            if ("datasize" in data) {
                $("#datapoint_selection").prop("max", `${data["datasize"]}`)
                $("#datapoint_selection").prop("placeholder", `Max value: ${data["datasize"]}`)
            } else if ("feature_weights" in data) {
                // $("#a_range").prop("min", data["feature_weights"]["A"])

            }

        } else if (data["role"] === "assistant" || data["role"] === "user") {
            addMessage(data)
        } else if (data["role"] === "tracker_entry") {
            console.info("Received tracker entry", data["tracker"])
            addMessage(data["tracker"])
        } else if (data["role"] === "partial") {
            addPartialMessage(data)
        } else {
            console.error("Unknown role. The following data has been received:")
            console.log(data)

            // hideBotTyping();
            //data["msg_id"] = lastUsedId
            //
            // setBotResponse(data)
        }
    }


}

function resetChatMessages() {
    $("#chats").html("")
    messageHistory = []
    lastUsedId = -1
}

function resetUI() {
    if(standalone){
        return
    }
    for (let i = 0; i < container_count; i++) {
        $(`#content_main_${i}`).html("")
        $(`#content_main_${i}`).show()
    }
    // $(`#content_main_${lastUsedDisplay}`).show()
    // lastUsedDisplay++
    // lastUsedDisplay%=container_count
}


function onErrorHandler(e) {
    hideBotTyping()
    reconnectTries++
    console.error(e)
}

function onOpenHandler(e) {

    if (standalone) {

        try {
            if(standalone_with_chat) {
                $("#userInput").prop("disabled", false)
                send({'type': 'change_setting', 'setting': 'selected_chat_mode', 'value': 'dashboard_chat'})
            }
            connectionEstablishedHandler()


        } catch (e) {
            console.error(e)
        }
        return
    }
    $("#userInput").prop("disabled", false)
    openChat()
    if (reconnectTries > 0) {
        showMessage(`Connection to server re-established`, 2000, "success")
        resetUI()
    }
    resetChatMessages()
    reconnectTries = 0
    hideBotTyping()
    console.info("Connected to server")
}

function onCloseHandler(e) {

    if (e["code"] == 1000) {
        return
    }
    $("#userInput").prop("disabled", true)
    showMessage(`Connection to server lost ${reconnectTries + 1} times. Retrying...`, 2000, "warning")
    setTimeout(initializeWebSocket, 2000);
}


