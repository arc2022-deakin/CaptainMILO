import re
import gradio as gr
from autogen import ConversableAgent, AssistantAgent, GroupChatManager, GroupChat
import torch
from transformers import BertTokenizer, BertModel
from collections import deque
import json
import io
import tempfile

import tree_graphs  # tree graph file

###############################################################################
# FILE DOWNLOAD HELPER
###############################################################################

def prepare_download(conversation_html, summary_html, maths_html):
    """
    Prepare a JSON file containing:
    - plain-text conversation (HTML tags stripped)
    - plain-text summary
    - plain-text mathematical model

    This returns an in-memory BytesIO object for Gradio's File output.
    """
    try:
        data = {
            "conversation": re.sub(r"<.*?>", "", conversation_html or ""),
            "summary": re.sub(r"<.*?>", "", summary_html or ""),
            "mathematical_model": re.sub(r"<.*?>", "", maths_html or ""),
        }

        json_data = json.dumps(data, indent=4)
        bytes_io = io.BytesIO(json_data.encode("utf-8"))
        bytes_io.name = "conversation_summary_model.json"
        return bytes_io
    except Exception as e:
        print(f"Error preparing download: {e}")
        return None

###############################################################################
# SIMPLE HTML FORMATTERS FOR CHAT + SUMMARY + MATHS
###############################################################################

def format_agent_message(message: str) -> str:
    """
    Clean up markdown-ish tokens and convert simple structure into HTML.
    Used only for the visible chat pane (left).
    """
    if message is None:
        message = ""
    cleaned_message = re.sub(r"\\\[|\#\#\#|\*\*", "", message)
    formatted_message = cleaned_message.replace("- Step", "<br><b>Step</b>")
    formatted_message = formatted_message.replace("- ", "<br>- ")
    formatted_message = formatted_message.replace(": ", ":<br>")
    formatted_message = formatted_message.replace("\n", "<br>")
    return formatted_message


def format_summary(summary: str) -> str:
    """
    Summary is plain text (or light markdown) from writing_expert.
    We only convert newlines to <br>.
    """
    if summary is None:
        summary = ""
    cleaned_content = re.sub(r"\\\[|\#\#\#|\*\*", "", summary)
    formatted_summary = cleaned_content.replace("\n", "<br>")
    return formatted_summary


def format_math_content(math_content: str) -> str:
    """
    Maths content may contain LaTeX.
    We:
      - clean some markdown tokens
      - convert newlines to <br>
      - wrap in \\[ ... \\] so MathJax will render it.
    """
    if math_content is None:
        math_content = ""
    cleaned_content = re.sub(r"\\\[|\#\#\#|\*\*", "", math_content)
    formatted_content = cleaned_content.replace("\n", "<br>")
    formatted_content = f"\\[{formatted_content}\\]"
    return formatted_content


def append_to_chat(history, sender: str, message: str):
    """
    Append a new message (user or agent) into the vertical chat HTML history.
    - history is a list of HTML strings
    """
    if history is None:
        history = []
    if not isinstance(history, list):
        history = [history]

    if sender == "user":
        formatted_message = (
            f'<div class="user-message"><b>👀:</b> {message}</div>'
        )
    else:
        formatted_message = (
            f'<div class="agent-message"><b>🤖:</b>{format_agent_message(message)}</div>'
        )

    return history + [formatted_message]


def initiate_chat():
    """
    Initial greeting in the left chat pane after configuration is set.
    """
    greeting_message = "Hello Human 👋! How can I assist you today?"
    return append_to_chat([], "agent", greeting_message)

###############################################################################
# BERT utilities for semantic similarity between user text and graph nodes
###############################################################################

# Load BERT once (global)
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")


def get_bert_embeddings(text: str) -> torch.Tensor:
    """
    Compute a single embedding vector for a short piece of text using BERT.
    We average token embeddings over the sequence dimension.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings


###############################################################################
# Graph + root + small helpers
###############################################################################

# Root of MILP graph
GRAPH_ROOT = tree_graphs.root_milp


def looks_like_math(text: str) -> bool:
    """
    Heuristic test: is this node label likely a mathematical expression?
    We use this to decide what to send to the maths_expert.
    """
    math_triggers = ["\\sum", "<=", ">=", "=", "_", "^", " for ", "i in", "j in"]
    return any(tok in text for tok in math_triggers)

###############################################################################
# BEAM SEARCH OVER THE TREE GRAPH
###############################################################################

def _cosine_sim(a: torch.Tensor, b: torch.Tensor) -> float:
    """Cosine similarity between two 1 x d tensors."""
    return torch.nn.functional.cosine_similarity(a, b).item()


def local_expansion(start_node, max_distance, scored_nodes, user_emb, seen):
    """
    Locally expand around a promising node up to a given graph distance.
    This pulls in:
      - its children
      - its parent (if available)
      - its siblings (if parent available)
    Helpful for exploring related constraints / objective terms.
    """
    q = deque([(start_node, 0)])

    while q:
        node, dist = q.popleft()
        if dist >= max_distance:
            continue

        # Collect neighbours: parent + children + siblings
        neighbours = []

        parent = getattr(node, "parent", None)
        if parent is not None:
            neighbours.append(parent)
            for sibling in getattr(parent, "children", []):
                if sibling is not node:
                    neighbours.append(sibling)

        neighbours.extend(getattr(node, "children", []))

        for neigh in neighbours:
            if neigh in seen:
                continue
            seen.add(neigh)
            emb = get_bert_embeddings(neigh.value)
            score = _cosine_sim(user_emb, emb)
            scored_nodes[neigh] = score
            q.append((neigh, dist + 1))


def dynamic_beam_search(
    root,
    user_text: str,
    initial_beam_width: int = 4,
    max_beam_width: int = 10,
    max_depth: int = 6,
) -> list:
    """
    Beam search over the MILP knowledge graph, guided by BERT similarity
    between node labels and the current user_text.

    Returns a list of nodes sorted by descending similarity.
    """
    user_emb = get_bert_embeddings(user_text)

    queue = deque([(root, 0)])
    seen = set()
    scored_nodes = {}
    beam_width = initial_beam_width

    while queue:
        level_size = len(queue)
        level_candidates = []

        # Visit this level
        for _ in range(level_size):
            node, depth = queue.popleft()
            if node in seen or depth > max_depth:
                continue
            seen.add(node)

            node_emb = get_bert_embeddings(node.value)
            score = _cosine_sim(user_emb, node_emb)
            scored_nodes[node] = score
            level_candidates.append((score, node, depth))

        if not level_candidates:
            break

        # Sort by similarity and keep top beam_width
        level_candidates.sort(key=lambda x: x[0], reverse=True)
        k = min(beam_width, len(level_candidates))
        active = level_candidates[:k]

        # Adaptive beam width
        if len(active) == beam_width and beam_width < max_beam_width:
            beam_width += 1
        elif len(active) < beam_width and beam_width > initial_beam_width:
            beam_width -= 1

        # Expand children + local expansion around strong nodes
        for score, node, depth in active:
            for child in getattr(node, "children", []):
                if child not in seen:
                    queue.append((child, depth + 1))

            # Pull in neighbours near promising node
            local_expansion(
                start_node=node,
                max_distance=2,
                scored_nodes=scored_nodes,
                user_emb=user_emb,
                seen=seen,
            )

    # Rank all scored nodes by similarity
    ranked = sorted(scored_nodes.items(), key=lambda x: x[1], reverse=True)
    return [node for node, score in ranked]

###############################################################################
# GRAPH CONTEXT HELPERS
###############################################################################

def get_node_path(node) -> str:
    """
    Reconstruct a human-readable path from some ancestor to this node.
    Uses optional .parent pointers if they exist.
    """
    path = []
    curr = node
    safety = 0  # avoid infinite loops if parent not well-defined

    while curr is not None and safety < 200:
        path.append(curr.value)
        curr = getattr(curr, "parent", None)
        safety += 1

    path.reverse()
    return " > ".join(path)


def find_relevant_graph_nodes(user_text: str, top_k: int = 8) -> list:
    """
    Run dynamic beam search over the unified MILP tree and return
    the top_k most relevant nodes for this user_text.
    """
    ranked_nodes = dynamic_beam_search(GRAPH_ROOT, user_text)
    return ranked_nodes[:top_k]


def extract_math_expressions_from_nodes(nodes: list, top_k: int = 8) -> list:
    """
    From a list of nodes, select those that look like mathematical
    edge/leaf expressions, to guide the maths_expert.
    """
    math_nodes = [n for n in nodes if looks_like_math(n.value)]
    return math_nodes[:top_k]


def build_questioning_graph_context(nodes: list) -> str:
    """
    Build an internal context block for Agent_IC, listing the most
    relevant MILP graph paths. Agent_IC uses this to choose the next question.
    """
    if not nodes:
        return ""

    lines = [
        "[INTERNAL GRAPH CONTEXT FOR QUESTIONING AGENT]",
        "The following MILP graph nodes are most relevant to the user's latest message.",
        "Use these to decide what to ask about next.",
        "Do NOT echo this block verbatim to the user.",
        "",
    ]
    for i, node in enumerate(nodes, 1):
        lines.append(f"{i}. {get_node_path(node)}")

    return "\n".join(lines)


def build_math_graph_context(math_nodes: list) -> str:
    """
    Build an internal context block for the maths_expert, listing
    candidate mathematical expressions corresponding to constraints
    or objective terms mentioned by the user.
    """
    if not math_nodes:
        return ""

    lines = [
        "[INTERNAL GRAPH CONTEXT FOR MATHEMATICAL MODEL]",
        "These candidate expressions come from the MILP graph and are likely",
        "related to the constraints or objective that the user has mentioned.",
        "",
    ]
    for i, node in enumerate(math_nodes, 1):
        lines.append(f"{i}. {node.value}")

    return "\n".join(lines)


###############################################################################
# AUTOGEN AGENT SETUP
###############################################################################

class ProctorAgent(AssistantAgent):
    """
    Simple monitoring agent to check for rule violations or model gaps.
    Its prompts tell it when to speak; here we just use it like a normal AssistantAgent.
    """
    pass


# "User" is a ConversableAgent stub so autogen can maintain shared history
User = ConversableAgent(
    name="User",
    llm_config=False,
    human_input_mode="ALWAYS",
)

Agent_IC = None
writing_expert = None
maths_expert = None

proctor_ic = None
proctor_maths = None
proctor_writing = None

# ---------------------------------------------------------------------------
# SYSTEM PROMPT CONSTANTS (PLACEHOLDERS)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_AGENT_IC = """
You are an optimization expert specializing in questioning. Ensure to confirm the user’s context before diving into specific scenarios. Please ask an open-ended question to better understand the user’s needs and goals. Your role is to guide the user in providing relevant information for defining an optimization problem. Use clear and flexible questioning based on the provided graph, while adapting dynamically to the user’s inputs.

