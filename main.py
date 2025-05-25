# main.py
import osmnx as ox
import matplotlib.pyplot as plt
import random

# Importar a função de preparação do grafo do arquivo graph.py
# Certifique-se de que graph.py está na mesma pasta ou no PYTHONPATH
from graph import carregar_e_preparar_grafo 

# Importar os algoritmos de busca dos arquivos .py correspondentes
from dijkstra import uniform_cost_search
from a_star import a_star_search, euclidean_distance_heuristic # Importar a heurística também

def calcular_custo_caminho(graph, path):
    """Calcula o custo total (comprimento) de um caminho no grafo."""
    if not path or len(path) < 2:
        return 0
    cost = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        min_len = float('inf')
        if graph.has_edge(u,v): # Verifica se existe alguma aresta entre u e v
            # Iterar sobre as chaves das múltiplas arestas (se houver)
            # graph[u][v] retorna um AtlasView, que é como um dicionário de dicionários de atributos
            for k in graph[u][v]: 
                 min_len = min(min_len, graph[u][v][k].get('length', float('inf')))
            
            if min_len == float('inf'): # Se nenhuma aresta tiver 'length' ou não for encontrada
                print(f"MAIN.PY: Aviso - Aresta entre {u} e {v} não possui atributo 'length' válido.")
            else:
                cost += min_len
        else:
            # Isso não deveria acontecer se o caminho foi gerado corretamente pelo grafo
            print(f"MAIN.PY: Aviso - Aresta não encontrada entre {u} e {v} no caminho {path}.")
            return float('inf') # Indica um problema no caminho
    return cost

def main_testes_busca():
    print("MAIN.PY: Iniciando testes dos algoritmos de busca...")

    # 1. Carregar e preparar o grafo e os pontos de ônibus
    # O plot do grafo geral é opcional aqui, então definimos como False.
    G, bus_stop_node_ids = carregar_e_preparar_grafo(plotar_grafo_geral=False)

    if G is None:
        print("MAIN.PY: Falha ao carregar o grafo. Encerrando testes.")
        return
    
    if not bus_stop_node_ids:
        print("MAIN.PY: Nenhum nó de ponto de ônibus identificado. Não é possível realizar o teste de busca de rota.")
        return

    # 2. Selecionar nós de origem e destino para teste
    random.seed(42) # Para reprodutibilidade dos testes
    
    if len(bus_stop_node_ids) < 1: # Verificação redundante, já que o anterior cobriria, mas seguro.
        print("MAIN.PY: Não há pontos de ônibus suficientes para selecionar um destino.")
        return
    goal_node_test = random.choice(bus_stop_node_ids)
    
    # Garantir que a origem não seja o mesmo que o destino e exista no grafo
    possible_start_nodes = [n for n in G.nodes() if n != goal_node_test]
    if not possible_start_nodes:
        print("MAIN.PY: Não há nós suficientes no grafo para selecionar uma origem diferente do destino.")
        return
    start_node_test = random.choice(possible_start_nodes)
    
    # Garantir que os nós de teste realmente existem no grafo (importante se G for muito pequeno)
    if not G.has_node(start_node_test) or not G.has_node(goal_node_test):
        print(f"MAIN.PY: Nó de origem ({start_node_test}) ou destino ({goal_node_test}) não encontrado no grafo. Encerrando.")
        return

    print(f"\nMAIN.PY: --- TESTE DOS ALGORITMOS DE BUSCA ---")
    print(f"Origem: {start_node_test}, Destino (Ponto de Ônibus): {goal_node_test}")

    # --- Testar UCS ---
    print("\nMAIN.PY: Executando Busca de Custo Uniforme (UCS)...")
    path_ucs = uniform_cost_search(G, start_node_test, goal_node_test)

    if path_ucs:
        cost_ucs = calcular_custo_caminho(G, path_ucs)
        print(f"UCS - Caminho encontrado: {path_ucs}")
        print(f"UCS - Número de passos: {len(path_ucs)}")
        print(f"UCS - Custo do caminho (distância): {cost_ucs:.2f} metros")

        output_filename_ucs = f"rota_ucs_{start_node_test}_para_{goal_node_test}.png"
        print(f"MAIN.PY: Plotando rota UCS e salvando em {output_filename_ucs}...")
        try:
            fig, ax = ox.plot_graph_route(G, path_ucs, route_color='blue', route_linewidth=3,
                                          node_size=0, show=False, close=False, save=True,
                                          filepath=output_filename_ucs, dpi=300, bgcolor='w')
            ax.set_title(f"Rota UCS de {start_node_test} para {goal_node_test}\nCusto: {cost_ucs:.0f}m", 
                         color='black', y=0.01, fontsize=8)
            plt.close(fig) # Fechar a figura para liberar memória
        except Exception as e:
            print(f"MAIN.PY: Erro ao plotar/salvar rota UCS: {e}")
    else:
        print("UCS - Nenhum caminho encontrado.")

    # --- Testar A* ---
    print("\nMAIN.PY: Executando Busca A* (A-Estrela)...")
    path_a_star = a_star_search(G, start_node_test, goal_node_test, heuristic_func=euclidean_distance_heuristic)

    if path_a_star:
        cost_a_star = calcular_custo_caminho(G, path_a_star)
        print(f"A* - Caminho encontrado: {path_a_star}")
        print(f"A* - Número de passos: {len(path_a_star)}")
        print(f"A* - Custo do caminho (distância): {cost_a_star:.2f} metros")

        output_filename_a_star = f"rota_a_star_{start_node_test}_para_{goal_node_test}.png"
        print(f"MAIN.PY: Plotando rota A* e salvando em {output_filename_a_star}...")
        try:
            fig, ax = ox.plot_graph_route(G, path_a_star, route_color='green', route_linewidth=3,
                                          node_size=0, show=False, close=False, save=True,
                                          filepath=output_filename_a_star, dpi=300, bgcolor='w')
            ax.set_title(f"Rota A* de {start_node_test} para {goal_node_test}\nCusto: {cost_a_star:.0f}m", 
                         color='black', y=0.01, fontsize=8)
            plt.close(fig) # Fechar a figura para liberar memória
        except Exception as e:
            print(f"MAIN.PY: Erro ao plotar/salvar rota A*: {e}")
            
    else:
        print("A* - Nenhum caminho encontrado.")

    print("\nMAIN.PY: Testes concluídos.")

if __name__ == "__main__":
    main_testes_busca()
