document.addEventListener("DOMContentLoaded", function () {
  let calendar;
  let rawEvents = [];
  let filteredOutlet = "ALL";

  function initCalendar(events) {
    const calendarEl = document.getElementById("calendar");
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      locale: "ko",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,listMonth",
      },
      events: events,
      eventClick: function (info) {
        const event = info.event;
        const id = event.extendedProps.event_id;
        if (id) {
          const url = `https://symist.github.io/Discounts/pages/event-${id}.html`;
          window.open(url, "_blank");
        } else {
          alert("상세 페이지를 찾을 수 없습니다.");
        }
      },
    });
    calendar.render();
  }

  function filterEvents(outlet) {
    filteredOutlet = outlet;
    document.querySelectorAll(".filter-btn").forEach((btn) => btn.classList.remove("active"));
    event.target.classList.add("active");

    if (!calendar) return;

    const filtered = outlet === "ALL" ? rawEvents : rawEvents.filter((e) => e.outlet === outlet);
    calendar.removeAllEvents();
    filtered.forEach((event) => calendar.addEvent(event));
  }

  window.filterEvents = filterEvents;

  function parseSheetData(data, outletName) {
    const rows = data.values.slice(1);
    const grouped = {};

    for (const row of rows) {
      if (row.length < 13 || !row[0] || !row[1]) continue;

      const [title, period, , , thumbnail, , desc, brand, product, price, , , eventId] = row;
      const dates = period.split("~");
      if (dates.length !== 2) continue;

      const start = parseDate(dates[0]);
      const end = parseDate(dates[1]);
      if (!start || !end) {
        console.log("❌ 날짜 파싱 제외 대상:", period);
        continue;
      }

      const key = `${title}_${start}_${end}`;
      if (!grouped[key]) {
        grouped[key] = {
          title: `[${outletName}] ${title}`,
          start,
          end,
          description: desc,
          outlet: outletName,
          items: [],
          thumbnail,
          event_id: eventId
        };
      }

      grouped[key].items.push({ brand, product, price });
    }

    return Object.values(grouped);
  }

  function parseDate(str) {
    const clean = str.replace(/\([^)]*\)/g, "").trim();
    if (!clean.includes(".")) return null;
    const parts = clean.split(".").map((p) => p.padStart(2, "0"));
    if (parts.length !== 2) return null;
    const [month, day] = parts;
    return `2025-${month}-${day}`;
  }

  function loadAllSheets() {
    const sheetId = "16JLl5-GVDSSQsdMowjZkTAzOmi6qkkz93to_GxMjQ18";
    const apiKey = "{{GOOGLE_API_KEY}}";
    const sheets = [
      { name: "Sheet1", outlet: "송도" },
      { name: "Sheet2", outlet: "김포" },
      { name: "Sheet3", outlet: "스페이스원" },
    ];

    gapi.load("client", () => {
      gapi.client.init({ apiKey }).then(() => {
        Promise.all(
          sheets.map((s) =>
            gapi.client.request({
              path: `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${s.name}!A2:M`,
            }).then((response) => parseSheetData(response.result, s.outlet))
          )
        ).then((results) => {
          rawEvents = results.flat();
          initCalendar(rawEvents);
        });
      });
    });
  }

  loadAllSheets();
});