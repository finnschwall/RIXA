$("#profile_pic").toggle();
$(".widget").toggle();

let msgId=-1


function uploadTracker(tracker_yaml){
    resetChatMessages()
    send({"type":"upload_tracker", "tracker": tracker_yaml})
}

function fakeMessage(msg, role="assistant"){
    // role can be user or assistant
    send({"type":"fake_message", "content": msg, "role": role})
}

function submitBugReport(){
    let bugReport = $("#bugReportContent").val()
    if(bugReport.length < 10){
        showMessage("Please enter a more detailed report", 5000, "warning")
        return
    }

    let browserInfo = navigator.userAgent;
    let platform = navigator.platform;
    let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    let screenResolution = window.screen.width + "x" + window.screen.height;
    let locale = navigator.language;
    let onlineStatus = navigator.onLine;
    let cookiesEnabled = navigator.cookieEnabled;

    // Create an object to hold all the information
    let reportInfo = {
        "type": "bug_report",
        "report": bugReport,
        "browserInfo": browserInfo,
        "platform": platform,
        "timezone": timezone,
        "screenResolution": screenResolution,
        "locale": locale,
        "onlineStatus": onlineStatus,
        "cookiesEnabled": cookiesEnabled,
    };

    input = document.getElementById('bugReportAttachment');
    const file = input.files[0];
   if (file) {
        if (!file.type.match('image.*')) {
               alert("Please select an image file.");
               input.value = ''; // Reset the file input
       }
       const reader = new FileReader();
       reader.onload = function(event) {
               const imgData = event.target.result;
               reportInfo["image"] = imgData;
               send(reportInfo)
           };
           reader.readAsDataURL(file);
   }
   else{
       send(reportInfo)
   }


    $("#bugReportContent").val("")
    $("#bugReport").modal('hide')
    showMessage("Bug report submitted successfully", 5000, "info")
}



function showCitation(msgIndex, citationIndex){
    let msg = messageHistory.find(obj => obj.index === msgIndex)
    let citation = msg["citations"].find(obj => obj.index === citationIndex)
    let url = (citation.hasOwnProperty('url') ? citation['url'] : citation.source) || citation.source
    let citationDetails = `
        <strong>${citation.header}</strong><br>
        ${citation['subheader'] || 'No subheader available'}<br>
        ${citation['location'] || 'No location available'}<br>
        From: ${citation.document_title}<br>
        Authors: ${citation['authors'] || 'No authors available'}<br>
        Publisher: ${citation['publisher'] || 'No publisher available'}<br>
        Source: <a href="${url}" target="_blank">${url}</a>
        <br><br>${citation.content}
    `;
    $("#citationBody").html(citationDetails)
    $("#citationDisplay").modal('show')
}


