const featureMapping = {
  "Lead Time": "lead_time",
  "Country": "country",
  "Total Of Special Requests": "total_of_special_requests",
  "ADR": "adr",
  "Arrival Date Week Number": "arrival_date_week_number",
  "Market Segment": "market_segment",
  "Arrival Date Day Of Month": "arrival_date_day_of_month",
  "Previous Cancellations": "previous_cancellations",
  "Arrival Date Month": "arrival_date_month",
  "Stays In Week Nights": "stays_in_week_nights",
  "Booking Changes": "booking_changes",
  "Stays In Weekend Nights": "stays_in_weekend_nights",
  "Reserved Room Type": "reserved_room_type",
  "Adults": "adults",
  "Hotel": "hotel",
  "Children": "children"
};

const PDP_HISTORY_KEY = 'pdpHistory';
let pendingRequests = 0;

function setLoadingState(active) {
  pendingRequests = active ? pendingRequests + 1 : Math.max(pendingRequests - 1, 0);
  console.log("inside setLoadinState", pendingRequests);
  const isDisabled = pendingRequests > 0;
  
  // Disable critical buttons
  $("#confirmButton, #generatePdpButton, #modalConfirm").prop("disabled", isDisabled);
  
  // Visual feedback
  $("#confirmButton, #generatePdpButton").css({
    opacity: isDisabled ? 0.6 : 1,
    cursor: isDisabled ? 'not-allowed' : 'pointer'
  });
}

function populateFeatureCheckboxes() {
  const container = document.getElementById("featureCheckboxes");
  container.innerHTML = "";

  // Use sessionStorage instead of localStorage
  const sessionState = JSON.parse(sessionStorage.getItem(PDP_HISTORY_KEY)) || {
      features: [],
      target: '0'
  };

  for (const [userFriendly, backendName] of Object.entries(featureMapping)) {
      const label = document.createElement("label");
      label.innerHTML = `
          <input type="checkbox" value="${backendName}" 
              ${sessionState.features.includes(backendName) ? 'checked' : ''}>
          ${userFriendly}
      `;
      container.appendChild(label);
  }

  $("#targetSelect").val(sessionState.target);
}

function showLoading(selector) {
  $(selector).html(`
    <div class="loading">
      <img src="https://i.gifer.com/VAyR.gif" alt="Loading..." />
    </div>
  `);
}

function hideLoading(selector) {
  $(selector).find(".loading").remove();
}

function loadVisualizations() {
  setLoadingState(true);
  showLoading("#limeplot");
  callPluginFunction("confusion", "explain_with_lime", [], {});
  setLoadingState(true);
  showLoading("#counterfactualplot");
  callPluginFunction("confusion", "generate_counterfactual_explanations", [5], {});
}

