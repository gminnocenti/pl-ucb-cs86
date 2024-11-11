import networkx as nx
import pygraphviz as pgv
import numpy as np
import prairielearn as pl
import moviepy.editor as mpy
import warnings
import os
import tempfile
import lxml
import base64
import random
from networkx.drawing.nx_agraph import to_agraph

# Default parameters
ENGINE_DEFAULT = "dot"
PARAMS_TYPE_DEFAULT = "adjacency-matrix"
DIRECTED_DEFAULT = "False"
DURATION_FRAME_DEFAULT = 2
ALGORITHM_DEFAULT = "dfs"
SHOW_STEPS_DEFAULT="True"
SHOW_WEIGHTS_DEFAULT="False"
ERROR_CHANCE_DEFAULT="False"

"""THIS SECTION CONTAINS THE FUNCTIONS TO GENERATE VIDEO FROM A MATRIX"""


def generate_frames_bfs_from_matrix(matrix, start_node, show_steps, show_weights, directed,error_chance, size="5,5"):
    # If matrix is passed, convert to a graph using networkx
    if isinstance(matrix, np.ndarray):  # Check if the input is still a matrix
        if directed == "True":
            G = nx.from_numpy_array(matrix, create_using=nx.DiGraph())  # Use DiGraph for directed graphs
        else:
            G = nx.from_numpy_array(matrix)
    else:
        G = matrix  # If it's already a graph, just use it directly

    # Convert the NetworkX graph to a PyGraphviz graph
    A = nx.nx_agraph.to_agraph(G)

    # Get BFS traversal order using a custom BFS to introduce errors
    bfs_edges, bfs_nodes = custom_bfs_with_errors(G, start_node, error_chance)


    # List to store frames for the animation
    frames = []

    # Create the animation by incrementally highlighting nodes and edges
    for i in range(1, len(bfs_nodes) + 1):
        # Create a new AGraph object for each frame
        A_temp = A.copy()

        # Highlight nodes in BFS order
        nodes_to_highlight = bfs_nodes[:i]
        for node in nodes_to_highlight:
            A_temp.get_node(node).attr['color'] = 'red'
            A_temp.get_node(node).attr['style'] = 'filled'
            A_temp.get_node(node).attr['fillcolor'] = 'red'

        # Highlight edges in BFS order
        edges_to_highlight = bfs_edges[:i-1]  # Highlight edges based on BFS progression
        for edge in edges_to_highlight:
            A_temp.get_edge(edge[0], edge[1]).attr['color'] = 'blue'
            A_temp.get_edge(edge[0], edge[1]).attr['penwidth'] = 2.5

        # Optionally set the graph title to indicate the current step and node
        if show_steps == "True":
            A_temp.graph_attr['label'] = f"Step {i}: Current Node {bfs_nodes[i-1]} (BFS)"
            A_temp.graph_attr['labelloc'] = 'top'

        # Optionally display weights
        if show_weights == "True":
            for u, v, data in G.edges(data=True):
                weight = data.get('weight', 1.0)  # Default weight if not present
                A_temp.get_edge(u, v).attr['label'] = str(weight)

        # Set the size of the graph image
        A_temp.graph_attr['size'] = size
        A_temp.graph_attr['dpi'] = "300"

        # Save the graph to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        A_temp.draw(temp_file.name, format="png", prog="dot")

        # Add the temporary file path to the frames list
        frames.append(temp_file.name)

    return frames

def custom_bfs_with_errors(G, start_node, error_chance):
    """
    Custom BFS implementation that introduces errors during traversal.
    If error_chance is 'True', errors are introduced by modifying the traversal path.
    All nodes are guaranteed to be visited at least once.
    """
    visited = set()
    bfs_nodes = []
    bfs_edges = []
    
    queue = [start_node]
    visited.add(start_node)

    while queue:
        node = queue.pop(0)
        bfs_nodes.append(node)

        # Get all neighbors
        neighbors = list(G.neighbors(node))
        
        # If error_chance is enabled, introduce errors by shuffling neighbors, skipping nodes, or revisiting nodes
        if error_chance == "True":
            if random.random() < 0.5 and neighbors:  # 50% chance to skip a node (if there are any neighbors)
                skipped_node = random.choice(neighbors)
                neighbors.remove(skipped_node)  # Remove the skipped node from neighbors

            if random.random() < 0.5 and len(visited) > 1:  # 50% chance to backtrack to a previous node
                backtrack_node = random.choice(list(visited))
                neighbors = [backtrack_node]  # Force backtrack to a previously visited node

            random.shuffle(neighbors)  # Shuffle neighbors to introduce randomness in traversal order

        # Explore all neighbors and add them to the queue if not visited
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                bfs_edges.append((node, neighbor))  # Record the edge visited

    return bfs_edges, bfs_nodes


