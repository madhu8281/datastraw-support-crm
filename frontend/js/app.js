/* =========================================================
   DataStraw Support Dashboard
   ========================================================= */


const searchInput =
  document.getElementById(
    "search-input"
  );

const statusFilter =
  document.getElementById(
    "status-filter"
  );

const priorityFilter =
  document.getElementById(
    "priority-filter"
  );

const loadingState =
  document.getElementById(
    "loading-state"
  );

const emptyState =
  document.getElementById(
    "empty-state"
  );

const tableWrapper =
  document.getElementById(
    "table-wrapper"
  );

const ticketRows =
  document.getElementById(
    "ticket-rows"
  );

const resultCount =
  document.getElementById(
    "result-count"
  );


/* =========================================================
   ADMIN
   ========================================================= */

const adminLogin =
  document.getElementById(
    "admin-login"
  );

const adminLoginBtn =
  document.getElementById(
    "admin-login-btn"
  );

const adminUnlockBtn =
  document.getElementById(
    "dashboard-unlock-btn"
  );

const adminPassword =
  document.getElementById(
    "dashboard-admin-password"
  );

const adminError =
  document.getElementById(
    "dashboard-admin-error"
  );

const adminStatus =
  document.getElementById(
    "admin-status"
  );

const adminDashboard =
  document.getElementById(
    "admin-dashboard"
  );


const ADMIN_SESSION_KEY =
  "datastraw_admin_password";


function getAdminPassword() {

  try {

    return sessionStorage.getItem(
      ADMIN_SESSION_KEY
    );

  } catch {

    return null;

  }

}


function setAdminMode(password) {

  try {

    sessionStorage.setItem(
      ADMIN_SESSION_KEY,
      password
    );

  } catch {}


  adminStatus.textContent =
    "Admin unlocked";

  adminStatus.className =
    "admin-status unlocked";

  adminLoginBtn.textContent =
    "Lock admin";

  hide(adminLogin);

  show(adminDashboard);

}


function lockAdmin() {

  try {

    sessionStorage.removeItem(
      ADMIN_SESSION_KEY
    );

  } catch {}


  adminStatus.textContent =
    "Admin locked";

  adminStatus.className =
    "admin-status locked";

  adminLoginBtn.textContent =
    "Admin access";

  hide(adminDashboard);

}


adminLoginBtn.addEventListener(
  "click",
  () => {

    if (getAdminPassword()) {

      lockAdmin();

      return;
    }

    adminLogin.classList.toggle(
      "hidden"
    );

    if (
      !adminLogin.classList.contains(
        "hidden"
      )
    ) {

      adminPassword.focus();

    }

  }
);


adminUnlockBtn.addEventListener(
  "click",
  async () => {

    const value =
      adminPassword.value.trim();

    adminError.textContent =
      "";

    if (!value) {

      adminError.textContent =
        "Enter the admin password.";

      return;
    }


    adminUnlockBtn.disabled =
      true;

    adminUnlockBtn.textContent =
      "Checking...";


    try {

      await api.verifyAdmin(
        value
      );

      setAdminMode(
        value
      );

      await Promise.all([
        loadStats(),
        loadTickets()
      ]);

      adminPassword.value = "";

    } catch (error) {

      adminError.textContent =
        error.message;

    } finally {

      adminUnlockBtn.disabled =
        false;

      adminUnlockBtn.textContent =
        "Unlock";

    }

  }
);


adminPassword.addEventListener(
  "keydown",
  event => {

    if (
      event.key === "Enter"
    ) {

      adminUnlockBtn.click();

    }

  }
);


/* =========================================================
   ADMIN TICKET TABLE
   ========================================================= */

