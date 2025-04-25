const featureMapping = {
  "Hotel": "hotel",
  "Reserved Room Type": "reserved_room_type",
  "Lead Time": "lead_time",
  "Deposit Type": "deposit_type",
  "Market Segment": "market_segment",
  "Arrival Date Week Number": "arrival_date_week_number",
  "Arrival Date Day Of Month": "arrival_date_day_of_month",
  "Arrival Date Month": "arrival_date_month",
  "Adults": "adults",
  "Children": "children",
  "Country": "country",
  "Previous Cancellations": "previous_cancellations",
  "Booking Changes": "booking_changes",
  "Total Of Special Requests": "total_of_special_requests",
  "Stays In Week Nights": "stays_in_week_nights",
  "Stays In Weekend Nights": "stays_in_weekend_nights",
  "ADR": "adr",
};

const PDP_HISTORY_KEY = 'pdpHistory';
const HISTOGRAM_HISTORY_KEY = 'histogramHistory';
let pendingRequests = 0;

// Global variables for user and decision
var currentUsername = username; 
var decisionChoice = "";

function generateBookingSummary(data) {
  console.log("generateBookingSummary data:", data);

  // Extract each field by its display title
  const adults        = parseInt(data["Adults"].value, 10);
  const children      = parseInt(data["Children"].value, 10);
  const leadTime      = parseInt(data["Lead Time"].value, 10);
  const hotel         = data["Hotel"].value;
  const weekNights    = parseInt(data["Stays In Week Nights"].value, 10);
  const weekendNights = parseInt(data["Stays In Weekend Nights"].value, 10);
  const totalNights   = weekNights + weekendNights;
  const roomType      = data["Reserved Room Type"].value;
  const adr           = data["ADR"].value;
  const day           = parseInt(data["Arrival Date Day Of Month"].value, 10);
  const month         = data["Arrival Date Month"].value;
  const weekNum       = parseInt(data["Arrival Date Week Number"].value, 10);
  const country       = data["Country"].value;
  const depositType   = data["Deposit Type"].value;
  const marketSeg     = data["Market Segment"].value;

  // Pluralization helper
  const pluralize = (count, singular, plural) =>
    `${count} ${count === 1 ? singular : (plural || singular + "s")}`;

  const adultText  = pluralize(adults, "adult");
  const childText  = children > 0 ? ` and ${pluralize(children, "child")}` : "";
  const dayText    = pluralize(leadTime, "day");
  const nightText  = pluralize(totalNights, "night");

  // Market‐segment phrase lookup
  const segmentMap = {
    "Groups":        "as part of a group reservation",
    "Corporate":     "under a corporate agreement",
    "Offline TA/TO": "via an offline travel agent",
    "Online TA":     "through an online travel agency",
    "Direct":        "via direct booking"
  };
  const segmentPhrase = segmentMap[marketSeg] || `through ${marketSeg.toLowerCase()}`;

  // Deposit phrasing
  // New deposit phrasing logic:
  let depositPhrase;
  const d = depositType.toLowerCase();
  if (d.includes("no deposit")) {
    depositPhrase = "no";
  } else if (d.includes("non refund")) {
    depositPhrase = "non‑refundable";
  } else {
    depositPhrase = "refundable";
  }

  // Build the narrative
  const summary =
    `The booking comprises ${adultText}${childText} and was placed ${dayText} prior to arrival ${segmentPhrase}. ` +
    `The guests plan to stay at the ${hotel} hotel for ${nightText} ` +
    `(${weekNights} weekday and ${weekendNights} weekend), in a ${roomType} room. ` +
    `The average daily rate during the stay is ${adr}. ` +
    `The scheduled arrival is on the ${day}th of ${month} (week ${weekNum}), ` +
    `the guests are from ${country} and paid a ${depositPhrase} deposit.`;

  console.log("generateBookingSummary returning:", summary);
  return summary;
}

function setLoadingState(active) {
  pendingRequests = active ? pendingRequests + 1 : Math.max(pendingRequests - 1, 0);
  const isDisabled = pendingRequests > 0;
  $("#confirmButton, #generatePdpButton, #generateHistogramButton, #modalConfirm")
    .prop("disabled", isDisabled)
    .css({
      opacity: isDisabled ? 0.6 : 1,
      cursor: isDisabled ? 'not-allowed' : 'pointer'
    });
}

