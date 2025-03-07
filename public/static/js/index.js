let important = [];
function toggleImportant(id) {
  if (important.length == 0) {
    const urgent_placeholder = document.getElementById("urgent-placeholder");

    urgent_placeholder.remove();
  }

  const visit_element = document.getElementById(`must-visit-${id}`);

  if (visit_element) {
    visit_element.remove();
    important = important.filter((im) => im != id);

    const store_element = document.getElementById(`store${id}`);
    if (store_element) {
      store_element.checked = false;
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
  }

  if (important.length == 0) {
    const must_visit = document.getElementById("must-visit");

    const p = document.createElement("p");
    p.id = "urgent-placeholder";
    p.innerText = "Urgent stores that must be visited will be displayed here.";

    must_visit.append(p);
  }
}

function getImportant() {
  return important;
}
