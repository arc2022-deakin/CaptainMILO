class GraphNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

root_milp = GraphNode("MILP")

# Create Production Planning graph
root_production = GraphNode("Production Planning")

# Entities Subgraph
entities_node = GraphNode("Entities")
periods_node = GraphNode("Periods")
periods_node.add_child(GraphNode("Multi-period"))
periods_node.add_child(GraphNode("T = {t}"))
products_node = GraphNode("Products")
products_node.add_child(GraphNode("Single-product"))
products_node.add_child(GraphNode("Multi-product"))
products_node.add_child(GraphNode("P = {p}"))
entities_node.add_child(periods_node)
entities_node.add_child(products_node)
root_production.add_child(entities_node)

# Parameters Subgraph
parameters_node = GraphNode("Parameters")

# Initial Inventory
initial_inventory_node = GraphNode("Initial inventory")
initial_inventory_node.add_child(GraphNode("I_0"))
initial_inventory_node.add_child(GraphNode("I_{0,p}"))
parameters_node.add_child(initial_inventory_node)

# Cost
cost_node = GraphNode("Cost")

# Unit Production Cost
unit_production_cost_node = GraphNode("Unit production cost")

labour_node = GraphNode("Labour")

# Labour Types
regular_time_workers_node = GraphNode("Regular time workers")
regular_time_workers_node.add_child(GraphNode("c_t"))
regular_time_workers_node.add_child(GraphNode("c_{t,p}"))
over_time_workers_node = GraphNode("Over time workers")
over_time_workers_node.add_child(GraphNode("o_t"))
over_time_workers_node.add_child(GraphNode("o_{t,p}"))

labour_node.add_child(regular_time_workers_node)
labour_node.add_child(over_time_workers_node)
unit_production_cost_node.add_child(labour_node)

# Unit Material Cost
unit_material_cost_node = GraphNode("Unit material cost")
unit_material_cost_node.add_child(GraphNode("m_t"))
unit_material_cost_node.add_child(GraphNode("m_{t,p}"))
unit_production_cost_node.add_child(unit_material_cost_node)

cost_node.add_child(unit_production_cost_node)

# Unit Holding Cost
unit_holding_cost_node = GraphNode("Unit holding cost")
unit_holding_cost_node.add_child(GraphNode("h_t"))
unit_holding_cost_node.add_child(GraphNode("h_{t,p}"))
cost_node.add_child(unit_holding_cost_node)

# Set-up Cost
set_up_cost_node = GraphNode("Set-up cost")
set_up_cost_node.add_child(GraphNode("s_t"))
set_up_cost_node.add_child(GraphNode("s_{t,p}"))
cost_node.add_child(set_up_cost_node)

# Shortage Cost
shortage_cost_node = GraphNode("Shortage cost")
shortage_cost_node.add_child(GraphNode("g_t"))
shortage_cost_node.add_child(GraphNode("g_{t,p}"))
cost_node.add_child(shortage_cost_node)

parameters_node.add_child(cost_node)

# Demand
demand_node = GraphNode("Demand")
demand_node.add_child(GraphNode("d_t"))
demand_node.add_child(GraphNode("d_{t,p}"))
parameters_node.add_child(demand_node)

# Labour Hour Required
labour_hour_required_node = GraphNode("Labour hour required")
labour_hour_required_node.add_child(GraphNode("h_t"))
labour_hour_required_node.add_child(GraphNode("h_{t,p}"))
parameters_node.add_child(labour_hour_required_node)

# Limitations
limitations_node = GraphNode("Limitations")

# Labour Hour Limit
labour_hour_limit_node = GraphNode("Labour hour limit")
labour_hour_limit_node.add_child(GraphNode("UB^L_t"))
labour_hour_limit_node.add_child(GraphNode("UB^L_{t,p}"))
limitations_node.add_child(labour_hour_limit_node)

# Material Budget Limit
material_budget_limit_node = GraphNode("Material budget limit")
material_budget_limit_node.add_child(GraphNode("UB^M_t"))
material_budget_limit_node.add_child(GraphNode("UB^M_{t,p}"))
limitations_node.add_child(material_budget_limit_node)

parameters_node.add_child(limitations_node)
root_production.add_child(parameters_node)

# Decision Subgraph
decision_node = GraphNode("Decision")

# How Many to Produce
how_many_to_produce_node = GraphNode("How many to produce")
by_regular_hour_node = GraphNode("by regular hour labour")
by_regular_hour_node.add_child(GraphNode("x_t"))
by_regular_hour_node.add_child(GraphNode("x_{t,p}"))
by_over_time_node = GraphNode("by over time labour")
by_over_time_node.add_child(GraphNode("y_t"))
by_over_time_node.add_child(GraphNode("y_{t,p}"))
how_many_to_produce_node.add_child(by_regular_hour_node)
how_many_to_produce_node.add_child(by_over_time_node)
decision_node.add_child(how_many_to_produce_node)

# Inventory to Hold
inventory_to_hold_node = GraphNode("Inventory to hold")
inventory_to_hold_node.add_child(GraphNode("z_t"))
inventory_to_hold_node.add_child(GraphNode("z_{t,p}"))
decision_node.add_child(inventory_to_hold_node)

# To Produce or Not
to_produce_or_not_node = GraphNode("To produce or not")
to_produce_or_not_node.add_child(GraphNode("u_t"))
to_produce_or_not_node.add_child(GraphNode("u_{t,p}"))
decision_node.add_child(to_produce_or_not_node)

# Shortage
shortage_node = GraphNode("Shortage")
shortage_node.add_child(GraphNode("v_t"))
shortage_node.add_child(GraphNode("v_{t,p}"))
decision_node.add_child(shortage_node)

root_production.add_child(decision_node)

# Objective Function Subgraph
objective_node = GraphNode("Objective function")

# Total Regular Hour Labour Cost
total_regular_hour_cost_node = GraphNode("Total regular hour labour cost")
total_regular_hour_cost_node.add_child(GraphNode("\\sum_t c_tx_t"))
total_regular_hour_cost_node.add_child(GraphNode("\\sum_t \\sum_p c_{t,p} x_{t,p}"))
objective_node.add_child(total_regular_hour_cost_node)

# Total Over Time Labour Cost
total_over_time_cost_node = GraphNode("Total over time labour cost")
total_over_time_cost_node.add_child(GraphNode("\\sum_t o_t y_t"))
total_over_time_cost_node.add_child(GraphNode("\\sum_t \\sum_p o_{t,p} y_{t,p}"))
objective_node.add_child(total_over_time_cost_node)

# Total Holding Cost
total_holding_cost_node = GraphNode("Total holding cost")
total_holding_cost_node.add_child(GraphNode("\\sum_t h_t z_t"))
total_holding_cost_node.add_child(GraphNode("\\sum_t \\sum_p h_{t,p} z_{t,p}"))
objective_node.add_child(total_holding_cost_node)

# Total Set-up Cost
total_set_up_cost_node = GraphNode("Total set-up cost")
total_set_up_cost_node.add_child(GraphNode("\\sum_t s_t u_t"))
total_set_up_cost_node.add_child(GraphNode("\\sum_t \\sum_p s_{t,p} u_{t,p}"))
objective_node.add_child(total_set_up_cost_node)

# Total Shortage Cost
total_shortage_cost_node = GraphNode("Total shortage cost")
total_shortage_cost_node.add_child(GraphNode("\\sum_t g_t v_t"))
total_shortage_cost_node.add_child(GraphNode("\\sum_t \\sum_p g_{t,p} v_{t,p}"))
objective_node.add_child(total_shortage_cost_node)

# Total Material Cost
total_material_cost_node = GraphNode("Total material cost")
total_material_cost_node.add_child(GraphNode("\\sum_t m_t x_t"))
total_material_cost_node.add_child(GraphNode("\\sum_t m_{t,p} x_{t,p}"))
objective_node.add_child(total_material_cost_node)

root_production.add_child(objective_node)

# Constraints Subgraph
constraints_node = GraphNode("Constraints")

# Explicit Constraints
explicit_constraints_node = GraphNode("Explicit constraints")

# Demand of Production
demand_production_node = GraphNode("Demand of production")
demand_for_each_t_node = GraphNode("for each t")
demand_for_each_t_node.add_child(GraphNode("v_t + x_t + y_t - u_{t-1} + u_t"))
demand_for_each_tp_node = GraphNode("for each t, for each p")
demand_for_each_tp_node.add_child(GraphNode("v_{t,p} + x_{t,p} + y_{t,p} - u_{t-1,p} + u_{t,p}"))
demand_production_node.add_child(demand_for_each_t_node)
demand_production_node.add_child(demand_for_each_tp_node)
explicit_constraints_node.add_child(demand_production_node)

# Inventory Balance
inventory_balance_node = GraphNode("Inventory balance")
inventory_balance_for_each_t_node = GraphNode("for each t")
inventory_balance_for_each_t_node.add_child(GraphNode("u_t = u_{t-1} + x_t - d_t + y_t - v_t"))
inventory_balance_for_each_tp_node = GraphNode("for each t, for each p")
inventory_balance_for_each_tp_node.add_child(GraphNode("u_{t,p} = u_{t-1,p} + x_{t,p} - d_{t,p} + y_{t,p} - v_{t,p}"))
inventory_balance_node.add_child(inventory_balance_for_each_t_node)
inventory_balance_node.add_child(inventory_balance_for_each_tp_node)
explicit_constraints_node.add_child(inventory_balance_node)