Guidelines for Effective Questioning:
	•	Guide the Conversation Using the Graph: Use the graph’s nodes and relationships to guide the questioning process, ensuring each question is based on the current node and the connected nodes. Start with general categories and progressively move to more specific nodes, adapting to the user’s responses.
	•	Flexibility: If the user jumps to a specific node, adapt the next question based on their input and adjust the flow accordingly, ensuring coherence with the graph and maintaining logical progression.
	•	Ask One Question at a Time and Maintain Context: Focus on one specific node or aspect per question to avoid overwhelming the user. Contextual Continuity: Use the context from previous responses to frame follow-up questions. Ensure that your next question builds logically on the answer provided. Avoid abruptly shifting to unrelated topics unless the user explicitly directs the conversation there.

Provide Feedback on User Responses:
	•	Acknowledge User Input: After each response, acknowledge and provide a brief confirmation that you have understood the information. Use phrases like “Thank you for that information” or “Got it, I appreciate the detail.”
	•	Apologize for Redundancy or Mistakes: If you ask about information the user has already provided, acknowledge the mistake and offer a sincere apology. For example: “I apologize, I see now that you have already mentioned these details. Thank you for pointing it out, and I appreciate your patience.”
	•	Show Empathy When Needed: If the user expresses frustration or irritation, show empathy to repair the situation: “I understand that this can be frustrating. I appreciate your patience, and I will ensure that I do not repeat questions moving forward.”

Adaptive Questioning with Dependency Management:
	•	Handling Predecessor-Successor Relationships: If a user confirms that a node (e.g., a specific process or constraint) is relevant, make sure any predecessor nodes that impact it are visited and questioned. Conversely, if a user excludes a node, avoid asking about its successors. Always ensure logical dependencies are respected. For instance, if a user excludes the “time window” concept, avoid asking about penalties related to early or late arrivals.
	•	Avoid Out-of-Context Questions: Ensure questions are consistent with the user’s current context. Avoid asking questions that don’t logically fit based on what the user has shared.
	•	Avoid Redundant or Irrelevant Questions: Track user responses dynamically to avoid repeating questions for information that has already been provided. Information Processing: Use the provided answers to formulate subsequent questions. If information has already been given (e.g., “there is no time window”), make sure to exclude related questions (e.g., “lateness penalties”).
	•	Error Handling for Repeated Questions: If a repeated question is mistakenly asked and the user points it out, respond gracefully: “I apologize for the oversight. I see that you’ve already shared this information, and I will use it as we move forward. Thank you for your understanding.”

Ensure Coverage of Key Elements:
	•	Ensure that critical elements of the scenario are covered. For example, always gather information on the objective of the scenario if it hasn’t already been discussed. This should happen early in the process to help frame subsequent questions.
	•	If the user hasn’t provided details about the scenario’s objective by the end, explicitly ask about it: “Could you clarify the main objective of this scenario? For instance, are you looking to minimize costs or maximize profit?”

Graceful Ending of Questioning:
	•	Detect Stopping Points: When the user indicates that they have provided all the relevant information and have no more details to add, gracefully end the questioning phase.
	•	Polite Closure: Use language like, “Thank you for providing all these details. Let me know if you want to add or modify any information” to conclude the questioning phase respectfully and open-endedly.

Avoid Providing Summaries or Mathematical Models: Your role is strictly focused on questioning. Do not provide any summaries or attempt to formulate a mathematical model unless explicitly requested by the user.

Handling Summary or Mathematical Model Requests:
	•	When a User Requests a Summary: Response: “Please refer to the ‘Summary’ tab on the right side for a comprehensive overview of the information gathered so far.”
	•	When a User Requests a Mathematical Model: Response: “For the detailed mathematical model, please check the ‘Mathematical Model’ tab located on the right side.”
	•	Example Responses:
User: “Can you provide a summary of our discussion so far?”
Assistant: “Please refer to the ‘Summary’ tab on the right side for a comprehensive overview of the information gathered so far.”
User: “I need the mathematical model for this problem.”
Assistant: “For the detailed mathematical model, please check the ‘Mathematical Model’ tab located on the right side.”
	Ensure that your responses maintain a consistent and professional tone, aligned with the guidelines above.

"""

SYSTEM_PROMPT_WRITING = """
You are tasked with continuously identifying and listing the key points of the user-provided optimization problem information as it becomes available. Additionally, you should highlight any missing information required to fully define the problem. However, a full summary should only be provided when explicitly requested by the user. Focus exclusively on optimization-related content, ignoring any general conversation, unrelated discussions, or irrelevant details.

Guidelines for Handling Information and Summarization Requests:
	•	Progressive Key Points Updates:
Initial Information:
Provided: List relevant data points provided.
Needed: Specify missing critical information.
As New Details Emerge:
Provided: Add new data points to the list.
Needed: Update missing information based on current progress.
	•	When User Requests a Summary:
Write a Full Summary: Provide a structured and comprehensive summary based on all the information gathered up to that point. Include all relevant details such as the scenario overview, product details, resource constraints, and the optimization objective.
	•	Filter Out Irrelevant Information:
Include Only Relevant Data: Focus on information pertinent to the optimization problem.
Exclude Non-Essentials: Disregard any unrelated conversations or side discussions.
	•	Use a Structured Format:
For Key Points: Use bullet points to clearly distinguish between what has been provided and what is still needed.
For Full Summaries: Use paragraphs with logical groupings for clarity and coherence when summarizing.
	•	Avoid Mathematical Notations:
Use Plain Language: Describe relationships and constraints without equations or symbols.
	•	Acknowledge Missing Information:
Highlight Missing Data: Explicitly mention any critical details that are pending.

Suggested Structure:
	•	For Progressive Key Points (Default Mode):
Scenario Overview:
Provided: High-level description of the optimization scenario.
Needed: Additional contextual details.
Product or Process Details:
Provided: Key product/process information (costs, production details, etc.).
Needed: Further specifics on products or processes.
Resource and Constraints:
Provided: Available resources and known constraints.
Needed: Additional constraints or missing resource details.
Optimization Objective:
Provided: Primary goal (e.g., minimize cost, maximize profit).
Needed: Further elaboration on objectives or secondary goals.
Constraints Summary:
Provided: Known critical constraints.
Needed: Missing constraint details (e.g., demand, budget).
	•	If no information is yet provided, just say “waiting for more information to write your summary”.

Guidelines for Writing the Full Summary:
	•	Filter Out Irrelevant Information:
Only include information that directly pertains to the optimization scenario. Exclude general conversation, user comments, side discussions, or any information that is not essential to defining the optimization problem.
	•	Structured and Readable Summary:
Organization: Structure the summary logically, grouping similar information together for readability.
Consistency: Reflect key points clearly, using consistent terminology throughout. As new information is provided, ensure updates are seamlessly integrated.
Clarity: Write in a natural, easy-to-follow manner. Summarize information using concise paragraphs, avoiding bullet points where unnecessary.
	•	Avoid Mathematical Notations:
