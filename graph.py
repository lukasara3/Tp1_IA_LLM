import osmnx as ox
import pandas as pd
import matplotlib.pyplot as plt # Importar Matplotlib para plotagem

# Definição do local
place = "Belo Horizonte, Minas Gerais, Brazil"

# 1. Carregar o grafo de caminhada para Belo Horizonte
print(f"Carregando grafo de caminhada para {place}...")
G = ox.graph_from_place(place, network_type="walk")
print(f"Grafo carregado com {len(G.nodes)} nós e {len(G.edges)} arestas.")

# 2. Buscar os pontos de ônibus usando as tags combinadas
# (locais que são tanto uma plataforma de transporte público quanto um ponto de ônibus)
bus_stop_tags_query = {"public_transport": "platform", "highway": "bus_stop"}
print(f"Buscando por pontos de ônibus com as tags: {bus_stop_tags_query}...")
features = ox.features.features_from_place(place, tags=bus_stop_tags_query)
print(f"Encontrados {len(features)} feições de pontos de ônibus.")

# Lista para armazenar os IDs dos nós do grafo que são pontos de ônibus
bus_stop_node_ids_in_graph = []

if not features.empty:
    # 3. Obter um ponto representativo para cada feição de ponto de ônibus
    # (útil se algumas feições forem polígonos, embora para pontos de ônibus geralmente sejam pontos)
    feature_points = features.representative_point()

    # 4. Encontrar os nós do grafo mais próximos a esses pontos representativos
    print("Encontrando nós do grafo mais próximos dos pontos de ônibus...")
    # nearest_graph_nodes é uma série de IDs de nós do grafo G
    nearest_graph_nodes_series = ox.distance.nearest_nodes(G, Y=feature_points.y, X=feature_points.x)
    
    # 5. Definir as tags de interesse dos pontos de ônibus para armazenar nos nós do grafo
    useful_bus_tags = ["name", "ref", "shelter", "bench", "bin", "operator", "network"]
    
    print("Adicionando informações dos pontos de ônibus aos nós do grafo...")
    count_updated_nodes = 0
    
    # Iterar sobre os nós do grafo mais próximos e as informações das feições de ônibus correspondentes
    # Assegurar que estamos iterando sobre os valores da Série e os dicionários de feições
    for graph_node_id, bus_feature_info_dict in zip(nearest_graph_nodes_series.values, features[useful_bus_tags].to_dict(orient="records")):
        # Limpar o dicionário de informações do ponto de ônibus, removendo valores NaN
        cleaned_bus_feature_info = {k: v for k, v in bus_feature_info_dict.items() if pd.notna(v)}
        
        # Atualizar o nó do grafo com as informações do ponto de ônibus
        if G.has_node(graph_node_id):
            G.nodes[graph_node_id].update({"bus_stop": cleaned_bus_feature_info})
            bus_stop_node_ids_in_graph.append(graph_node_id) # Adicionar à lista para plotagem
            count_updated_nodes +=1
        else:
            print(f"Aviso: Nó {graph_node_id} (mais próximo da feição) não encontrado no grafo G. Pulando.")
    
    print(f"{count_updated_nodes} nós do grafo foram atualizados com informações de pontos de ônibus.")
else:
    print("Nenhuma feição de ponto de ônibus encontrada com as tags especificadas.")

# --- SEÇÃO DE PLOTAGEM ---
print("\nPreparando para plotar o grafo...")

if not G.nodes:
    print("Grafo está vazio, não há nada para plotar.")
else:
    node_colors = []
    node_sizes = []
    
    # Definir cores e tamanhos para os nós
    for node_id, data in G.nodes(data=True):
        if 'bus_stop' in data:  # Se o nó foi marcado como um ponto de ônibus
            node_colors.append('red')    # Cor vermelha para pontos de ônibus
            node_sizes.append(20)        # Tamanho maior para destacar
        else:
            node_colors.append('gray') # Cor cinza para outros nós
            node_sizes.append(0)         # Tamanho 0 para não poluir (ou um valor pequeno como 1 ou 2)

    if not bus_stop_node_ids_in_graph:
        print("Nenhum ponto de ônibus foi adicionado ao grafo para destaque. Plotando grafo simples.")
        # Plotar o grafo sem destaque especial se nenhum ponto de ônibus foi processado
        fig, ax = ox.plot_graph(G,
                                node_size=0, # Esconder todos os nós ou usar um tamanho pequeno
                                edge_linewidth=0.2,
                                edge_color='lightgray',
                                show=False, close=False,
                                bgcolor='w')
        ax.set_title("Grafo de Caminhada de Belo Horizonte (Sem Pontos de Ônibus Destacados)", color='black', y=0.01)
    else:
        print(f"Plotando grafo com {len(bus_stop_node_ids_in_graph)} pontos de ônibus destacados.")
        # Plotar o grafo, destacando os nós dos pontos de ônibus
        fig, ax = ox.plot_graph(G,
                                node_color=node_colors,
                                node_size=node_sizes,
                                edge_linewidth=0.2,       # Linhas das ruas mais finas
                                edge_color='lightgray',   # Cor das ruas
                                show_nodes=True,          # Garantir que os nós (destacados) sejam mostrados
                                show=False, close=False,  # Para adicionar mais elementos antes de mostrar
                                bgcolor='w')              # Cor de fundo branca
        ax.set_title(f"Grafo de Caminhada de BH com {len(bus_stop_node_ids_in_graph)} Pontos de Ônibus Destacados", color='black', y=0.01, fontsize=10)

    plt.show() # Exibir o gráfico