# Labour Hour Limit
labour_hour_limit_for_each_t_node = GraphNode("for each t")
labour_hour_limit_for_each_t_node.add_child(GraphNode("UB^L_t \\geq h_t x_t + h_t y_t"))
labour_hour_limit_for_each_tp_node = GraphNode("for each t, for each p")
labour_hour_limit_for_each_tp_node.add_child(GraphNode("UB^L_{t,p} \\geq h_{t,p} x_{t,p} + h_t y_{t,p}"))
labour_hour_limit_node.add_child(labour_hour_limit_for_each_t_node)
labour_hour_limit_node.add_child(labour_hour_limit_for_each_tp_node)
explicit_constraints_node.add_child(labour_hour_limit_node)

# Material Budget Limit
material_budget_limit_for_each_t_node = GraphNode("for each t")
material_budget_limit_for_each_t_node.add_child(GraphNode("UB^M_t \\geq m_t x_t + m_t y_t"))
material_budget_limit_for_each_tp_node = GraphNode("for each t, for each p")
material_budget_limit_for_each_tp_node.add_child(GraphNode("UB^M_{t,p} \\geq m_{t,p} x_{t,p} + m_{t,p} y_{t,p}"))
material_budget_limit_node.add_child(material_budget_limit_for_each_t_node)
material_budget_limit_node.add_child(material_budget_limit_for_each_tp_node)
explicit_constraints_node.add_child(material_budget_limit_node)

# Implicit Constraints
implicit_constraints_node = GraphNode("Implicit constraints")

# Production is possible only if set-up is "true"
production_possible_node = GraphNode("Production is possible only if set-up is 'true'")
production_for_each_t_node = GraphNode("for each t")
production_for_each_t_node.add_child(GraphNode("y_t + x_t \\leq D_t u_t"))
production_for_each_tp_node = GraphNode("for each t, for each p")
production_for_each_tp_node.add_child(GraphNode("y_{t,p} + x_{t,p} \\leq D_{t,p} u_{t,p}"))
production_possible_node.add_child(production_for_each_t_node)
production_possible_node.add_child(production_for_each_tp_node)
implicit_constraints_node.add_child(production_possible_node)

explicit_constraints_node.add_child(implicit_constraints_node)
constraints_node.add_child(explicit_constraints_node)

root_production.add_child(constraints_node)

root_milp.add_child(root_production)


################################################################################
################################################################################
#TSP Graph
################################################################################
################################################################################

# TSP Node
tsp_node = GraphNode("Travel Salesman Problem (TSP)")

# Nodes Subgraph
nodes_node = GraphNode("Nodes")
nodes_node.add_child(GraphNode("I = {1,2,..., i, ...}"))

# Nodes Subcategories
cities_node = GraphNode("Cities to visit")
customers_node = GraphNode("Customers to visit")
patients_node = GraphNode("Patients to visit")
a_new_instance_node = GraphNode("A new instance")

nodes_node.add_child(cities_node)
nodes_node.add_child(customers_node)
nodes_node.add_child(patients_node)
nodes_node.add_child(a_new_instance_node)

# Edges Subgraph
edges_node = GraphNode("Edges")
edges_node.add_child(GraphNode("E = {ij for all i, j in I}"))

# Edge Types
flights_node = GraphNode("Flights")
roads_node = GraphNode("Roads")
rails_node = GraphNode("Rails")

edges_node.add_child(flights_node)
edges_node.add_child(roads_node)
edges_node.add_child(rails_node)

nodes_node.add_child(edges_node)

# Costs Subgraph
costs_node = GraphNode("Costs")
costs_node.add_child(GraphNode("c_ij for ij in E"))

# Cost Components
travel_time_node = GraphNode("Travel time")
travel_cost_node = GraphNode("Travel cost")

# Travel Cost Types
airfare_node = GraphNode("Airfare")
vehicle_cost_node = GraphNode("Vehicle cost")

travel_cost_node.add_child(airfare_node)
travel_cost_node.add_child(vehicle_cost_node)

costs_node.add_child(travel_time_node)
costs_node.add_child(travel_cost_node)

nodes_node.add_child(costs_node)

# Service Requirements Subgraph
service_requirements_node = GraphNode("Service requirements")
service_time_node = GraphNode("Service time")
service_time_node.add_child(GraphNode("s_i for i in I"))

# Service Requirement Types
servicing_customers_node = GraphNode("Servicing customers")
examining_patients_node = GraphNode("Examining patients")

service_time_node.add_child(servicing_customers_node)
service_time_node.add_child(examining_patients_node)
service_requirements_node.add_child(service_time_node)

nodes_node.add_child(service_requirements_node)

# Penalties Subgraph
penalties_node = GraphNode("Penalties")

# Punctuality
punctuality_node = GraphNode("Punctuality")

earliness_penalty_node = GraphNode("Earliness penalty")
earliness_penalty_node.add_child(GraphNode("p_i^E for i in I"))

lateness_penalty_node = GraphNode("Lateness penalty")
lateness_penalty_node.add_child(GraphNode("p_i^L for i in I"))

punctuality_node.add_child(earliness_penalty_node)
punctuality_node.add_child(lateness_penalty_node)

# Missing Nodes Penalty
missing_nodes_node = GraphNode("Missing nodes")
missing_nodes_node.add_child(GraphNode("p_i^M for i in I"))

# Missing Node Types
not_visiting_cities_node = GraphNode("Not visiting cities")
not_servicing_customers_node = GraphNode("Not servicing customers")
not_visiting_patients_node = GraphNode("Not visiting patients")

missing_nodes_node.add_child(not_visiting_cities_node)
missing_nodes_node.add_child(not_servicing_customers_node)
missing_nodes_node.add_child(not_visiting_patients_node)

penalties_node.add_child(punctuality_node)
penalties_node.add_child(missing_nodes_node)

nodes_node.add_child(penalties_node)

# Nodes Must Be Visited
nodes_must_be_visited_node = GraphNode("Nodes must be visited")
subset_i_node = GraphNode("I^- subset of I")

# Required Node Sets
set_of_cities_node = GraphNode("Set of cities must be visited")
set_of_customers_node = GraphNode("Set of customers must be visited")
set_of_patients_node = GraphNode("Set of patients must be visited")

subset_i_node.add_child(set_of_cities_node)
subset_i_node.add_child(set_of_customers_node)
subset_i_node.add_child(set_of_patients_node)

nodes_must_be_visited_node.add_child(subset_i_node)
nodes_node.add_child(nodes_must_be_visited_node)

# Values Subgraph
values_node = GraphNode("Values")
values_node.add_child(GraphNode("w_i for i in I"))

# Value Types
attractions_node = GraphNode("Attractions")
revenue_node = GraphNode("Revenue")
urgency_node = GraphNode("Urgency")

values_node.add_child(attractions_node)
values_node.add_child(revenue_node)
values_node.add_child(urgency_node)

nodes_node.add_child(values_node)

# Budget Subgraph
budget_node = GraphNode("Budget")

# Financial Limit
financial_limit_node = GraphNode("Financial limit")
financial_limit_node.add_child(GraphNode("b_max"))

budget_for_holiday_node = GraphNode("Budget for holiday")
budget_for_travel_cost_node = GraphNode("Budget for travel cost")

financial_limit_node.add_child(budget_for_holiday_node)
financial_limit_node.add_child(budget_for_travel_cost_node)

budget_node.add_child(financial_limit_node)

# Time Limit
time_limit_node = GraphNode("Time limit")
time_limit_node.add_child(GraphNode("t_max"))

budget_node.add_child(time_limit_node)
nodes_node.add_child(budget_node)

# Time Windows Subgraph
time_windows_node = GraphNode("Time windows")
time_windows_node.add_child(GraphNode("[e_i, l_i] for i in I"))

# Time Window Types
customer_availability_node = GraphNode("Customer availability")
patient_availability_node = GraphNode("Patient availability/schedule")

time_windows_node.add_child(customer_availability_node)
time_windows_node.add_child(patient_availability_node)

nodes_node.add_child(time_windows_node)

# Objective Subgraph
objective_node = GraphNode("Objective")

# Minimization
minimization_node = GraphNode("Minimization")

minimizing_total_cost_node = GraphNode("Minimizing total cost")
minimizing_total_cost_node.add_child(GraphNode("sum_{ij in E} c_ij x_ij"))

minimization_node.add_child(minimizing_total_cost_node)

# Minimizing Total Penalty
minimizing_total_penalty_node = GraphNode("Minimizing total penalty")

penalizing_unpunctuality_node = GraphNode("Penalizing unpunctuality")
penalizing_unpunctuality_node.add_child(GraphNode("sum_{i in I} (p_i^E z_i^E + p_i^L z_i^L)"))

penalizing_missing_nodes_node = GraphNode("Penalizing missing nodes")
penalizing_missing_nodes_node.add_child(GraphNode("sum_{i in I} p_i^M (1-y_i)"))

minimizing_total_penalty_node.add_child(penalizing_unpunctuality_node)
minimizing_total_penalty_node.add_child(penalizing_missing_nodes_node)

minimization_node.add_child(minimizing_total_penalty_node)
objective_node.add_child(minimization_node)

# Maximization
maximization_node = GraphNode("Maximization")

maximizing_total_value_node = GraphNode("Maximizing total value")
maximizing_total_value_node.add_child(GraphNode("sum_{i in I} w_i y_i"))

maximizing_total_profit_node = GraphNode("Maximizing total profit")
maximizing_total_profit_node.add_child(GraphNode("sum_{i in I} (w_i y_i - p_i^M (1-y_i))"))

maximization_node.add_child(maximizing_total_value_node)
maximization_node.add_child(maximizing_total_profit_node)

objective_node.add_child(maximization_node)
nodes_node.add_child(objective_node)

# Decision Variables Subgraph
decision_variables_node = GraphNode("Decision variables")

# Nodes Visited
nodes_visited_node = GraphNode("Nodes visited")
nodes_visited_node.add_child(GraphNode("y_i = 0/1 for i in I"))