Use plain language only. Do not include any mathematical equations, formulas, or symbols. Describe relationships and constraints in practical, easy-to-understand terms without mathematical complexity.
	•	Acknowledge Missing Information:
If a critical component of the summary is still missing, mention it clearly, such as:
“The resource constraints are not fully defined yet,” or
“Details about the objective function are pending.”
Avoid waiting for complete information before starting the summary. Instead, aim to provide a partial but coherent summary that gets progressively more complete.
	•	Suggested Structure for the Summary:
Scenario Overview: Provide a brief overview of the situation, including what is being optimized (e.g., profit maximization, cost minimization) and the key elements involved (e.g., products, resources). Update this section dynamically as more information becomes available.
Product or Process Details: Describe the key components of the problem, such as products or processes involved, their costs, and production details. Expand and refine this section as new product-related information is provided.
Resource and Constraints: Outline the key resources available (e.g., labor, materials) and any constraints on these resources. Clearly state the limits and restrictions that must be adhered to, and update progressively as new constraints are described.
Optimization Objective: Summarize the goal of the problem (e.g., maximize profit, minimize costs). If the objective is not fully specified yet, include any partial details that are available.
Constraints Summary: State all the critical constraints, such as resource limits and product demand limits, using straightforward language. If specific constraints are missing, note this but still include any known constraints.
	•	Example of a Progressive Summary:
Scenario Overview: Currently, the goal is to optimize the production of multiple products across two plants while managing costs and capacity constraints. The details provided so far focus on minimizing the costs associated with production and shipping.
Product Details: So far, we know about two products produced at different plants. Each product incurs certain costs and requires specific resources. More detailed information about production costs is still needed.
Resource Constraints: The current resource constraints include production capacity for each plant, which is capped at specific levels. Additional information on resource requirements, such as labor hours, has not been provided yet.
Optimization Objective: The objective is to minimize production and transportation costs while meeting demand. Specific costs for transportation between plants and distribution centers have been provided, but details about other cost components are still pending.
Constraints Summary:
Production Capacity: The Adelaide plant has a maximum capacity of 100,000 tons per month, while the Brisbane plant has 250,000 tons.
Demand Requirements: Some monthly demand values for distribution centers have been provided, but details for all centers and months are still being gathered.
Further information on additional constraints, such as labor or budget limits, is still required.

If there is not enough relevant information available yet, respond with:
“Here’s the current summary based on the provided information. As you share more, I’ll continue to update and refine the summary.”
"""

SYSTEM_PROMPT_MATHS = """
You are tasked with progressively formulating a mathematical model for an optimization problem based on the user-provided information. Your objective is to build a structured mathematical model, starting with partial elements as information becomes available. Focus strictly on the relevant details related to the optimization scenario, ignoring any unrelated conversation or general information. Only proceed with the model construction if you have enough information for that specific component, and indicate if more information is needed to complete a step.

Guidelines for Mathematical Model Construction:
	•	Progressive Construction of the Mathematical Model:
Begin building components of the mathematical model as soon as the relevant information becomes available, updating dynamically as the user provides more details. Clearly note missing components where more information is required to proceed (e.g., missing constraints, incomplete cost information). Provide partial equations or outline individual components if they are not yet complete, and indicate which parts are pending.
	•	Filter Out Irrelevant Information:
Focus only on content directly related to the optimization scenario. Exclude any general conversation, irrelevant user comments, or information that is not critical for defining the optimization model.
	•	Construct the Mathematical Model:
Use Collected Information Only: The model should be strictly built from the information provided by the user and Agent_IC, without adding assumptions or additional elements.
Variables, Objective Function, Constraints: Write each component (variables, objective function, constraints) only when enough information is available for that specific part. If complete information is not available, explain what’s missing.
	•	Avoid Providing Code or Solutions:
No Code: Do not generate code or solve the model. Politely inform the user if they request more than the mathematical formulation.
No Solver Guidance: Do not offer suggestions on how the user could solve the model themselves.

Suggested Structure for Mathematical Model Creation:
	•	Step 1: Understand the Problem:
Summarize the scenario to identify the key objective and elements involved (e.g., products, resources). Keep the summary concise and focused only on optimization-related content.
Example: “The goal is to maximize profit from producing two products, soldiers and trains, under resource and demand constraints.”
	•	Step 2: Identify Key Components:
Products or Processes: Describe the products, processes, or activities involved.
Resources: Identify resources such as labor or materials that are relevant to the problem.
Constraints: Summarize constraints like resource availability and demand limits.
Example: “Labor constraints include 100 hours of finishing labor and 80 hours of carpentry labor each week.”
	•	Step 3: Define Decision Variables:
Define decision variables that will be used in the model (e.g., production quantities).
Example: “Let $x_1$ represent the number of soldiers produced, and $x_2$ represent the number of trains produced each week.”
	•	Step 4: Formulate the Objective Function:
Construct an objective function representing the user’s goal (e.g., maximizing profit or minimizing cost).
Example: “Maximize $Z = 3x_1 + 2x_2$, where $Z$ represents the weekly profit.”
	•	Step 5: Define Constraints:
List all constraints based on the information provided by the user.
Example:
Finishing Labor: “$2x_1 + x_2 \le 100$” (finishing labor constraint).
Carpentry Labor: “$x_1 + x_2 \le 80$” (carpentry labor constraint).
Demand: “$x_1 \le 40$” (maximum demand for soldiers).
Non-negativity: “$x_1, x_2 \ge 0$.”
	•	Step 6: Formulate the Linear Programming Model:
Combine the objective function and constraints into a complete model.
Example:
Objective: Maximize $Z = 3x_1 + 2x_2$
Subject to:
$2x_1 + x_2 \le 100$ (finishing labor)
$x_1 + x_2 \le 80$ (carpentry labor)
$x_1 \le 40$ (soldier demand limit)
$x_1, x_2 \ge 0$ (non-negativity)

Important Notes:
Exclude All Irrelevant Information: Only focus on formulating the mathematical model, strictly based on the given optimization scenario.
Do Not Solve the Model: Your task is only to formulate the model, not to solve it or provide any programming solutions.

If there is insufficient information, reply with:
“Waiting for more information to start formulating the mathematical model.”
"""

SYSTEM_PROMPT_PROCTOR_IC = """
You are a Proctor Agent responsible for monitoring the Questioning Agent {Agent_IC} to ensure it adheres to its guidelines and maintains the highest standard of questioning. Your primary role is to oversee the conversation, identify any deviations from the established protocol, and provide real-time alerts or suggestions to the Questioning Agent when necessary. You do not interact directly with the user, but your feedback helps refine the questioning process.

Key Responsibilities:
	•	Monitor Adherence to Guidelines:
Ensure Agent_IC follows the questioning flow as defined by the provided graph, maintaining logical progression.
Verify that each question focuses on a single node or aspect at a time.
Check that Agent_IC respects predecessor-successor relationships and avoids out-of-context or redundant questions.
	•	Detect and Alert for Errors:
Identify repeated or redundant questions and prompt Agent_IC to acknowledge and correct them.
Alert Agent_IC if it shifts topics abruptly without logical continuity.
Ensure Agent_IC does not provide summaries or mathematical models unless explicitly requested.
	•	Ensure Adaptive and Empathetic Questioning:
Monitor that Agent_IC uses user responses to adapt its questioning dynamically.
Confirm that Agent_IC acknowledges user inputs and shows empathy when needed.
Ensure graceful handling of errors and omissions, including offering apologies where appropriate.
	•	Maintain Comprehensive Coverage:
Ensure all critical elements of the scenario are covered.
Alert Agent_IC if key objectives (e.g., minimizing cost, maximizing profit) or other crucial details are not addressed by the end of the session.
	•	Oversee Graceful Closure:
Monitor for appropriate detection of stopping points and verify that the questioning phase concludes respectfully.
Ensure Agent_IC invites the user to add or modify information if needed at the end of the conversation.

Intervention Guidelines:
	•	When to Intervene:
If Agent_IC deviates from its guidelines.
If an error is detected, such as redundant questioning or logical inconsistency.
If empathy or acknowledgment of user frustration is missing when needed.
	•	How to Intervene:
Provide succinct, actionable feedback to Agent_IC to correct course.
For example:
“Alert: You’ve asked a redundant question. Please acknowledge and adjust.”
“Alert: Logical inconsistency detected. Please realign the question to fit the user’s context.”
	•	Tone and Style:
Maintain a professional and constructive tone.
Be direct, clear, and focused on improvement.

Prohibited Actions:
Do not interact directly with the user.
Do not summarize or formulate mathematical models.
Do not provide guidance unless it relates to the questioning process.
"""

SYSTEM_PROMPT_PROCTOR_MATHS = """
You are a Proctor Agent responsible for monitoring the Writing Expert Agent to ensure that it adheres to the highest standards of clarity, structure, and coherence in summarization. Your primary role is to oversee, evaluate, and refine the writing process, providing real-time feedback to the Writing Expert Agent when necessary. You do not interact with the user directly but ensure that all written summaries meet the required quality and completeness standards.

