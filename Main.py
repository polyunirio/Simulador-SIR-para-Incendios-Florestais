from Simulation import SimulationApp
from Mapa import Mapa
from Visualizer import Visualizer
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import random
import networkx as nx
from Config import (
    GRID_SIZE_X, GRID_SIZE_Y, DEFAULT_NUM_SIMULATIONS, DEFAULT_INITIAL_INFECTED,
    DEFAULT_SIMULATION_STEPS, DEFAULT_PROBABILITY_THRESHOLD,
    MULTIPLE_SIMULATIONS_FILE, INITIAL_INFECTED_NODES_FILE,
    SIMULATION_RESULTS_CSV, DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y
)


class SimulationRunner:
    def __init__(self, num_simulations=DEFAULT_NUM_SIMULATIONS, grid_size_x=GRID_SIZE_X, grid_size_y=GRID_SIZE_Y, existing_map=None):
        self.num_simulations = num_simulations
        self.results = []
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.shared_map = existing_map if existing_map else Mapa(
            self.grid_size_x, self.grid_size_y)
        print("Mapa de terreno " + ("existente será usado" if existing_map else "criado") +
              " e será reutilizado em todas as simulações")
        self.initial_infected_nodes = None
        self.simulation_histories = []

    def select_initial_infected(self, initial_infected_count=DEFAULT_INITIAL_INFECTED):
        all_nodes = list(self.shared_map.graph.nodes())
        self.initial_infected_nodes = random.sample(
            all_nodes, initial_infected_count)
        print("Nós selecionados para infecção inicial:")
        print(self.initial_infected_nodes)
        return self.initial_infected_nodes

    def run_simulations(self, initial_infected=DEFAULT_INITIAL_INFECTED, simulation_steps=DEFAULT_SIMULATION_STEPS):
        import time

        start_time = time.time()

        print(
            f"Iniciando {self.num_simulations} simulações com os mesmos parâmetros")
        self.results = []
        self.simulation_histories = []

        if self.initial_infected_nodes is None:
            self.select_initial_infected(initial_infected)

        print(
            f"Configuração: {initial_infected} infectados iniciais, {simulation_steps} passos")
        print(
            f"Usando sempre os mesmos {len(self.initial_infected_nodes)} nós infectados inicialmente")

        for i in range(self.num_simulations):
            sim_start_time = time.time()
            print(f"\nExecutando simulação {i+1}/{self.num_simulations}")

            app = SimulationApp(self.grid_size_x, self.grid_size_y)
            app.terrain_map = self.shared_map
            app.sir_model = app.sir_model.__class__(self.shared_map)

            app.sir_model.initialize_states(initial_infected, infection_strategy="manual",
                                            manual_nodes=self.initial_infected_nodes)
            app.sir_model.run_simulation(simulation_steps)

            counts = app.sir_model.get_state_counts()
            self.results.append(counts)
            self.simulation_histories.append(app.sir_model.history)

            sim_end_time = time.time()
            sim_duration = sim_end_time - sim_start_time

            final_susceptible = counts[-1][0]
            final_infected = counts[-1][1]
            final_recovered = counts[-1][2]
            print(f"Simulação {i+1} concluída em {sim_duration:.2f} segundos. Resultado: {final_susceptible} suscetíveis, "
                  f"{final_infected} infectados, {final_recovered} recuperados")

        end_time = time.time()
        total_duration = end_time - start_time
        print(f"\nTempo total de execução: {total_duration:.2f} segundos "
              f"({total_duration/60:.2f} minutos)")

        print("\nGerando visualizações...")

        t = time.perf_counter()
        self.visualize_simulation_results()
        print(
            f"✓ Gráfico de resultados criado ({time.perf_counter() - t:.2f}s)")

        t = time.perf_counter()
        self.save_results_to_csv()
        print(f"✓ CSV salvo ({time.perf_counter() - t:.2f}s)")

        t = time.perf_counter()
        self.visualize_probability_map()
        print(f"✓ Mapas criados ({time.perf_counter() - t:.2f}s)")

        return self.results

    def visualize_simulation_results(self):
        import scipy.stats as stats
        plt.figure(figsize=(DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y))

        time_steps = len(self.results[0])

        results_array = np.array(self.results)
        susceptible_values = results_array[:, :, 0]
        infected_values = results_array[:, :, 1]
        recovered_values = results_array[:, :, 2]

        susceptible_means = np.mean(susceptible_values, axis=0)
        infected_means = np.mean(infected_values, axis=0)
        recovered_means = np.mean(recovered_values, axis=0)

        susceptible_stds = np.std(susceptible_values, axis=0)
        infected_stds = np.std(infected_values, axis=0)
        recovered_stds = np.std(recovered_values, axis=0)

        if len(self.results) > 1:
            susceptible_sem = stats.sem(susceptible_values, axis=0)
            infected_sem = stats.sem(infected_values, axis=0)
            recovered_sem = stats.sem(recovered_values, axis=0)

            s_ci_lower = susceptible_means - 1.96 * susceptible_sem
            s_ci_upper = susceptible_means + 1.96 * susceptible_sem
            i_ci_lower = infected_means - 1.96 * infected_sem
            i_ci_upper = infected_means + 1.96 * infected_sem
            r_ci_lower = recovered_means - 1.96 * recovered_sem
            r_ci_upper = recovered_means + 1.96 * recovered_sem
        else:
            s_ci_lower = s_ci_upper = susceptible_means
            i_ci_lower = i_ci_upper = infected_means
            r_ci_lower = r_ci_upper = recovered_means

        time_range = np.arange(time_steps)

        plt.rcParams.update({
            'font.size': 15,
            'axes.titlesize': 14,
            'axes.labelsize': 14,
            'legend.fontsize': 13,
            'xtick.labelsize': 13,
            'ytick.labelsize': 13
        })

        plt.plot(time_range, susceptible_means,
                 'g-', label='Suscetíveis (média)')
        plt.fill_between(time_range,
                         np.maximum(0, s_ci_lower),
                         np.minimum(len(self.shared_map.graph), s_ci_upper),
                         color='g', alpha=0.3, label='IC 95% Suscetíveis')

        plt.plot(time_range, infected_means,
                 color='black', label='Infectados (média)')
        plt.fill_between(time_range,
                         np.maximum(0, i_ci_lower),
                         np.minimum(len(self.shared_map.graph), i_ci_upper),
                         color='yellow', alpha=0.3, label='IC 95% Infectados')

        plt.plot(time_range, recovered_means, color='red',
                 linestyle='-', label='Recuperados (média)')
        plt.fill_between(time_range,
                         np.maximum(0, r_ci_lower),
                         np.minimum(len(self.shared_map.graph), r_ci_upper),
                         color='red', alpha=0.3, label='IC 95% Recuperados')

        plt.title(
            f'Resultados de {self.num_simulations} Simulações (Média com IC 95%)')
        plt.xlabel('Passos de Tempo')
        plt.ylabel('Número de Indivíduos')
        plt.legend()
        plt.grid(True)
        plt.xlim(0, 200)
        plt.tight_layout()
        plt.savefig(MULTIPLE_SIMULATIONS_FILE)
        print(
            f"Gráfico de resultados múltiplos salvo em '{os.path.abspath(MULTIPLE_SIMULATIONS_FILE)}'")
        plt.show()

        self.visualize_initial_infected()

    def visualize_initial_infected(self):
        plt.figure(figsize=(DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y))

        pos = {node: node for node in self.shared_map.graph.nodes()}
        node_colors = []
        node_sizes = []

        for node in self.shared_map.graph.nodes():
            if node in self.initial_infected_nodes:
                node_colors.append('black')
                node_sizes.append(20)
            else:
                node_colors.append(self.shared_map.node_colors[node])
                node_sizes.append(10)

        nx.draw_networkx_nodes(
            self.shared_map.graph,
            pos,
            node_color=node_colors,
            node_size=node_sizes
        )
        nx.draw_networkx_edges(self.shared_map.graph, pos, alpha=0.1)

        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black',
                       markersize=10, label='Infectados Iniciais'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                       markersize=10, label='Rios/Barreiras'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange',
                       markersize=10, label='Florestas Úmidas'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue',
                       markersize=10, label='Florestas de Transição'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
                       markersize=10, label='Vegetação Seca')
        ]
        plt.legend(handles=legend_elements, loc='center left',
                   bbox_to_anchor=(1.0, 0.5))

        plt.title('Mapa com Nós Inicialmente Infectados')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(INITIAL_INFECTED_NODES_FILE)
        print(
            f"Mapa de nós infectados inicialmente salvo em '{os.path.abspath(INITIAL_INFECTED_NODES_FILE)}'")
        plt.show()

    def save_results_to_csv(self):
        data = []

        for sim_idx, sim_result in enumerate(self.results):
            for step_idx, (s, i, r) in enumerate(sim_result):
                data.append({
                    'simulation': sim_idx + 1,
                    'step': step_idx,
                    'susceptible': s,
                    'infected': i,
                    'recovered': r,
                    'total': s + i + r
                })

        df = pd.DataFrame(data)
        df.to_csv(SIMULATION_RESULTS_CSV, index=False)
        print(
            f"Resultados salvos em '{os.path.abspath(SIMULATION_RESULTS_CSV)}'")

        return df

    def visualize_probability_map(self):
        print("\nCriando mapas de probabilidade da infecção...")

        prob_visualizer = Visualizer(
            self.shared_map, self.simulation_histories)

        prob_visualizer.calculate_probability_matrix()

        print("\nCriando animação do caminho provável da infecção...")
        ani = prob_visualizer.create_probability_animation(
            threshold=DEFAULT_PROBABILITY_THRESHOLD,
            frame_step=2
        )

        return ani


def main():
    mapa = Mapa()

    print("Iniciando runner de simulações múltiplas...")

    runner = SimulationRunner()
    runner.run_simulations()

    print("\nProcesso de simulações múltiplas concluído!")

    plt.show()


if __name__ == "__main__":
    main()