function renderRow(ticket) {

  const admin =
    Boolean(
      getAdminPassword()
    );


  const action =
    admin

      ? `
        <div class="quick-action">

          <select
            class="select quick-status"
            data-ticket-id="${escapeHtml(ticket.ticket_id)}"
          >

            <option
              ${ticket.status === "Open" ? "selected" : ""}
            >
              Open
            </option>

            <option
              ${ticket.status === "In Progress" ? "selected" : ""}
            >
              In Progress
            </option>

            <option
              ${ticket.status === "Closed" ? "selected" : ""}
            >
              Closed
            </option>

          </select>


          <select
            class="select quick-priority"
            data-ticket-id="${escapeHtml(ticket.ticket_id)}"
          >

            <option
              ${ticket.priority === "High" ? "selected" : ""}
            >
              High
            </option>

            <option
              ${ticket.priority === "Medium" ? "selected" : ""}
            >
              Medium
            </option>

            <option
              ${ticket.priority === "Low" ? "selected" : ""}
            >
              Low
            </option>

          </select>


          <button
            class="btn btn-primary btn-small quick-save"
            data-ticket-id="${escapeHtml(ticket.ticket_id)}"
          >
            Save
          </button>


          <a
            class="btn btn-secondary btn-small"
            href="ticket.html?id=${encodeURIComponent(ticket.ticket_id)}"
          >
            View
          </a>

        </div>
      `

      : `
        <a
          class="btn btn-secondary btn-small"
          href="ticket.html?id=${encodeURIComponent(ticket.ticket_id)}"
        >
          View
        </a>
      `;


  return `

    <tr>

      <td>
        <span class="ticket-id">
          ${escapeHtml(ticket.ticket_id)}
        </span>
      </td>

      <td>
        ${escapeHtml(ticket.customer_name)}
      </td>

      <td class="cell-subject">
        ${escapeHtml(ticket.subject)}
      </td>

      <td>
        ${priorityBadge(ticket.priority)}
      </td>

      <td>
        ${statusBadge(ticket.status)}
      </td>

      <td class="cell-muted">
        ${formatDate(ticket.created_at)}
      </td>

      <td class="cell-action">
        ${action}
      </td>

    </tr>

  `;
}


async function loadStats() {

  try {

    const stats =
      await api.getStats();


    document.getElementById(
      "stat-total"
    ).textContent =
      stats.total;


    document.getElementById(
      "stat-open"
    ).textContent =
      stats.open;


    document.getElementById(
      "stat-progress"
    ).textContent =
      stats.in_progress;


    document.getElementById(
      "stat-closed"
    ).textContent =
      stats.closed;


    document.getElementById(
      "stat-high"
    ).textContent =
      stats.high_priority_open
        ? stats.high_priority_open +
          " high priority"
        : "";

  } catch (error) {

    console.error(
      "Stats failed:",
      error
    );

  }

}


async function loadTickets() {

  clearMessage(
    "error-box"
  );

  show(loadingState);
  hide(emptyState);
  hide(tableWrapper);


  const filters = {

    search:
      searchInput.value.trim(),

    status:
      statusFilter.value,

    priority:
      priorityFilter.value

  };


  try {

    const tickets =
      await api.listTickets(
        filters
      );


    hide(loadingState);


    if (!tickets.length) {

      const filtered =
        filters.search ||
        filters.status ||
        filters.priority;


      document.getElementById(
        "empty-title"
      ).textContent =
        filtered
          ? "No tickets match"
          : "No tickets yet";


      document.getElementById(
        "empty-text"
      ).textContent =
        filtered
          ? "Try a different search."
          : "Raise the first customer ticket.";


      show(emptyState);

      return;

    }


    ticketRows.innerHTML =
      tickets
        .map(renderRow)
        .join("");


    resultCount.textContent =
      tickets.length === 1
        ? "1 ticket"
        : tickets.length + " tickets";


    show(tableWrapper);

    bindQuickActions();

  } catch (error) {

    hide(loadingState);

    showMessage(
      "error-box",
      error.message
    );

  }

}


function bindQuickActions() {

  document
    .querySelectorAll(
      ".quick-save"
    )
    .forEach(
      btn => {

        btn.addEventListener(
          "click",
          async () => {

            const id =
              btn.dataset.ticketId;


            const select =
              document.querySelector(
                `.quick-status[data-ticket-id="${CSS.escape(id)}"]`
              );


            const priority =
              document.querySelector(
                `.quick-priority[data-ticket-id="${CSS.escape(id)}"]`
              );


            const password =
              getAdminPassword();


            if (!password) {

              lockAdmin();

              return;
            }


            btn.disabled =
              true;

            btn.textContent =
              "Saving...";


            try {

              await api.updateTicket(
                id,
                {
                  status:
                    select.value,

                  priority:
                    priority.value
                },
                password
              );


              await Promise.all([
                loadStats(),
                loadTickets()
              ]);


            } catch (error) {

              if (
                error.status === 401
              ) {

                lockAdmin();

                adminError.textContent =
                  "Admin session expired. Unlock again.";

              } else {

                showMessage(
                  "error-box",
                  error.message
                );

              }

            } finally {

              btn.disabled =
                false;

              btn.textContent =
                "Save";

            }

          }
        );

      }
    );

}


function debounce(
  fn,
  delay
) {

  let timerId;

  return function (...args) {

    clearTimeout(
      timerId
    );

    timerId =
      setTimeout(
        () =>
          fn.apply(
            this,
            args
          ),
        delay
      );

  };

}