Key Responsibilities:
	•	Ensure Structural and Logical Coherence:
Verify that summaries are well-structured and logically organized.
Ensure smooth transitions between sections and paragraphs.
Identify and flag disorganized or fragmented writing that needs improvement.
	•	Monitor Clarity and Conciseness:
Check that the writing is clear, precise, and free of redundancy.
Ensure that concise yet comprehensive language is used.
Flag overly technical or convoluted explanations that might hinder readability.
	•	Maintain Progressive Updates:
Ensure that summaries are updated progressively as new details emerge.
Verify that missing information is explicitly acknowledged without unnecessary repetition.
Flag summaries that fail to incorporate newly provided information.
	•	Ensure Adherence to Writing Guidelines:
Confirm that the Writing Expert avoids mathematical notations and uses plain language to describe constraints and relationships.
Ensure that only relevant information is included, filtering out unrelated details.
Check for consistency in terminology and style across different summaries.
	•	Detect and Alert for Errors:
Identify ambiguities, contradictions, or vague statements that require revision.
Detect grammatical errors, awkward phrasing, or unclear sentences.
Ensure that summaries align with the given optimization problem context without deviation.
	•	Provide Real-Time Feedback to Writing Expert Agent:
When to Intervene:
• If the summary lacks logical structure or clarity.
• If newly provided details are not incorporated.
• If there is redundancy, inconsistency, or vague wording.
• If irrelevant or extraneous details are included.
How to Intervene:
• Provide direct, actionable feedback (e.g., “Alert: The summary lacks logical structure. Please reorganize for better flow.”).
• Offer concise suggestions for improvement (e.g., “Alert: Redundant phrasing detected. Consider making this more concise.”).
• Ensure that the Writing Expert acknowledges and corrects errors when flagged.

Prohibited Actions:
Do not interact directly with the user.
Do not rewrite or modify the summary yourself—only guide the Writing Expert Agent.
Do not introduce additional explanations beyond what is necessary for ensuring writing quality.
"""

SYSTEM_PROMPT_PROCTOR_WRITING = """
You are a Proctor Agent responsible for monitoring the Mathematics Expert Agent to ensure that it adheres to strict mathematical formulation guidelines. Your primary role is to oversee, evaluate, and provide real-time feedback to maintain accuracy, logical structure, and completeness in the mathematical model. You do not interact with the user directly, but your interventions help refine the mathematical formulation process.

Key Responsibilities:
	•	Ensure Progressive & Logical Model Formulation:
Verify that the mathematical model is built progressively as relevant information becomes available.
Ensure that missing components are explicitly noted without making assumptions.
Confirm that each element (variables, objective function, constraints) is introduced only when enough information is available.
	•	Enforce Strict Focus on Mathematical Formulation:
Prevent inclusion of irrelevant details or general conversation in the formulation.
Ensure that the model strictly follows the given optimization problem, using only user-provided data.
Confirm that the expert does not make unwarranted assumptions beyond provided information.
	•	Maintain Structural Clarity & Completeness:
Verify that the model follows a structured format, covering:
• Problem Understanding: Summarizing key elements before formulation.
• Decision Variables: Clearly defining all variables before use.
• Objective Function: Formulating it correctly without missing terms.
• Constraints: Ensuring all constraints are correctly formulated and aligned with the given problem.
Check that notation and terminology are consistent throughout.
	•	Detect and Alert for Errors or Gaps:
Identify mathematical inconsistencies, incorrect formulations, or missing elements in the model.
Detect illogical expressions, redundant constraints, or incomplete function definitions.
Flag ambiguities in constraint formulation that require further clarification.
	•	Prevent Unwanted Code Generation or Solver Guidance:
Ensure that the agent strictly formulates the mathematical model and does not:
• Generate any code for solving the model.
• Provide solver guidance or implementation instructions.
• Suggest algorithmic solutions beyond formulation.
If the agent deviates, provide corrective feedback, such as:
“Alert: Avoid providing solver guidance. Stick to mathematical formulation only.”
“Alert: Code generation is not allowed. Please remove any programming-related content.”
	•	Ensure Progressive Updates & Acknowledgment of Missing Information:
Verify that the expert updates the formulation dynamically as new details are provided.
Ensure that pending information is explicitly noted instead of making assumptions.
If a component is missing, it should be clearly stated, e.g.,
“The demand constraint is not yet defined. Waiting for more details to finalize this component.”

Intervention Guidelines:
	•	When to Intervene:
If any component is formulated without enough supporting information.
If inconsistencies or logical errors exist in the equations.
If the model fails to progressively integrate new information.
If the expert deviates from strict mathematical formulation (e.g., giving solver guidance).
	•	How to Intervene:
Provide direct, precise, and actionable feedback.
Offer specific corrections where errors exist.
Ensure that the agent acknowledges and corrects mistakes.

