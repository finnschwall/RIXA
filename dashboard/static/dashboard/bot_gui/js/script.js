$("#profile_pic").toggle();
$(".widget").toggle();

let msgId=-1

function showMessage(message, timeout=5000, theme="info"){
    console.log(message, timeout, theme)
    $("#toast_text").html(message)
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

  $("#chats").on('dblclick', event => {
      if(event.target.className=="botMsg" || event.target.className=="userMsg"){
          // sub_id_span_
          msgId=-1
          msgId = parseInt(event.target.id.substring(12))
          if(msgId==-1){
              $("#liveToast").show()
              $("#liveToast").delay(8000).hide(1000)
              return
          }
          let msg = messageHistory.find(obj => obj.msg_id === msgId)
          let metadata = "metadata" in msg ? msg["metadata"] : {"There is no metadata available":""}
          metadata["id"] = msg["msg_id"]
          console.log(msg)

          $("#messageCloseUp").modal('show')
          $("#messageCloseUpContent").val(msg["content"])//event.target.innerHTML

          let metaList = ""
          for(let i in metadata){
              if(i == "context"){
                  metaList+=`<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${i}
                    <div style="margin-left: 0.5rem;max-height: 8rem; overflow-y: scroll">${metadata[i]}</div></li>`
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

      }
  });
  
});

function deleteMessage(el){
    $("#userInput").prop("disabled",true)
    send({"content":`##tracker delete -m_id ${msgId}`})
}

