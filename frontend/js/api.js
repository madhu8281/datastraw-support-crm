/* ==========================================================================
   api.js - shared helpers used by all three pages.

   Loaded first in every HTML file, so the functions here are available to
   app.js, create-ticket.js and ticket.js.
   ========================================================================== */

/**
 * Where the API lives.
 *
 * In production (and when running uvicorn locally) FastAPI serves BOTH the
 * HTML and the API from the same address, so a relative "/api" is correct
 * and we never have to edit a hard-coded URL before deploying.
 *
 * The only exception is opening index.html directly from the file system
 * (file:///...). Then there is no server, so we point at the local backend.
 */
const API_BASE =
  window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : "/api";

/**
 * One wrapper around fetch() for every request in the app.
 *
 * It does three jobs:
 *   1. sends JSON and asks for JSON back
 *   2. turns any non-2xx response into a thrown Error with a readable message
 *   3. turns a network failure into a readable message too
 *
 * Because every caller can rely on "it either returns data or throws",
 * the page code stays short.
 */
async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(API_BASE + path, {
      ...options,
      // Merge headers rather than letting `options.headers` fully replace
      // this default, so a caller can add X-Admin-Password without having
      // to remember to also repeat Content-Type every time.
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
  } catch (networkError) {
    // fetch() only rejects when the request never reached the server:
    // no internet, server down, wrong port.
    throw new Error("Could not reach the server. Check that the backend is running.");
  }

  // Some platform-level errors are HTML/text instead of JSON. Read the
  // response safely so the customer never sees "Unexpected token <".
  let body = null;
  if (response.status !== 204) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      body = await response.json().catch(() => null);
    } else {
      const text = await response.text().catch(() => "");
      if (text) body = { detail: text.slice(0, 300) };
    }
  }

  if (!response.ok) {
    let message = (body && body.detail) || "Request failed (" + response.status + ")";
    // Our backend adds an "errors" array for validation problems (422).
    if (body && Array.isArray(body.errors) && body.errors.length) {
      message += " " + body.errors.join(" · ");
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return body;
}

/* --- Small API functions, named after what they do ----------------------- */
const api = {
  listTickets(params = {}) {
    // URLSearchParams handles the encoding, so "In Progress" safely becomes
    // "In%20Progress" without us doing string surgery.
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.status) query.set("status", params.status);
    if (params.priority) query.set("priority", params.priority);
    const suffix = query.toString() ? "?" + query.toString() : "";
    return apiRequest("/tickets" + suffix);
  },

  getStats() {
    return apiRequest("/stats");
  },

  verifyAdmin(adminPassword) {
    return apiRequest("/admin/verify", {
      method: "POST",
      headers: { "X-Admin-Password": adminPassword },
    });
  },

  getTicket(ticketId) {
    let adminPassword = null;
    try { adminPassword = sessionStorage.getItem("datastraw_admin_password"); } catch {}
    return apiRequest("/tickets/" + encodeURIComponent(ticketId), {
      headers: adminPassword ? { "X-Admin-Password": adminPassword } : {},
    });
  },

  createTicket(data) {
    return apiRequest("/tickets", { method: "POST", body: JSON.stringify(data) });
  },

  updateTicket(ticketId, data, adminPassword) {
    return apiRequest("/tickets/" + encodeURIComponent(ticketId), {
      method: "PUT",
      body: JSON.stringify(data),
      // Only attached when we actually have a password to send, so an
      // absent one comes through as "no header" rather than "header set
      // to the text null" - the server treats both the same, but this
      // keeps the request honest.
      headers: adminPassword ? { "X-Admin-Password": adminPassword } : {},
    });
  },
};

/* --- Formatting helpers -------------------------------------------------- */

/**
 * The backend stores and returns UTC timestamps without a timezone marker
 * ("2026-05-04T09:15:00"). JavaScript would read that as LOCAL time and the
 * clock would be wrong by a few hours. Adding "Z" tells it "this is UTC",
 * and toLocaleString then converts it to the viewer's own timezone.
 */
function parseUtc(value) {
  if (!value) return null;
  const hasZone = /Z|[+-]\d{2}:\d{2}$/.test(value);
  const date = new Date(hasZone ? value : value + "Z");
  return isNaN(date.getTime()) ? null : date;
}

function formatDate(value) {
  const date = parseUtc(value);
  if (!date) return "-";
  return date.toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatDateTime(value) {
  const date = parseUtc(value);
  if (!date) return "-";
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Escape anything a customer typed before putting it into innerHTML.
 * Without this, a description containing <script> would actually run in the
 * agent's browser (an XSS bug). Turning < > & " into HTML entities makes the
 * text display exactly as typed and never execute.
 */
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** "In Progress" -> "status-in-progress" so the CSS class matches. */
function statusBadge(status) {
  const slug = String(status).toLowerCase().replace(/\s+/g, "-");
  return '<span class="badge status-' + slug + '">' + escapeHtml(status) + "</span>";
}

function priorityBadge(priority) {
  const slug = String(priority).toLowerCase();
  return '<span class="badge priority-' + slug + '">' + escapeHtml(priority) + "</span>";
}

/* --- Tiny DOM helpers ---------------------------------------------------- */
function show(element) { if (element) element.classList.remove("hidden"); }
function hide(element) { if (element) element.classList.add("hidden"); }

function showMessage(boxId, text) {
  const box = document.getElementById(boxId);
  if (!box) return;
  box.textContent = text;
  show(box);
}

function clearMessage(boxId) {
  const box = document.getElementById(boxId);
  if (!box) return;
  box.textContent = "";
  hide(box);
}
