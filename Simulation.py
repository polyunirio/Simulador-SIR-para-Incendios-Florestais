from Mapa import Mapa
from SIRmodel import SIRmodel
from Config import GRID_SIZE_X, GRID_SIZE_Y, DEFAULT_SIMULATION_STEPS, DEFAULT_INITIAL_INFECTED

"""Simulador"""


class SimulationApp:

    def __init__(self, grid_size_x=GRID_SIZE_X, grid_size_y=GRID_SIZE_Y):
        self.terrain_map = Mapa(grid_size_x, grid_size_y)
        self.sir_model = SIRmodel(self.terrain_map)

    def run(self, initial_infected=DEFAULT_INITIAL_INFECTED, infection_strategy="random",
            simulation_steps=DEFAULT_SIMULATION_STEPS):

        print(
            f"Iniciando simulação com grid {self.terrain_map.grid_size_x}x{self.terrain_map.grid_size_y}")
        print(f"Número de nós: {len(self.terrain_map.graph)}")

        # Inicializar e executar a simulação SIR
        self.sir_model.initialize_states(initial_infected, infection_strategy)
        self.sir_model.run_simulation(simulation_steps)
