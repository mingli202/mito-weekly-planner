const body = document.body;
let map;
let infoWindow;
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
  });
}

async function initMap() {
  const { Map, InfoWindow } = await google.maps.importLibrary("maps");
  const { AdvancedMarkerElement, PinElement } =
    await google.maps.importLibrary("marker");

  map = new Map(document.getElementById("map"), {
    center: { lat: 45.55090134296241, lng: -73.68035515427918 },
    zoom: 11,
    mapId: "my-map",
  });

  infoWindow = new InfoWindow();

  const req = await fetch("/static/data/locations-fixed.json");
  const json = await req.json();

  for (const location of json) {
    const icon = document.createElement("div");
    icon.innerHTML = '<i class="fa-solid fa-store"></i>';

    const pin = new PinElement({
      scale: 1.0,
      background: "#7ad03a",
      borderColor: "#7ad03a",
      glyph: icon,
    });

    const marker = new AdvancedMarkerElement({
      map: map,
      position: { lat: location.latitude, lng: location.longitude },
      title: `#${location["No Mag."]}`,
      content: pin.element,
      gmpClickable: true,
    });

    marker.addListener("click", ({ domEvent, latLng }) => {
      const { target } = domEvent;

      infoWindow.close();
      infoWindow.setContent(marker.title);
      infoWindow.open(marker.map, marker);
    });

    storeMarkers[location["No Mag."]] = marker;
  }
}

initMap();