# Nodes Visited Types
visiting_cities_node = GraphNode("Visiting cities")
visiting_customers_node = GraphNode("Visiting customers")
visiting_patients_node = GraphNode("Visiting patients")

nodes_visited_node.add_child(visiting_cities_node)
nodes_visited_node.add_child(visiting_customers_node)
nodes_visited_node.add_child(visiting_patients_node)

decision_variables_node.add_child(nodes_visited_node)

# Edge Traveled
edge_traveled_node = GraphNode("Edge traveled")
edge_traveled_node.add_child(GraphNode("x_ij = 0/1 for ij in E"))

# Edge Traveled Types
flight_node = GraphNode("Flight from city to another city")
travel_customer_node = GraphNode("Travel from customer to another customer")
travel_patient_node = GraphNode("Travel from patient to another patient")

edge_traveled_node.add_child(flight_node)
edge_traveled_node.add_child(travel_customer_node)
edge_traveled_node.add_child(travel_patient_node)

decision_variables_node.add_child(edge_traveled_node)

# Arrival Time
arrival_time_node = GraphNode("Arrival time")
arrival_time_node.add_child(GraphNode("a_i >= 0 for i in I"))

# Arrival Time Types
arrival_city_node = GraphNode("Arrival time at city")
arrival_customer_node = GraphNode("Arrival time at customer")
arrival_patient_node = GraphNode("Arrival time at patient")

arrival_time_node.add_child(arrival_city_node)
arrival_time_node.add_child(arrival_customer_node)
arrival_time_node.add_child(arrival_patient_node)

decision_variables_node.add_child(arrival_time_node)

# Early Arrival
early_arrival_node = GraphNode("Early arrival")
early_arrival_node.add_child(GraphNode("z_i^E = 0/1 for i in I"))

# Early Arrival Types
early_arrival_city_node = GraphNode("Arriving at city earlier than scheduled")
early_arrival_customer_node = GraphNode("Arriving at customer earlier than scheduled")
early_arrival_patient_node = GraphNode("Arriving at patient earlier than scheduled")

early_arrival_node.add_child(early_arrival_city_node)
early_arrival_node.add_child(early_arrival_customer_node)
early_arrival_node.add_child(early_arrival_patient_node)

decision_variables_node.add_child(early_arrival_node)

# Late Arrival
late_arrival_node = GraphNode("Late arrival")
late_arrival_node.add_child(GraphNode("z_i^L = 0/1 for i in I"))

# Late Arrival Types
late_arrival_city_node = GraphNode("Arriving at city later than scheduled")
late_arrival_customer_node = GraphNode("Arriving at customer later than scheduled")
late_arrival_patient_node = GraphNode("Arriving at patient later than scheduled")

late_arrival_node.add_child(late_arrival_city_node)
late_arrival_node.add_child(late_arrival_customer_node)
late_arrival_node.add_child(late_arrival_patient_node)

decision_variables_node.add_child(late_arrival_node)

# Position Along Route
position_along_route_node = GraphNode("Position along route")
position_along_route_node.add_child(GraphNode("u_i = integer for the position of node i along the route"))

decision_variables_node.add_child(position_along_route_node)
nodes_node.add_child(decision_variables_node)

# Constraints Subgraph
constraints_node = GraphNode("Constraints")

# Nodes Must Be Visited
nodes_must_be_visited_constraint_node = GraphNode("Nodes must be visited")
nodes_must_be_visited_constraint_node.add_child(GraphNode("y_i = 1 for i in I^-"))

# Nodes Must Be Visited Types
cities_visited_node = GraphNode("Cities must be visited")
customers_visited_node = GraphNode("Customers must be visited")
patients_visited_node = GraphNode("Patients must be visited")

nodes_must_be_visited_constraint_node.add_child(cities_visited_node)
nodes_must_be_visited_constraint_node.add_child(customers_visited_node)
nodes_must_be_visited_constraint_node.add_child(patients_visited_node)

constraints_node.add_child(nodes_must_be_visited_constraint_node)

# Time Window Satisfaction
time_window_satisfaction_node = GraphNode("Time window satisfaction")

# No Violation (Hard Constraint)
no_violation_node = GraphNode("No violation (hard constraint)")
no_violation_node.add_child(GraphNode("e_i <= a_i <= l_i for i in I"))

# Penalizing Violation (Soft Constraint)
penalizing_violation_node = GraphNode("Penalizing violation (soft constraint)")

earliness_node = GraphNode("Earliness")
earliness_node.add_child(GraphNode("M z_i^E >= e_i - a_i for i in I"))

lateness_node = GraphNode("Lateness")
lateness_node.add_child(GraphNode("M z_i^L >= a_i - l_i for i in I"))

penalizing_violation_node.add_child(earliness_node)
penalizing_violation_node.add_child(lateness_node)

time_window_satisfaction_node.add_child(no_violation_node)
time_window_satisfaction_node.add_child(penalizing_violation_node)

constraints_node.add_child(time_window_satisfaction_node)

# Budget
budget_constraint_node = GraphNode("Budget")

financial_limit_node = GraphNode("Financial limit")
financial_limit_node.add_child(GraphNode("sum_{ij in E} c_ij x_ij <= b_max"))

time_limit_node = GraphNode("Time limit")
time_limit_node.add_child(GraphNode("sum_{ij in E} c_ij x_ij + sum_{i in I} s_i y_i <= t_max"))

time_limit_node.add_child(GraphNode("a_i + s_i y_i <= t_max for i in I"))

budget_constraint_node.add_child(financial_limit_node)
budget_constraint_node.add_child(time_limit_node)

constraints_node.add_child(budget_constraint_node)

# Loop
loop_node = GraphNode("Loop")

closed_loop_node = GraphNode("Closed loop with flow balance")
closed_loop_node.add_child(GraphNode("sum_{i in I} x_ij - sum_{i in I} x_ji = 0 for j in I"))

open_loop_node = GraphNode("Open loop with flow balance")
open_loop_node.add_child(GraphNode("sum_{i in I} x_ij - sum_{i in I} x_ji = 0 for j in I \\backslash 0"))

loop_node.add_child(closed_loop_node)
loop_node.add_child(open_loop_node)

constraints_node.add_child(loop_node)

# Visited Nodes Constraint
visited_nodes_node = GraphNode("Visited nodes")
visited_nodes_node.add_child(GraphNode("y_i <= sum_{j in I} x_ij for i in I"))

# Subtour Elimination
subtour_elimination_node = GraphNode("Subtour elimination")

dfj_node = GraphNode("DFJ")
mtz_node = GraphNode("MTZ")

mtz_node.add_child(GraphNode("u_i+1-u_j <= M(1-x_{ij}) for i, j in I (M is a big number)"))

subtour_elimination_node.add_child(dfj_node)
subtour_elimination_node.add_child(mtz_node)

constraints_node.add_child(subtour_elimination_node)

# Capacity Constraint
capacity_node = GraphNode("Capacity")

# No Self-Pointing Constraint
no_self_pointing_node = GraphNode("No self-pointing")
no_self_pointing_node.add_child(GraphNode("x_ii = 0 for all i in I"))

# Start from Depot Constraint
start_from_depot_node = GraphNode("Start from depot (fixed point)")
start_from_depot_node.add_child(GraphNode("y_0 = 1"))

# Tag Color Coding Constraint
tag_color_coding_node = GraphNode("Tag color coding")

# Tag Colors
yellow_tag_node = GraphNode("yellow for family-holiday instance")
red_tag_node = GraphNode("red for last-mile delivery instance")
green_tag_node = GraphNode("green for home-care instance")

tag_color_coding_node.add_child(yellow_tag_node)
tag_color_coding_node.add_child(red_tag_node)
tag_color_coding_node.add_child(green_tag_node)

constraints_node.add_child(capacity_node)
constraints_node.add_child(no_self_pointing_node)
constraints_node.add_child(start_from_depot_node)
constraints_node.add_child(tag_color_coding_node)

# Add Constraints to TSP
tsp_node.add_child(constraints_node)

# Add TSP to MILP
root_milp.add_child(tsp_node)


################################################################################
################################################################################
# Blending Problems
################################################################################
################################################################################

blending_node = GraphNode("Blending problems")

# Entities
entities_node = GraphNode("Entities")

ingredients_set_node = GraphNode("Set of ingredients or raw materials")
ingredients_set_node.add_child(GraphNode("I = {i}"))

products_set_node = GraphNode("Set of products")
products_set_node.add_child(GraphNode("J = {j}"))

entities_node.add_child(ingredients_set_node)
entities_node.add_child(products_set_node)

blending_node.add_child(entities_node)

# Parameters
parameters_node = GraphNode("Parameters")

# Blend ratio requirements
blend_ratio_node = GraphNode("Blend ratio requirements")

lower_bound_node = GraphNode("Lower bound")
lower_bound_node.add_child(GraphNode("a_L(i,j), \\forall i \\in I, \\forall j \\in J"))

upper_bound_node = GraphNode("Upper bound")
upper_bound_node.add_child(GraphNode("a_U(i,j), \\forall i \\in I, \\forall j \\in J"))

blend_ratio_node.add_child(lower_bound_node)
blend_ratio_node.add_child(upper_bound_node)
parameters_node.add_child(blend_ratio_node)

# Costs
costs_node = GraphNode("Costs")
costs_node.add_child(GraphNode("c_i, \\forall i \\in I"))
parameters_node.add_child(costs_node)

# Ingredient supply limit
ingredient_supply_node = GraphNode("Ingredient supply limit")
ingredient_supply_node.add_child(GraphNode("s_i, \\forall i \\in I"))
parameters_node.add_child(ingredient_supply_node)

