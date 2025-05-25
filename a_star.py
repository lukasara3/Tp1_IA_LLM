# a_star.py
import heapq
import math # Para a distância Euclidiana

def euclidean_distance_heuristic(graph, node1_id, node2_id):
    """
    Calcula a distância Euclidiana (linha reta) como heurística.
    Assume que os nós possuem atributos 'x' (longitude) e 'y' (latitude).
    IMPORTANTE: Se as coordenadas 'x' e 'y' do osmnx forem graus de lat/lon,
    esta não é uma distância métrica real (metros). No entanto, para a heurística A*,
    ela pode funcionar para priorizar nós "aparentemente" mais próximos.
    Para distâncias reais em metros, o grafo precisaria ser projetado ou
    uma fórmula como Haversine deveria ser usada. Para uma heurística, isso é um começo.
    """
    try:
        node1 = graph.nodes[node1_id]
        node2 = graph.nodes[node2_id]
        
        # Verificar se as coordenadas existem para evitar KeyError
        if 'x' not in node1 or 'y' not in node1 or 'x' not in node2 or 'y' not in node2:
            # print(f"A*: Aviso - Coordenadas 'x' ou 'y' ausentes nos nós {node1_id} ou {node2_id} para heurística.")
            return float('inf') # Não é possível calcular a heurística

        dx = node1['x'] - node2['x']
        dy = node1['y'] - node2['y']
        return math.sqrt(dx**2 + dy**2)
    except KeyError:
        # Lidar com o caso onde o nó não existe no grafo (embora deva existir se chamado corretamente)
        # print(f"A*: Aviso - Nó {node1_id} ou {node2_id} não encontrado no grafo para cálculo de heurística.")
        return float('inf')


def a_star_search(graph, start_node_id, goal_node_id, heuristic_func=euclidean_distance_heuristic):
    """
    Implementa o algoritmo de Busca A* (A-Estrela).

    Args:
        graph (networkx.MultiDiGraph): O grafo do osmnx.
        start_node_id (int): O ID do nó de início.
        goal_node_id (int): O ID do nó de destino.
        heuristic_func (function): Função heurística que recebe (graph, no_atual_id, no_destino_id).

    Returns:
        list: Uma lista de IDs de nós representando o caminho mais curto da origem ao destino.
              Retorna None se nenhum caminho for encontrado.
    """
    # Fila de prioridade armazena tuplas: (f_score, id_do_no_atual)
    # f_score = g_score (custo real da origem até o nó atual) + h_score (heurística do nó atual até o destino)
    
    # Inicializar g_score para todos os nós como infinito
    g_score = {node: float('inf') for node in graph.nodes()}
    g_score[start_node_id] = 0
    
    # f_score inicial para o nó de partida (g_score é 0)
    initial_f_score = heuristic_func(graph, start_node_id, goal_node_id)
    priority_queue = [(initial_f_score, start_node_id)]
    
    came_from = {start_node_id: None}

    print(f"A*: Iniciando busca de {start_node_id} para {goal_node_id}")

    while priority_queue:
        current_f_score, current_node = heapq.heappop(priority_queue)

        # Log para depuração
        # print(f"A*: Visitando {current_node} com f_score {current_f_score} (g_score: {g_score.get(current_node, float('inf'))})")

        if current_node == goal_node_id:
            print(f"A*: Destino {goal_node_id} alcançado com custo g_score {g_score[goal_node_id]}!")
            path = []
            node_iter = goal_node_id
            while node_iter is not None:
                path.append(node_iter)
                node_iter = came_from[node_iter]
            return path[::-1]

        # Otimização: se já encontramos um caminho melhor para current_node depois que ele foi adicionado à fila.
        # O f_score na fila pode estar desatualizado se o g_score do current_node foi melhorado por outro caminho
        # e um novo item (com f_score menor) foi adicionado à fila para current_node.
        # No entanto, o g_score[current_node] seria o valor atualizado.
        # A condição `tentative_g_score < g_score.get(neighbor, float('inf'))` já previne
        # a exploração de caminhos piores. Se um nó é retirado da PQ, é porque ele tinha o menor f_score *naquele momento*.
        
        if not graph.has_node(current_node):
            # print(f"A*: Atenção - Nó {current_node} não encontrado no grafo ao tentar obter vizinhos.")
            continue

        for neighbor in graph.neighbors(current_node):
            if not graph.has_node(neighbor):
                # print(f"A*: Atenção - Vizinho {neighbor} de {current_node} não é um nó válido.")
                continue

            min_edge_length = float('inf')
            if graph.has_edge(current_node, neighbor):
                for edge_key in graph.get_edge_data(current_node, neighbor):
                    edge_data = graph.get_edge_data(current_node, neighbor)[edge_key]
                    min_edge_length = min(min_edge_length, edge_data.get('length', float('inf')))
            
            if min_edge_length == float('inf'):
                continue

            tentative_g_score = g_score[current_node] + min_edge_length

            if tentative_g_score < g_score.get(neighbor, float('inf')): # Usar .get para segurança
                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g_score
                h_score = heuristic_func(graph, neighbor, goal_node_id)
                f_score = tentative_g_score + h_score
                heapq.heappush(priority_queue, (f_score, neighbor))
                
    print(f"A*: Nenhum caminho encontrado de {start_node_id} para {goal_node_id}")
    return None