function populateFeatureCheckboxes() {
  const container = document.getElementById("featureCheckboxes");
  container.innerHTML = "";
  const sessionState = JSON.parse(sessionStorage.getItem(PDP_HISTORY_KEY)) || { features: [], target: '0' };
  for (const [label, value] of Object.entries(featureMapping)) {
    const lbl = document.createElement("label");
    lbl.innerHTML = `
      <input type="checkbox" value="${value}"
        ${sessionState.features.includes(value) ? 'checked' : ''}>
      ${label}
    `;
    container.appendChild(lbl);
  }
  $("#targetSelect").val(sessionState.target);
}

function populateHistogramRadios() {
  // Check if the radio container exists; if not, create one.
  let container = document.getElementById("histogramFeatureRadios");
  if (!container) {
    container = document.createElement("div");
    container.id = "histogramFeatureRadios";

    // — ADDED: Use the same CSS class as PDP options so radios get the grey boxes, grid gaps, etc.
    container.classList.add("checkbox-group");

    // Replace the old <select> (if it exists) with this radio container
    const oldSelect = document.getElementById("featureSelect");
    if (oldSelect) {
      oldSelect.parentNode.replaceChild(container, oldSelect);
    } else {
      document.getElementById("histogramOptions")
        .insertBefore(container, document.getElementById("splitByTarget").parentNode);
    }
  } else {
    // Clear previous radios if already created.
    container.innerHTML = "";
  }

  // Load the user's last selection
  const sessionState = JSON.parse(sessionStorage.getItem(HISTOGRAM_HISTORY_KEY)) || { selectedFeature: "" };

  // Iterate over featureMapping in insertion order to create styled radio labels
  for (const [userFriendly, backendName] of Object.entries(featureMapping)) {
    const labelEl = document.createElement("label");

    labelEl.innerHTML = `
      <input 
        type="radio" 
        name="histogramFeature" 
        value="${backendName}"
        ${sessionState.selectedFeature === backendName ? "checked" : ""}
      >
      ${userFriendly}
    `;
    container.appendChild(labelEl);
  }
}


function showLoading(sel) {
  $(sel).html(`
    <div class="loading">
      <img src="https://i.gifer.com/VAyR.gif" alt="Loading..."/>
    </div>
  `);
}

