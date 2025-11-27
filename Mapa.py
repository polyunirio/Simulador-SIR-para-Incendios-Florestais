import networkx as nx
import matplotlib.pyplot as plt
import random
import os
import csv
from matplotlib.lines import Line2D
from Config import GRID_SIZE_X, GRID_SIZE_Y, TERRAIN_SUSCEPTIBILITY, TERRAIN_MAP_FILE, DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y


class Mapa:
    """Classe do mapa de terreno e respectivas propriedades"""

    def __init__(self, grid_size_x=GRID_SIZE_X, grid_size_y=GRID_SIZE_Y, csv_file=None):
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.graph = nx.grid_2d_graph(grid_size_x, grid_size_y)
        self.node_colors = {}

        self.susceptibility = TERRAIN_SUSCEPTIBILITY

        if csv_file and os.path.exists(csv_file):
            self.load_map_from_csv(csv_file)
        else:
            self.create_geographic_pattern()

    def create_geographic_pattern(self, seed=None):
        if seed is not None:
            random.seed(seed)
        colors = ['red', 'orange', 'blue', 'green']
        weights = [0.2, 0.3, 0.3, 0.2]
        for node in self.graph.nodes():
            self.node_colors[node] = random.choices(
                colors, weights=weights, k=1)[0]

    def load_map_from_csv(self, csv_file):

        try:
            # Ler o arquivo CSV como uma matriz
            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                matrix = list(reader)

            rows = len(matrix)
            if rows > 0:
                cols = len(matrix[0])
            else:
                raise ValueError("Arquivo CSV vazio")

            if rows != self.grid_size_y or cols != self.grid_size_x:
                print(f"Redimensionando o grid para {cols}x{rows}")
                self.grid_size_x = cols
                self.grid_size_y = rows
                self.graph = nx.grid_2d_graph(
                    self.grid_size_x, self.grid_size_y)

            for node in self.graph.nodes():
                self.node_colors[node] = 'green'

            for y in range(rows):
                for x in range(min(cols, len(matrix[y]))):
                    if matrix[y][x].strip() in ['red', 'orange', 'blue', 'green']:
                        self.node_colors[(x, y)] = matrix[y][x].strip()

            print(f"Mapa carregado com sucesso a partir do arquivo {csv_file}")
            print(f"Dimensões do mapa: {self.grid_size_x}x{self.grid_size_y}")

        except Exception as e:
            print(f"Erro ao carregar o arquivo CSV: {e}")
            print("Usando padrão geográfico aleatório como fallback")
            self.create_geographic_pattern()

    def save_map_to_csv(self, csv_file):

        try:
            with open(csv_file, 'w', newline='') as file:
                writer = csv.writer(file)

                for y in range(self.grid_size_y):
                    row = []
                    for x in range(self.grid_size_x):
                        row.append(self.node_colors.get((x, y), 'green'))
                    writer.writerow(row)

            print(f"Mapa salvo com sucesso no arquivo {csv_file}")

        except Exception as e:
            print(f"Erro ao salvar o arquivo CSV: {e}")

    def visualize(self, title="Mapa de Terreno"):

        plt.figure(figsize=(DEFAULT_VIEWSIZE_X, DEFAULT_VIEWSIZE_Y))
        pos = {node: node for node in self.graph.nodes()}

        nx.draw_networkx_nodes(self.graph, pos,
                               node_color=[self.node_colors[node]
                                           for node in self.graph.nodes()],
                               node_size=20/max(self.grid_size_x, self.grid_size_y))
        nx.draw_networkx_edges(self.graph, pos, alpha=0.1)

        plt.title(title)
        plt.axis('on')

        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label=label,
                   markerfacecolor=color, markersize=10)
            for color, label in zip(['red', 'orange', 'blue', 'green'],
                                    ['Rios/Barreiras', 'Florestas Úmidas',
                                     'Florestas de Transição', 'Vegetação Seca'])
        ]
        plt.legend(handles=legend_elements, loc='center left',
                   bbox_to_anchor=(1.0, 0.5))

        plt.tight_layout()
        plt.savefig(TERRAIN_MAP_FILE)
        print(
            f"Mapa do terreno salvo em '{os.path.abspath(TERRAIN_MAP_FILE)}'")
        plt.show()
