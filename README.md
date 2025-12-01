# CaptainMILO: AI-Assisted MILP Formulation with Knowledge Graphs

Welcome to CaptainMILO! 🚀

CaptainMILO is an AI-powered multi-agent system designed to assist engineers and managers in formulating Mixed-Integer Linear Programming (MILP) models through natural language interactions. Unlike traditional AI tools that require deep technical expertise, CaptainMILO engages users in an interactive, adaptive conversation, guiding them through problem formulation without needing prior knowledge of MILP structures.

## Why CaptainMILO?
- 🧠 Human-in-the-Loop AI: Works as a co-pilot, assisting users in defining optimization problems dynamically.
- 📊 Knowledge Graph-Driven: Utilizes structured Knowledge Graphs (KGs) to ensure accurate MILP formulations.
- 💡 Adaptive & Interactive: Uses a multi-agent system to refine problem definitions in real time.
- ⚡ Benchmark Performance: Outperforms GPT-4o Zero-Shot and Graph-Guided Prompting in MILP formulation accuracy and usability.

## How It Works
- 1️⃣ Users describe an optimization problem in natural language.
- 2️⃣ CaptainMILO dynamically asks clarifying questions, guided by structured KGs.
- 3️⃣ The system progressively constructs a MILP model, refining constraints and objectives based on user input.
- 4️⃣ Users receive a well-structured MILP formulation, ensuring accuracy and completeness.

## 🖥️ Interface Overview

The chatbot interface consists of the following key components:

### 1️⃣ Model Selection & API Key Input  
- Select the AI model (**e.g., GPT-4o**) from the dropdown.  
- Enter an **API key** for access.  
- Adjust system settings via the **"Set Configuration"** button.  

### 2️⃣ Chat Interaction Panel (Left Side)  
- Displays the **ongoing conversation** between the user and CaptainMILO.  
- Users describe their **optimization problem in natural language**, and CaptainMILO **asks clarifying questions** dynamically, guided by structured KGs.  
### 3️⃣ Dynamic Summary & Mathematical Model Panel (Right Side)  
- This panel **progressively updates in real-time** based on user inputs:  
  - **Summary Mode:** Provides an evolving **natural language summary** of the problem, capturing user-provided details as the conversation unfolds.  
  - **Mathematical Model Mode:** Dynamically constructs and refines the **MILP model**, updating variables, constraints, and the objective function as more information is provided.  
- Users can switch between these views using the **"Switch to Mathematical Model"** button.  

### 4️⃣ User Input & Controls (Bottom Section)  
- **Text input box** for user responses.  
- **Send button (➤)** to submit queries.  
- **Download button** to export the **conversation or the generated MILP model**.  

## 🔹 How It Works  
- 1️⃣ The user **describes the optimization problem** in natural language.  
- 2️⃣ CaptainMILO **asks relevant follow-up questions**, dynamically adjusting based on user responses.  
- 3️⃣ The **Summary Panel updates progressively**, ensuring an accurate and structured representation of the problem.  
- 4️⃣ As more details are provided, the **Mathematical Model Panel dynamically updates**, refining constraints, decision variables, and objectives.  
- 5️⃣ The user can **review, refine, and download** the evolving problem description and MILP model at any point.  

This interactive, step-by-step approach ensures that users do not need deep technical knowledge to create complex MILP models—making optimization more accessible and intuitive.

Here is the screenshot of CaptainMILO user interface developed in HuggingFace.

![image](https://github.com/user-attachments/assets/63b68899-5963-4048-8425-8edd71eb542d)