function hideLoading(sel) {
  $(sel).find(".loading").remove();
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
  $("#pdpOptions, #histogramOptions").hide();

  setLoadingState(true);
  callPluginFunction("confusion", "show_datapoint", [], {});
  loadVisualizations();
  setLoadingState(true);
  showLoading("#shapelyplot");
  callPluginFunction("confusion", "draw_importances_dashboard", [], {});

  $("#confirmButton").click(() => {
    if (pendingRequests) return;
    $("#customModal").css("display", "flex");
  });

  $("#customModal").click(e => {
    if (e.target === e.currentTarget) $(e.currentTarget).hide();
  });

  $("#modalConfirm").click(() => {
    decisionChoice = "confirm_datapoint";
    $("#customModal").hide();
    $("#likertModal").css("display", "flex");
    $("#likertForm")[0].reset();
    $("#likertDone").prop("disabled", true);
  });

  $("#modalCancel").click(() => {
    decisionChoice = "decline_datapoint";
    $("#customModal").hide();
    $("#likertModal").css("display", "flex");
    $("#likertForm")[0].reset();
    $("#likertDone").prop("disabled", true);
  });

  $("#likertForm input[type='radio']").change(() => {
    const ok = $("#likertForm input[name='confidence']:checked").length > 0;
    $("#likertDone").prop("disabled", !ok);
  });

  $("#likertDone").click(() => {
    if (pendingRequests) return;
    const ans = parseInt($("#likertForm input[name='confidence']:checked").val(), 10);
    $("#likertModal").hide();
    setLoadingState(true);
    callPluginFunction("confusion", "next_datapoint", [], {
      username: currentUsername,
      datapoint_choice: decisionChoice,
      answers: [{ id: 'q1', answer: ans }]
    });
    loadVisualizations();
  });

  $("#pdpButton").click(() => {
    if (pendingRequests) return;
    $("#histogramOptions").hide();
    $("#pdpOptions").toggle(() => {
      if ($("#pdpOptions").is(":visible")) {
        populateFeatureCheckboxes();
        const off = $("#pdpButton").offset(), h = $("#pdpButton").outerHeight();
        $("#pdpOptions").css("top", off.top + h + 10 + "px");
      }
    });
  });

  $("#histogramButton").click(() => {
    if (pendingRequests) return;
    $("#pdpOptions").hide();
    $("#histogramOptions").toggle(() => {
      if ($("#histogramOptions").is(":visible")) {
        populateHistogramRadios();
        const off = $("#histogramButton").offset(), h = $("#histogramButton").outerHeight();
        $("#histogramOptions").css("top", off.top + h + 10 + "px");
      }
    });
  });

  $("#generatePdpButton").click(() => {
    if (pendingRequests) return;
    const feats = $(".checkbox-group input:checked").map((i,el)=>el.value).get();
    const tgt   = $("#targetSelect").val();
    if (!feats.length) { alert("Please select at least one feature."); return; }
    sessionStorage.setItem(PDP_HISTORY_KEY, JSON.stringify({ features: feats, target: tgt }));
    setLoadingState(true);
    showLoading("#pdpplot");
    if (!$("#pdpContainer").is(":visible")) $("#pdpContainer").show();
    callPluginFunction("confusion", "draw_pdp_dashboard", [feats, parseInt(tgt, 10)], {});
    $("#pdpOptions").hide();
  });

  $("#generateHistogramButton").click(() => {
    if (pendingRequests) return;
    const feat  = $("input[name='histogramFeature']:checked").val();
    const split = $("#splitByTarget").is(':checked');
    if (!feat) { alert("Please select a feature."); return; }
    sessionStorage.setItem(HISTOGRAM_HISTORY_KEY,
      JSON.stringify({ selectedFeature: feat, splitByTarget: split }));
    setLoadingState(true);
    showLoading("#histogramplot");
    if (!$("#histogramContainer").is(":visible")) $("#histogramContainer").show();
    callPluginFunction("confusion", "generate_histogram", [feat, split], {});
    $("#histogramOptions").hide();
  });
}

function messageHandler(msg) {
  const html = msg.content;
  if (msg.role === "datapoint") {
    updateDatapointDisplay(msg.content);
    setLoadingState(false);
  }
  if (html.includes("SHAP")) {
    $("#shapelyplot").html(html); hideLoading("#shapelyplot"); setLoadingState(false);
  }
  if (html.includes("LIME")) {
    $("#limeplot").html(html); hideLoading("#limeplot"); setLoadingState(false);
  }
  if (html.includes("COUNTERFACTUAL")) {
    $("#counterfactualplot").html(html); hideLoading("#counterfactualplot"); setLoadingState(false);
  }
  if (html.includes("PDP")) {
    $("#pdpplot").html(html); hideLoading("#pdpplot"); setLoadingState(false);
  }
  if (html.includes("HISTOGRAM")) {
    $("#histogramplot").html(html); hideLoading("#histogramplot"); setLoadingState(false);
  }
}

function updateDatapointDisplay(datapointInfo) {
  $("#pdpContainer, #histogramContainer").hide();
  console.log("updateDatapointDisplay called with:", datapointInfo);
  const { prediction, confidence, data } = datapointInfo;
  let headerHTML = "", valueHTML = "";

  for (const key in data) {
    headerHTML += `<th>${data[key].title}</th>`;
    valueHTML  += `<td>${data[key].value}</td>`;
  }
  $("#featureHeader").html(headerHTML);
  $("#featureValues").html(valueHTML);

  $("#predictionText").text(prediction);
  $("#confidenceText").text(`${confidence} %`);

  // Use the narrative template for the summary
  const summaryText = generateBookingSummary(data);
  console.log("updateDatapointDisplay summary:", summaryText);
  $("#datapointSummary").text(summaryText);

  // Auto‑resize banner & push content down
  const bannerEl = document.getElementById("banner");
  const mainEl   = document.getElementById("mainContent");
  bannerEl.style.height   = "auto";
  bannerEl.style.overflow = "visible";
  const newH = bannerEl.getBoundingClientRect().height;
  mainEl.style.marginTop  = `${newH}px`;
}
