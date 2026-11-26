/* Progressive enhancement for the public verification walkthrough. No network calls or production execution. */
(() => {
 "use strict";
 const ready = () => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduced && "IntersectionObserver" in window) document.documentElement.classList.add("rp-enhanced");
  document.querySelectorAll("[data-reveal]").forEach(node => { if (!("IntersectionObserver" in window) || reduced) {node.classList.add("is-visible");} });
  if ("IntersectionObserver" in window && !reduced) {
   const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) {entry.target.classList.add("is-visible");observer.unobserve(entry.target);}
   }), {threshold:.08,rootMargin:"0px 0px -35px 0px"});
   document.querySelectorAll("[data-reveal]").forEach(el => observer.observe(el));
  }
  const balance = document.getElementById("rp-balance"), amount=document.getElementById("rp-amount");
  const auth=document.getElementById("rp-authorized"), preview=document.getElementById("rp-preview");
  if (!(balance && amount && auth && preview)) return;
  const input=document.getElementById("rp-trace-input"), expected=document.getElementById("rp-trace-expected");
  const observed=document.getElementById("rp-trace-observed"), status=document.getElementById("rp-preview-status");
  const toggleLabel=document.querySelector(".rp-toggle-text");
  const cases={valid:{balance:120,amount:35,authorized:true},funds:{balance:20,amount:35,authorized:true},permission:{balance:120,amount:35,authorized:false}};
  let lastPreview=null;
  const evaluate=()=>{
   const b=Number(balance.value), a=Number(amount.value), authorized=auth.checked;
   if(!Number.isSafeInteger(b)||!Number.isSafeInteger(a)||b<0||a<=0||b>1000000||a>1000000) return null;
   const outcome=!authorized?"permission_denied":a>b?"insufficient_funds":"ok";
   return {outcome, remaining:outcome==="ok"?b-a:b};
  };
  const update=()=>{
   const e=evaluate();
   toggleLabel.textContent=auth.checked?"Yes":"No";
   input.textContent="balance="+(balance.value||"?")+" · amount="+(amount.value||"?")+" · authorized="+auth.checked;
   expected.textContent=e?"status="+e.outcome+" · remaining="+e.remaining:"Enter whole numbers within the stated limits";
   preview.disabled=!e;
   if (!lastPreview || lastPreview!==input.textContent){observed.textContent="Select “Preview model result” to compare";status.innerHTML='<span class="rp-status-dot"></span> NOT EVALUATED';}
  };
  document.querySelectorAll("[data-case]").forEach(btn=>btn.addEventListener("click",()=>{
    const chosen=cases[btn.dataset.case];if(!chosen)return;
    balance.value=chosen.balance;amount.value=chosen.amount;auth.checked=chosen.authorized;
    document.querySelectorAll("[data-case]").forEach(item=>{const selected=item===btn;item.classList.toggle("is-selected",selected);item.setAttribute("aria-pressed",String(selected));});
    lastPreview=null;update();
  }));
  [balance,amount,auth].forEach(el=>el.addEventListener("input",()=>{lastPreview=null;update();}));
  preview.addEventListener("click",()=>{
   const e=evaluate();if(!e)return;
   lastPreview=input.textContent;
   observed.textContent="status="+e.outcome+" · remaining="+e.remaining;
   status.innerHTML='<span class="rp-status-dot"></span> MODEL PREVIEW MATCHES EXPECTED';
  });
  update();
 };
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",ready);else ready();
})();