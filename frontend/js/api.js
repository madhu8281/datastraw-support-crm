const API_BASE =
  window.location.protocol === "file:"
    ? "http://127.0.0.1:8000/api"
    : "/api";


async function apiRequest(path, options = {}) {

  let response;

  try {

    response = await fetch(
      API_BASE + path,
      {
        ...options,

        headers: {
          "Content-Type": "application/json",
          ...(options.headers || {})
        }
      }
    );

  } catch (networkError) {

    throw new Error(
      "Could not reach the server. Check that the backend is running."
    );
  }


  const body =
    response.status === 204
      ? null
      : await response.json().catch(() => null);


  if (!response.ok) {

    let message =
      (body && body.detail)
      ||
      "Request failed (" + response.status + ")";


    if (
      body &&
      Array.isArray(body.errors) &&
      body.errors.length
    ) {

      message +=
        " " +
        body.errors.join(" · ");
    }


    const error =
      new Error(message);

    error.status =
      response.status;

    throw error;
  }


  return body;
}


const api = {

  listTickets(params = {}) {

    const query =
      new URLSearchParams();

    if (params.search)
      query.set(
        "search",
        params.search
      );

    if (params.status)
      query.set(
        "status",
        params.status
      );

    if (params.priority)
      query.set(
        "priority",
        params.priority
      );

    const suffix =
      query.toString()
        ? "?" + query.toString()
        : "";

    return apiRequest(
      "/tickets" + suffix
    );
  },


  getStats() {

    return apiRequest(
      "/stats"
    );
  },


  verifyAdmin(adminPassword) {

    return apiRequest(
      "/admin/verify",
      {
        method: "POST",

        headers: {
          "X-Admin-Password":
            adminPassword
        }
      }
    );
  },


  getTicket(ticketId) {

    return apiRequest(
      "/tickets/" +
      encodeURIComponent(ticketId)
    );
  },


  createTicket(data) {

    return apiRequest(
      "/tickets",
      {
        method: "POST",
        body: JSON.stringify(data)
      }
    );
  },


  updateTicket(
    ticketId,
    data,
    adminPassword
  ) {

    return apiRequest(
      "/tickets/" +
      encodeURIComponent(ticketId),
      {
        method: "PUT",

        body:
          JSON.stringify(data),

        headers:
          adminPassword
            ? {
                "X-Admin-Password":
                  adminPassword
              }
            : {}
      }
    );
  },


  // -------------------------------------------------------
  // CUSTOMER EMAIL SEARCH
  // -------------------------------------------------------

  getCustomerTickets(email) {

    return apiRequest(
      "/customer/tickets?email=" +
      encodeURIComponent(email)
    );
  }
};


// -------------------------------------------------------
// HELPERS
// -------------------------------------------------------

function parseUtc(value) {

  if (!value)
    return null;

  const hasZone =
    /Z|[+-]\d{2}:\d{2}$/.test(value);

  const date =
    new Date(
      hasZone
        ? value
        : value + "Z"
    );

  return isNaN(date.getTime())
    ? null
    : date;
}


function formatDate(value) {

  const date =
    parseUtc(value);

  if (!date)
    return "-";

  return date.toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric"
    }
  );
}


function formatDateTime(value) {

  const date =
    parseUtc(value);

  if (!date)
    return "-";

  return date.toLocaleString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    }
  );
}


function escapeHtml(value) {

  if (
    value === null ||
    value === undefined
  )
    return "";

  return String(value)
    .replace(
      /&/g,
      "&amp;"
    )
    .replace(
      /</g,
      "&lt;"
    )
    .replace(
      />/g,
      "&gt;"
    )
    .replace(
      /"/g,
      "&quot;"
    )
    .replace(
      /'/g,
      "&#39;"
    );
}


function statusBadge(status) {

  const slug =
    String(status)
      .toLowerCase()
      .replace(/\s+/g, "-");

  return (
    '<span class="badge status-' +
    slug +
    '">' +
    escapeHtml(status) +
    "</span>"
  );
}


function priorityBadge(priority) {

  const slug =
    String(priority)
      .toLowerCase();

  return (
    '<span class="badge priority-' +
    slug +
    '">' +
    escapeHtml(priority) +
    "</span>"
  );
}


function show(element) {

  if (element)
    element.classList.remove(
      "hidden"
    );
}


function hide(element) {

  if (element)
    element.classList.add(
      "hidden"
    );
}


function showMessage(
  boxId,
  text
) {

  const box =
    document.getElementById(
      boxId
    );

  if (!box)
    return;

  box.textContent =
    text;

  show(box);
}


function clearMessage(boxId) {

  const box =
    document.getElementById(
      boxId
    );

  if (!box)
    return;

  box.textContent = "";

  hide(box);
}
