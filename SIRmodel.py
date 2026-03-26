import random
import numpy as np
from Config import DEFAULT_BETA, DEFAULT_GAMMA, DEFAULT_SIMULATION_STEPS


class SIRmodel:

    SUSCEPTIBLE = 0
    INFECTED = 1
    RECOVERED = 2

    def __init__(self, terrain_map, beta=DEFAULT_BETA, gamma=DEFAULT_GAMMA,
                 track_changes=False):

        self.terrain_map = terrain_map
        self.beta = beta
        self.gamma = gamma
        self.track_changes = track_changes

        self.all_nodes = list(terrain_map.graph.nodes())
        self.n_nodes = len(self.all_nodes)
        self.node_to_idx = {node: i for i, node in enumerate(self.all_nodes)}
        self.idx_to_node = {i: node for node, i in self.node_to_idx.items()}

        self.states_array = np.zeros(self.n_nodes, dtype=np.uint8)

        self.history_counts = []

        if self.track_changes:
            self.state_changes = []

        self._initialize_caches()

    def _initialize_caches(self):
        graph = self.terrain_map.graph

        self.neighbors_dict = {
            node: set(graph.neighbors(node))
            for node in self.all_nodes
        }

        self.susceptibility_array = np.array([
            self.terrain_map.susceptibility[self.terrain_map.node_colors[node]]
            for node in self.all_nodes
        ], dtype=np.float32)

    def initialize_states(self, initial_infected_count=10,
                          infection_strategy="random", manual_nodes=None):

        self.states_array[:] = self.SUSCEPTIBLE

        if infection_strategy == "manual":
            if manual_nodes is None or len(manual_nodes) == 0:
                raise ValueError(
                    "É necessário fornecer uma lista de nós para infecção manual.")
            initial_infected = manual_nodes
        else:
            initial_infected = random.sample(
                self.all_nodes, initial_infected_count)

        for node in initial_infected:
            idx = self.node_to_idx[node]
            self.states_array[idx] = self.INFECTED

        initial_counts = self._count_states()
        self.history_counts = [initial_counts]

        if self.track_changes:
            self.state_changes = []
            for node in initial_infected:
                self.state_changes.append(
                    (0, self.node_to_idx[node], self.INFECTED))

        print(f"Nós infectados inicialmente: {initial_infected[:5]}..."
              if len(initial_infected) > 5 else f"Nós infectados inicialmente: {initial_infected}")

        return self.states_array

    def _count_states(self):

        counts = np.bincount(self.states_array, minlength=3)
        return (int(counts[0]), int(counts[1]), int(counts[2]))

    def run_simulation(self, steps=DEFAULT_SIMULATION_STEPS):

        neighbors_dict = self.neighbors_dict
        susceptibility_array = self.susceptibility_array

        susceptible_nodes = set(
            self.all_nodes[i] for i in range(self.n_nodes)
            if self.states_array[i] == self.SUSCEPTIBLE
        )
        infected_nodes = set(
            self.all_nodes[i] for i in range(self.n_nodes)
            if self.states_array[i] == self.INFECTED
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

                node_idx = self.node_to_idx[node]
                effective_beta = self.beta * susceptibility_array[node_idx]

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
                idx = self.node_to_idx[node]
                self.states_array[idx] = self.INFECTED
            for node in new_recovered:
                idx = self.node_to_idx[node]
                self.states_array[idx] = self.RECOVERED

            current_counts = (
                len(susceptible_nodes),
                len(infected_nodes),
                self.n_nodes - len(susceptible_nodes) - len(infected_nodes)
            )
            self.history_counts.append(current_counts)

            if self.track_changes:
                for node in new_infected:
                    self.state_changes.append(
                        (step + 1, self.node_to_idx[node], self.INFECTED))
                for node in new_recovered:
                    self.state_changes.append(
                        (step + 1, self.node_to_idx[node], self.RECOVERED))

            if not infected_nodes:
                final_counts = (len(susceptible_nodes), 0,
                                self.n_nodes - len(susceptible_nodes))
                for _ in range(step + 1, steps):
                    self.history_counts.append(final_counts)

                print(
                    f"Simulação encerrada no passo {step+1}/{steps} (sem infectados)")
                break

        final_s, final_i, final_r = self.history_counts[-1]
        print(f"Simulação completa. Nós finais: "
              f"{final_s} suscetíveis, {final_i} infectados, {final_r} recuperados")

        return self.history_counts

    def get_state_counts(self):
        return self.history_counts

    def reconstruct_history(self):
        if not self.track_changes:
            raise ValueError(
                "track_changes deve ser True para reconstruir histórico")

        n_steps = len(self.history_counts)
        history = []

        current_state = np.zeros(self.n_nodes, dtype=np.uint8)

        change_idx = 0
        for step in range(n_steps):

            while (change_idx < len(self.state_changes) and
                   self.state_changes[change_idx][0] == step):
                _, node_idx, new_state = self.state_changes[change_idx]
                current_state[node_idx] = new_state
                change_idx += 1

            state_dict = {
                self.idx_to_node[i]: int(current_state[i])
                for i in range(self.n_nodes)
            }
            history.append(state_dict)

        return history

    def get_current_state_dict(self):
        return {
            self.idx_to_node[i]: int(self.states_array[i])
            for i in range(self.n_nodes)
        }
