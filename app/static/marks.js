/* Original candy marks in public brand colors. Not Ferrara logos or pack art. */
const BRAND_MARKS = {
  Nerds: '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><circle cx="11" cy="12" r="4" fill="#7b2d8e"/><circle cx="18" cy="9" r="3" fill="#b06ad4"/><circle cx="22" cy="16" r="4" fill="#7b2d8e"/><circle cx="14" cy="18" r="3.4" fill="#d7a6ea"/><circle cx="13" cy="24" r="2.3" fill="#7b2d8e"/></svg>',
  Trolli: '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 21c4-12 6 8 10-4s8-8 12 1" fill="none" stroke="#3d7a12" stroke-width="4" stroke-linecap="round"/><circle cx="26" cy="17" r="1.5" fill="#1d3d09"/></svg>',
  SweeTarts: '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="10" fill="#e23d8c"/><circle cx="16" cy="16" r="4" fill="#fff"/></svg>',
  "Laffy Taffy": '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M3 16 L9 11 H23 L29 16 L23 21 H9 Z" fill="#f0a202"/><path d="M9 11 L16 16 L9 21 M23 11 L16 16 L23 21" fill="none" stroke="#c48400" stroke-width="1.2"/></svg>',
  Butterfinger: '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><rect x="6" y="7" width="20" height="5" rx="1.5" fill="#e07a1f"/><rect x="6" y="13.5" width="20" height="5" rx="1.5" fill="#f4a24a"/><rect x="6" y="20" width="20" height="5" rx="1.5" fill="#e07a1f"/></svg>',
  "Baby Ruth": '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><rect x="5" y="11" width="22" height="10" rx="3" fill="#8c4a2f"/><path d="M8 16h16" stroke="#e7c7a4" stroke-width="2" stroke-linecap="round"/></svg>',
  "Brach's": '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 26C8 18 6 13 10 10c3-2 6 1 6 1s3-3 6-1c4 3 2 8-6 16z" fill="#dc1a41"/></svg>',
  Lemonhead: '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><ellipse cx="16" cy="17" rx="10" ry="8" fill="#e6b800"/><path d="M16 9c2 4 2 10 0 16" fill="none" stroke="#fff4b0" stroke-width="1.5"/></svg>',
};

function brandMark(name) {
  return BRAND_MARKS[name] || "";
}

function paintBrandMarks(root) {
  (root || document).querySelectorAll(".fam").forEach((node) => {
    if (node.querySelector("svg")) return;
    const name = node.textContent.trim();
    const svg = BRAND_MARKS[name];
    if (svg) node.insertAdjacentHTML("afterbegin", svg);
  });
}

paintBrandMarks(document);