function showMessage(message, timeout=5000, theme="info"){
    console.info("Displaying message:", message, timeout, theme)
    $("#toast_text").html(message)
    $("#toast_title").text(theme.charAt(0).toUpperCase() + theme.slice(1))
    $("#toast_title").text(theme.charAt(0).toUpperCase() + theme.slice(1))
    for(let i in ["danger","info", "success", "warning"]){
        $("#toast_header_div").removeClass(`text-bg-${i}`)
        $("#liveToast").removeClass(`text-bg-${i}`);
    }
    $("#toast_header_div").addClass(`text-bg-${theme}`)
    $("#liveToast").addClass(`text-bg-${theme}`);
    const now = new Date();
const timeString = now.toLocaleTimeString("de-DE", { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    $("#toast_timestamp").html(timeString)
    toastJS.show()
    if(timeout_id !=-1){
        clearTimeout(timeout_id)
    }
    if(timeout!=-1){
        timeout_id= setTimeout(
          function()
              {
                toastJS.hide()
                  timeout_id=-1
              }, timeout);
    }


}


function openChat(){
    $("#profile_pic").fadeOut();
    $(".widget").fadeIn();
}

function closeChat(){
    $("#profile_pic").fadeIn();
    $(".widget").fadeOut();
}


function switchCSS(name){

    if(name in themes){
        $("#stylesheet").attr("href",themes[name])
    }
    else{
        console.error("theme does not exist")
    }
}



let isMaximized = false;
function toggleMaxChat(){
    if(isMaximized){
        // $("#chat_top_bar").css("display","")
        $("#textareaContainer").css("height","70%")
        $("#sendButtonDiv").css({"height": "2.5em", "width": "2.5em"})
        $("#sendButton").css("font-size","1.5em")
        // $("#userInput").css({"margin-top": "0.1em", "margin-left": "0.1em"})
 }
    else {
        // $("#chat_top_bar").css("display","none")
        // $("#textareaContainer").css("height","90%")
        $("#sendButtonDiv").css({"height": "4em", "width": "5em"})
        $("#sendButton").css("font-size","3em")
        // $("#userInput").css({"margin-top": "1em", "margin-left": "1em"})
    }
    // $("#userInputDiv").toggleClass("col-9")
    // $("#userInputDiv").toggleClass("col-10")
    $("#widget_container").toggleClass("widget-max")
    $("#chats").toggleClass("chats-max")
    isMaximized=!isMaximized
}





window.addEventListener('load', () => {
  // initialization
  $(document).ready(() => {
    $(".dropdown-trigger").dropdown();
  });

  $("#chatModeSelector").change(function(){
    send({"type":"change_setting" , "setting":"selected_chat_mode", "value": this.value})
      resetChatMessages()
  });

 $('#enableContext').change(function() {
     send({"type":"change_setting" , "setting":"enable_knowledge_retrieval", "value": this.checked})
       });
 $('#enableFunctions').change(function() {
     send({"type":"change_setting" , "setting":"enable_function_calls", "value": this.checked})
       });
  
  $('#maximizeChat').on('change', function() {
    let newState = $(this).is(':checked')
      toggleMaxChat()
});


   $("#dark_mode").click(() => {
       switchCSS("slate")
  });

   $("#light_mode").click(() => {
     switchCSS("materia")
  });

  $("#profile_pic").click(() => {
    openChat()
  });

  $("#close").click(() => {
    closeChat()
    scrollToBottomOfResults();
  });
    
  $("#close_shortcut").click(() => {
      if(isMaximized){
          toggleMaxChat()
          return
      }
    closeChat()
    scrollToBottomOfResults();
  });

  document.addEventListener('dblclick', function(event) {
      let isChatElement = false
      let target_id = event.target.id
      if(event.target.id.startsWith("sub_id_span_")){
          isChatElement = true
      }
      if(!isChatElement){
          if(event.target.parentElement.id.startsWith("sub_id_span_")) {
              isChatElement = true
              target_id = event.target.parentElement.id
          }
      }
      if(!isChatElement){
          return
      }

      msgId=-1
          msgId = parseInt(target_id.substring(12))
          if(msgId==-1){
              $("#liveToast").show()
              $("#liveToast").delay(8000).hide(1000)
              return
          }
          let msg = messageHistory.find(obj => obj.index === msgId)
        console.log(msg)

          let code = "code" in msg ? msg["code"] : "No code used"
          //properly format code
            code = code.replace(/</g, "&lt;").replace(/>/g, "&gt;")
            code = code.replace(/(?:\r\n|\r|\n)/g, '<br>')
          $("#modalCodeDisplay").html(code)

          let metadata = "metadata" in msg ? msg["metadata"] : {"There is no metadata available":""}
          metadata["Index"] = msg["index"]

          $("#messageCloseUp").modal('show')
          $("#messageCloseUpContent").val(msg["content"])//event.target.innerHTML

          let metaList = ""
          for(let i in metadata){
              if(i == "timings"){
                  let response_time = metadata[i]["total_time"]
                  metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
                    Response time
                    <span class="badge bg-primary">${response_time} s</span></li>`
              }
              else if(i == "t_per_s"){
                  continue
                  metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
                    Token/s
                    <div style="margin-left: 0.5rem;max-height: 8rem; overflow-y: scroll">${metadata[i]['token_total_per_s']}</div></li>`
              }
              else if(i=="tokens"){
                    metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
                        Tokens
                        <div style="margin-left: 0.5rem;max-height: 8rem; overflow-y: scroll">${metadata[i]['total_tokens']}</div></li>`
              }
              else {
                  metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${i}
                    <span class="badge bg-primary">${metadata[i]}</span></li>`
              }

          }
          $("#metadata_list").html(metaList)

          let role = "role" in msg ? msg["role"] : "none"
          switch (role){
              case "user":
                  $("#btnradio1").prop("checked",true)
                  break;
              case "assistant":
                  $("#btnradio2").prop("checked",true)
                  break;
              case "system":
                  $("#btnradio3").prop("checked",true)
                  break;
              case "server":
                  $("#btnradio4").prop("checked",true)
                  break;
              default:
                  $("#btnradio5").prop("checked",true)
          }


});

  // $("#chats").on('dblclick', event => {
  //     if(event.target.className=="botMsg" || event.target.className=="userMsg"){
  //         // sub_id_span_
  //         msgId=-1
  //         msgId = parseInt(event.target.id.substring(12))
  //         // console.log(msgId)
  //         // console.log(event.target)
  //         // console.log(event.target.id)
  //         if(msgId==-1){
  //             $("#liveToast").show()
  //             $("#liveToast").delay(8000).hide(1000)
  //             return
  //         }
  //         let msg = messageHistory.find(obj => obj.index === msgId)
  //
  //         let code = "code" in msg ? msg["code"] : "No code used"
  //         //properly format code
  //           code = code.replace(/</g, "&lt;").replace(/>/g, "&gt;")
  //           code = code.replace(/(?:\r\n|\r|\n)/g, '<br>')
  //         $("#modalCodeDisplay").html(code)
  //
  //         let metadata = "metadata" in msg ? msg["metadata"] : {"There is no metadata available":""}
  //         metadata["Index"] = msg["index"]
  //
  //         $("#messageCloseUp").modal('show')
  //         $("#messageCloseUpContent").val(msg["content"])//event.target.innerHTML
  //
  //         let metaList = ""
  //         for(let i in metadata){
  //             if(i == "timings"){
  //                 let response_time = metadata[i]["total_time"]
  //                 metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
  //                   Response time
  //                   <span class="badge bg-primary">${response_time} s</span></li>`
  //             }
  //             else if(i == "t_per_s"){
  //                 continue
  //                 metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
  //                   Token/s
  //                   <div style="margin-left: 0.5rem;max-height: 8rem; overflow-y: scroll">${metadata[i]['token_total_per_s']}</div></li>`
  //             }
  //             else if(i=="tokens"){
  //                   metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
  //                       Tokens
  //                       <div style="margin-left: 0.5rem;max-height: 8rem; overflow-y: scroll">${metadata[i]['total_tokens']}</div></li>`
  //             }
  //             else {
  //                 metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
  //                   ${i}
  //                   <span class="badge bg-primary">${metadata[i]}</span></li>`
  //             }
  //
  //         }
  //         $("#metadata_list").html(metaList)
  //
  //         let role = "role" in msg ? msg["role"] : "none"
  //         switch (role){
  //             case "user":
  //                 $("#btnradio1").prop("checked",true)
  //                 break;
  //             case "assistant":
  //                 $("#btnradio2").prop("checked",true)
  //                 break;
  //             case "system":
  //                 $("#btnradio3").prop("checked",true)
  //                 break;
  //             case "server":
  //                 $("#btnradio4").prop("checked",true)
  //                 break;
  //             default:
  //                 $("#btnradio5").prop("checked",true)
  //         }
  //
  //     }
  // });
  
});

function deleteMessage(el){
    $("#userInput").prop("disabled",true)
    send({"content":`##tracker delete -m_id ${msgId}`})
}

