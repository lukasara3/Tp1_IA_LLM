import osmnx as ox
import pandas as pd
import matplotlib.pyplot as plt 

place = "Belo Horizonte, Minas Gerais, Brazil"

print(f"Carregando grafo de caminhada para {place}...")
G = ox.graph_from_place(place, network_type="walk")
print(f"Grafo carregado com {len(G.nodes)} nós e {len(G.edges)} arestas.")

# 2. Defini pontos de onibus como interesse
bus_stop_tags_query = {"public_transport": "platform", "highway": "bus_stop"}
print(f"Buscando por pontos de ônibus com as tags: {bus_stop_tags_query}...")
features = ox.features.features_from_place(place, tags=bus_stop_tags_query)
print(f"Encontrados {len(features)} feições de pontos de ônibus.")

# ids dos nós do grafo que são pontos de ônibus
bus_stop_node_ids_in_graph = []

if not features.empty:
    # ponto representativo para cada feição de ponto de ônibus
    feature_points = features.representative_point()

    # nós do grafo mais próximos a esses pontos representativos
    print("Encontrando nós do grafo mais próximos dos pontos de ônibus...")
    # nearest_graph_nodes_data é um array NumPy (ou lista) de IDs de nós do grafo G
    nearest_graph_nodes_data = ox.distance.nearest_nodes(G, Y=feature_points.y, X=feature_points.x)
    
    # tags de interesse dos pontos de ônibus para armazenar nos nós do grafo
    useful_bus_tags = ["name", "ref", "shelter", "bench", "bin", "operator", "network"]
    
    # Filtrar useful_bus_tags para incluir apenas colunas que realmente existem em 'features'
    actual_useful_tags = [tag for tag in useful_bus_tags if tag in features.columns]
    if not actual_useful_tags:
        print(f"Atenção: Nenhuma das 'useful_bus_tags' ({useful_bus_tags}) foi encontrada nas colunas de 'features'. As informações dos pontos de ônibus podem ficar vazias.")
    
    print("Adicionando informações dos pontos de ônibus aos nós do grafo...")
    count_updated_nodes = 0
    
    # Iterar sobre os nós do grafo mais próximos e as informações das feições de ônibus correspondentes
    for graph_node_id, bus_feature_info_dict in zip(nearest_graph_nodes_data, features[actual_useful_tags].to_dict(orient="records")):
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

print("\nPreparando para plotar o grafo...")

if not G.nodes:
    print("Grafo está vazio, não há nada para plotar.")
else:
    node_colors = []
    node_sizes = []
    
    for node_id, data in G.nodes(data=True):
        if 'bus_stop' in data:  
            node_colors.append('red')    # Cor vermelha para pontos de ônibus
            node_sizes.append(5)        
        else:
            node_colors.append('lightgray') 
            node_sizes.append(0)        
    # Nome do arquivo para salvar o gráfico
    output_filename = "grafo_bh_com_pontos_onibus_v2.png" 

    if not bus_stop_node_ids_in_graph:
        print("Nenhum ponto de ônibus foi adicionado ao grafo para destaque. Plotando grafo simples.")
        fig, ax = ox.plot_graph(G,
                                node_size=0, 
                                edge_linewidth=0.3,
                                edge_color='gray',  
                                show=False, close=False, 
                                save=True, filepath=output_filename, 
                                dpi=300, 
                                bgcolor='w')
        ax.set_title("Grafo de Caminhada de Belo Horizonte (Sem Pontos de Ônibus Destacados)", color='black', y=0.01, fontsize=8)
        print(f"Gráfico salvo como: {output_filename}")
    else:
        print(f"Plotando grafo com {len(bus_stop_node_ids_in_graph)} pontos de ônibus destacados.")
        fig, ax = ox.plot_graph(G,
                                node_color=node_colors,
                                node_size=node_sizes,
                                edge_linewidth=0.3,      
                                edge_color='gray',        
                                node_zorder=2,           
                                show=False, close=False, 
                                save=True, filepath=output_filename, 
                                dpi=300, 
                                bgcolor='w')              
        ax.set_title(f"Grafo de Caminhada de BH com {len(bus_stop_node_ids_in_graph)} Pontos de Ônibus Destacados", color='black', y=0.01, fontsize=8)
        print(f"Gráfico salvo como: {output_filename}")

    plt.close(fig) 