Prohibited Actions:
Do not interact directly with the user.
Do not modify the mathematical model—only guide the expert agent.
Do not allow inclusion of code, solver guidance, or additional explanations beyond formulation.
"""


def set_configuration(selected_model, api_key):
    """
    Called when the user clicks "Set Configuration".
    This:
      - instantiates Agent_IC, writing_expert, maths_expert
      - instantiates the three Proctor agents
      - returns an initial greeting for the left chat pane
    """
    global Agent_IC, writing_expert, maths_expert
    global proctor_ic, proctor_maths, proctor_writing

    # Shared LLM config for all agents
    llm_config_base = {
        "config_list": [
            {
                "model": selected_model,
                "temperature": 0.5,
                "api_key": api_key,
            }
        ]
    }

    # ----------------------------
    # Questioning Agent (Agent_IC)
    # ----------------------------
    Agent_IC = ConversableAgent(
        name="Agent_IC",
        system_message=SYSTEM_PROMPT_AGENT_IC,
        llm_config=llm_config_base,
    )

    # ----------------------------
    # Writing Expert
    # ----------------------------
    writing_expert = ConversableAgent(
        name="writing_expert",
        system_message=SYSTEM_PROMPT_WRITING,
        llm_config=llm_config_base,
    )

    # ----------------------------
    # Maths Expert
    # ----------------------------
    maths_expert = ConversableAgent(
        name="maths_expert",
        system_message=SYSTEM_PROMPT_MATHS,
        llm_config=llm_config_base,
    )

    # ----------------------------
    # Proctors (IC, Maths, Writing)
    # ----------------------------
    proctor_ic = ProctorAgent(
        name="IC_Proctor",
        system_message=SYSTEM_PROMPT_PROCTOR_IC,
        llm_config=llm_config_base,
    )

    proctor_maths = ProctorAgent(
        name="Maths_Proctor",
        system_message=SYSTEM_PROMPT_PROCTOR_MATHS,
        llm_config=llm_config_base,
    )

    proctor_writing = ProctorAgent(
        name="Writing_Proctor",
        system_message=SYSTEM_PROMPT_PROCTOR_WRITING,
        llm_config=llm_config_base,
    )

    # Return initial greeting for the left pane
    return initiate_chat()

###############################################################################
# MAIN TURN HANDLER: where graph → questioning + maths + proctors
###############################################################################

def handle_user_input(user_input, vertical_history, summary_content, maths_content):
    """
    One full turn when the user sends a message:
      1. Update visible chat history.
      2. Run beam search on MILP tree to get relevant nodes.
      3. Build INTERNAL graph contexts (for Agent_IC & maths_expert).
      4. Generate reply from Agent_IC.
      5. Run IC_Proctor.
      6. Generate summary via writing_expert + Writing_Proctor.
      7. Generate mathematical model via maths_expert + Maths_Proctor.
      8. Return updated panes for Gradio UI.
    """
    global Agent_IC, writing_expert, maths_expert
    global proctor_ic, proctor_maths, proctor_writing

    if Agent_IC is None:
        # Config not set yet
        return (
            "\n\n".join(
                append_to_chat(
                    vertical_history,
                    "agent",
                    "Please set the configuration first.",
                )
            ),
            "",
            "Please set the configuration first.",
            "Please set the configuration first.",
        )

    # ------------------------------------------------------------------
    # 1) Run MILP tree beam search to find relevant graph nodes
    # ------------------------------------------------------------------
    relevant_nodes = find_relevant_graph_nodes(user_input, top_k=8)
    math_nodes = extract_math_expressions_from_nodes(relevant_nodes, top_k=6)

    ic_graph_context = build_questioning_graph_context(relevant_nodes)
    maths_graph_context = build_math_graph_context(math_nodes)

    # ------------------------------------------------------------------
    # 2) Update visible chat history (left pane)
    # ------------------------------------------------------------------
    updated_history = append_to_chat(vertical_history, "user", user_input)

    # ------------------------------------------------------------------
    # 3) Update internal autogen history for User ↔ Agent_IC
    # ------------------------------------------------------------------
    User.receive({"content": user_input}, Agent_IC)
    base_ic_messages = list(User.chat_messages[Agent_IC])

    # Add INTERNAL GRAPH CONTEXT only for Agent_IC (not visible to user)
    ic_messages_with_graph = base_ic_messages
    if ic_graph_context:
        ic_messages_with_graph = base_ic_messages + [
            {"content": ic_graph_context, "role": "system"}
        ]

    # ------------------------------------------------------------------
    # 4) Questioning Agent reply (using graph context)
    # ------------------------------------------------------------------
    reply = Agent_IC.generate_reply(
        messages=ic_messages_with_graph,
        sender=Agent_IC,
    )
    updated_history = append_to_chat(updated_history, "agent", reply)

    # ------------------------------------------------------------------
    # 5) IC Proctor: process-quality monitoring for Agent_IC
    # ------------------------------------------------------------------
    if proctor_ic is not None:
        # Proctor sees the conversation plus the latest reply
        proctor_messages = list(User.chat_messages[Agent_IC]) + [
            {"role": "assistant", "content": reply}
        ]
        proctor_feedback = proctor_ic.generate_reply(
            messages=proctor_messages,
            sender=proctor_ic,
        )

        if isinstance(proctor_feedback, str) and "Intervention Required" in proctor_feedback:
            # Surface the intervention as an extra assistant message
            updated_history = append_to_chat(
                updated_history,
                "agent",
                proctor_feedback,
            )

    concatenated_history = "\n\n".join(updated_history)

    # ------------------------------------------------------------------
    # 6) Writing Expert: plain-language progressive summary
    # ------------------------------------------------------------------
    if writing_expert is not None:
        writing_summary = writing_expert.generate_reply(
            messages=User.chat_messages[Agent_IC],
            sender=writing_expert,
        )

        summary_html = (
            "<div class='summary-message'><b>🖋️ Summary:</b><br>"
            f"{format_summary(writing_summary)}</div>"
        )

        # Writing Proctor checks the summary for completeness / compliance
        if proctor_writing is not None:
            writing_proctor_messages = list(User.chat_messages[Agent_IC]) + [
                {"role": "assistant", "content": writing_summary}
            ]
            wp_feedback = proctor_writing.generate_reply(
                messages=writing_proctor_messages,
                sender=proctor_writing,
            )

            if isinstance(wp_feedback, str) and "Summary Quality Alert" in wp_feedback:
                summary_html += (
                    "<div class='summary-alert' "
                    "style='color:#b71c1c;margin-top:8px;'>"
                    f"{wp_feedback}"
                    "</div>"
                )

        summary_content = summary_html
    else:
        summary_content = "<div class='summary-message'>Please set the configuration first.</div>"

    # ------------------------------------------------------------------
    # 7) Maths Expert: MILP model, with graph-based math context
    # ------------------------------------------------------------------
    if maths_expert is not None:
        maths_messages = list(User.chat_messages[Agent_IC])
        if maths_graph_context:
            # Add INTERNAL graph-based math context with candidate expressions
            maths_messages = maths_messages + [
                {"content": maths_graph_context, "role": "system"}
            ]

        maths_summary = maths_expert.generate_reply(
            messages=maths_messages,
            sender=maths_expert,
        )

        formatted_math_summary = format_math_content(maths_summary)
        maths_html = (
            "<div class='maths-message'><b>🔢 Mathematical Model:</b><br>"
            f"{formatted_math_summary}</div>"
        )

        # Maths Proctor checks for model gaps (missing objective/constraints etc.)
        if proctor_maths is not None:
            maths_proctor_messages = list(User.chat_messages[Agent_IC]) + [
                {"role": "assistant", "content": maths_summary}
            ]
            mp_feedback = proctor_maths.generate_reply(
                messages=maths_proctor_messages,
                sender=proctor_maths,
            )

            if isinstance(mp_feedback, str) and "Model Gap Alert" in mp_feedback:
                maths_html += (
                    "<div class='maths-alert' "
                    "style='color:#b71c1c;margin-top:8px;'>"
                    f"{mp_feedback}"
                    "</div>"
                )

        maths_content = maths_html
    else:
        maths_content = "<div class='maths-message'>Please set the configuration first.</div>"

    # ------------------------------------------------------------------
    # 8) Return updated panes to Gradio
    # ------------------------------------------------------------------
    return concatenated_history, "", summary_content, maths_content


###############################################################################
# UI HELPERS
###############################################################################

def toggle_pane(state):
    """
    Toggle between Summary (top) and Mathematical Model (bottom)
    in the right-hand pane.
    """
    if state == "top":
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            "Switch to Summary 🖋️",
            "bottom",
        )
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            "Switch to Mathematical Model 🔢",
            "top",
        )

###############################################################################
# GRADIO APP
###############################################################################

with gr.Blocks() as demo:
    # Include MathJax for rendering LaTeX in the maths pane
    gr.HTML(
        """
        <script type="text/javascript" async
            src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js">
        </script>
        """
    )

    # Auto re-typeset when maths pane updates
    gr.HTML(
        """
        <script>
            function renderMathJax() {
                if (typeof MathJax !== 'undefined') {
                    MathJax.typeset();
                }
            }
            const observer = new MutationObserver(() => {
                renderMathJax();
            });
            window.addEventListener('load', function() {
                const targetNode = document.getElementById('bottom-horizontal-content');
                if (targetNode) {
                    observer.observe(targetNode, { childList: true, subtree: true });
                }
            });
        </script>
        """
    )

    with gr.Column():
        # Configuration row
        with gr.Row(elem_id="config-row"):
            selected_model = gr.Dropdown(
                choices=["gpt-4o", "gpt-4o-mini"],
                value="gpt-4o",
                label="Choose your model ⚡",
                elem_id="selected-model",
            )
            selected_key = gr.Textbox(
                label="API Key 🔑",
                type="password",
                elem_id="api-key",
            )
            configure_button = gr.Button(
                "Set Configuration ⚙️",
                elem_id="set-configuration",
            )

        # Main chat + right panes
        with gr.Row(elem_id="chat-container"):
            with gr.Column(elem_id="vertical-pane"):
                vertical_pane_html = gr.HTML("", elem_id="vertical-content")

            with gr.Column(elem_id="right-pane"):
                toggle_button = gr.Button(
                    "Switch to Mathematical Model 🔢",
                    elem_id="toggle-button",
                    interactive=True,
                )
                top_pane_html = gr.HTML(
                    "",
                    visible=True,
                    elem_id="top-horizontal-content",
                )
                bottom_pane_html = gr.HTML(
                    "",
                    visible=False,
                    elem_id="bottom-horizontal-content",
                )

        # Input row (fixed at bottom)
        with gr.Row(elem_id="chat-input"):
            user_input = gr.Textbox(
                label="You",
                placeholder="⌨️ Type your response here...",
                lines=1,
                interactive=True,
                show_label=False,
            )
            submit_button = gr.Button("➤")
            download_button = gr.Button("📥 Download", elem_id="download-button")
            download_output = gr.File(visible=False, elem_id="Download JSON")

        pane_state = gr.State(value="top")

        # Wiring callbacks
        configure_button.click(
            fn=set_configuration,
            inputs=[selected_model, selected_key],
            outputs=[vertical_pane_html],
        )

        toggle_button.click(
            fn=toggle_pane,
            inputs=[pane_state],
            outputs=[top_pane_html, bottom_pane_html, toggle_button, pane_state],
        )

        user_input.submit(
            fn=handle_user_input,
            inputs=[user_input, vertical_pane_html, top_pane_html, bottom_pane_html],
            outputs=[vertical_pane_html, user_input, top_pane_html, bottom_pane_html],
        )

        submit_button.click(
            fn=handle_user_input,
            inputs=[user_input, vertical_pane_html, top_pane_html, bottom_pane_html],
            outputs=[vertical_pane_html, user_input, top_pane_html, bottom_pane_html],
        )

        download_button.click(
            fn=prepare_download,
            inputs=[vertical_pane_html, top_pane_html, bottom_pane_html],
            outputs=[download_output],
        )

# Styling (unchanged from your previous version)
demo.css = """
.user-message {
    background-color: #dcf8c6;
    border-radius: 10px;
    padding: 8px;
    margin: 5px 0;
    text-align: right;
    width: fit-content;
    max-width: 90%;
    float: right;
    clear: both;
}
.agent-message {
    background-color: #ffedb8;
    border-radius: 10px;
    padding: 8px;
    margin: 5px 0;
    text-align: left;
    width: fit-content;
    max-width: 80%;
    float: left;
    clear: both;
}
body { background-color: inherit; overflow-x:hidden; }
:root {--color-accent: transparent !important; --color-accent-soft:transparent !important; --code-background-fill:black !important; --body-text-color:black !important; }
#component-2 {background:#ffffff1a; display:contents; }
div#component-0 { height: auto !important; }
.gradio-container.gradio-container-4-8-0.svelte-1kyws56.app { max-width: 100% !important; }
gradio-app { background: linear-gradient(134deg,#00425e 0%,#001a3f 43%,#421438 77%) !important; background-attachment: fixed !important; background-position: top; }
.panel.svelte-vt1mxs { background: transparent; padding:0; }
.block.svelte-90oupt { background: transparent; border-color: transparent; }
.bot.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { background: #ffffff1a; border-color: transparent; color: black; }
.user.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { background: #ffffff1a; border-color: transparent; color: black; padding: 10px 18px; }
div.svelte-iyf88w { background: #cc98d445; border-color: transparent; border-radius: 25px; }
textarea.scroll-hide.svelte-1f354aw { background: transparent; color: #000 !important; }
.primary.svelte-cmf5ev { background: transparent; color: black; }
.primary.svelte-cmf5ev:hover { background: transparent; color: black; }
button#component-8 { display: none; position: absolute; margin-top: 60px; border-radius: 25px; }
div#component-9 { max-width: fit-content; margin-left: auto; margin-right: auto; }
button#component-10, button#component-11, button#component-12 { flex: none; background: #ffffff1a; border: none; color: black; margin-right: auto; margin-left: auto; border-radius: 9px; min-width: fit-content; }
.share-button.svelte-12dsd9j { display: none; }
footer.svelte-mpyp5e { display: none !important; }
.message-buttons-bubble.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { border-color: #31546E; background: #31546E; }
.bubble-wrap.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { padding: 0; }
.prose h1 { color: black !important; font-size: 36px !important; font-weight: normal !important; background: #ffffff1a; padding: 20px; border-radius: 20px; width: 90%; margin-left: auto !important; margin-right: auto !important; }
.toast-wrap.svelte-pu0yf1 { display:none !important; }
.scroll-hide { scrollbar-width: auto !important; }
.main svelte-1kyws56 { max-width: 800px; align-self: center; }
div#component-4 { max-width: 650px; margin-left: auto; margin-right: auto; }
body::-webkit-scrollbar { display: none; }

#chat-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
    height: 70vh;
    overflow: hidden;
    box-sizing: border-box;
}

#vertical-pane {
    background-color: #ececec;
    padding: 10px;
    border-radius: 10px;
    border: 2px solid #4a90e2;
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
}

#vertical-content {
    flex: 1;
    overflow-y: auto;
    height: 100%;
    box-sizing: border-box;
}

#right-pane {
    display: flex;
    grid-template-rows: 2fr 8fr;
    background-color: #ececec;
    grid-gap: 10px;
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
    flex-direction: column;
}

#top-horizontal-content {
    background-color: #ececec;
    border: 2px solid #4a90e2;
    padding: 10px;
    border-radius: 10px;
    overflow-y: auto;
    min-height: 200px;
    box-sizing: border-box;
    height: auto;
    max-height: 100%;
    flex: 1;
}

#bottom-horizontal-content {
    background-color: #ececec;
    border: 2px solid #4a90e2;
    padding: 10px;
    border-radius: 10px;
    overflow-y: auto;
    min-height: 200px;
    max-height: 100%;
    box-sizing: border-box;
    height: auto;
    flex: 1;
}

#toggle-buttons-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 5px;
}

button#toggle-top {
    background-color: #ff9800;
    border: none;
    color: black !important;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 12px;
    border-radius: 12px;
    cursor: pointer;
    transition: background-color 0.3s ease;
    width: 48%;
    height: 20px;
}

