/* RealmProof public engineering desk. Pure browser-side examples: no requests, storage, credentials or chain calls. */
(() => {
  "use strict";
  function ready() {
    const tabs = Array.from(document.querySelectorAll("[data-lab][role=tab]"));
    const panels = tabs.map(tab => document.getElementById(tab.getAttribute("aria-controls")));
    function activate(index, focus) {
      tabs.forEach((tab, i) => {
        const selected = i === index;
        tab.setAttribute("aria-selected", String(selected));
        tab.setAttribute("tabindex", selected ? "0" : "-1");
        tab.classList.toggle("is-active", selected);
        if (panels[i]) panels[i].hidden = !selected;
      });
      if (focus) tabs[index].focus();
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => activate(index, false));
      tab.addEventListener("keydown", event => {
        const step = event.key === "ArrowRight" || event.key === "ArrowDown" ? 1 :
                     event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 0;
        const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 :
                     step ? (index + step + tabs.length) % tabs.length : -1;
        if (next >= 0) { event.preventDefault(); activate(next, true); }
      });
    });
    const role = document.getElementById("rp-policy-role");
    const action = document.getElementById("rp-policy-action");
    const verdict = document.getElementById("rp-policy-verdict");
    const reason = document.getElementById("rp-policy-reason");
    if (role && action && verdict && reason) {
      const reset = () => {
        verdict.textContent = "Ready for evaluation";
        verdict.dataset.verdict = "";
        reason.textContent = "Select Evaluate to inspect the rule applied.";
      };
      role.addEventListener("change", reset);
      action.addEventListener("change", reset);
      document.getElementById("rp-policy-run").addEventListener("click", () => {
        const matrix = {viewer: ["read"], editor: ["read","modify","publish"], owner: ["read","modify","publish"]};
        const allowed = (matrix[role.value] || []).includes(action.value);
        verdict.textContent = allowed ? "ALLOW · example policy" : "DENY · example policy";
        verdict.dataset.verdict = allowed ? "allow" : "deny";
        reason.textContent = "role=" + role.value + " · operation=" + action.value +
                             " · permitted=" + String(allowed);
      });
    }

    const before = document.getElementById("rp-source-before");
    const after = document.getElementById("rp-source-after");
    const diffOutput = document.getElementById("rp-diff-output");
    const diffCount = document.getElementById("rp-diff-count");
    if (before && after && diffOutput && diffCount) {
      const baseline = before.value, changed = after.value;
      const reset = () => {
        diffOutput.textContent = "Run comparison to inspect changed lines.";
        diffCount.textContent = "NOT COMPARED";
      };
      before.addEventListener("input", reset);
      after.addEventListener("input", reset);
      document.getElementById("rp-diff-reset").addEventListener("click", () => {
        before.value = baseline; after.value = changed; reset();
      });
      document.getElementById("rp-diff-run").addEventListener("click", () => {
        const a = before.value.replace(/\r\n?/g, "\n").split("\n");
        const z = after.value.replace(/\r\n?/g, "\n").split("\n");
        if (a.length > 50 || z.length > 50) {
          diffCount.textContent = "INPUT LIMIT";
          diffOutput.textContent = "Compare no more than 50 lines in each editor.";
          return;
        }
        const m = a.length, n = z.length;
        const dp = Array.from({length:m+1}, () => Array(n+1).fill(0));
        for (let i=m-1;i>=0;i--) for (let j=n-1;j>=0;j--)
          dp[i][j] = a[i]===z[j] ? 1+dp[i+1][j+1] : Math.max(dp[i+1][j],dp[i][j+1]);
        let i=0,j=0,plus=0,minus=0;
        const fragment = document.createDocumentFragment();
        while (i<m || j<n) {
          let type, line;
          if (i<m && j<n && a[i]===z[j]) {type="same";line=a[i++];j++;}
          else if (j<n && (i===m || dp[i][j+1]>dp[i+1][j])) {type="add";line=z[j++];plus++;}
          else {type="remove";line=a[i++];minus++;}
          const el = document.createElement("div");
          el.className = "rp-diff-line rp-diff-" + type;
          const prefix=document.createElement("span");
          prefix.textContent=type==="add"?"+":type==="remove"?"−":" ";
          const code=document.createElement("code");
          code.textContent=line || " ";
          el.append(prefix,code);
          fragment.append(el);
        }
        diffOutput.replaceChildren(fragment);
        diffCount.textContent = plus + " ADDED · " + minus + " REMOVED";
        if (!plus && !minus) diffCount.textContent = "NO TEXT CHANGE";
      });
    }

    const textA = document.getElementById("rp-fingerprint-a");
    const textB = document.getElementById("rp-fingerprint-b");
    const hashA = document.getElementById("rp-fingerprint-hash-a");
    const hashB = document.getElementById("rp-fingerprint-hash-b");
    const fingerprintStatus = document.getElementById("rp-fingerprint-status");
    const fingerprintNote = document.getElementById("rp-fingerprint-note");
    const fingerprintRun = document.getElementById("rp-fingerprint-run");
    if (textA && textB && hashA && hashB && fingerprintRun) {
      let revision = 0;
      const reset=() => {
        revision++;
        hashA.textContent="Run calculation to generate the digest.";
        hashB.textContent="Run calculation to generate the digest.";
        fingerprintStatus.textContent="NOT COMPUTED";
        fingerprintStatus.dataset.match="";
        fingerprintNote.textContent="Local computation only; no blockchain verification.";
      };
      textA.addEventListener("input", reset);
      textB.addEventListener("input", reset);
      const sha256 = async value => {
        const bytes = new TextEncoder().encode(value);
        const digest = await crypto.subtle.digest("SHA-256", bytes);
        return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2,"0")).join("");
      };
      fingerprintRun.addEventListener("click", async () => {
        if (!window.crypto || !window.crypto.subtle || !window.TextEncoder) {
          fingerprintStatus.textContent="UNAVAILABLE";
          fingerprintNote.textContent="SHA-256 requires a secure browser context (HTTPS or localhost).";
          return;
        }
        const version=revision, x=textA.value, y=textB.value;
        fingerprintRun.disabled=true;
        fingerprintStatus.textContent="CALCULATING";
        try {
          const [a,z] = await Promise.all([sha256(x),sha256(y)]);
          if (version !== revision) return;
          hashA.textContent=a;
          hashB.textContent=z;
          const same=a===z;
          fingerprintStatus.textContent=same?"DIGESTS MATCH":"DIGESTS DIFFER";
          fingerprintStatus.dataset.match=same?"same":"different";
          fingerprintNote.textContent=same ?
            "Both inputs produce the same SHA-256 digest. This does not prove their origin." :
            "The inputs differ by content. Their SHA-256 digests are different.";
        } catch (_) {
          if (version !== revision) return;
          fingerprintStatus.textContent="CALCULATION FAILED";
          fingerprintNote.textContent="This browser could not calculate the digest locally.";
        } finally {
          fingerprintRun.disabled=false;
        }
      });
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready);
  else ready();
})();