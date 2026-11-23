/* Dashboard charts. Served from our own origin, so it satisfies the CSP (no inline script). */
(function () {
  "use strict";
  var holder = document.getElementById("dash-data");
  if (!holder || typeof Chart === "undefined") { return; }
  var COLORS = { blue: "#0d6efd", green: "#198754", cyan: "#0dcaf0", red: "#dc3545", grey: "#adb5bd" };

  fetch(holder.dataset.url, { credentials: "same-origin", headers: { Accept: "application/json" } })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var latest = d.latest;
      if (latest) {
        var scored = latest.components.filter(function (c) { return c.score !== null; });
        new Chart(document.getElementById("chart-components"), {
          type: "bar",
          data: { labels: scored.map(function (c) { return c.label; }),
                  datasets: [{ label: "Score (0-100)", data: scored.map(function (c) { return c.score; }), backgroundColor: COLORS.blue }] },
          options: { indexAxis: "y", scales: { x: { min: 0, max: 100 } }, plugins: { legend: { display: false } } }
        });
        if (latest.has_skills) {
          var s = latest.skill_status;
          new Chart(document.getElementById("chart-skills"), {
            type: "doughnut",
            data: { labels: ["Matched", "Inferred (partial)", "Missing"],
                    datasets: [{ data: [s.matched, s.partial, s.missing], backgroundColor: [COLORS.green, COLORS.cyan, COLORS.red] }] }
          });
        }
      }
      if (d.history.length) {
        new Chart(document.getElementById("chart-history"), {
          type: "line",
          data: { labels: d.history.map(function (h) { return h.date; }),
                  datasets: [{ label: "Compatibility score", data: d.history.map(function (h) { return h.score; }),
                               borderColor: COLORS.blue, backgroundColor: COLORS.blue, tension: 0.2 }] },
          options: { scales: { y: { min: 0, max: 100 } } }
        });
      }
    })
    .catch(function () { holder.insertAdjacentText("beforeend", " Charts could not be loaded."); });
})();
