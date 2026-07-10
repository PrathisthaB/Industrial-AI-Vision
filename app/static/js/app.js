/*
 * Industrial AI Vision — shared client-side utilities.
 * Page-specific logic (live feed control, chart wiring) lives inline in each
 * template's {% block scripts %} since it depends on server-rendered data;
 * this file holds small helpers reused across pages.
 */

function formatTimestamp(isoString) {
  try {
    const d = new Date(isoString.replace(" ", "T"));
    return d.toLocaleString();
  } catch (e) {
    return isoString;
  }
}

function toast(message, kind = "info") {
  console.log(`[${kind}]`, message);
}