def generate_frames_dfs_from_matrix(matrix, start_node, show_steps, show_weights, directed, error_chance,size="5,5"):
    # If matrix is passed, convert to a graph using networkx
    if isinstance(matrix, np.ndarray):  # Check if the input is still a matrix
        if directed == "True":
            G = nx.from_numpy_array(matrix, create_using=nx.DiGraph())  # Use DiGraph for directed graphs
        else:
            G = nx.from_numpy_array(matrix)
    else:
        G = matrix  # If it's already a graph, just use it directly

    # Convert the NetworkX graph to a PyGraphviz graph
    A = nx.nx_agraph.to_agraph(G)

    # Get DFS traversal order using a custom DFS to introduce errors
    dfs_nodes, dfs_edges = custom_dfs_with_errors(G, start_node, error_chance)


    # List to store frames for the animation
    frames = []

    # Create the animation by incrementally highlighting nodes and edges
    for i in range(1, len(dfs_nodes) + 1):
        # Create a new AGraph object for each frame
        A_temp = A.copy()

        # Highlight nodes in DFS order
        nodes_to_highlight = dfs_nodes[:i]
        for node in nodes_to_highlight:
            A_temp.get_node(node).attr['color'] = 'red'
            A_temp.get_node(node).attr['style'] = 'filled'
            A_temp.get_node(node).attr['fillcolor'] = 'red'

        # Highlight edges in DFS order
        edges_to_highlight = dfs_edges[:i-1]  # Highlight edges based on DFS progression
        for edge in edges_to_highlight:
            A_temp.get_edge(edge[0], edge[1]).attr['color'] = 'blue'
            A_temp.get_edge(edge[0], edge[1]).attr['penwidth'] = 2.5

        # Optionally set the graph title to indicate the current step and node
        if show_steps == "True":
            A_temp.graph_attr['label'] = f"Step {i}: Current Node {dfs_nodes[i-1]} (DFS)"
            A_temp.graph_attr['labelloc'] = 'top'

        # Optionally display weights
        if show_weights == "True":
            for u, v, data in G.edges(data=True):
                weight = data.get('weight', 1.0)  # Default weight if not present
                A_temp.get_edge(u, v).attr['label'] = str(weight)

        # Set the size of the graph image
        A_temp.graph_attr['size'] = size
        A_temp.graph_attr['dpi'] = "300"

        # Save the graph to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        A_temp.draw(temp_file.name, format="png", prog="dot")

        # Add the temporary file path to the frames list
        frames.append(temp_file.name)

    return frames

def custom_dfs_with_errors(G, start_node, error_chance):
    """
    Custom DFS implementation that introduces errors during traversal.
    If error_chance is 'True', errors are introduced by modifying the traversal path.
    """
    visited = set()
    dfs_nodes = []
    dfs_edges = []

    def dfs(node):
        visited.add(node)
        dfs_nodes.append(node)
        # Get all neighbors
        neighbors = list(G.neighbors(node))
        
        # If error_chance is enabled, introduce errors by shuffling neighbors, skipping nodes, or revisiting nodes
        if error_chance == "True":
            if random.random() < 0.1:  # 50% chance to skip a node for testing
                # Randomly skip a node and continue traversal
                skipped_node = random.choice(neighbors)
                neighbors.remove(skipped_node)  # Remove the skipped node from neighbors

            if random.random() < 0.5:  # 50% chance to force backtracking to a previous node
                if len(visited) > 1:  # Can only backtrack if we've already visited at least one node
                    backtrack_node = random.choice(list(visited))
                    neighbors = [backtrack_node]  # Force backtrack to a previously visited node

            random.shuffle(neighbors)  # Shuffle neighbors to introduce randomness in traversal order

        # Explore all neighbors
        for neighbor in neighbors:
            if neighbor not in visited:
                dfs_edges.append((node, neighbor))  # Record the edge visited
                dfs(neighbor)  # Recur to the neighbor

    # Start DFS traversal from the start_node
    dfs(start_node)

    return dfs_nodes, dfs_edges
