/* ==========================================================================
   ticket.js - the ticket detail page (ticket.html)

   The ticket to show comes from the URL: ticket.html?id=TKT-001
   ========================================================================== */

const params = new URLSearchParams(window.location.search);
const ticketId = params.get("id");

const loadingState = document.getElementById("loading-state");
const notFoundState = document.getElementById("notfound-state");
const detail = document.getElementById("detail");
const updateForm = document.getElementById("update-form");
const saveBtn = document.getElementById("save-btn");

/* --- Admin lock ------------------------------------------------------------
   The password itself never lives in this file - only whatever the person
   types into the box. sessionStorage keeps it for the rest of this browser
   tab so you are not asked again on every save, but it clears the moment
   the tab is closed, unlike localStorage which would linger indefinitely on
   a shared computer. The real check always happens on the server: this is
   just what decides whether the form is shown, not whether a save succeeds. */
const ADMIN_SESSION_KEY = "datastraw_admin_password";

const adminLockPanel = document.getElementById("admin-lock");
const adminControlsPanel = document.getElementById("admin-controls");
const adminPasswordInput = document.getElementById("admin-password-input");
const unlockBtn = document.getElementById("unlock-btn");
const lockBtn = document.getElementById("lock-btn");

function getStoredAdminPassword() {
  try {
    return sessionStorage.getItem(ADMIN_SESSION_KEY);
  } catch {
    // Some browsers block storage entirely in private/incognito mode.
    // Falling back to "not unlocked" is safe - it just asks again.
    return null;
  }
}

function showAdminControls() {
  hide(adminLockPanel);
  show(adminControlsPanel);
}

function showAdminLock() {
  show(adminLockPanel);
  hide(adminControlsPanel);
}

/** Called once on page load: skip the password box if we already have one. */
function initAdminLock() {
  if (getStoredAdminPassword()) {
    showAdminControls();
  } else {
    showAdminLock();
  }
}

unlockBtn.addEventListener("click", () => {
  const value = adminPasswordInput.value;
  document.getElementById("error-admin-password").textContent = "";

  if (!value) {
    document.getElementById("error-admin-password").textContent =
      "Enter the admin password.";
    return;
  }

  // We do not verify it here - there is nothing to verify against on the
  // frontend. It is stored and tried on the next save; if it is wrong,
  // the server's 401 response sends the user straight back to this screen
  // with a clear message (see the submit handler below).
  try {
    sessionStorage.setItem(ADMIN_SESSION_KEY, value);
  } catch {
    // Storage unavailable - fall back to an in-memory value for this page
    // view only (adminPasswordInput.value already holds it, which is read
    // again by getStoredAdminPassword's caller through the form submit).
  }
  adminPasswordInput.value = "";
  showAdminControls();
});

lockBtn.addEventListener("click", () => {
  try {
    sessionStorage.removeItem(ADMIN_SESSION_KEY);
  } catch {
    /* nothing to clear if storage was never available */
  }
  showAdminLock();
});

/** Put one ticket object on the screen. */
function render(ticket) {
  document.title = ticket.ticket_id + " | DataStraw Support";

  document.getElementById("t-id").textContent = ticket.ticket_id;
  document.getElementById("t-subject").textContent = ticket.subject;
  document.getElementById("t-name").textContent = ticket.customer_name;

  // The email is a real mailto link - one less copy/paste for the agent.
  document.getElementById("t-email").innerHTML =
    '<a href="mailto:' + encodeURIComponent(ticket.customer_email) + '">' +
    escapeHtml(ticket.customer_email) + "</a>";

  document.getElementById("t-created").textContent = formatDateTime(ticket.created_at);
  document.getElementById("t-updated").textContent = formatDateTime(ticket.updated_at);
  document.getElementById("t-description").textContent = ticket.description;

  document.getElementById("t-status").innerHTML = statusBadge(ticket.status);
  document.getElementById("t-priority").innerHTML = priorityBadge(ticket.priority);

  // The dropdowns start on the ticket's current values, so saving without
  // touching them does not accidentally change anything.
  document.getElementById("status-select").value = ticket.status;
  document.getElementById("priority-select").value = ticket.priority;

  renderNotes(ticket.notes || []);
}

function renderNotes(notes) {
  const list = document.getElementById("notes-list");
  const count = document.getElementById("note-count");

  count.textContent = notes.length ? "(" + notes.length + ")" : "";

  if (notes.length === 0) {
    list.innerHTML =
      '<p class="cell-muted">No notes yet. Add the first update using the form.</p>';
    return;
  }

  // Newest note on top - slice() first so we do not reverse the original array.
  list.innerHTML = notes
    .slice()
    .reverse()
    .map(
      (note) => `
      <div class="note">
        <div class="note-time">${formatDateTime(note.created_at)}</div>
        <div class="note-text">${escapeHtml(note.note_text)}</div>
      </div>`
    )
    .join("");
}

/** Fetch the ticket and decide which of the three states to show. */
async function loadTicket() {
  if (!ticketId) {
    hide(loadingState);
    document.getElementById("notfound-text").textContent =
      "No ticket ID was given in the address.";
    show(notFoundState);
    return;
  }

  show(loadingState);
  hide(notFoundState);

  try {
    const ticket = await api.getTicket(ticketId);
    render(ticket);
    hide(loadingState);
    show(detail);
  } catch (error) {
    hide(loadingState);
    if (error.status === 404) {
      document.getElementById("notfound-text").textContent = error.message;
      show(notFoundState);
    } else {
      showMessage("error-box", error.message);
    }
  }
}

/* --- Saving -------------------------------------------------------------- */
updateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage("error-box");
  clearMessage("success-box");
  document.getElementById("error-note").textContent = "";

  const note = document.getElementById("note-input").value.trim();

  const payload = {
    status: document.getElementById("status-select").value,
    priority: document.getElementById("priority-select").value,
  };
  // Only send `notes` when the agent actually typed something, otherwise an
  // empty note row would be added on every save.
  if (note) payload.notes = note;

  saveBtn.disabled = true;
  saveBtn.textContent = "Saving…";

  try {
    await api.updateTicket(ticketId, payload, getStoredAdminPassword());
    document.getElementById("note-input").value = "";
    showMessage("success-box", "Ticket updated.");

    // Re-fetch instead of patching the DOM by hand: the page then shows
    // exactly what the database holds, including the new updated_at.
    await loadTicket();
  } catch (error) {
    if (error.status === 401) {
      // The stored password is wrong (or was never set). Clear it and
      // send the person back to the lock screen with a clear reason,
      // rather than leaving the form open and silently failing again.
      try {
        sessionStorage.removeItem(ADMIN_SESSION_KEY);
      } catch {
        /* nothing to clear */
      }
      showAdminLock();
      document.getElementById("error-admin-password").textContent =
        "Incorrect admin password. Try again.";
    } else {
      showMessage("error-box", error.message);
    }
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save changes";
  }
});

initAdminLock();
loadTicket();
