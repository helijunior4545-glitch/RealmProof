(() => {
 const items = Array.from(document.querySelectorAll(".rp-cap-item"));
 if (!items.length) return;
 const explorer = items[0].parentElement;
 explorer.classList.add("is-enhanced");
 const activate = item => { for (const other of items) other.open = other === item; };
 for (const item of items) {
   const summary = item.querySelector("summary");
   summary.addEventListener("pointerenter", event => {
     if (event.pointerType === "mouse" && matchMedia("(hover: hover) and (min-width: 761px)").matches && !explorer.querySelector(".rp-cap-content :focus")) activate(item);
   });
   summary.addEventListener("focus", () => activate(item));
   summary.addEventListener("click", event => { event.preventDefault(); activate(item); });
 }
})();