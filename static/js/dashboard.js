console.log("JS is loaded!");


function connectionEstablishedHandler() {
    console.log("connected!");
    // Call the "explain_with_lime" plugin from "confusion.py"
    callPluginFunction("confusion", "explain_with_lime", [], {});
    callPluginFunction("confusion", "generate_counterfactual_explanations", [5], {});
    callPluginFunction("confusion", "draw_importances_dashboard", [], {});
}

// Triggered whenever a message is received from the backend
function messageHandler(msg) {
    console.log("Message received from backend:", msg);

    
    html_content = msg["content"];
    
    
    if (html_content.includes("LIME")) {
        $("#limeplot").html(html_content); 
    }
    if (html_content.includes("COUNTERFACTUAL")) {
        $("#counterfactual").html(html_content); 
    }
    if (html_content.includes("SHAP")) {
        $("#shapelyplot").html(html_content); 
    }
}


document.addEventListener("DOMContentLoaded", function () {
    connectionEstablishedHandler();
});