# Demand of products
demand_node = GraphNode("Demand of products")
demand_node.add_child(GraphNode("d_j, \\forall j \\in J"))
parameters_node.add_child(demand_node)

# Quality of products
quality_products_node = GraphNode("Quality of products")

quality_score_node = GraphNode("Quality score of ingredient i in Product j")
quality_score_node.add_child(GraphNode("q_{i,j}, \\forall i \\in I, \\forall j \\in J"))
quality_products_node.add_child(quality_score_node)

quality_threshold_node = GraphNode("Quality threshold of Product j")

quality_upper_node = GraphNode("Upper limit")
quality_upper_node.add_child(GraphNode("Q^U_j, \\forall j \\in J"))

quality_lower_node = GraphNode("Lower limit")
quality_lower_node.add_child(GraphNode("Q^L_j, \\forall j \\in J"))

quality_threshold_node.add_child(quality_upper_node)
quality_threshold_node.add_child(quality_lower_node)
quality_products_node.add_child(quality_threshold_node)

parameters_node.add_child(quality_products_node)

# Production capacity limit
production_capacity_node = GraphNode("Production capacity limit")

capacity_upper_node = GraphNode("Capacity limit of Product j")
capacity_upper_node.add_child(GraphNode("P^U_j, \\forall j \\in J"))

capacity_lower_node = GraphNode("Minimum production")
capacity_lower_node.add_child(GraphNode("P^L_j, \\forall j \\in J"))

production_capacity_node.add_child(capacity_upper_node)
production_capacity_node.add_child(capacity_lower_node)

parameters_node.add_child(production_capacity_node)

blending_node.add_child(parameters_node)

# Decision Variables
decision_node = GraphNode("Decision variables")

amount_ingredient_node = GraphNode("Amount of ingredient i in Product j")
amount_ingredient_node.add_child(GraphNode("x_{i,j}, \\forall i \\in I, \\forall j \\in J"))

produce_or_not_node = GraphNode("To produce j or not")
produce_or_not_node.add_child(GraphNode("y_j \\in \\{0,1\\}, \\forall j \\in J"))

decision_node.add_child(amount_ingredient_node)
decision_node.add_child(produce_or_not_node)

blending_node.add_child(decision_node)

# Objective
objective_node = GraphNode("Objective")

min_cost_node = GraphNode("Minimise total cost of ingredients used")
min_cost_node.add_child(GraphNode("v_{min} = \\sum_{i \\in I} \\sum_{j \\in J} c_i x_{i,j}"))

max_quality_node = GraphNode("Maximise overall product quality")
max_quality_node.add_child(GraphNode("v_{max} = \\sum_{i \\in I} \\sum_{j \\in J} q_{i,j} x_{i,j}"))

objective_node.add_child(min_cost_node)
objective_node.add_child(max_quality_node)

blending_node.add_child(objective_node)

# Constraints
constraints_node = GraphNode("Constraints")

# Explicit constraints
explicit_constraints_node = GraphNode("Explicit constraints")

# Blend ratios
blend_ratios_constraint_node = GraphNode("Blend ratios")

ratio_at_least_lb_node = GraphNode("The ratio of ingredient i in Product j must be at least the lower bound")
ratio_at_least_lb_node.add_child(
    GraphNode("x_{i,j} \\ge a_L(i,j) \\sum_{k \\in I} x_{k,j}, \\forall i \\in I, \\forall j \\in J")
)

ratio_at_most_ub_node = GraphNode("The ratio of ingredient i in Product j must be no more than the upper bound")
ratio_at_most_ub_node.add_child(
    GraphNode("x_{i,j} \\le a_U(i,j) \\sum_{k \\in I} x_{k,j}, \\forall i \\in I, \\forall j \\in J")
)

blend_ratios_constraint_node.add_child(ratio_at_least_lb_node)
blend_ratios_constraint_node.add_child(ratio_at_most_ub_node)

explicit_constraints_node.add_child(blend_ratios_constraint_node)

# Demand requirements
demand_requirements_node = GraphNode("Demand requirements")

demand_at_least_node = GraphNode("Product j produced must be at least meeting the demand")
demand_at_least_node.add_child(
    GraphNode("\\sum_{i \\in I} x_{i,j} \\ge d_j, \\forall j \\in J")
)

demand_at_most_node = GraphNode("Product j produced must be no more than the demand")
demand_at_most_node.add_child(
    GraphNode("\\sum_{i \\in I} x_{i,j} \\le d_j, \\forall j \\in J")
)

demand_requirements_node.add_child(demand_at_least_node)
demand_requirements_node.add_child(demand_at_most_node)

explicit_constraints_node.add_child(demand_requirements_node)

# Supply limits
supply_limits_node = GraphNode("Supply limits")
supply_limits_node.add_child(
    GraphNode("\\sum_{j \\in J} x_{i,j} \\le s_i, \\forall i \\in I")
)
explicit_constraints_node.add_child(supply_limits_node)

# Production capacity limits
prod_capacity_limits_node = GraphNode("Production capacity limits")

prod_cap_upper_node = GraphNode("Product j produced must not exceed capacity upper limit")
prod_cap_upper_node.add_child(
    GraphNode("\\sum_{i \\in I} x_{i,j} \\le P^U_j, \\forall j \\in J")
)

prod_cap_lower_node = GraphNode("Product j produced must be at least minimum production")
prod_cap_lower_node.add_child(
    GraphNode("\\sum_{i \\in I} x_{i,j} \\ge P^L_j, \\forall j \\in J")
)

prod_capacity_limits_node.add_child(prod_cap_upper_node)
prod_capacity_limits_node.add_child(prod_cap_lower_node)

explicit_constraints_node.add_child(prod_capacity_limits_node)

# Quality threshold constraints
quality_threshold_constraints_node = GraphNode("Quality threshold constraints")

quality_at_least_node = GraphNode("Total quality score of Product j must be at least the lower threshold")
quality_at_least_node.add_child(
    GraphNode("\\sum_{i \\in I} q_{i,j} x_{i,j} \\ge Q^L_j, \\forall j \\in J")
)

quality_at_most_node = GraphNode("Total quality score of Product j must be at most the upper threshold")
quality_at_most_node.add_child(
    GraphNode("\\sum_{i \\in I} q_{i,j} x_{i,j} \\le Q^U_j, \\forall j \\in J")
)

quality_threshold_constraints_node.add_child(quality_at_least_node)
quality_threshold_constraints_node.add_child(quality_at_most_node)

explicit_constraints_node.add_child(quality_threshold_constraints_node)

constraints_node.add_child(explicit_constraints_node)

# Implicit constraints
implicit_constraints_node = GraphNode("Implicit constraints")

link_constraints_node = GraphNode("Link constraints")

link_min_node = GraphNode("Link minimum production with binary decision")
link_min_node.add_child(
    GraphNode("\\sum_{i \\in I} x_{i,j} \\ge P^L_j y_j, \\forall j \\in J")
)

link_max_node = GraphNode("Link capacity upper limit with binary decision")
link_max_node.add_child(
    GraphNode("\\sum_{i \\in I} x_{i,j} \\le P^U_j y_j, \\forall j \\in J")
)

link_constraints_node.add_child(link_min_node)
link_constraints_node.add_child(link_max_node)

implicit_constraints_node.add_child(link_constraints_node)
constraints_node.add_child(implicit_constraints_node)

blending_node.add_child(constraints_node)

# Attach Blending Problems to MILP root
root_milp.add_child(blending_node)


################################################################################
################################################################################
# Facility Location
################################################################################
################################################################################

facility_location_node = GraphNode("Facility location")

# Entities
entities_node = GraphNode("Entities")

customers_node = GraphNode("Customers")
customers_node.add_child(GraphNode("M"))

facilities_node = GraphNode("Facilities")
facilities_node.add_child(GraphNode("F"))

# Facility types (tags)
capacitated_tag_node = GraphNode("Capacitated")
uncapacitated_tag_node = GraphNode("Uncapacitated")
facilities_node.add_child(capacitated_tag_node)
facilities_node.add_child(uncapacitated_tag_node)

entities_node.add_child(customers_node)
entities_node.add_child(facilities_node)

facility_location_node.add_child(entities_node)

# Parameters
parameters_node = GraphNode("Parameters")

# Cost
cost_node = GraphNode("Cost")

transport_cost_node = GraphNode("Transportation from facility to customer")
transport_cost_node.add_child(GraphNode("C_{f,m}, \\forall f \\in F, \\forall m \\in M"))

setup_cost_node = GraphNode("Set-up cost of facility")
setup_cost_node.add_child(GraphNode("S_f, \\forall f \\in F"))

cost_node.add_child(transport_cost_node)
cost_node.add_child(setup_cost_node)
parameters_node.add_child(cost_node)

# Demand of customers
demand_node = GraphNode("Demand of customers")
demand_node.add_child(GraphNode("D_m, \\forall m \\in M"))
parameters_node.add_child(demand_node)

# Capacity of facilities
capacity_node = GraphNode("Capacity of facilities")
capacity_node.add_child(GraphNode("U_f, \\forall f \\in F"))
parameters_node.add_child(capacity_node)

# Limitations
limitations_node = GraphNode("Limitations")

total_budget_node = GraphNode("Total set-up budget")
total_budget_node.add_child(GraphNode("B"))

max_facilities_node = GraphNode("Max number of facilities allowed")
max_facilities_node.add_child(GraphNode("K_{vmax}"))

min_facilities_node = GraphNode("Min number of facilities required")
min_facilities_node.add_child(GraphNode("K_{vmin}"))

limitations_node.add_child(total_budget_node)
limitations_node.add_child(max_facilities_node)
limitations_node.add_child(min_facilities_node)

