""" Configurações centralizadas """

# Configurações do grid
GRID_SIZE_X = 100
GRID_SIZE_Y = 100

# Configurações de simulação
DEFAULT_SIMULATION_STEPS = 200
DEFAULT_INITIAL_INFECTED = 10
DEFAULT_NUM_SIMULATIONS = 50

# Configurações do modelo SIR
DEFAULT_BETA = 0.3       # Taxa de transmissão
DEFAULT_GAMMA = 1./10    # Taxa de recuperação

# Configurações de visualização
DEFAULT_PROBABILITY_THRESHOLD = 0.5
DEFAULT_VIEWSIZE_X = 12
DEFAULT_VIEWSIZE_Y = 7

# Definição das suscetibilidades de cada tipo de terreno
TERRAIN_SUSCEPTIBILITY = {
    'red': 0.0,     # Nós imunes / rios
    'orange': 0.3,  # Nós resistentes / Florestas úmidas
    'blue': 0.6,    # Suscetíveis / Floresta de transição
    'green': 0.9    # Altamente Suscetíveis / Mata seca
}

# Nomes de arquivos para saída
TERRAIN_MAP_FILE = 'network_terrain.png'
FINAL_STATE_FILE = 'sir_final_state.png'
MULTIPLE_SIMULATIONS_FILE = 'multiple_simulations_results.png'
INITIAL_INFECTED_NODES_FILE = 'initial_infected_nodes.png'
SIMULATION_RESULTS_CSV = 'simulation_results.csv'
PROBABLE_INFECTION_PATH_FILE = 'probable_infection_path.mp4'
PROBABILITY_MAP_EARLY = 'probability_map_early.png'
PROBABILITY_MAP_MIDDLE = 'probability_map_middle.png'
PROBABILITY_MAP_FINAL = 'probability_map_final.png'
