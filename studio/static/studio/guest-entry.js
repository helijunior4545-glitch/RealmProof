const guestEntry = document.getElementById("guest-entry");

if (guestEntry) {
  const button = guestEntry.querySelector("button");

  guestEntry.addEventListener("submit", event => {
    if (guestEntry.getAttribute("aria-busy") === "true") {
      event.preventDefault();
      return;
    }
    guestEntry.setAttribute("aria-busy", "true");
    button.disabled = true;
    button.textContent = "Preparing your guest session…";
  });

  guestEntry.requestSubmit();
}