def generate_frames_dijkstra_from_matrix(matrix, start_node, show_steps, show_weights, directed, error_chance, size="5,5"):
    # Generate graph from matrix
    if isinstance(matrix, np.ndarray):
        if directed == "True":
            G = nx.from_numpy_array(matrix, create_using=nx.DiGraph())
        else:
            G = nx.from_numpy_array(matrix)
    else:
        G = matrix

    # Set error chance probability
    error_chance_prob = 1.0 if error_chance == "True" else 0.0

    # Initialize AGraph object for visualization
    A = nx.nx_agraph.to_agraph(G)

    # Run Dijkstra's algorithm to get shortest paths and predecessors
    shortest_paths = nx.single_source_dijkstra_path_length(G, start_node)
    predecessors = nx.single_source_dijkstra_path(G, start_node)

    frames = []           # List to store frames
    visited_nodes = set() # Track visited nodes
    visited_edges = set() # Track visited edges

    # Step 0: Add initial frame with no nodes or edges colored
    step_count = 0        # Track step count

    # Loop through each target node in shortest paths
    for target_node in shortest_paths.keys():
        step_count += 1

        A_temp = A.copy()

        # Determine the correct path to the target node
        correct_path = predecessors[target_node]

        # Introduce a traversal error based on `error_chance`
        if random.random() < error_chance_prob:
            # Choose a random wrong path
            wrong_path = random.choice(list(G.nodes))  # Choose random node as an incorrect path
            wrong_path = predecessors.get(wrong_path, correct_path)  # Get some path, which might be incorrect

            # You can introduce an error by manually changing the path like this:
            if len(wrong_path) > 1:
                wrong_path = wrong_path[::-1]  # Reversing path to make it wrong (as an example)

            # Make sure the path is different from the correct path
            path = wrong_path
        else:
            # No error, use the correct path
            path = correct_path

        visited_nodes.update(path)

        # Color nodes and edges in path up to the current target
        for node in visited_nodes:
            A_temp.get_node(node).attr['color'] = 'red'
            A_temp.get_node(node).attr['style'] = 'filled'
            A_temp.get_node(node).attr['fillcolor'] = 'red'

        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            visited_edges.add(edge)
            A_temp.get_edge(edge[0], edge[1]).attr['color'] = 'blue'
            A_temp.get_edge(edge[0], edge[1]).attr['penwidth'] = 2.5

        # Set graph attributes for steps and weights
        if show_steps == "True":
            A_temp.graph_attr['label'] = f"Shortest Route to Node: {target_node}"
            A_temp.graph_attr['labelloc'] = 'top'

        if show_weights == "True":
            for u, v, data in G.edges(data=True):
                weight = data.get('weight', 1.0)
                A_temp.get_edge(u, v).attr['label'] = str(weight)

        # Set image size and DPI
        A_temp.graph_attr['size'] = size
        A_temp.graph_attr['dpi'] = "300"

        # Generate image and save temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        A_temp.draw(temp_file.name, format="png", prog="dot")
        frames.append(temp_file.name)

    return frames

"""THIS SECTION CONTAINS THE FUNCTIONS TO CREATE A VIDEO FROM A DICTIOANRY OF DOTTY COMMANDS"""
def create_graph_frame_dotty(dot_commands_dict,size="5,5"):
    frames = []
    
    # Loop over the dictionary of DOT commands
    for step, dot_command in dot_commands_dict.items():
        # Create a Pygraphviz AGraph object from the DOT command string
        A = pgv.AGraph(string=dot_command)
        A.graph_attr['size'] = size  
        A.graph_attr['dpi'] = "300"          
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        image_path = temp_file.name
        A.draw(image_path, format="png", prog="dot")  
        frames.append(image_path)
    return frames 



