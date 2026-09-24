/* ==========================================================================
   create-ticket.js - the new ticket form (create-ticket.html)

   Flow: validate in the browser -> POST /api/tickets -> show the new
   ticket ID -> open the ticket detail page.
   ========================================================================== */

const form = document.getElementById("ticket-form");
const submitBtn = document.getElementById("submit-btn");

const fields = ["customer_name", "customer_email", "subject", "description"];

/** Print the message under one field and mark the input red. */
function setFieldError(field, message) {
  document.getElementById("error-" + field).textContent = message;
  document.getElementById(field).classList.toggle("invalid", Boolean(message));
}

function clearFieldErrors() {
  fields.forEach((field) => setFieldError(field, ""));
}

/**
 * Browser-side validation.
 *
 * Note this does NOT replace the backend checks in schemas.py. Anyone can
 * bypass the browser with curl or Postman, so the server validates too.
 * This copy exists only to give instant feedback without a round trip.
 */
function validate(values) {
  let firstInvalid = null;

  if (values.customer_name.length < 2) {
    setFieldError("customer_name", "Enter the customer's name (at least 2 characters).");
    firstInvalid = firstInvalid || "customer_name";
  }

  // A deliberately simple pattern: something, @, something, dot, something.
  // The real check is EmailStr on the server.
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.customer_email)) {
    setFieldError("customer_email", "Enter a valid email address, like name@example.com.");
    firstInvalid = firstInvalid || "customer_email";
  }

  if (values.subject.length < 3) {
    setFieldError("subject", "Enter a short subject (at least 3 characters).");
    firstInvalid = firstInvalid || "subject";
  }

  if (values.description.length < 5) {
    setFieldError("description", "Describe the issue in a few words (at least 5 characters).");
    firstInvalid = firstInvalid || "description";
  }

  return firstInvalid;
}

form.addEventListener("submit", async (event) => {
  // Stop the browser from reloading the page - we send the data ourselves.
  event.preventDefault();

  clearFieldErrors();
  clearMessage("error-box");
  clearMessage("success-box");

  const values = {
    customer_name: document.getElementById("customer_name").value.trim(),
    customer_email: document.getElementById("customer_email").value.trim(),
    subject: document.getElementById("subject").value.trim(),
    description: document.getElementById("description").value.trim(),
    priority: document.getElementById("priority").value,
  };

  const firstInvalid = validate(values);
  if (firstInvalid) {
    document.getElementById(firstInvalid).focus();
    return;
  }

  // Loading state: disable the button so a double click cannot create
  // two identical tickets.
  submitBtn.disabled = true;
  submitBtn.textContent = "Creating…";

  try {
    const created = await api.createTicket(values);

    showMessage(
      "success-box",
      "Ticket " + created.ticket_id + " created. Opening it now…"
    );
    form.reset();

    // Short pause so the agent actually sees the generated ID.
    setTimeout(() => {
      window.location.href = "ticket.html?id=" + encodeURIComponent(created.ticket_id);
    }, 1200);
  } catch (error) {
    showMessage("error-box", error.message);
    submitBtn.disabled = false;
    submitBtn.textContent = "Create ticket";
  }
});
