import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
import numpy as np
import os
from Config import (
    DEFAULT_PROBABILITY_THRESHOLD, PROBABLE_INFECTION_PATH_FILE,
    DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y
)


class Visualizer:
    def __init__(self, terrain_map, simulation_results):
        self.terrain_map = terrain_map
        self.simulation_results = simulation_results
        self.graph = terrain_map.graph
        self.node_colors = terrain_map.node_colors

        self.SUSCEPTIBLE = 0
        self.INFECTED = 1
        self.RECOVERED = 2

    def calculate_probability_matrix(self):

        n_simulations = len(self.simulation_results)
        max_steps = max(len(history) for history in self.simulation_results)

        all_nodes = list(self.graph.nodes())
        n_nodes = len(all_nodes)
        node_to_idx = {node: i for i, node in enumerate(all_nodes)}

        indexed_results = []
        for sim_history in self.simulation_results:
            indexed_results.append([
                {node_to_idx[node]: state for node,
                    state in state_dict.items()}
                for state_dict in sim_history
            ])

        infected_matrix = np.zeros((max_steps, n_nodes), dtype=np.uint16)
        recovered_matrix = np.zeros((max_steps, n_nodes), dtype=np.uint16)

        for sim_history in indexed_results:
            for t, state_dict in enumerate(sim_history):
                for idx, state in state_dict.items():
                    if state == self.INFECTED:
                        infected_matrix[t, idx] += 1
                    elif state == self.RECOVERED:
                        recovered_matrix[t, idx] += 1

        infected_prob = infected_matrix.astype(np.float32) / n_simulations
        recovered_prob = recovered_matrix.astype(np.float32) / n_simulations

        self.infected_prob = infected_prob
        self.recovered_prob = recovered_prob
        self.all_nodes = all_nodes
        self.node_to_idx = node_to_idx

        return infected_prob, recovered_prob

    def _calculate_ever_infected(self, threshold, max_step):
        n_nodes = self.infected_prob.shape[1]
        combined_prob = self.infected_prob[:max_step +
                                           1] + self.recovered_prob[:max_step+1]
        ever_infected = np.any(combined_prob >= threshold, axis=0)

        return ever_infected

    def _get_node_colors_for_step(self, step, threshold, ever_infected):
        r_prob = self.recovered_prob[step]
        i_prob = self.infected_prob[step]

        node_colors = []

        for node in self.graph.nodes():
            node_idx = self.node_to_idx[node]

            # Verificar se o nó foi infectado com probabilidade >= threshold
            if ever_infected[node_idx]:
                # Se recuperado com probabilidade >= threshold
                if r_prob[node_idx] >= threshold:
                    node_colors.append('gray')
                # Se infectado (I ou I+R >= threshold, mas R < threshold)
                elif (i_prob[node_idx] + r_prob[node_idx]) >= threshold:
                    node_colors.append('black')
                else:
                    node_colors.append(self.node_colors[node])
            else:
                node_colors.append(self.node_colors[node])

        return node_colors

    def _create_legend_elements(self, threshold):
        return [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black',
                       markersize=10, label=f'Infectado (I+R >={threshold*100:.0f}%)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
                       markersize=10, label=f'Recuperado (R >={threshold*100:.0f}%)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                       markersize=10, label='Rios/Barreiras'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange',
                       markersize=10, label='Florestas Úmidas'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue',
                       markersize=10, label='Florestas de Transição'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
                       markersize=10, label='Vegetação Seca')
        ]

    def create_probability_animation(self, threshold=DEFAULT_PROBABILITY_THRESHOLD,
                                     save_file=PROBABLE_INFECTION_PATH_FILE,
                                     frame_step=1, use_mp4=False):
        if not hasattr(self, 'infected_prob'):
            self.calculate_probability_matrix()

        plt.ioff()

        fig, ax = plt.subplots(
            figsize=(DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y))
        pos = {node: node for node in self.graph.nodes()}
        max_steps = self.infected_prob.shape[0]

        node_list = list(self.graph.nodes())
        initial_colors = [self.node_colors[node] for node in node_list]

        nodes_artist = nx.draw_networkx_nodes(
            self.graph, pos, node_color=initial_colors, ax=ax, node_size=20
        )
        nx.draw_networkx_edges(self.graph, pos, alpha=0.1, ax=ax)

        legend = ax.legend(handles=self._create_legend_elements(threshold),
                           loc='center left', bbox_to_anchor=(1.0, 0.5))
        ax.set_aspect('equal')
        ax.axis('off')
        title = ax.set_title('')

        def update(frame):
            ever_infected = self._calculate_ever_infected(threshold, frame)
            node_colors_frame = self._get_node_colors_for_step(
                frame, threshold, ever_infected
            )

            nodes_artist.set_color(node_colors_frame)
            title.set_text(
                f'Provável Caminho de Infecção (Passo {frame}/{max_steps-1})\n'
                f'Baseado em {len(self.simulation_results)} simulações, '
                f'limiar de probabilidade: {threshold*100:.0f}%'
            )
            return nodes_artist, title

        frames = range(0, max_steps, frame_step)
        ani = animation.FuncAnimation(
            fig, update, frames=frames, blit=True, repeat=False, interval=100
        )

        if save_file:
            if use_mp4 or save_file.endswith('.mp4'):
                try:
                    from matplotlib.animation import FFMpegWriter
                    writer = FFMpegWriter(fps=10, codec='libx264')
                    output_file = save_file.replace('.gif', '.mp4')
                    ani.save(output_file, writer=writer)
                    print(
                        f"Animação salva como MP4 em '{os.path.abspath(output_file)}'")
                except Exception as e:
                    print(f"Erro ao salvar MP4: {e}. Tentando GIF...")
                    writer = animation.PillowWriter(fps=10)
                    ani.save(save_file, writer=writer)
                    print(
                        f"Animação salva como GIF em '{os.path.abspath(save_file)}'")
            else:
                writer = animation.FFMpegWriter(fps=10)
                ani.save(save_file, writer=writer)
                print(f"Animação salva em '{os.path.abspath(save_file)}'")

        plt.tight_layout()

        plt.close(fig)
        return ani

    def save_probability_map(self, step, threshold=DEFAULT_PROBABILITY_THRESHOLD, filename=None):
        if not hasattr(self, 'infected_prob'):
            self.calculate_probability_matrix()

        plt.figure(figsize=(DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y))
        pos = {node: node for node in self.graph.nodes()}

        ever_infected = self._calculate_ever_infected(threshold, step)
        node_colors_frame = self._get_node_colors_for_step(
            step, threshold, ever_infected)

        nx.draw_networkx_nodes(
            self.graph, pos, node_color=node_colors_frame, node_size=40
        )
        nx.draw_networkx_edges(self.graph, pos, alpha=0.1)

        plt.title(f'Provável Estado da Infecção (Passo {step})\n'
                  f'Baseado em {len(self.simulation_results)} simulações')

        plt.legend(handles=self._create_legend_elements(threshold),
                   loc='center left', bbox_to_anchor=(1.0, 0.5))
        plt.axis('off')
        plt.tight_layout()

        if filename:
            plt.savefig(filename)
            print(
                f"Mapa de probabilidade salvo em '{os.path.abspath(filename)}'")

        plt.show()
