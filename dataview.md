## 🔍 Suspected One-Way Links

```dataviewjs
const pages = dv.pages('"success_criteria"').concat(dv.pages('"symptom"')).concat(dv.pages('"root_cause"'));
let seen = {};

for (let p of pages) {
  let fromId = p.id;
  let links = (p.caused_by || []).concat(p.triggers_symptoms || []).concat(p.triggers_root_causes || []).concat(p.threatened_by || []);
  for (let toId of links) {
    toId = String(toId).replace("[[", "").replace("]]", "").trim();
    if (!seen[fromId]) seen[fromId] = new Set();
    seen[fromId].add(toId);
  }
}

let result = [];

for (let fromId in seen) {
  for (let toId of seen[fromId]) {
    if (!seen[toId] || !seen[toId].has(fromId)) {
      result.push({ Source: fromId, Target: toId, Issue: "Unidirectional" });
    }
  }
}

dv.table(["Source", "Target", "Issue"], result.map(row => [row.Source, row.Target, row.Issue]))