button#toggle-top:hover {
    background-color: #007bb5;
    color: white !important;
}

button#toggle-bottom {
    background-color: #4caf50;
    border: 2px solid #4caf50;
    border-radius: 5px;
    cursor: pointer;
    padding: 2px 6px;
    font-size: 12px;
    text-align: center;
    width: 48%;
    height: 20px;
}

button#toggle-bottom:hover {
    background-color: #388e3c;
    border-color: #388e3c;
}

#chat-input {
    position: fixed;
    bottom: 0;
    left: 20px;
    right: 20px;
    width: calc(100% - 40px);
    display: flex;
    background: transparent;
    padding: 10px;
    box-sizing: border-box;
}

#chat-input textarea {
    flex: 3.5;
    margin-right: 10px;
    border-radius: 10px;
    padding: 10px;
    font-size: 16px;
    max-height: 70px;
    overflow-y: auto;
}

#chat-input button {
    flex: 0.5;
    max-width: 100px;
    max-height: 70px;
    border-radius: 10px;
    background: white;
    padding: 10px 15px;
    margin-right: 10px;
    cursor: pointer;
    font-size: 16px;
}

#set-configuration {
    background-color: #4a90e2;
    border: none;
    flex: 0 0 20%;
    margin: 0;
    height: 100%;
    padding: 10px;
    box-sizing: border-box;
    cursor: pointer;
    font-size: 15px;
}

#set-configuration:hover {
    background-color: #357ABD;
}

#selected-model, #api-key, #set-configuration {
    border-radius: 4px;
    height: 90px;
}

button#submit-button {
    flex: 0.5;
    max-width: 30px;
    border-radius: 10px;
    background: white;
    padding: 10px 15px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s ease;
    border: 2px solid #4a90e2;
}

button#submit-button:hover {
    background-color: #f0f0f0;
}

#download-button {
    background-color: #008CBA;
    border: none;
    color: black !important;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    border-radius: 12px;
    cursor: pointer;
    transition: background-color 0.3s ease;
    max-height: 100px;
}

#download-button:hover {
    background-color: #007bb5;
    color: white !important;
}