function connectionEstablishedHandler() {
  console.log("Connection established. Ready to load data.");

  // Initially hide PDP Options
  $("#pdpOptions").hide();

  // Load the initial datapoint
  setLoadingState(true);
  callPluginFunction("confusion", "show_datapoint", [], {});
  
  // Load initial plots
  loadVisualizations(); // Load LIME and Counterfactual visualizations on page load
  setLoadingState(true); // Start loading
  showLoading("#shapelyplot");
  callPluginFunction("confusion", "draw_importances_dashboard", [], {}); // SHAP is loaded once
  console.log("Second pending reques after shapely", pendingRequests);
  
  // Show the modal when "Confirm" button is clicked
  $("#confirmButton").click(() => {
    if (pendingRequests > 0) return;
    $("#customModal").css("display", "flex");
  });

  // Close confirmation modal when clicking outside, without proceeding
  $("#customModal").click(function(event) {
    if (event.target === this) { // Clicked on overlay
      $(this).hide();
      // No next datapoint or Likert scale shown
    }
  });

  // If user confirms or cancels in the modal, show Likert scale
  $("#modalConfirm, #modalCancel").click(function () {
    $("#customModal").hide();
    $("#likertModal").css("display", "flex");
    $("#likertForm")[0].reset();
    $("#likertDone").prop("disabled", true);
  });

  // Enable Done button only when all Likert questions are answered
  $("#likertForm input[type='radio']").change(function() {
    const q1Answered = $("#likertForm input[name='q1']:checked").length > 0;
    const q2Answered = $("#likertForm input[name='q2']:checked").length > 0;
    if (q1Answered && q2Answered) {
      $("#likertDone").prop("disabled", false);
    } else {
      $("#likertDone").prop("disabled", true);
    }
  });

  // Handle Likert Done button click
  $("#likertDone").click(function() {
    if (pendingRequests > 0) return;
    // Collect responses
    const q1Value = $("#likertForm input[name='q1']:checked").val();
    const q2Value = $("#likertForm input[name='q2']:checked").val();
    console.log("Likert responses:", {q1: q1Value, q2: q2Value});
    // Hide modal and proceed to next datapoint
    $("#likertModal").hide();
    setLoadingState(true);
    callPluginFunction("confusion", "next_datapoint", [], {});
    loadVisualizations();
  });

  // Remove the ability to close Likert modal by clicking outside
  // $("#likertModal").click(function(event) { ... }) is removed

  // Toggle PDP Options
  $('#pdpButton').click(() => {
    if (pendingRequests > 0) return;
  
    // Toggle the PDP options panel
    $('#pdpOptions').toggle(() => {
      // If now visible, dynamically place it just below the button
      if ($('#pdpOptions').is(":visible")) {
        populateFeatureCheckboxes(); // existing call
  
        // Compute button’s position
        const buttonOffset = $('#pdpButton').offset();
        const buttonHeight = $('#pdpButton').outerHeight();
  
        // Add some extra spacing (e.g., 10px)
        const newTop = buttonOffset.top + buttonHeight + 10;
  
        // Update the panel’s position
        $('#pdpOptions').css({ top: newTop + 'px' });
      }
    });
  });
  

  // Generate PDP Plot
  $('#generatePdpButton').click(() => {
    if (pendingRequests > 0) return;
    
    const selectedFeatures = $(".checkbox-group input:checked")
      .map((i, el) => el.value).get();
    const selectedTarget = $('#targetSelect').val();

    if (!selectedFeatures.length) {
      alert("Please select at least one feature.");
      return;
    }
  
    sessionStorage.setItem(PDP_HISTORY_KEY, JSON.stringify({
      features: selectedFeatures,
      target: selectedTarget
    }));

    setLoadingState(true);
    showLoading("#pdpplot");
    callPluginFunction("confusion", "draw_pdp_dashboard", 
      [selectedFeatures, parseInt(selectedTarget)], {}
    );
    $('#pdpOptions').hide();
  });
}

function messageHandler(msg) {
  console.log("Message from backend:", msg);
  const html_content = msg["content"];

  if (msg.role === "datapoint") {
    console.log("Updating Datapoint display...");
    updateDatapointDisplay(msg.content);
    setLoadingState(false);
  }
  if (html_content.includes("SHAP")) {
    $("#shapelyplot").html(html_content);
    hideLoading("#shapelyplot");
    setLoadingState(false);
  }
  if (html_content.includes("LIME")) {
    $("#limeplot").html(html_content);
    hideLoading("#limeplot");
    setLoadingState(false);
  }
  if (html_content.includes("COUNTERFACTUAL")) {
    $("#counterfactualplot").html(html_content);
    hideLoading("#counterfactualplot");
    setLoadingState(false);
  }
  if (html_content.includes("PDP")) {
    $("#pdpplot").html(html_content);
    hideLoading("#pdpplot");
    setLoadingState(false);
  }
}

function updateDatapointDisplay(datapointInfo) {
  const { prediction, confidence, data } = datapointInfo;
  let headerHTML = "";
  let valueHTML = "";
  for (const key in data) {
    headerHTML += `<th>${data[key].title}</th>`;
    valueHTML += `<td>${data[key].value}</td>`;
  }
  $("#featureHeader").html(headerHTML);
  $("#featureValues").html(valueHTML);
  $("#predictionText").text(prediction);
  $("#confidenceText").text(`${confidence} %`);
  
  // Update the summary text using the same data as the table
  const summaryParts = [];
  for (const key in data) {
    summaryParts.push(`${data[key].title} is ${data[key].value}`);
  }
  const summaryText = "This datapoint shows that " + summaryParts.join(", ") + ".";
  $("#datapointSummary").text(summaryText);
}