parameters_node.add_child(limitations_node)

facility_location_node.add_child(parameters_node)

# Decision
decision_node = GraphNode("Decision")

fraction_demand_node = GraphNode("Fraction of demand of a customer satisfied by a facility")
fraction_demand_node.add_child(GraphNode("y_{f,m}, \\forall f \\in F, \\forall m \\in M"))

setup_decision_node = GraphNode("To set up facility at a location or not")
setup_decision_node.add_child(GraphNode("x_f, \\forall f \\in F"))

decision_node.add_child(fraction_demand_node)
decision_node.add_child(setup_decision_node)

facility_location_node.add_child(decision_node)

# Objective function
objective_node = GraphNode("Objective function")

total_oper_cost_node = GraphNode("Total operation cost")
total_oper_cost_node.add_child(
    GraphNode("\\sum_{f \\in F} \\sum_{m \\in M} C_{f,m} y_{f,m}")
)

total_setup_cost_node = GraphNode("Total set-up cost")
total_setup_cost_node.add_child(
    GraphNode("\\sum_{f \\in F} S_f x_f")
)

objective_node.add_child(total_oper_cost_node)
objective_node.add_child(total_setup_cost_node)

facility_location_node.add_child(objective_node)

# Constraints
constraints_node = GraphNode("Constraints")

# Basic constraints
basic_constraints_node = GraphNode("Basic constraints")

supply_sum_node = GraphNode("Sum of supply to each customer must be 1")
supply_sum_node.add_child(
    GraphNode("\\sum_{f \\in F} y_{f,m} = 1, \\forall m \\in M")
)

basic_constraints_node.add_child(supply_sum_node)
constraints_node.add_child(basic_constraints_node)

# Set-up logic constraints
setup_logic_node = GraphNode("Set-up logic constraints")

capacitated_node = GraphNode("Capacitated")
capacitated_node.add_child(
    GraphNode("\\sum_{m \\in M} D_m y_{f,m} \\leq U_f x_f, \\forall f \\in F")
)

uncapacitated_node = GraphNode("Uncapacitated")
uncapacitated_node.add_child(
    GraphNode("y_{f,m} \\leq x_f, \\forall f \\in F, \\forall m \\in M")
)

setup_logic_node.add_child(capacitated_node)
setup_logic_node.add_child(uncapacitated_node)

constraints_node.add_child(setup_logic_node)

# Budget constraint
budget_constraint_node = GraphNode("Budget constraint")
budget_constraint_node.add_child(
    GraphNode("\\sum_{f \\in F} S_f x_f \\leq B")
)
constraints_node.add_child(budget_constraint_node)

# User constraints
user_constraints_node = GraphNode("User constraints")

max_facility_constraint_node = GraphNode("Max number of facility allowed")
max_facility_constraint_node.add_child(
    GraphNode("\\sum_{f \\in F} x_f \\leq K_{vmax}")
)

min_facility_constraint_node = GraphNode("Min number of facility required")
min_facility_constraint_node.add_child(
    GraphNode("\\sum_{f \\in F} x_f \\geq K_{vmin}")
)

user_constraints_node.add_child(max_facility_constraint_node)
user_constraints_node.add_child(min_facility_constraint_node)

constraints_node.add_child(user_constraints_node)

facility_location_node.add_child(constraints_node)

# Attach Facility Location to MILP root
root_milp.add_child(facility_location_node)


################################################################################
################################################################################
# 3D Packing
################################################################################
################################################################################

packing_3d_node = GraphNode("3D Packing")

# Entities
entities_node = GraphNode("Entities")

items_set_node = GraphNode("Set of items")
items_set_node.add_child(GraphNode("I = {i}"))

containers_set_node = GraphNode("Set of containers")
containers_set_node.add_child(GraphNode("K = {k}"))

entities_node.add_child(items_set_node)
entities_node.add_child(containers_set_node)

packing_3d_node.add_child(entities_node)

# Parameters
parameters_node = GraphNode("Parameters")

# Costs
costs_node = GraphNode("Costs")

packing_items_node = GraphNode("Packing items")

packing_items_ind_node = GraphNode("Container independent")
packing_items_ind_node.add_child(GraphNode("c_i, \\forall i \\in I"))

packing_items_dep_node = GraphNode("Container dependent")
packing_items_dep_node.add_child(GraphNode("c_{i,k}, \\forall i \\in I, \\forall k \\in K"))

packing_items_node.add_child(packing_items_ind_node)
packing_items_node.add_child(packing_items_dep_node)

using_containers_node = GraphNode("Using containers")
using_containers_node.add_child(GraphNode("f_k, \\forall k \\in K"))

costs_node.add_child(packing_items_node)
costs_node.add_child(using_containers_node)

parameters_node.add_child(costs_node)

# Demands
demands_node = GraphNode("Demands")
demands_node.add_child(GraphNode("d_i, \\forall i \\in I"))
parameters_node.add_child(demands_node)

# Sizes
sizes_node = GraphNode("Sizes")

volume_item_node = GraphNode("Volume of item")
volume_item_node.add_child(GraphNode("v_i, \\forall i \\in I"))

weight_item_node = GraphNode("Weight of item")
weight_item_node.add_child(GraphNode("w_i, \\forall i \\in I"))

sizes_node.add_child(volume_item_node)
sizes_node.add_child(weight_item_node)

parameters_node.add_child(sizes_node)

# Capacity
capacity_node = GraphNode("Capacity")

volume_limit_container_node = GraphNode("Volume limit of container")
volume_limit_container_node.add_child(GraphNode("V_k, \\forall k \\in K"))

weight_limit_container_node = GraphNode("Weight limit of container")
weight_limit_container_node.add_child(GraphNode("W_k, \\forall k \\in K"))

capacity_node.add_child(volume_limit_container_node)
capacity_node.add_child(weight_limit_container_node)

parameters_node.add_child(capacity_node)

# Compatibility
compatibility_node = GraphNode("Compatibility")

between_items_node = GraphNode("Between items - set of incompatible item pairs")
between_items_node.add_child(GraphNode("P^{I} \\subseteq I \\times I"))

between_items_and_containers_node = GraphNode("Between containers and items - set of incompatible item–container pairs")
between_items_and_containers_node.add_child(GraphNode("P^{C} \\subseteq I \\times K"))

compatibility_node.add_child(between_items_node)
compatibility_node.add_child(between_items_and_containers_node)

parameters_node.add_child(compatibility_node)

# Dimensions (optional if volumes are given)
dimensions_node = GraphNode("Dimensions (optional if volumes are given)")

item_dimensions_node = GraphNode("Item dimensions (length, width, height)")
item_dimensions_node.add_child(GraphNode("(l_i, w_i, h_i), \\forall i \\in I"))

container_dimensions_node = GraphNode("Container dimensions (length, width, height)")
container_dimensions_node.add_child(GraphNode("(L_k, W_k, H_k), \\forall k \\in K"))

dimensions_node.add_child(item_dimensions_node)
dimensions_node.add_child(container_dimensions_node)

parameters_node.add_child(dimensions_node)

# Resources
resources_node = GraphNode("Resources")

max_containers_node = GraphNode("Maximum number of available containers (optional)")
max_containers_node.add_child(GraphNode("U"))

resources_node.add_child(max_containers_node)

parameters_node.add_child(resources_node)

# Loading times (optional)
loading_times_param_node = GraphNode("Loading times (optional)")

loading_time_container_ind_node = GraphNode("Container independent loading time per item")
loading_time_container_ind_node.add_child(GraphNode("t_i, \\forall i \\in I"))

loading_time_container_dep_node = GraphNode("Container dependent loading time")
loading_time_container_dep_node.add_child(GraphNode("t_{i,k}, \\forall i \\in I, \\forall k \\in K"))

max_loading_time_node = GraphNode("Maximum loading time per container")
max_loading_time_node.add_child(GraphNode("T^{\\max}_k, \\forall k \\in K"))

loading_times_param_node.add_child(loading_time_container_ind_node)
loading_times_param_node.add_child(loading_time_container_dep_node)
loading_times_param_node.add_child(max_loading_time_node)

parameters_node.add_child(loading_times_param_node)

# Load balancing
load_balancing_param_node = GraphNode("Load balancing (optional)")

weight_diff_node = GraphNode("Difference in weight between containers")
weight_diff_node.add_child(GraphNode("\\varepsilon^w_0"))

volume_diff_node = GraphNode("Difference in volume between containers")
volume_diff_node.add_child(GraphNode("\\varepsilon^v_0"))

load_balancing_param_node.add_child(weight_diff_node)
load_balancing_param_node.add_child(volume_diff_node)

parameters_node.add_child(load_balancing_param_node)

packing_3d_node.add_child(parameters_node)

# Decision variables
decision_node = GraphNode("Decision variables")

item_placement_node = GraphNode("Item placement (required)")

# If multiple copies allowed
num_items_node = GraphNode("Number of items of type i packed in container k")
num_items_node.add_child(GraphNode("x_{i,k} \\in \\mathbb{Z}_+, \\forall i \\in I, \\forall k \\in K"))

# Binary placement
binary_item_placement_node = GraphNode("Item i is placed in container k or not")
binary_item_placement_node.add_child(GraphNode("z_{i,k} \\in \\{0,1\\}, \\forall i \\in I, \\forall k \\in K"))

item_placement_node.add_child(num_items_node)
item_placement_node.add_child(binary_item_placement_node)

container_use_node = GraphNode("Container use (optional)")
container_use_node.add_child(GraphNode("y_k \\in \\{0,1\\}, \\forall k \\in K"))

decision_node.add_child(item_placement_node)
decision_node.add_child(container_use_node)

packing_3d_node.add_child(decision_node)

# Objectives
objectives_node = GraphNode("Objectives")