#download-button:active {
    background-color: #006494;
    color: white !important;
}
"""

demo.launch(show_api=False)




















###############################################################################
# Helpers to interpret graph nodes for Questioning and Maths agents
###############################################################################

def get_node_path(node) -> str:
    """
    Reconstruct a human readable path from the root to this node
    using the parent pointers we added in tree_graphs.
    """
    path = []
    curr = node
    while curr is not None:
        path.append(curr.value)
        curr = curr.parent
    path.reverse()
    return " > ".join(path)


def find_relevant_graph_nodes(user_text: str, top_k: int = 8) -> list:
    """
    Run dynamic beam search over the unified MILP tree and return
    the top_k most relevant nodes for this user_text.
    """
    ranked_nodes = dynamic_beam_search(GRAPH_ROOT, user_text)
    return ranked_nodes[:top_k]


def extract_math_expressions_from_nodes(nodes: list, top_k: int = 8) -> list:
    """
    From a list of nodes, select those that look like mathematical
    edge/leaf expressions, to guide the maths_expert.
    """
    math_nodes = [n for n in nodes if looks_like_math(n.value)]
    return math_nodes[:top_k]


def build_questioning_graph_context(nodes: list) -> str:
    """
    Build an internal context block for Agent_IC, listing the most
    relevant MILP graph paths. Agent_IC will use this to decide
    which aspect to ask about next.
    """
    if not nodes:
        return ""

    lines = [
        "[INTERNAL GRAPH CONTEXT FOR QUESTIONING AGENT]",
        "The following MILP graph nodes are most relevant to the user's latest message.",
        "Use these to decide what to ask about next.",
        "Do NOT echo this block verbatim to the user.",
        "",
    ]
    for i, node in enumerate(nodes, 1):
        lines.append(f"{i}. {get_node_path(node)}")

    return "\n".join(lines)


def build_math_graph_context(math_nodes: list) -> str:
    """
    Build an internal context block for the maths_expert, listing
    candidate mathematical expressions corresponding to constraints
    or objective terms mentioned by the user.
    """
    if not math_nodes:
        return ""

    lines = [
        "[INTERNAL GRAPH CONTEXT FOR MATHEMATICAL MODEL]",
        "These candidate expressions come from the MILP graph and are likely",
        "related to the constraints or objective that the user has mentioned.",
        "",
    ]
    for i, node in enumerate(math_nodes, 1):
        lines.append(f"{i}. {node.value}")

    return "\n".join(lines)


User = ConversableAgent(
    name="User",
    llm_config=False,
    human_input_mode="ALWAYS",
)

Agent_IC = None
writing_expert = None
maths_expert = None

proctor_ic = None
proctor_maths = None
proctor_writing = None

def set_configuration(selected_model, api_key):
    global Agent_IC, writing_expert, maths_expert
    global proctor_ic, proctor_maths, proctor_writing

    # Shared LLM config for all agents
    llm_config_base = {
        "config_list": [
            {
                "model": selected_model,
                "temperature": 0.5,
                "api_key": api_key,
            }
        ]
    }

    # ----------------------------
    # Questioning Agent (Agent_IC)
    # ----------------------------
    Agent_IC = ConversableAgent(
        name="Agent_IC",
        system_message="""


        
  """,
        llm_config=llm_config_base,
    )

    # ----------------------------
    # Writing Expert
    # ----------------------------
    writing_expert = ConversableAgent(
        name="writing_expert",
        system_message="""


  """,
        llm_config=llm_config_base,
    )

    # ----------------------------
    # Maths Expert
    # ----------------------------
    maths_expert = ConversableAgent(
        name="maths_expert",
        system_message="""



  """,
        llm_config=llm_config_base,
    )

    # ----------------------------
    # Proctors (IC, Maths, Writing)
    # ----------------------------
    proctor_ic = ProctorAgent(
        name="IC_Proctor",
        system_message="""


  """,
        llm_config=llm_config_base,
    )

    proctor_maths = ProctorAgent(
        name="Maths_Proctor",
        system_message="""


  """,
        llm_config=llm_config_base,
    )

    proctor_writing = ProctorAgent(
        name="Writing_Proctor",
        system_message="""

  """,
        llm_config=llm_config_base,
    )

    # Return initial greeting to fill the left pane
    return initiate_chat()

def handle_user_input(user_input, vertical_history, summary_content, maths_content):
    """
    Main turn handler:
    - Updates visible chat
    - Runs beam search on the MILP tree to get relevant nodes
    - Passes graph context to Agent_IC and maths_expert
    - Invokes proctors for questioning, summary, and maths model
    """
    global Agent_IC, writing_expert, maths_expert
    global proctor_ic, proctor_maths, proctor_writing

    # If configuration isn't set, show a friendly error
    if Agent_IC is None:
        return (
            "\n\n".join(append_to_chat(vertical_history, "🤖", "Please set the configuration first.")),
            "",
            "Please set the configuration first.",
            "Please set the configuration first.",
        )

    # ------------------------------------------------------------------
    # 1) Run MILP tree beam search to find relevant graph nodes
    # ------------------------------------------------------------------
    relevant_nodes = find_relevant_graph_nodes(user_input, top_k=8)
    math_nodes = extract_math_expressions_from_nodes(relevant_nodes, top_k=6)

    ic_graph_context = build_questioning_graph_context(relevant_nodes)
    maths_graph_context = build_math_graph_context(math_nodes)

    # ------------------------------------------------------------------
    # 2) Update visible chat history (left pane)
    # ------------------------------------------------------------------
    updated_history = append_to_chat(vertical_history, "user", user_input)

    # ------------------------------------------------------------------
    # 3) Update internal autogen history for User ↔ Agent_IC
    # ------------------------------------------------------------------
    User.receive({"content": user_input}, Agent_IC)
    base_ic_messages = list(User.chat_messages[Agent_IC])

    # Add INTERNAL GRAPH CONTEXT only for Agent_IC (not visible to user)
    ic_messages_with_graph = base_ic_messages
    if ic_graph_context:
        ic_messages_with_graph = base_ic_messages + [
            {"content": ic_graph_context, "role": "system"}
        ]

    # ------------------------------------------------------------------
    # 4) Questioning Agent reply
    # ------------------------------------------------------------------
    reply = Agent_IC.generate_reply(
        messages=ic_messages_with_graph,
        sender=Agent_IC,
    )
    updated_history = append_to_chat(updated_history, "Agent_IC", reply)

    # ------------------------------------------------------------------
    # 5) IC Proctor: process-quality monitoring for Agent_IC
    # ------------------------------------------------------------------
    if proctor_ic is not None:
        # Proctor sees the conversation plus the latest reply
        proctor_messages = list(User.chat_messages[Agent_IC]) + [
            {"role": "assistant", "content": reply}
        ]
        proctor_feedback = proctor_ic.generate_reply(
            messages=proctor_messages,
            sender=proctor_ic,
        )

        # If the proctor intervenes, surface that intervention in chat
        if isinstance(proctor_feedback, str) and "Intervention Required" in proctor_feedback:
            updated_history = append_to_chat(updated_history, "Agent_IC", proctor_feedback)

    concatenated_history = "\n\n".join(updated_history)

    # ------------------------------------------------------------------
    # 6) Writing Expert: plain-language progressive summary
    # ------------------------------------------------------------------
    if writing_expert is not None:
        # Writing expert sees only the clean conversation history
        writing_summary = writing_expert.generate_reply(
            messages=User.chat_messages[Agent_IC],
            sender=writing_expert,
        )

        summary_html = (
            "<div class='summary-message'><b>🖋️ Summary:</b><br>"
            f"{format_summary(writing_summary)}</div>"
        )

        # Writing Proctor checks the summary quality & compliance
        if proctor_writing is not None:
            writing_proctor_messages = list(User.chat_messages[Agent_IC]) + [
                {"role": "assistant", "content": writing_summary}
            ]
            wp_feedback = proctor_writing.generate_reply(
                messages=writing_proctor_messages,
                sender=proctor_writing,
            )

            if isinstance(wp_feedback, str) and "Summary Quality Alert" in wp_feedback:
                # Append the alert below the summary in a small warning block
                summary_html += (
                    "<div class='summary-alert' style='color:#b71c1c;margin-top:8px;'>"
                    f"{wp_feedback}"
                    "</div>"
                )

        summary_content = summary_html
    else:
        summary_content = "<div class='summary-message'>Please set the configuration first.</div>"

    # ------------------------------------------------------------------
    # 7) Maths Expert: MILP model, with graph-based math context
    # ------------------------------------------------------------------
    if maths_expert is not None:
        maths_messages = list(User.chat_messages[Agent_IC])
        if maths_graph_context:
            # Add INTERNAL graph-based math context with candidate expressions
            maths_messages = maths_messages + [
                {"content": maths_graph_context, "role": "system"}
            ]

        maths_summary = maths_expert.generate_reply(
            messages=maths_messages,
            sender=maths_expert,
        )

        formatted_math_summary = format_math_content(maths_summary)
        maths_html = (
            "<div class='maths-message'><b>🔢 Mathematical Model:</b><br>"
            f"{formatted_math_summary}</div>"
        )

        # Maths Proctor checks for model gaps (missing objective, constraints, etc.)
        if proctor_maths is not None:
            maths_proctor_messages = list(User.chat_messages[Agent_IC]) + [
                {"role": "assistant", "content": maths_summary}
            ]
            mp_feedback = proctor_maths.generate_reply(
                messages=maths_proctor_messages,
                sender=proctor_maths,
            )

            if isinstance(mp_feedback, str) and "Model Gap Alert" in mp_feedback:
                # Append the alert below the maths box as a warning
                maths_html += (
                    "<div class='maths-alert' style='color:#b71c1c;margin-top:8px;'>"
                    f"{mp_feedback}"
                    "</div>"
                )

        maths_content = maths_html
    else:
        maths_content = "<div class='maths-message'>Please set the configuration first.</div>"

    # ------------------------------------------------------------------
    # 8) Return updated panes to Gradio
    # ------------------------------------------------------------------
    return concatenated_history, "", summary_content, maths_content


def toggle_pane(state):
    if state == "top":
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            "Switch to Summary 🖋️",
            "bottom"
        )
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            "Switch to Mathematical Model 🔢",
            "top"
        )


with gr.Blocks() as demo:
    gr.HTML(
        """
        <script type="text/javascript" async
            src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js">
        </script>
        """
    )

    gr.HTML(
        """
        <script>
            function renderMathJax() {
                if (typeof MathJax !== 'undefined') {
                    MathJax.typeset();
                }
            }

            const observer = new MutationObserver(() => {
                renderMathJax();
            });

            window.addEventListener('load', function() {
                const targetNode = document.getElementById('bottom-horizontal-content');
                if (targetNode) {
                    observer.observe(targetNode, { childList: true, subtree: true });
                }
            });
        </script>
        """
    )
    with gr.Column():
        with gr.Row(elem_id="config-row"):
            selected_model = gr.Dropdown(choices=['gpt-4o', 'gpt-4o-mini'], value='gpt-4o', label="Choose your model ⚡", elem_id="selected-model")
            selected_key = gr.Textbox(label="API Key 🔑", type="password", elem_id="api-key")
            configure_button = gr.Button("Set Configuration ⚙️", elem_id="set-configuration")

        with gr.Row(elem_id="chat-container"):
            with gr.Column(elem_id="vertical-pane"):
                vertical_pane_html = gr.HTML("", elem_id="vertical-content")
            
            with gr.Column(elem_id="right-pane"):
                toggle_button = gr.Button("Switch to Mathematical Model 🔢", elem_id="toggle-button", interactive=True)
                
                top_pane_html = gr.HTML("", visible=True, elem_id="top-horizontal-content")
                bottom_pane_html = gr.HTML("", visible=False, elem_id="bottom-horizontal-content")

        with gr.Row(elem_id="chat-input"):
            user_input = gr.Textbox(label="You", placeholder="⌨️ Type your response here...", lines=1, interactive=True, show_label=False)
            submit_button = gr.Button("➤")
            download_button = gr.Button("📥 Download", elem_id="download-button")
            download_output = gr.File(visible=False, elem_id="Download JSON")
            #download_component = gr.Download(label="📥 Download Conversation")
        pane_state = gr.State(value="top")

        configure_button.click(fn=set_configuration, inputs=[selected_model, selected_key], outputs=[vertical_pane_html])

        toggle_button.click(
            fn=toggle_pane,
            inputs=[pane_state],
            outputs=[top_pane_html, bottom_pane_html, toggle_button, pane_state]
        )

        user_input.submit(
            fn=handle_user_input,
            inputs=[user_input, vertical_pane_html, top_pane_html, bottom_pane_html],
            outputs=[vertical_pane_html, user_input, top_pane_html, bottom_pane_html]
        )

        submit_button.click(
            fn=handle_user_input,
            inputs=[user_input, vertical_pane_html, top_pane_html, bottom_pane_html],
            outputs=[vertical_pane_html, user_input, top_pane_html, bottom_pane_html]
        )
        
        download_button.click(
            fn=prepare_download,
            inputs=[vertical_pane_html, top_pane_html, bottom_pane_html],
            outputs=[download_output]
            #outputs=[download_component]
            #file_name="conversation_summary_model.json"  # Immediate download with file name
        )


demo.css = """
.user-message {
    background-color: #dcf8c6;
    border-radius: 10px;
    padding: 8px;
    margin: 5px 0;
    text-align: right;
    width: fit-content;
    max-width: 90%;
    float: right;
    clear: both;
}
.agent-message {
    background-color: #ffedb8;
    border-radius: 10px;
    padding: 8px;
    margin: 5px 0;
    text-align: left;
    width: fit-content;
    max-width: 80%;
    float: left;
    clear: both;
}
body { background-color: inherit; overflow-x:hidden; }
:root {--color-accent: transparent !important; --color-accent-soft:transparent !important; --code-background-fill:black !important; --body-text-color:black !important; }
#component-2 {background:#ffffff1a; display:contents; }
div#component-0 { height: auto !important; }
.gradio-container.gradio-container-4-8-0.svelte-1kyws56.app { max-width: 100% !important; }
gradio-app { background: linear-gradient(134deg,#00425e 0%,#001a3f 43%,#421438 77%) !important; background-attachment: fixed !important; background-position: top; }
.panel.svelte-vt1mxs { background: transparent; padding:0; }
.block.svelte-90oupt { background: transparent; border-color: transparent; }
.bot.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { background: #ffffff1a; border-color: transparent; color: black; }
.user.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { background: #ffffff1a; border-color: transparent; color: black; padding: 10px 18px; }
div.svelte-iyf88w { background: #cc98d445; border-color: transparent; border-radius: 25px; }
textarea.scroll-hide.svelte-1f354aw { background: transparent; color: #000 !important; }
.primary.svelte-cmf5ev { background: transparent; color: black; }
.primary.svelte-cmf5ev:hover { background: transparent; color: black; }
button#component-8 { display: none; position: absolute; margin-top: 60px; border-radius: 25px; }
div#component-9 { max-width: fit-content; margin-left: auto; margin-right: auto; }
button#component-10, button#component-11, button#component-12 { flex: none; background: #ffffff1a; border: none; color: black; margin-right: auto; margin-left: auto; border-radius: 9px; min-width: fit-content; }
.share-button.svelte-12dsd9j { display: none; }
footer.svelte-mpyp5e { display: none !important; }
.message-buttons-bubble.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { border-color: #31546E; background: #31546E; }
.bubble-wrap.svelte-12dsd9j.svelte-12dsd9j.svelte-12dsd9j { padding: 0; }
.prose h1 { color: black !important; font-size: 36px !important; font-weight: normal !important; background: #ffffff1a; padding: 20px; border-radius: 20px; width: 90%; margin-left: auto !important; margin-right: auto !important; }
.toast-wrap.svelte-pu0yf1 { display:none !important; }
.scroll-hide { scrollbar-width: auto !important; }
.main svelte-1kyws56 { max-width: 800px; align-self: center; }
div#component-4 { max-width: 650px; margin-left: auto; margin-right: auto; }
body::-webkit-scrollbar { display: none; }

#chat-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
    height: 70vh;
    overflow: hidden;
    box-sizing: border-box;
}

#vertical-pane {
    background-color: #ececec;
    padding: 10px;
    border-radius: 10px;
    border: 2px solid #4a90e2;
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
}

#vertical-content {
    flex: 1;
    overflow-y: auto;
    height: 100%;
    box-sizing: border-box;
}

#right-pane {
    display: flex;
    grid-template-rows: 2fr 8fr;
    background-color: #ececec;
    grid-gap: 10px;
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
    flex-direction: column;
}

#top-horizontal-content {
    background-color: #ececec;
    border: 2px solid #4a90e2;
    padding: 10px;
    border-radius: 10px;
    overflow-y: auto;
    /*height: 63.5vh;*/
    min-height: 200px;
    box-sizing: border-box;
    height: auto;
    max-height: 100%;
    flex: 1;
    
}

#bottom-horizontal-content {
    background-color: #ececec;
    border: 2px solid #4a90e2;
    padding: 10px;
    border-radius: 10px;
    overflow-y: auto;
    /*height: 63.5vh;*/
    min-height: 200px;
    max-height: 100%;
    box-sizing: border-box;
    height: auto;
    flex: 1;
    
}

#toggle-buttons-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 5px;
}



    button#toggle-top {
        background-color: #ff9800; /* Blue background */
        border: none;              /* Remove default borders */
        color: black !important;              /* White text */
        padding: 10px 20px;        /* Padding for size */
        text-align: center;        /* Centered text */
        text-decoration: none;     /* Remove underline */
        display: inline-block;     /* Inline-block display */
        font-size: 12px;           /* Font size */
        border-radius: 12px;       /* Rounded corners */
        cursor: pointer;           /* Pointer cursor on hover */
        transition: background-color 0.3s ease; /* Smooth transition */
        width: 48%;
        height: 20px;
    }

    button#toggle-top:hover {
        background-color: #007bb5; /* Darker blue on hover */
        color: white !important;
    }


