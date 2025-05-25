# ucs.py
import heapq # Para a fila de prioridade

def uniform_cost_search(graph, start_node_id, goal_node_id):
    """
    Implementa o algoritmo de Busca de Custo Uniforme (UCS).

    Args:
        graph (networkx.MultiDiGraph): O grafo do osmnx.
        start_node_id (int): O ID do nó de início.
        goal_node_id (int): O ID do nó de destino.

    Returns:
        list: Uma lista de IDs de nós representando o caminho mais curto da origem ao destino.
              Retorna None se nenhum caminho for encontrado.
    """
    # Fila de prioridade armazena tuplas: (custo_acumulado, id_do_no_atual, caminho_ate_agora)
    # Ou, de forma mais eficiente para reconstrução: (custo_acumulado, id_do_no_atual)
    # e um dicionário 'veio_de' para reconstruir o caminho.

    # Fila de prioridade: (custo, no_id)
    priority_queue = [(0, start_node_id)] 
    
    # Dicionário para rastrear o nó pelo qual chegamos a um nó específico no caminho de menor custo
    came_from = {start_node_id: None}
    
    # Dicionário para armazenar o custo (g_score) para alcançar cada nó a partir do início
    cost_so_far = {start_node_id: 0}

    print(f"UCS: Iniciando busca de {start_node_id} para {goal_node_id}")

    while priority_queue:
        current_cost, current_node = heapq.heappop(priority_queue)

        # Log para depuração (pode ser removido ou ajustado)
        # print(f"UCS: Visitando {current_node} com custo {current_cost}")

        if current_node == goal_node_id:
            print(f"UCS: Destino {goal_node_id} alcançado com custo {current_cost}!")
            # Reconstruir o caminho
            path = []
            node_iter = goal_node_id
            while node_iter is not None:
                path.append(node_iter)
                node_iter = came_from[node_iter]
            return path[::-1] # Retorna o caminho revertido (origem -> destino)

        # Se já encontramos um caminho mais curto para este nó (devido a como heapq funciona), pulamos.
        # Isso é mais relevante se um nó puder ser adicionado múltiplas vezes à fila com custos diferentes.
        # A verificação `new_cost < cost_so_far.get(neighbor, float('inf'))` abaixo geralmente lida com isso.
        if current_cost > cost_so_far.get(current_node, float('inf')): # Adicionado .get para segurança
            continue

        # Explorar vizinhos
        if not graph.has_node(current_node):
            # print(f"UCS: Atenção - Nó {current_node} não encontrado no grafo ao tentar obter vizinhos.")
            continue
            
        for neighbor in graph.neighbors(current_node):
            if not graph.has_node(neighbor): # Verificação extra
                # print(f"UCS: Atenção - Vizinho {neighbor} de {current_node} não é um nó válido.")
                continue

            # Calcular o custo para ir de current_node para neighbor
            # Em um MultiDiGraph, pode haver múltiplas arestas. Pegamos a de menor 'length'.
            min_edge_length = float('inf')
            if graph.has_edge(current_node, neighbor):
                for edge_key in graph.get_edge_data(current_node, neighbor):
                    edge_data = graph.get_edge_data(current_node, neighbor)[edge_key]
                    min_edge_length = min(min_edge_length, edge_data.get('length', float('inf')))
            
            if min_edge_length == float('inf'): # Nenhuma aresta com 'length' ou nenhuma aresta
                continue 
            
            new_cost = cost_so_far[current_node] + min_edge_length

            if new_cost < cost_so_far.get(neighbor, float('inf')): # Usar .get para segurança
                cost_so_far[neighbor] = new_cost
                heapq.heappush(priority_queue, (new_cost, neighbor))
                came_from[neighbor] = current_node
                
    print(f"UCS: Nenhum caminho encontrado de {start_node_id} para {goal_node_id}")
    return None # Caminho não encontrado