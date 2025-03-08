const body = document.body;
let map;
let startingMarker;
let storeMarkers = {};

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
      }
    }
  } catch (e) {}
});

async function addMarker(location) {
  if (startingMarker) {
    startingMarker.map = null;
  }

  const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

  startingMarker = new AdvancedMarkerElement({
    map: map,
    position: {
      lat: location.latitude,
      lng: location.longitude,
    },
    title: "Starting Address",
    id: "starting-marker",
  });
}

async function initMap() {
  const { Map } = await google.maps.importLibrary("maps");

  map = new Map(document.getElementById("map"), {
    center: { lat: 45.55090134296241, lng: -73.68035515427918 },
    zoom: 11,
    mapId: "my-map",
  });

  const req = await fetch("/api/stores", {
    method: "POST",
  });

  console.log(req);
}

initMap();