searchInput.addEventListener(
  "input",
  debounce(
    loadTickets,
    300
  )
);


statusFilter.addEventListener(
  "change",
  loadTickets
);


priorityFilter.addEventListener(
  "change",
  loadTickets
);


/* =========================================================
   CUSTOMER EMAIL PORTAL
   ========================================================= */

const customerEmail =
  document.getElementById(
    "customer-email"
  );

const customerSearchBtn =
  document.getElementById(
    "customer-search-btn"
  );

const customerError =
  document.getElementById(
    "customer-error"
  );

const customerLoading =
  document.getElementById(
    "customer-loading"
  );

const customerResults =
  document.getElementById(
    "customer-results"
  );


function renderCustomerTicket(
  ticket
) {

  let statusMessage = "";

  if (ticket.status === "Open") {

    statusMessage =
      "Your ticket has been received and is waiting for support.";

  } else if (
    ticket.status === "In Progress"
  ) {

    statusMessage =
      "Our support team is currently working on your issue.";

  } else if (
    ticket.status === "Closed"
  ) {

    statusMessage =
      "This issue has been marked as resolved/closed.";

  }


  return `

    <div
      class="card"
      style="
        padding:20px;
        margin-bottom:15px;
      "
    >

      <div
        style="
          display:flex;
          justify-content:space-between;
          gap:15px;
          flex-wrap:wrap;
        "
      >

        <div>

          <span class="ticket-id">
            ${escapeHtml(ticket.ticket_id)}
          </span>

          <h3 style="margin-top:8px;">
            ${escapeHtml(ticket.subject)}
          </h3>

        </div>


        <div>

          ${statusBadge(ticket.status)}

        </div>

      </div>


      <p
        style="
          margin-top:15px;
          font-weight:600;
        "
      >
        ${escapeHtml(statusMessage)}
      </p>


      <div
        style="
          margin-top:15px;
        "
      >

        <strong>
          Issue:
        </strong>

        <p>
          ${escapeHtml(ticket.description)}
        </p>

      </div>


      <div
        class="cell-muted"
        style="margin-top:15px;"
      >

        Priority:
        ${escapeHtml(ticket.priority)}

        <br>

        Created:
        ${formatDateTime(ticket.created_at)}

        <br>

        Last updated:
        ${formatDateTime(ticket.updated_at)}

      </div>

    </div>

  `;
}


async function searchCustomerTickets() {

  customerError.textContent =
    "";

  customerResults.innerHTML =
    "";

  hide(customerResults);


  const email =
    customerEmail.value
      .trim()
      .toLowerCase();


  if (!email) {

    customerError.textContent =
      "Please enter your email address.";

    return;

  }


  customerSearchBtn.disabled =
    true;

  customerSearchBtn.textContent =
    "Checking...";

  show(customerLoading);


  try {

    const tickets =
      await api.getCustomerTickets(
        email
      );


    hide(customerLoading);


    if (!tickets.length) {

      customerError.textContent =
        "No tickets were found for this email address.";

      return;

    }


    customerResults.innerHTML = `

      <h3>
        Your tickets
      </h3>

      <p
        class="cell-muted"
        style="margin-bottom:15px;"
      >
        ${tickets.length}
        ticket${tickets.length === 1 ? "" : "s"}
        found for
        ${escapeHtml(email)}
      </p>

      ${tickets
        .map(renderCustomerTicket)
        .join("")}

    `;


    show(customerResults);

  } catch (error) {

    hide(customerLoading);

    customerError.textContent =
      error.message;

  } finally {

    customerSearchBtn.disabled =
      false;

    customerSearchBtn.textContent =
      "Check ticket";

  }

}


customerSearchBtn.addEventListener(
  "click",
  searchCustomerTickets
);


customerEmail.addEventListener(
  "keydown",
  event => {

    if (
      event.key === "Enter"
    ) {

      searchCustomerTickets();

    }

  }
);


/* =========================================================
   INITIAL ADMIN CHECK
   ========================================================= */

const storedAdminPassword =
  getAdminPassword();


if (storedAdminPassword) {

  api.verifyAdmin(
    storedAdminPassword
  )

    .then(
      async () => {

        setAdminMode(
          storedAdminPassword
        );

        await Promise.all([
          loadStats(),
          loadTickets()
        ]);

      }
    )

    .catch(
      () => {

        lockAdmin();

      }
    );

} else {

  hide(adminDashboard);

}