minimisation_node = GraphNode("Minimisation")

# Minimise total cost
min_total_cost_node = GraphNode("Minimise total cost")

cost_items_ind_node = GraphNode("Packing cost independent of containers, W.R.T. items")
cost_items_ind_node.add_child(
    GraphNode("\\min v^{cost} = \\sum_{i \\in I} c_i \\sum_{k \\in K} x_{i,k}")
)

cost_items_dep_node = GraphNode("Packing cost dependent on containers, W.R.T. items and containers")
cost_items_dep_node.add_child(
    GraphNode("\\min v^{cost} = \\sum_{i \\in I} \\sum_{k \\in K} c_{i,k} x_{i,k}")
)

container_cost_node = GraphNode("Cost of using containers")
container_cost_node.add_child(
    GraphNode("\\min v^{cont} = \\sum_{k \\in K} f_k y_k")
)

min_total_cost_node.add_child(cost_items_ind_node)
min_total_cost_node.add_child(cost_items_dep_node)
min_total_cost_node.add_child(container_cost_node)

# Minimise space wastage
min_space_waste_node = GraphNode("Minimise space wastage")

min_weight_waste_node = GraphNode("Minimise space wastage W.R.T. weight")
min_weight_waste_node.add_child(
    GraphNode("\\min v^{waste}_w = \\sum_{k \\in K} \\left(W_k - \\sum_{i \\in I} w_i x_{i,k}\\right)")
)

min_volume_waste_node = GraphNode("Minimise space wastage W.R.T. volume")
min_volume_waste_node.add_child(
    GraphNode("\\min v^{waste}_v = \\sum_{k \\in K} \\left(V_k - \\sum_{i \\in I} v_i x_{i,k}\\right)")
)

min_space_waste_node.add_child(min_weight_waste_node)
min_space_waste_node.add_child(min_volume_waste_node)

# Combined objective
combined_obj_node = GraphNode("Minimise cost and space wastage with weights")
combined_obj_node.add_child(
    GraphNode(
        "\\min v = \\alpha v^{cost} + \\beta v^{cont} + "
        "\\gamma v^{waste}_w + \\delta v^{waste}_v"
    )
)

minimisation_node.add_child(min_total_cost_node)
minimisation_node.add_child(min_space_waste_node)
minimisation_node.add_child(combined_obj_node)

objectives_node.add_child(minimisation_node)

packing_3d_node.add_child(objectives_node)

# Constraints
constraints_node = GraphNode("Constraints")

# Demand satisfaction
demand_satisfaction_node = GraphNode("Demand satisfaction")
demand_satisfaction_node.add_child(
    GraphNode("\\sum_{k \\in K} x_{i,k} \\ge d_i, \\forall i \\in I")
)
constraints_node.add_child(demand_satisfaction_node)

# Capacity constraints
capacity_constraints_node = GraphNode("Capacity constraints")

weight_limit_constr_node = GraphNode("Weight limit per container")
weight_limit_constr_node.add_child(
    GraphNode("\\sum_{i \\in I} w_i x_{i,k} \\le W_k y_k, \\forall k \\in K")
)

volume_limit_constr_node = GraphNode("Volume limit per container")
volume_limit_constr_node.add_child(
    GraphNode("\\sum_{i \\in I} v_i x_{i,k} \\le V_k y_k, \\forall k \\in K")
)

capacity_constraints_node.add_child(weight_limit_constr_node)
capacity_constraints_node.add_child(volume_limit_constr_node)

constraints_node.add_child(capacity_constraints_node)

# Container availability
container_availability_node = GraphNode("Container availability")
container_availability_node.add_child(
    GraphNode("\\sum_{k \\in K} y_k \\le U")
)
constraints_node.add_child(container_availability_node)

# Load balancing
load_balancing_constraints_node = GraphNode("Load balancing")

lb_weight_node = GraphNode("Weight based")
lb_weight_node.add_child(
    GraphNode(
        "\\left| \\sum_{i \\in I} w_i x_{i,k} - "
        "\\sum_{i \\in I} w_i x_{i,k'} \\right| \\le "
        "\\varepsilon^w_0, \\forall k,k' \\in K"
    )
)

lb_volume_node = GraphNode("Volume based")
lb_volume_node.add_child(
    GraphNode(
        "\\left| \\sum_{i \\in I} v_i x_{i,k} - "
        "\\sum_{i \\in I} v_i x_{i,k'} \\right| \\le "
        "\\varepsilon^v_0, \\forall k,k' \\in K"
    )
)

load_balancing_constraints_node.add_child(lb_weight_node)
load_balancing_constraints_node.add_child(lb_volume_node)

constraints_node.add_child(load_balancing_constraints_node)

# Compatibility constraints
compatibility_constraints_node = GraphNode("Compatibility")

between_items_constr_node = GraphNode("Between item pairs (no incompatible items together)")
between_items_constr_node.add_child(
    GraphNode(
        "x_{i,k} + x_{j,k} \\le M_{i,j,k}, "
        "\\forall (i,j) \\in P^{I}, \\forall k \\in K"
    )
)

between_items_containers_constr_node = GraphNode("Between items and containers")
between_items_containers_constr_node.add_child(
    GraphNode(
        "x_{i,k} = 0, \\forall (i,k) \\in P^{C}"
    )
)

compatibility_constraints_node.add_child(between_items_constr_node)
compatibility_constraints_node.add_child(between_items_containers_constr_node)

constraints_node.add_child(compatibility_constraints_node)

# Loading time constraints (optional)
loading_time_constraints_node = GraphNode("Loading time constraints (optional)")

total_loading_time_node = GraphNode("Total loading time per container bounded")
total_loading_time_node.add_child(
    GraphNode(
        "\\sum_{i \\in I} t_{i,k} x_{i,k} \\le T^{\\max}_k, \\forall k \\in K"
    )
)

loading_time_constraints_node.add_child(total_loading_time_node)

constraints_node.add_child(loading_time_constraints_node)

# Binary and integrality constraints (implicit)
integrality_constraints_node = GraphNode("Binary and integrality constraints (implicit)")
integrality_constraints_node.add_child(
    GraphNode("x_{i,k} \\in \\mathbb{Z}_+, z_{i,k} \\in \\{0,1\\}, y_k \\in \\{0,1\\}")
)

constraints_node.add_child(integrality_constraints_node)

# Linking constraints (implicit)
linking_constraints_node = GraphNode("Linking constraints (implicit)")

link_x_y_node = GraphNode("Linking x and y")
link_x_y_node.add_child(
    GraphNode("x_{i,k} \\le M y_k, \\forall i \\in I, \\forall k \\in K")
)

link_x_z_node = GraphNode("Linking x and z (if both used)")
link_x_z_node.add_child(
    GraphNode("z_{i,k} = 1 \\Rightarrow x_{i,k} \\ge 1, \\forall i \\in I, \\forall k \\in K")
)

linking_constraints_node.add_child(link_x_y_node)
linking_constraints_node.add_child(link_x_z_node)

constraints_node.add_child(linking_constraints_node)

packing_3d_node.add_child(constraints_node)

# Attach 3D Packing to MILP root
root_milp.add_child(packing_3d_node)

################################################################################
################################################################################
# Shift Scheduling (daily, period = time-slot)
################################################################################
################################################################################

shift_daily_node = GraphNode("Shift Scheduling (daily, period = time-slot)")

# Entities
entities_node = GraphNode("Entities")

# Planning horizon and periods
planning_horizon_node = GraphNode("Planning horizon")
planning_horizon_node.add_child(GraphNode("T_e^{(max)}"))

set_periods_node = GraphNode("Set of periods (with time increment)")
set_periods_node.add_child(
    GraphNode("T = {1, 2, ..., T_{(max)}} with L_size determined by modeller")
)

# Shifts and breaks
shifts_node = GraphNode("Shifts")

set_of_shifts_given_node = GraphNode("Set of shifts (given)")
set_of_shifts_given_node.add_child(GraphNode("S = {s}"))

set_of_shifts_hidden_node = GraphNode("Set of shifts (hidden)")
shifts_node.add_child(set_of_shifts_given_node)
shifts_node.add_child(set_of_shifts_hidden_node)

# Break types
break_types_node = GraphNode("Types of breaks (1st break, 2nd break, lunch, ...)")
break_types_node.add_child(GraphNode("G = {1, 2, ..., L}"))

break_shift_types_node = GraphNode("Set of break types mapped to shifts")
break_shift_types_node.add_child(
    GraphNode("B = \\cup_{g \\in G} B_g, \\; B_g \\text{ constructed based on requirements}")
)

# Shift timing info
start_time_shift_node = GraphNode("Start time of each shift")
start_time_shift_node.add_child(GraphNode("start_s \\; \\forall s \\in S"))

duration_shift_node = GraphNode("(Regular) duration of each shift")
duration_shift_node.add_child(GraphNode("duration_s \\; \\forall s \\in S"))

overtime_shift_node = GraphNode("Overtime of each shift (optional)")
overtime_shift_node.add_child(GraphNode("ot_s \\; \\forall s \\in S"))

shifts_node.add_child(break_types_node)
shifts_node.add_child(break_shift_types_node)
shifts_node.add_child(start_time_shift_node)
shifts_node.add_child(duration_shift_node)
shifts_node.add_child(overtime_shift_node)

entities_node.add_child(planning_horizon_node)
entities_node.add_child(set_periods_node)
entities_node.add_child(shifts_node)

shift_daily_node.add_child(entities_node)

# Parameters
parameters_node = GraphNode("Parameters")

# --- Breaks-related parameters ------------------------------------------------
breaks_param_node = GraphNode("Breaks")

eligibility_node = GraphNode("Eligibility of breaks")

