# graph.py
import osmnx as ox
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd # Para carregar/salvar features em GeoJSON

# Definição do local (pode ser um parâmetro da função se quiser mais flexibilidade)
PLACE_NAME = "Belo Horizonte, Minas Gerais, Brazil"

# Nomes de arquivos para cache local
PLACE_FILE_PREFIX = PLACE_NAME.split(",")[0].lower().replace(" ", "_")
GRAPH_FILEPATH = f"{PLACE_FILE_PREFIX}_walk.graphml"
FEATURES_FILEPATH_GEOJSON = f"{PLACE_FILE_PREFIX}_bus_stops.geojson"

def carregar_e_preparar_grafo(plotar_grafo_geral=False, nome_arquivo_plot="grafo_bh_pontos_onibus.png"):
    """
    Carrega o grafo de caminhada de Belo Horizonte, identifica pontos de ônibus,
    associa-os aos nós do grafo e, opcionalmente, plota o grafo geral.

    Args:
        plotar_grafo_geral (bool): Se True, plota o grafo com todos os pontos de ônibus destacados.
        nome_arquivo_plot (str): Nome do arquivo para salvar o plot do grafo geral.

    Returns:
        tuple: (networkx.MultiDiGraph, list)
               Retorna o grafo G processado e a lista de IDs dos nós que são pontos de ônibus.
               Retorna (None, []) em caso de falha no carregamento do grafo.
    """
    G = None
    features = None # Será um GeoDataFrame
    bus_stop_node_ids_in_graph = []

    # --- Configurações OSMnx ---
    # Estas configurações serão aplicadas quando as funções do osmnx forem chamadas DENTRO desta função.
    ox.settings.overpass_endpoint = "https://overpass.kumi.systems/api" 
    # ox.settings.overpass_endpoint = "https://lz4.overpass-api.de/api" # Outra opção
    # ox.settings.overpass_endpoint = "https://z.overpass-api.de/api" # Mais uma opção
    
    ox.settings.timeout = 300 # Aumentar timeout para 5 minutos
    ox.settings.log_console = True 
    ox.settings.use_cache = True # Tentar usar o cache se houver dados

    # --- Tentar carregar de arquivos locais primeiro ---
    try:
        print(f"GRAPH.PY: Tentando carregar grafo de arquivo: {GRAPH_FILEPATH}")
        G = ox.load_graphml(GRAPH_FILEPATH)
        print(f"GRAPH.PY: Grafo carregado de {GRAPH_FILEPATH} com {len(G.nodes)} nós e {len(G.edges)} arestas.")
        
        print(f"GRAPH.PY: Tentando carregar features de arquivo: {FEATURES_FILEPATH_GEOJSON}")
        features = gpd.read_file(FEATURES_FILEPATH_GEOJSON)
        print(f"GRAPH.PY: Features carregadas de {FEATURES_FILEPATH_GEOJSON} com {len(features)} pontos.")

    except FileNotFoundError:
        print(f"GRAPH.PY: Arquivos locais ({GRAPH_FILEPATH} ou {FEATURES_FILEPATH_GEOJSON}) não encontrados. Baixando dados...")
        G = None 
        features = None 
    except Exception as e:
        print(f"GRAPH.PY: Erro ao carregar arquivos locais: {e}. Tentando baixar dados...")
        G = None
        features = None
    
    # --- Se não carregou dos arquivos, tentar baixar ---
    if G is None: 
        try:
            print(f"GRAPH.PY: Baixando grafo de caminhada para {PLACE_NAME}...")
            # A chamada ox.graph_from_place AQUI usará as ox.settings definidas acima.
            G = ox.graph_from_place(PLACE_NAME, network_type="walk")
            print(f"GRAPH.PY: Grafo para {PLACE_NAME} baixado com {len(G.nodes)} nós e {len(G.edges)} arestas.")
            print(f"GRAPH.PY: Salvando grafo em: {GRAPH_FILEPATH}")
            ox.save_graphml(G, filepath=GRAPH_FILEPATH)
        except Exception as e:
            print(f"GRAPH.PY: ERRO CRÍTICO ao baixar o grafo: {e}")
            return None, [] 

    if features is None and G: 
        try:
            bus_stop_tags_query = {"public_transport": "platform", "highway": "bus_stop"}
            print(f"GRAPH.PY: Baixando features (pontos de ônibus) para: {PLACE_NAME} com tags: {bus_stop_tags_query}...")
            # A chamada ox.features.features_from_place AQUI usará as ox.settings.
            features_gdf = ox.features.features_from_place(PLACE_NAME, tags=bus_stop_tags_query)
            
            if not features_gdf.empty:
                print(f"GRAPH.PY: Encontradas {len(features_gdf)} feições de pontos de ônibus.")
                print(f"GRAPH.PY: Salvando features em: {FEATURES_FILEPATH_GEOJSON}")
                features_gdf.to_file(FEATURES_FILEPATH_GEOJSON, driver="GeoJSON")
                features = features_gdf 
            else:
                print("GRAPH.PY: Nenhuma feição de ponto de ônibus encontrada para salvar.")
                features = gpd.GeoDataFrame() 
        except Exception as e:
            print(f"GRAPH.PY: ERRO ao baixar features dos pontos de ônibus: {e}")
            features = gpd.GeoDataFrame() 

    # --- Processar features e adicionar aos nós do grafo ---
    # (O restante da função permanece o mesmo)
    if G and features is not None and not features.empty:
        if isinstance(features, gpd.GeoDataFrame) and 'geometry' in features.columns and not features.geometry.isna().all():
            features_valid = features[features.geometry.is_valid & ~features.geometry.isna()].copy()
            
            if not features_valid.empty:
                feature_points = features_valid.representative_point()

                if not feature_points.x.isna().all() and not feature_points.y.isna().all():
                    nearest_graph_nodes_data = ox.distance.nearest_nodes(G, Y=feature_points.y, X=feature_points.x)
                    useful_bus_tags = ["name", "ref", "shelter", "bench", "bin", "operator", "network"]
                    actual_useful_tags = [tag for tag in useful_bus_tags if tag in features_valid.columns]
                    
                    print("GRAPH.PY: Adicionando informações dos pontos de ônibus aos nós do grafo...")
                    count_updated_nodes = 0
                    for graph_node_id, bus_feature_info_dict in zip(nearest_graph_nodes_data, features_valid[actual_useful_tags].to_dict(orient="records")):
                        cleaned_bus_feature_info = {k: v for k, v in bus_feature_info_dict.items() if pd.notna(v)}
                        if G.has_node(graph_node_id):
                            G.nodes[graph_node_id].update({"bus_stop": cleaned_bus_feature_info})
                            bus_stop_node_ids_in_graph.append(graph_node_id)
                            count_updated_nodes +=1
                    print(f"GRAPH.PY: {count_updated_nodes} nós do grafo foram atualizados com informações de pontos de ônibus.")
                else:
                    print("GRAPH.PY: Não foi possível obter pontos representativos válidos das features (coordenadas X ou Y ausentes).")
            else:
                print("GRAPH.PY: GeoDataFrame de features está vazio após limpeza de geometrias inválidas.")
        else:
            print("GRAPH.PY: Features não são um GeoDataFrame válido, não possuem coluna 'geometry' ou todas as geometrias são NaN.")
    elif G:
         print("GRAPH.PY: Features de pontos de ônibus não disponíveis ou grafo não carregado corretamente.")
    
    if plotar_grafo_geral and G:
        print(f"\nGRAPH.PY: Preparando para plotar o grafo geral e salvar como {nome_arquivo_plot}...")
        if not G.nodes:
            print("GRAPH.PY: Grafo está vazio, não há nada para plotar.")
        else:
            node_colors = ['red' if node_id in bus_stop_node_ids_in_graph else 'lightgray' for node_id in G.nodes()]
            node_sizes = [5 if node_id in bus_stop_node_ids_in_graph else 0 for node_id in G.nodes()]
            
            fig, ax = ox.plot_graph(G, node_color=node_colors, node_size=node_sizes,
                                    edge_linewidth=0.3, edge_color='gray', node_zorder=2,
                                    show=False, close=False, save=True, filepath=nome_arquivo_plot,
                                    dpi=300, bgcolor='w')
            title = f"Grafo de Caminhada de {PLACE_NAME.split(',')[0]}"
            if bus_stop_node_ids_in_graph:
                title += f" com {len(bus_stop_node_ids_in_graph)} Pontos de Ônibus"
            else:
                title += " (Sem Pontos de Ônibus Destacados)"
            ax.set_title(title, color='black', y=0.01, fontsize=8)
            print(f"GRAPH.PY: Gráfico salvo como: {nome_arquivo_plot}")
            plt.close(fig)
            
    return G, bus_stop_node_ids_in_graph

if __name__ == "__main__":
    print("Executando graph.py diretamente para carregar/processar dados e plotar o grafo geral...")
    G_principal, ids_pontos_onibus = carregar_e_preparar_grafo(plotar_grafo_geral=True, nome_arquivo_plot="mapa_geral_pontos_onibus.png")
    if G_principal:
        print(f"Execução direta de graph.py concluída. Nós no grafo: {len(G_principal.nodes)}")
        if ids_pontos_onibus:
            print(f"Número de nós de pontos de ônibus identificados: {len(ids_pontos_onibus)}")
        else:
            print("Nenhum ponto de ônibus identificado ou associado ao grafo.")
    else:
        print("Falha ao carregar o grafo na execução direta de graph.py.")
