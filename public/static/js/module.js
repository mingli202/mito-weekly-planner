const body = document.body;
let map;
let infoWindow;
let startingMarker;
let storeMarkers = {};
let important = [];

body.addEventListener("htmx:beforeSwap", async (e) => {
  try {
    const res = JSON.parse(e.detail.serverResponse);
    e.detail.serverResponse = res.html;

    const data = res.data;

    if (data.action) {
      switch (data.action) {
        case "removeStartingAddress": {
          startingMarker.map = null;
          startingMarker = null;
        }
        case "setStartingAddress": {
          await addMarker(data.location);
        }
        case "setCenter": {
          e.detail.shouldSwap = false;
          map.setCenter({
            lat: data.location.lat,
            lng: data.location.lng,
          });
        }
      }
    }
  } catch (_e) {}
});

async function addMarker(location) {
  if (startingMarker) {
    startingMarker.map = null;
  }

  const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
  const home = {
    lat: location.latitude,
    lng: location.longitude,
  };

  startingMarker = new AdvancedMarkerElement({
    map: map,
    position: home,
    title: "Starting Address",
  });
  map.setCenter(home);
}

async function initMap() {
  const { Map, InfoWindow } = await google.maps.importLibrary("maps");
  const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

  map = new Map(document.getElementById("map"), {
    center: { lat: 45.55090134296241, lng: -73.68035515427918 },
    zoom: 11,
    mapId: "my-map",
    streetViewControl: false,
  });

  infoWindow = new InfoWindow();

  const req = await fetch("/static/data/locations-fixed.json");
  const json = await req.json();

  for (const location of json) {
    const icon = document.createElement("div");
    icon.className = "pin";
    icon.innerHTML = `
      #${location["No Mag."]}
      <div class="pin-arrow"></div>
    `;

    const marker = new AdvancedMarkerElement({
      map: map,
      position: { lat: location.latitude, lng: location.longitude },
      title: `#${location["No Mag."]}`,
      content: icon,
      gmpClickable: true,
    });

    marker.addListener("click", async () => {
      const res = await fetch(`/api/store/${location["No Mag."]}`);
      const data = await res.json();

      infoWindow.close();
      infoWindow.setContent(`
        <div style="display: flex; flex-direction: column; gap: 0.25rem;">
          <div style="font-size: 1rem; color: black; font-weight: bold;">Store #${data["number"]}</div>
          <div>${data["name"]}</div>
          <div>
            <div>${data["addr"]}</div>
            <div>${data["city"]}, ${data["postalCode"]}</div>
          </div>
        </div>
      `);
      infoWindow.open(marker.map, marker);
    });

    storeMarkers[location["No Mag."]] = marker;
  }
}

initMap();

window.toggleImportant = (id) => {
  if (important.length == 0) {
    const urgent_placeholder = document.getElementById("urgent-placeholder");

    urgent_placeholder.remove();
  }

  const visit_element = document.getElementById(`must-visit-${id}`);

  const markerElement = document.querySelector(
    `gmp-advanced-marker[title="#${id}"]`,
  );

  if (visit_element) {
    visit_element.remove();
    important = important.filter((im) => im != id);

    const store_element = document.getElementById(`store${id}`);
    if (store_element) {
      store_element.checked = false;
    }

    const marker = storeMarkers[id];
    marker.content.classList.remove("important-pin");

    if (markerElement) {
      markerElement.style.zIndex = "";
    }
  } else {
    important.push(id);

    const must_visit = document.getElementById("must-visit");

    const el = document.createElement("div");
    el.id = `must-visit-${id}`;
    el.className = "must-visit-card";
    el.innerHTML = `
        <i
          class="fa-solid fa-xmark"
          style="color: var(--secondary-text)"
          onclick="toggleImportant(${id})"
        ></i>
      <span>${id}</span>
    `;

    must_visit.append(el);

    const marker = storeMarkers[id];
    marker.content.classList.add("important-pin");

    if (markerElement) {
      markerElement.style.zIndex = "10";
    }
  }

  if (important.length == 0) {
    const must_visit = document.getElementById("must-visit");

    const p = document.createElement("p");
    p.id = "urgent-placeholder";
    p.innerText = "Urgent stores that must be visited will be displayed here.";

    must_visit.append(p);
  }
};

window.getImportant = () => important;

window.showSchedule = (schedule, id) => {
  const days = ["monday", "tuesday", "wednesday", "thursday", "friday"];

  for (const pin of document.querySelectorAll("div.pin")) {
    pin.parentElement.style.visibility = "hidden";
  }

  const previousSelectedSchedule = document.querySelector(
    "div.selected-schedule",
  );
  if (previousSelectedSchedule) {
    if (previousSelectedSchedule.id === id) {
      unselectSchedule();
      return;
    }

    previousSelectedSchedule.classList.remove("selected-schedule");
    previousSelectedSchedule.classList.add("schedule-container");
  }

  const scheduleContainer = document.getElementById(id);
  scheduleContainer.classList.remove("schedule-container");
  scheduleContainer.classList.add("selected-schedule");

  for (let i = 0; i < days.length; i++) {
    const day = days[i];
    const daySchedule = schedule[i];

    const previousColoredDayElements = document.querySelectorAll(
      `div.${day}-pin`,
    );

    for (const el of previousColoredDayElements) {
      el.parentElement.style.zIndex = "";
      el.classList.remove(`${day}-pin`);
    }

    for (const store of daySchedule) {
      const pinElement = document.querySelector(
        `gmp-advanced-marker[title="#${store}"]>div`,
      );

      if (pinElement) {
        pinElement.parentElement.style.zIndex = "10";
        pinElement.parentElement.style.visibility = "visible";

        pinElement.classList.add(`${day}-pin`);
      }
    }
  }
};

window.unselectSchedule = () => {
  const scheduleContainer = document.querySelector("div.selected-schedule");

  if (scheduleContainer) {
    scheduleContainer.classList.remove("selected-schedule");
    scheduleContainer.classList.add("schedule-container");
  }

  for (const pin of document.querySelectorAll("div.pin")) {
    pin.parentElement.style.visibility = "visible";
    pin.className = "pin";
  }
};