min_dur_1_break_node = GraphNode("Minimum duration eligible for 1 break")
min_dur_1_break_node.add_child(GraphNode("\\ell_1"))

min_dur_2_break_node = GraphNode("Minimum duration eligible for 2 breaks")
min_dur_2_break_node.add_child(GraphNode("\\ell_2"))

min_dur_lunch_node = GraphNode("Minimum duration eligible for lunch break")
min_dur_lunch_node.add_child(GraphNode("\\ell_3"))

eligibility_node.add_child(min_dur_1_break_node)
eligibility_node.add_child(min_dur_2_break_node)
eligibility_node.add_child(min_dur_lunch_node)

# Duration of different breaks per shift
dur_breaks_node = GraphNode("Duration of different breaks for different shifts")
dur_breaks_node.add_child(
    GraphNode("d_{s,g} \\; \\forall s \\in S, \\forall g \\in G")
)

# Time windows of breaks
time_window_breaks_node = GraphNode("Time window of 1st, 2nd, lunch breaks")
time_window_breaks_node.add_child(
    GraphNode("earliest & latest time a break can start for each type g")
)
time_window_breaks_node.add_child(
    GraphNode("[e_{s,g}, l_{s,g}] \\; \\forall s \\in S, \\forall g \\in G")
)

start_break_node = GraphNode("Start time of each break (may be hidden)")
start_break_node.add_child(GraphNode("start_{s,g} \\in T"))

breaks_param_node.add_child(eligibility_node)
breaks_param_node.add_child(dur_breaks_node)
breaks_param_node.add_child(time_window_breaks_node)
breaks_param_node.add_child(start_break_node)

parameters_node.add_child(breaks_param_node)

# --- Demand parameters --------------------------------------------------------
demands_node = GraphNode("Demands")

min_emp_shift_ind_node = GraphNode("Minimum number of employees required per period (shift independent)")
min_emp_shift_ind_node.add_child(GraphNode("lb_t \\; \\forall t \\in T"))

min_emp_shift_dep_node = GraphNode("Minimum number of employees required per period (shift dependent)")
min_emp_shift_dep_node.add_child(GraphNode("lb_t(s) \\; \\forall t \\in T, \\forall s \\in S"))

exact_emp_shift_ind_node = GraphNode("Exact number of employees required per period (shift independent)")
exact_emp_shift_ind_node.add_child(GraphNode("exact_t \\; \\forall t \\in T"))

exact_emp_shift_dep_node = GraphNode("Exact number of employees required per period (shift dependent)")
exact_emp_shift_dep_node.add_child(GraphNode("exact_t(s) \\; \\forall t \\in T, \\forall s \\in S"))

max_emp_shift_ind_node = GraphNode("Maximum number of employees required per period (shift independent)")
max_emp_shift_ind_node.add_child(GraphNode("ub_t \\; \\forall t \\in T"))

max_emp_shift_dep_node = GraphNode("Maximum number of employees required per period (shift dependent)")
max_emp_shift_dep_node.add_child(GraphNode("ub_t(s) \\; \\forall t \\in T, \\forall s \\in S"))

demands_node.add_child(min_emp_shift_ind_node)
demands_node.add_child(min_emp_shift_dep_node)
demands_node.add_child(exact_emp_shift_ind_node)
demands_node.add_child(exact_emp_shift_dep_node)
demands_node.add_child(max_emp_shift_ind_node)
demands_node.add_child(max_emp_shift_dep_node)

parameters_node.add_child(demands_node)

# --- Cost parameters ----------------------------------------------------------
costs_node = GraphNode("Costs")

# Cost per shift
cost_per_shift_node = GraphNode("Cost per shift")

fixed_cost_shift_node = GraphNode("Fixed cost for each shift")
fixed_cost_shift_node.add_child(GraphNode("c^0_s \\; \\forall s \\in S"))

duration_dep_cost_shift_node = GraphNode("Duration dependent cost")
duration_dep_cost_shift_node.add_child(
    GraphNode("c^R, c^{OT} \\Rightarrow c_s = c^R \\cdot duration_s + c^{OT} \\cdot ot_s + c^0_s")
)

break_dep_cost_node = GraphNode("Break dependent cost (break time not paid)")
break_dep_cost_node.add_child(
    GraphNode("c_s = c^R * (duration_s - \\sum_{g \\in G} d_{s,g}) + c^{OT} * ot_s + c^0_s")
)

cost_per_shift_node.add_child(fixed_cost_shift_node)
cost_per_shift_node.add_child(duration_dep_cost_shift_node)
cost_per_shift_node.add_child(break_dep_cost_node)

# Cost per period
cost_per_period_node = GraphNode("Cost per period")
cost_per_period_node.add_child(GraphNode("Regular time: c^R"))
cost_per_period_node.add_child(GraphNode("Overtime: c^{OT}"))

# Limit on employees on break
max_on_break_node = GraphNode("Maximum number of employees on break per period")
max_on_break_node.add_child(GraphNode("h^B_t \\; \\forall t \\in T"))

costs_node.add_child(cost_per_shift_node)
costs_node.add_child(cost_per_period_node)
costs_node.add_child(max_on_break_node)

parameters_node.add_child(costs_node)

# --- Hidden coverage parameters ----------------------------------------------
coverage_param_node = GraphNode("Coverage indicator parameters (hidden)")

shift_covers_period_node = GraphNode("Binary parameter: shift s covers period t")
shift_covers_period_node.add_child(
    GraphNode(
        "a_s(t) = 1 \\text{ if } start_s \\le t < start_s + duration_s + ot_s; 0 \\text{ otherwise}"
    )
)

break_covers_period_node = GraphNode("Binary parameter: break g in shift s covers period t")
break_covers_period_node.add_child(
    GraphNode(
        "b_{g,s}(t) = 1 \\text{ if } start_{s,g} \\le t < start_{s,g} + d_{s,g}; 0 \\text{ otherwise}"
    )
)

coverage_param_node.add_child(shift_covers_period_node)
coverage_param_node.add_child(break_covers_period_node)

parameters_node.add_child(coverage_param_node)

shift_daily_node.add_child(parameters_node)

# Decision variables
decision_node = GraphNode("Decision variables")

num_staff_shift_node = GraphNode("Number of staff for each shift")
num_staff_shift_node.add_child(GraphNode("x_s \\; \\forall s \\in S"))

staff_on_break_node = GraphNode("Number of staff on break (type-dependent) for each shift and period")
staff_on_break_node.add_child(
    GraphNode("y_{g,s,t} \\; \\forall g \\in G, \\forall s \\in S, \\forall t \\in T")
)

decision_node.add_child(num_staff_shift_node)
decision_node.add_child(staff_on_break_node)

shift_daily_node.add_child(decision_node)

# Objectives
objectives_node = GraphNode("Objectives")

min_total_local_cost_node = GraphNode("Minimisation: minimising total local cost")
min_total_local_cost_node.add_child(
    GraphNode("v_{min}^{cost} = \\sum_{s \\in S} c_s x_s")
)

min_total_employees_node = GraphNode("Minimisation: minimising total number of employees")
min_total_employees_node.add_child(
    GraphNode("v_{min}^{staff} = \\sum_{s \\in S} x_s")
)

objectives_node.add_child(min_total_local_cost_node)
objectives_node.add_child(min_total_employees_node)

shift_daily_node.add_child(objectives_node)

# Constraints
constraints_node = GraphNode("Constraints")

# Minimum employees
min_emp_constraints_node = GraphNode("Minimum number of employees")

min_shift_ind_constr_node = GraphNode("Shift independent")
min_shift_ind_constr_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\ge lb_t, \\forall t \\in T")
)

min_shift_dep_constr_node = GraphNode("Shift dependent")
min_shift_dep_constr_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\ge lb_t(s), \\forall t \\in T, \\forall s \\in S")
)

min_emp_constraints_node.add_child(min_shift_ind_constr_node)
min_emp_constraints_node.add_child(min_shift_dep_constr_node)

constraints_node.add_child(min_emp_constraints_node)

# Demand satisfaction (exact)
exact_constraints_node = GraphNode("Demand satisfaction (exact number of employees)")

exact_shift_ind_constr_node = GraphNode("Shift independent")
exact_shift_ind_constr_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s = exact_t, \\forall t \\in T")
)

exact_shift_dep_constr_node = GraphNode("Shift dependent")
exact_shift_dep_constr_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s = exact_t(s), \\forall t \\in T, \\forall s \\in S")
)

exact_constraints_node.add_child(exact_shift_ind_constr_node)
exact_constraints_node.add_child(exact_shift_dep_constr_node)

constraints_node.add_child(exact_constraints_node)

# Maximum employees
max_emp_constraints_node = GraphNode("Maximum number of employees")

max_shift_ind_constr_node = GraphNode("Shift independent")
max_shift_ind_constr_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\le ub_t, \\forall t \\in T")
)

max_shift_dep_constr_node = GraphNode("Shift dependent")
max_shift_dep_constr_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\le ub_t(s), \\forall t \\in T, \\forall s \\in S")
)

max_emp_constraints_node.add_child(max_shift_ind_constr_node)
max_emp_constraints_node.add_child(max_shift_dep_constr_node)

constraints_node.add_child(max_emp_constraints_node)

# Limit on employees on break
limit_break_constr_node = GraphNode("Limit on employees on break")
limit_break_constr_node.add_child(
    GraphNode(
        "\\sum_{g \\in G} \\sum_{s \\in S} b_{g,s}(t) y_{g,s,t} \\le h^B_t, \\forall t \\in T"
    )
)

constraints_node.add_child(limit_break_constr_node)

