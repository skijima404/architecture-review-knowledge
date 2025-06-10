# Architecture Review Knowledge Vault

This repository contains a structured knowledge base for supporting architecture reviews.  
It is organized as an Obsidian Vault, describing Success Criteria, Symptoms (failure patterns), and Root Causes as a graph-based model.

---

## 📘 Purpose

- To capture and structure failure patterns and their underlying causes observed during architecture reviews.
- To translate cause-effect diagrams (e.g., Miro-based) into maintainable, navigable knowledge.
- To provide a foundation for analysis using Graph Databases or for supporting RAG (Retrieval-Augmented Generation) with AI.

---

## 📁 Directory Structure

```plaintext
vault/
├── success_criteria/     # Success Criteria nodes (red)
├── symptom/              # Observed failure symptoms (blue, solid lines)
├── root_cause/           # Structural causes (blue, dotted lines)
├── dataview/             # Obsidian Dataview queries
└── templates/            # Templates for node definition
```

---

## 🛠 How to Use

### Open in Obsidian

1. Launch the Obsidian app.
2. Use "Open folder as vault" and select this repository.

### Add a new node

1. Create a `.md` file under one of the folders: `success_criteria/`, `symptom/`, or `root_cause/`
2. Use the provided template and define metadata in the YAML frontmatter.
3. Use `caused_by` or `threatened_by` fields to define relationships.

---

## 🧠 Integration with Graph DB

This Vault can be converted into a Cypher script to import into Neo4j or other Graph DBs.  
Scripts for conversion will be maintained in a separate `scripts/` folder or repository.

---

## ⚠️ Notes

- Obsidian environment settings (plugins, themes, workspace) are excluded via `.gitignore`.
- Node `id` values (e.g., `rc-001`) should be unique and follow agreed naming rules.

---

## 📚 License

[MIT](LICENSE) or as defined by internal policy (update as necessary).