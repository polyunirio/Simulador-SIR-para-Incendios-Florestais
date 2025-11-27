import random
from Config import DEFAULT_BETA, DEFAULT_GAMMA, DEFAULT_SIMULATION_STEPS


class SIRmodel:

    SUSCEPTIBLE = 0
    INFECTED = 1
    RECOVERED = 2

    def __init__(self, terrain_map, beta=DEFAULT_BETA, gamma=DEFAULT_GAMMA):
        self.terrain_map = terrain_map
        self.beta = beta
        self.gamma = gamma
        self.states = {}
        self.history = []

        self._initialize_caches()

    def _initialize_caches(self):
        graph = self.terrain_map.graph

        self.all_nodes = list(graph.nodes())

        self.neighbors_dict = {
            node: set(graph.neighbors(node))
            for node in self.all_nodes
        }

        self.susceptibility_cache = {
            node: self.terrain_map.susceptibility[self.terrain_map.node_colors[node]]
            for node in self.all_nodes
        }

    def initialize_states(self, initial_infected_count=10, infection_strategy="random", manual_nodes=None):
        graph = self.terrain_map.graph

        self.states = {node: self.SUSCEPTIBLE for node in graph.nodes()}

        if infection_strategy == "manual":
            if manual_nodes is None or len(manual_nodes) == 0:
                raise ValueError(
                    "É necessário fornecer uma lista de nós para infecção manual.")
            initial_infected = manual_nodes
        else:
            initial_infected = random.sample(
                list(graph.nodes()), initial_infected_count)

        for node in initial_infected:
            self.states[node] = self.INFECTED

        self.history = [self.states.copy()]

        infected_nodes = [node for node,
                          state in self.states.items() if state == self.INFECTED]
        print("Nós infectados inicialmente:", infected_nodes)

        return self.states

    def run_simulation(self, steps=DEFAULT_SIMULATION_STEPS):

        neighbors_dict = self.neighbors_dict
        susceptibility_cache = self.susceptibility_cache

        susceptible_nodes = set(
            node for node in self.all_nodes
            if self.states[node] == self.SUSCEPTIBLE
        )
        infected_nodes = set(
            node for node in self.all_nodes
            if self.states[node] == self.INFECTED
        )

        for step in range(steps):
            new_infected = set()
            new_recovered = set()

            susceptible_at_risk = set()
            for infected_node in infected_nodes:
                susceptible_at_risk.update(
                    neighbors_dict[infected_node] & susceptible_nodes
                )

            for node in susceptible_at_risk:

                infected_neighbors_count = len(
                    neighbors_dict[node] & infected_nodes
                )

                effective_beta = self.beta * susceptibility_cache[node]

                prob_not_infected = (
                    1 - effective_beta) ** infected_neighbors_count

                infection_prob = 1 - prob_not_infected

                if random.random() < infection_prob:
                    new_infected.add(node)

            for node in infected_nodes:
                if random.random() < self.gamma:
                    new_recovered.add(node)

            susceptible_nodes -= new_infected
            infected_nodes |= new_infected
            infected_nodes -= new_recovered

            for node in new_infected:
                self.states[node] = self.INFECTED
            for node in new_recovered:
                self.states[node] = self.RECOVERED

            self.history.append(self.states.copy())

            if not infected_nodes:
                final_state = self.states.copy()
                for _ in range(step + 1, steps):
                    self.history.append(final_state.copy())
                print(
                    f"Simulação encerrada no passo {step+1}/{steps} (sem infectados)")
                break

        print(f"Simulação completa. Nós finais: "
              f"{len(susceptible_nodes)} suscetíveis, "
              f"0 infectados, "
              f"{len(self.all_nodes) - len(susceptible_nodes)} recuperados")

        return self.history

    def get_state_counts(self):
        counts = []
        for state in self.history:
            s_count = sum(1 for s in state.values() if s == self.SUSCEPTIBLE)
            i_count = sum(1 for s in state.values() if s == self.INFECTED)
            r_count = sum(1 for s in state.values() if s == self.RECOVERED)
            counts.append((s_count, i_count, r_count))

        return counts