# Integrality constraints (hidden)
integrality_node = GraphNode("Integrality constraints (hidden)")
integrality_node.add_child(
    GraphNode("x_s \\in \\mathbb{Z}_+, y_{g,s,t} \\in \\mathbb{Z}_+, \\forall g,s,t")
)

constraints_node.add_child(integrality_node)

shift_daily_node.add_child(constraints_node)

# Attach to MILP root
root_milp.add_child(shift_daily_node)

################################################################################
################################################################################
# Shift Scheduling (days-off, period = day)
################################################################################
################################################################################

shift_daysoff_node = GraphNode("Shift Scheduling (days-off, period = day)")

# Entities
entities_node_2 = GraphNode("Entities")

planning_horizon_2_node = GraphNode("Planning horizon")
planning_horizon_2_node.add_child(GraphNode("T_e^{(max)}"))

set_days_node = GraphNode("Set of days")
set_days_node.add_child(GraphNode("T = {1, 2, ..., T_{(max)}}"))

# Shift types
shift_types_node = GraphNode("Set of shift types (full/part-time)")
shift_types_node.add_child(GraphNode("G = {g}"))

# Shifts
shifts_2_node = GraphNode("Shifts")
set_shifts_2_node = GraphNode("Set of shifts")
set_shifts_2_node.add_child(GraphNode("S = S_g^0 \\; \\forall g \\in G"))
set_shifts_hidden_2_node = GraphNode("Set of shifts (hidden)")

start_shift_2_node = GraphNode("Start time of each shift")
start_shift_2_node.add_child(GraphNode("start_s \\; \\forall s \\in S"))

duration_shift_2_node = GraphNode("(Regular) duration of each shift")
duration_shift_2_node.add_child(GraphNode("duration_s \\; \\forall s \\in S"))

overtime_shift_2_node = GraphNode("Overtime of each shift (optional)")
overtime_shift_2_node.add_child(GraphNode("ot_s \\; \\forall s \\in S"))

shifts_2_node.add_child(set_shifts_2_node)
shifts_2_node.add_child(set_shifts_hidden_2_node)
shifts_2_node.add_child(start_shift_2_node)
shifts_2_node.add_child(duration_shift_2_node)
shifts_2_node.add_child(overtime_shift_2_node)

entities_node_2.add_child(planning_horizon_2_node)
entities_node_2.add_child(set_days_node)
entities_node_2.add_child(shift_types_node)
entities_node_2.add_child(shifts_2_node)

shift_daysoff_node.add_child(entities_node_2)

# Parameters
parameters_2_node = GraphNode("Parameters")

# Demands (per day)
demands_2_node = GraphNode("Demands")

min_emp_day_shift_ind_node = GraphNode("Minimum number of employees required per day (shift independent)")
min_emp_day_shift_ind_node.add_child(GraphNode("lb_t \\; \\forall t \\in T"))

min_emp_day_shift_dep_node = GraphNode("Minimum number of employees required per day (shift dependent)")
min_emp_day_shift_dep_node.add_child(GraphNode("lb_t(s) \\; \\forall t \\in T, \\forall s \\in S"))

exact_emp_day_shift_ind_node = GraphNode("Exact number of employees required per day (shift independent)")
exact_emp_day_shift_ind_node.add_child(GraphNode("exact_t \\; \\forall t \\in T"))

exact_emp_day_shift_dep_node = GraphNode("Exact number of employees required per day (shift dependent)")
exact_emp_day_shift_dep_node.add_child(GraphNode("exact_t(s) \\; \\forall t \\in T, \\forall s \\in S"))

max_emp_day_shift_ind_node = GraphNode("Maximum number of employees required per day (shift independent)")
max_emp_day_shift_ind_node.add_child(GraphNode("ub_t \\; \\forall t \\in T"))

max_emp_day_shift_dep_node = GraphNode("Maximum number of employees required per day (shift dependent)")
max_emp_day_shift_dep_node.add_child(GraphNode("ub_t(s) \\; \\forall t \\in T, \\forall s \\in S"))

demands_2_node.add_child(min_emp_day_shift_ind_node)
demands_2_node.add_child(min_emp_day_shift_dep_node)
demands_2_node.add_child(exact_emp_day_shift_ind_node)
demands_2_node.add_child(exact_emp_day_shift_dep_node)
demands_2_node.add_child(max_emp_day_shift_ind_node)
demands_2_node.add_child(max_emp_day_shift_dep_node)

parameters_2_node.add_child(demands_2_node)

# Workload
workload_node = GraphNode("Work load")
workload_node.add_child(GraphNode("L_g \\; \\forall g \\in G (fixed for each shift type)"))
parameters_2_node.add_child(workload_node)

# Costs
costs_2_node = GraphNode("Costs")

cost_per_shift_2_node = GraphNode("Cost per shift")

fixed_cost_shift_2_node = GraphNode("Fixed for each shift (given)")
fixed_cost_shift_2_node.add_child(GraphNode("c_s \\; \\forall s \\in S"))

workload_based_cost_node = GraphNode("Fixed for each shift by workload")
workload_based_cost_node.add_child(
    GraphNode("c_s = L_g * c \\; \\forall s \\in S, \\; c \\text{ is full-load shift cost}")
)

cost_per_shift_2_node.add_child(fixed_cost_shift_2_node)
cost_per_shift_2_node.add_child(workload_based_cost_node)

cost_per_period_2_node = GraphNode("Cost per period")
cost_per_period_2_node.add_child(GraphNode("Regular time: c^R"))
cost_per_period_2_node.add_child(GraphNode("Overtime: c^{OT}"))

costs_2_node.add_child(cost_per_shift_2_node)
costs_2_node.add_child(cost_per_period_2_node)

parameters_2_node.add_child(costs_2_node)

# Hidden coverage parameter a_s(t)
coverage_param_2_node = GraphNode("Coverage indicator (hidden)")
coverage_param_2_node.add_child(
    GraphNode(
        "a_s(t) = 1 \\text{ if } start_s \\le t < start_s + duration_s + ot_s; 0 \\text{ otherwise}"
    )
)

parameters_2_node.add_child(coverage_param_2_node)

shift_daysoff_node.add_child(parameters_2_node)

# Decision variables
decision_2_node = GraphNode("Decision variables")

num_staff_shift_2_node = GraphNode("Number of staff for each shift")
num_staff_shift_2_node.add_child(GraphNode("x_s \\; \\forall s \\in S"))

decision_2_node.add_child(num_staff_shift_2_node)

shift_daysoff_node.add_child(decision_2_node)

# Objectives
objectives_2_node = GraphNode("Objectives")

min_num_employees_node = GraphNode("Minimisation: total number of employees")
min_num_employees_node.add_child(
    GraphNode("v_{min}^{staff} = \\sum_{s \\in S} x_s")
)

min_total_cost_2_node = GraphNode("Minimisation: total local cost")
min_total_cost_2_node.add_child(
    GraphNode("v_{min}^{cost} = \\sum_{s \\in S} c_s x_s")
)

max_weekends_off_node = GraphNode("Maximisation: maximum number of weekends off (assuming t=1 is Monday)")
max_weekends_off_node.add_child(
    GraphNode("v_{max}^{weekend} = \\text{maximise number of weekends off}")
)

objectives_2_node.add_child(min_num_employees_node)
objectives_2_node.add_child(min_total_cost_2_node)
objectives_2_node.add_child(max_weekends_off_node)

shift_daysoff_node.add_child(objectives_2_node)

# Constraints
constraints_2_node = GraphNode("Constraints")

# Minimum employees
min_emp_2_node = GraphNode("Minimum number of employees")

min_emp_2_shift_ind_node = GraphNode("Shift independent")
min_emp_2_shift_ind_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\ge lb_t, \\forall t \\in T")
)

min_emp_2_shift_dep_node = GraphNode("Shift dependent")
min_emp_2_shift_dep_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\ge lb_t(s), \\forall t \\in T, \\forall s \\in S")
)

min_emp_2_node.add_child(min_emp_2_shift_ind_node)
min_emp_2_node.add_child(min_emp_2_shift_dep_node)

constraints_2_node.add_child(min_emp_2_node)

# Exact demand
exact_2_node = GraphNode("Demand satisfaction (exact number of employees)")

exact_2_shift_ind_node = GraphNode("Shift independent")
exact_2_shift_ind_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s = exact_t, \\forall t \\in T")
)

exact_2_shift_dep_node = GraphNode("Shift dependent")
exact_2_shift_dep_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s = exact_t(s), \\forall t \\in T, \\forall s \\in S")
)

exact_2_node.add_child(exact_2_shift_ind_node)
exact_2_node.add_child(exact_2_shift_dep_node)

constraints_2_node.add_child(exact_2_node)

# Maximum employees
max_emp_2_node = GraphNode("Maximum number of employees")

max_emp_2_shift_ind_node = GraphNode("Shift independent")
max_emp_2_shift_ind_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\le ub_t, \\forall t \\in T")
)

max_emp_2_shift_dep_node = GraphNode("Shift dependent")
max_emp_2_shift_dep_node.add_child(
    GraphNode("\\sum_{s \\in S} a_s(t) x_s \\le ub_t(s), \\forall t \\in T, \\forall s \\in S")
)

max_emp_2_node.add_child(max_emp_2_shift_ind_node)
max_emp_2_node.add_child(max_emp_2_shift_dep_node)

constraints_2_node.add_child(max_emp_2_node)

# Integrality
integrality_2_node = GraphNode("Integrality constraints (hidden)")
integrality_2_node.add_child(GraphNode("x_s \\in \\mathbb{Z}_+, \\forall s \\in S"))

constraints_2_node.add_child(integrality_2_node)

shift_daysoff_node.add_child(constraints_2_node)

# Attach days-off model to MILP root
root_milp.add_child(shift_daysoff_node)
