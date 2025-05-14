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

var currentUsername = username;
var decisionChoice = "";

function initLikertForm() {
  const form = $("#likertForm");
  form.empty();

  if (standalone_with_chat) {
    const questions = [
      {
        id: "q1",
        text: "How confident are you in your decision?",
        labelMin: "not confident at all",
        labelMax: "very confident"
      },
      {
        id: "q2",
        text: "How useful did you find the AI assistant's responses?",
        labelMin: "not useful at all",
        labelMax: "very useful"
      },
      {
        id: "q3",
        text: "How satisfied were you with the overall support from the AI assistant?",
        labelMin: "not satisfied at all",
        labelMax: "very satisfied"
      }
    ];
    questions.forEach(q => {
      form.append(`<p>${q.text}</p>`);
      const scaleDiv = $(`<div class="likert-scale"></div>`);
      for (let i = 1; i <= 5; i++) {
        scaleDiv.append(`
          <label>
            <input type="radio" name="${q.id}" value="${i}"> ${i}
          </label>
        `);
      }
      form.append(scaleDiv);
      form.append(`
        <div class="likert-scale-labels"
             style="display:flex; justify-content:space-between; font-size:0.9em; margin-top:5px;">
          <span>${q.labelMin}</span>
          <span>${q.labelMax}</span>
        </div>
      `);
    });
  } else {
    form.append(`<p>Confidence: How confident are you in your decision?</p>`);
    const scaleDiv = $(`<div class="likert-scale"></div>`);
    for (let i = 1; i <= 5; i++) {
      scaleDiv.append(`
        <label>
          <input type="radio" name="confidence" value="${i}"> ${i}
        </label>
      `);
    }
    form.append(scaleDiv);
    form.append(`
      <div class="likert-scale-labels"
           style="display:flex; justify-content:space-between; font-size:0.9em; margin-top:5px;">
        <span>Not confident at all</span>
        <span>Very confident</span>
      </div>
    `);
  }
}

function generateBookingSummary(data) {
  console.log("generateBookingSummary data:", data);

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

  const pluralize = (count, singular, plural) =>
    `${count} ${count === 1 ? singular : (plural || singular + "s")}`;

  const adultText  = pluralize(adults, "adult");
  const childText  = children > 0 ? ` and ${pluralize(children, "child")}` : "";
  const dayText    = pluralize(leadTime, "day");
  const nightText  = pluralize(totalNights, "night");

  const segmentMap = {
    "Groups":        "as part of a group reservation",
    "Corporate":     "under a corporate agreement",
    "Offline TA/TO": "via an offline travel agent",
    "Online TA":     "through an online travel agency",
    "Direct":        "via direct booking"
  };
  const segmentPhrase = segmentMap[marketSeg] || `through ${marketSeg.toLowerCase()}`;

  let depositPhrase;
  const d = depositType.toLowerCase();
  if (d.includes("no deposit")) {
    depositPhrase = "no deposit";
  } else if (d.includes("non")) {
    depositPhrase = "non-refundable";
  } else {
    depositPhrase = "refundable";
  }

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
  let container = document.getElementById("histogramFeatureRadios");
  if (!container) {
    container = document.createElement("div");
    container.id = "histogramFeatureRadios";
    container.classList.add("checkbox-group");
    const old = document.getElementById("featureSelect");
    if (old) old.parentNode.replaceChild(container, old);
    else document.getElementById("histogramOptions")
      .insertBefore(container, document.getElementById("splitByTarget").parentNode);
  } else {
    container.innerHTML = "";
  }

  const sessionState = JSON.parse(sessionStorage.getItem(HISTOGRAM_HISTORY_KEY)) || { selectedFeature: "" };
  for (const [label, value] of Object.entries(featureMapping)) {
    const lbl = document.createElement("label");
    lbl.innerHTML = `
      <input type="radio" name="histogramFeature" value="${value}"
        ${sessionState.selectedFeature === value ? "checked" : ""}>
      ${label}
    `;
    container.appendChild(lbl);
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
    initLikertForm();
    $("#likertForm")[0].reset();
    $("#likertDone").prop("disabled", true);
    $("#likertModal").
css("display", "flex");
  });

  $("#modalCancel").click(() => {
    decisionChoice = "decline_datapoint";
    $("#customModal").hide();
    initLikertForm();
    $("#likertForm")[0].reset();
    $("#likertDone").prop("disabled", true);
    $("#likertModal").css("display", "flex");
  });

  $("#likertModal").on("change", "input[type='radio']", () => {
    const needed = standalone_with_chat ? 3 : 1;
    const got    = $("#likertForm input[type='radio']:checked").
length;
    $("#likertDone").prop("disabled", got < needed);
  });

  $("#likertDone").click(() => {
    if (pendingRequests) return;
    $("#likertModal").hide();
    setLoadingState(true);

    const answers = [];
    if (standalone_with_chat) {
      ["q1","q2","q3"].forEach(id => {
        const val = parseInt($(`#likertForm input[name='${id}']:checked`).val(), 10);
        answers.push({ id, answer: val });
      });
    } else {
      const val = parseInt($("#likertForm input[name='confidence']:checked").val(), 10);
      answers.push({ id: "q1", answer: val });
    }

    callPluginFunction("confusion", "next_datapoint", [], {
      username: currentUsername,
      datapoint_choice: decisionChoice,
      answers: answers,
      current_study_mode:standalone_with_chat ? "dashboard_chat" : "dashboard"
    });
    loadVisualizations();
  });

  $('#pdpButton').click(() => {
    if (pendingRequests > 0) return;
    $('#histogramOptions').hide();
    $('#pdpOptions').toggle(() => {
      if ($('#pdpOptions').
is(":visible")) {
        populateFeatureCheckboxes();
        const off = $('#pdpButton').offset(), h = $('#pdpButton').outerHeight();
        $('#pdpOptions').css("top", off.top + h + 10 + "px");
      }
    });
  });

  $('#histogramButton').
click(() => {
    if (pendingRequests) return;
    $('#pdpOptions').hide();
    $('#histogramOptions').
toggle(() => {
      if ($('#histogramOptions').is(":visible")) {
        populateHistogramRadios();
        const off = $('#histogramButton').offset(), h = $('#histogramButton').outerHeight();
        $('#histogramOptions').css("top", off.top + h + 10 + "px");
      }
    });
  });

  $('#counterfactualButton').click(() => {
    if (pendingRequests > 0) return;
    setLoadingState(true);
    showLoading('#counterfactualplot');
    callPluginFunction("confusion", "generate_counterfactual_explanations", [5], {});
  });

  $("#generatePdpButton").
click(() => {
    if (pendingRequests) return;
    const feats = $(".checkbox-group input:checked").map((i,el) => el.value).get();
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
    const split = $("#splitByTarget").
is(':checked');
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
  if (msg.
role === "datapoint") {
    updateDatapointDisplay(msg.content);
    setLoadingState(false);
  if(standalone_with_chat){
    resetChatMessages()
  }
    return
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
  $("#pdpContainer, #histogramContainer").
hide();
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

  const summaryText = generateBookingSummary(data);
  console.log("updateDatapointDisplay summary:", summaryText);
  $("#datapointSummary").text(summaryText);

  const bannerEl = document.getElementById("banner");
  const mainEl   = document.getElementById("mainContent");
  bannerEl.style.height   = "auto";
  bannerEl.style.overflow = "visible";
  const newH = bannerEl.getBoundingClientRect().height;
  mainEl.style.marginTop  = `${newH}px`;
}