# Function to combine frames into a video
def create_video_from_frames(frames, output_file, frame_duration):
    clips = [mpy.ImageClip(f).set_duration(frame_duration) for f in frames]
    video = mpy.concatenate_videoclips(clips, method="compose")
    
    # Suppress console output by setting verbose=False
    video.write_videofile(output_file, fps=24, verbose=False, logger=None)
def create_weighted_graph(matrix):
    G = nx.Graph()  # Using undirected graph; change to nx.DiGraph() for directed
    size = matrix.shape[0]
    for i in range(size):
        for j in range(size):
            weight = matrix[i][j]
            if weight != 0 and weight != 100:  # Ignore self-loops and large values (representing infinity)
                G.add_edge(chr(65 + i), chr(65 + j), weight=weight)  # Use chr(65 + i) to convert to A, B, C, D, E
    return G

def render(element_html: str, data: pl.QuestionData) -> str:
    # Parse the input parameters
    element = lxml.html.fragment_fromstring(element_html)
    input_param_name = pl.get_string_attrib(element, "params-name")
    input_type = pl.get_string_attrib(element, "params-type", PARAMS_TYPE_DEFAULT)
    algorithm = pl.get_string_attrib(element, "algorithm", ALGORITHM_DEFAULT).lower()  # Select algorithm (dfs/bfs)
    frame_duration = float(pl.get_string_attrib(element, "frame-duration", DURATION_FRAME_DEFAULT))
    show_steps = pl.get_string_attrib(element, "show-steps", SHOW_STEPS_DEFAULT)
    show_weights = pl.get_string_attrib(element, "show-weights", SHOW_WEIGHTS_DEFAULT)
    directed_graph=pl.get_string_attrib(element, "directed-graph", DIRECTED_DEFAULT)
    error_chance=pl.get_string_attrib(element, "error-chance", ERROR_CHANCE_DEFAULT)
    # Create video for input type adjacency-matrix
    if input_type==PARAMS_TYPE_DEFAULT:
        matrix = np.array(pl.from_json(data["params"][input_param_name]))
        

        start_node = 0  # Assuming traversal starts at node 0
        if algorithm == "dfs":
            #G = nx.from_numpy_array(matrix, create_using=nx.DiGraph() if pl.get_boolean_attrib(element, "directed", DIRECTED_DEFAULT) else nx.Graph())
            #G = create_weighted_graph(matrix)
            #frames = generate_frames_dfs(G, start_node,show_steps,show_weights)
            frames=generate_frames_dfs_from_matrix(matrix, start_node,show_steps,show_weights,directed_graph,error_chance)
        elif algorithm == "bfs":
            #G = nx.from_numpy_array(matrix, create_using=nx.DiGraph() if pl.get_boolean_attrib(element, "directed", DIRECTED_DEFAULT) else nx.Graph())
            #frames = generate_frames_bfs(G, start_node,show_steps,show_weights)
            frames=generate_frames_bfs_from_matrix(matrix, start_node,show_steps,show_weights,directed_graph,error_chance)
        elif algorithm == "dijkstra":
            #G = nx.from_numpy_array(matrix, create_using=nx.DiGraph() if pl.get_boolean_attrib(element, "directed", DIRECTED_DEFAULT) else nx.Graph())
            #frames = generate_frames_bfs(G, start_node,show_steps,show_weights)
            frames=generate_frames_dijkstra_from_matrix(matrix, start_node,show_steps,show_weights,directed_graph,error_chance)

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    
    # Create video for input type dotty
    elif input_type=="dotty":
        dot_commands_dict = pl.from_json(data["params"][input_param_name])
        frames = create_graph_frame_dotty(dot_commands_dict)
        output_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    
    
    
    
    # Save the video to a temporary file
    output_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    create_video_from_frames(frames, output_file, frame_duration)

    # Read the video file and encode it in base64
    with open(output_file, "rb") as video_file:
        video_base64 = base64.b64encode(video_file.read()).decode('utf-8')

    
    return f'<video controls  width="100" height="100"><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video>'