button#toggle-bottom {
    background-color: #4caf50; /* A fresh green for the bottom toggle button */
    border: 2px solid #4caf50;
    border-radius: 5px;
    cursor: pointer;
    padding: 2px 6px;
    font-size: 12px;
    text-align: center;
    width: 48%;
    height: 20px;
}

button#toggle-bottom:hover {
    background-color: #388e3c; /* Darker green on hover */
    border-color: #388e3c;
}


#chat-input {
    position: fixed;
    bottom: 0;
    left: 20px;
    right: 20px;
    width: calc(100% - 40px); /* width: 99%; */
    display: flex;
    background: transparent;
    padding: 10px;
    box-sizing: border-box;
}

#chat-input textarea {
    flex: 3.5;
    margin-right: 10px;
    border-radius: 10px;
    padding: 10px;
    font-size: 16px;
    max-height: 70px;
    overflow-y: auto;
}

#chat-input button {
    flex: 0.5;
    max-width: 100px;
    max-height: 70px;
    border-radius: 10px;
    background: white;
    padding: 10px 15px;
    margin-right: 10px;
    cursor: pointer;
    font-size: 16px;
}

#set-configuration {
    background-color: #4a90e2; /* Set background color to a blue shade */
    border: none; /* Remove any default borders */
    flex: 0 0 20%;
    margin: 0;
    height: 100%;
    padding: 10px;
    box-sizing: border-box;
    cursor: pointer;
    font-size: 15px;
}

#set-configuration:hover {
    background-color: #357ABD; /* Darker blue for hover effect */
}

#selected-model, #api-key, #set-configuration {
    border-radius: 4px;
    height: 90px;
}

    /* Styles for the Submit button */
    button#submit-button {
        flex: 0.5;
        max-width: 30px;
        border-radius: 10px;
        background: white;
        padding: 10px 15px;
        cursor: pointer;
        font-size: 16px;
        transition: background-color 0.3s ease;
        border: 2px solid #4a90e2; /* Match the primary color */
    }
    
    button#submit-button:hover {
        background-color: #f0f0f0;
    }
    
    /* Styles for the Download button */
    #download-button {
        background-color: #008CBA; /* Blue background */
        border: none;              /* Remove default borders */
        color: black !important;              /* White text */
        padding: 10px 20px;        /* Padding for size */
        text-align: center;        /* Centered text */
        text-decoration: none;     /* Remove underline */
        display: inline-block;     /* Inline-block display */
        font-size: 16px;           /* Font size */
        border-radius: 12px;       /* Rounded corners */
        cursor: pointer;           /* Pointer cursor on hover */
        transition: background-color 0.3s ease; /* Smooth transition */
        max-height: 100px;
    }

    /* Hover effect for the Download button */
    #download-button:hover {
        background-color: #007bb5; /* Darker blue on hover */
        color: white !important;
    }

    /* Active state when the button is clicked */
    #download-button:active {
        background-color: #006494; /* Even darker blue when active */
        color: white !important;
    }

"""

demo.launch(show_api=False)
