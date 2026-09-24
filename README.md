# CaptainMILO: AI-Assisted MILP Formulation with Knowledge Graphs

![GitHub License](https://img.shields.io/badge/license-Apache%202.0-blue.svg) 

### 📄 Published Paper

**From Informal Descriptions to Formal MILP Models Through a Multi-Agent Approach with Structured Knowledge Integration**

Published in the **PAKDD 2026 – 30th Pacific-Asia Conference on Knowledge Discovery and Data Mining**, as part of the *Lecture Notes in Computer Science* series (Vol. 16599), Springer.

🔗 <a href="https://link.springer.com/chapter/10.1007/978-981-92-1465-5_21" target="_blank">Read the Published Paper on Springer ↗</a>

**DOI:** <a href="https://doi.org/10.1007/978-981-92-1465-5_21" target="_blank">10.1007/978-981-92-1465-5_21</a>

**Published:** 09 June 2026  
**Pages:** 265–277  
**Publisher:** Springer, Singapore

**Authors:** Jyotheesh Gaddam, Qingyang Li, Lele Zhang, Bahadorreza Ofoghi, Diego Molla-Aliod

---

CaptainMILO is an AI-powered multi-agent system designed to help engineers, analysts, and non-experts formulate Mixed-Integer Linear Programming (MILP) models from natural language descriptions.

Instead of manually writing constraints and objectives, users describe their optimisation scenario in plain language. CaptainMILO then guides a structured conversation, progressively constructing a well-formed MILP model using MILOG knowledge graphs and a graph-aware beam search engine.

---

## 🚀 Key Features

- **Human-in-the-loop optimisation assistant**
  Interacts conversationally to collect entities, objectives, and constraints for a wide range of MILP problems.

- **MILOG knowledge graph–driven**
  Uses structured MILP ontologies (MILOGs) to ground the formulation in well-defined variables, costs, and constraint patterns.

- **Multi-agent architecture**
  - *Questioning Agent (Agent_IC)* – asks context-aware, graph-guided questions.
  - *Writing Expert* – produces a progressive plain-language summary.
  - *Maths Expert* – builds the mathematical model step-by-step.
  - *Proctor Agents* – monitor quality and enforce behavioural rules.

- **Dynamic beam search over the knowledge graph**
  Each user message is mapped to relevant graph nodes via BERT embeddings and a dynamic beam search, ensuring questions and constraints stay aligned with MILP structure.

- **Progressive MILP model construction**
  The system incrementally builds the objective function, decision variables, and constraints as the conversation unfolds.

---

## 🧠 System Overview

At a high level, CaptainMILO works as follows:

1. The user describes an optimisation problem in natural language.
2. The **Questioning Agent** uses the MILOG tree graph plus beam search to decide which aspect to ask about next.
3. The **Writing Expert** maintains a running, human-readable summary of the problem definition.
4. The **Maths Expert** constructs a mathematical model only from information that has been explicitly stated, using graph-linked constraint templates.
5. **Proctor Agents** supervise each expert, detecting redundant questions, missing objectives, poor summaries, or invalid mathematical behaviour.
6. The user can review and download the full conversation, summary, and mathematical model as a JSON file.

CaptainMILO focuses on *formulation* only: it produces a MILP model but does not solve it.

---

## 🔧 Installation

### Prerequisites

- Python **3.10+**
- PyTorch
- Transformers
- Gradio
- An OpenAI-compatible API key

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

```bash
python Code/app.py
```

Then open the local URL printed in the terminal (usually `http://127.0.0.1:7860/`) in your browser.

---

## 💬 Usage Workflow

1. **Start the application**  
   Launch the Gradio interface using the command above.

2. **Configure the model**
   - Select a model (e.g. `gpt-4o`, `gpt-4o-mini`)
   - Paste your API key.
   - Click **“Set Configuration ⚙️”**.

3. **Describe your optimisation problem**
   Use natural language to describe your scenario.

4. **Answer clarifying questions**
   The Questioning Agent uses beam search to determine what to ask next.

5. **Monitor the right-hand panels**
   - **Summary tab**
   - **Mathematical Model tab**

6. **Download results**
   A JSON file with:
   - Full conversation
   - Final summary
   - Final mathematical model

---

## ⚠️ Limitations

- Requires an external LLM API key to function.
- Coverage depends on the MILOG graph.
- The system **only formulates** models, it does **not** solve them.

---
## 📁 Repository Structure

```
CaptainMILO/
├── Auto Answering Agent Testing/
│   ├── Automated agent behaviour evaluation
│   └── Batch test scripts and results
├── Code/
│   ├── Core multi-agent implementation
│   ├── Dynamic beam search engine
│   ├── MILP Knowledge Graph (tree_graphs)
│   ├── Gradio chat interface
│   └── Model configuration utilities
├── Human User Testing/
│   ├── Real-user interaction logs
│   └── Feedback and evaluation data
├── Knowledge Graphs/
│   ├── MILOG structures
│   ├── Constraint templates
│   └── GraphNode hierarchy definitions
├── Test Instances/
│   ├── Predefined optimisation scenarios
│   └── Evaluation input files
└── README.md
```

---
## 📜 Citation

If you use this work in your research, please cite:

```bibtex
@inproceedings{Gaddam2026CaptainMILO,
  author    = {Jyotheesh Gaddam and Qingyang Li and Lele Zhang and Bahadorreza Ofoghi and Diego Molla-Aliod},
  title     = {From Informal Descriptions to Formal MILP Models Through a Multi-Agent Approach with Structured Knowledge Integration},
  booktitle = {Advances in Knowledge Discovery and Data Mining},
  series    = {Lecture Notes in Computer Science},
  volume    = {16599},
  pages     = {265--277},
  year      = {2026},
  publisher = {Springer},
  doi       = {10.1007/978-981-92-1465-5_21}
}
