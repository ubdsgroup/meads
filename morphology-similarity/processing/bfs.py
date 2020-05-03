"""
Conatins implementation of BFS graph vectorization algorithm
"""
import processing 
from skimage.future import graph
import numpy as np

def generate_region_adjacency_graph(image):
    """
    Create a region adjacency graph from a given image
    Args:
        image (ndarray): grayscale image
    Return:
        rag (RAG): region adjacency graph
    """
    # identify neighbouring pixels with the same pixel value, assign 
    # them labels and split them.
    components, binary_image,label_image = \
            processing.extract_components(
                image,
                allow_blank_images=True,
                return_images=True)
    
    # make sure number of components = number of unique labels
    # make sure no component is being pruned
    assert len(components) == len(np.unique(label_image)), \
        "Total components != Total labels"

    # generate the Region Adjacency Graph
    rag = graph.rag_mean_color(binary_image, label_image)

    # calculate the signature of each component
    sigs = []
    for component in components:
        sig = processing.apply_signatures(
            component,
            "surface_volume_ratio_sig",
            allow_empty_sig=True)
        sigs.append(sig[0])

    # make sure number of signatures = number of components
    # Ensure no sig value is getting pruned
    assert len(components) == len(sigs), \
        "Total signatures != Total components"

    # add signatures as node weights
    for idx, sig in enumerate(sigs):
        rag.nodes[idx+1] ['weight'] = sig

        # remove unwanted data in the nodes
        del rag.nodes[idx+1] ['total color'] 

    # remove edge weights since they are not required
    for edge in rag.edges:
        node_1, node_2 = edge
        del rag[node_1][node_2]['weight'] 

    return rag



def get_max_degree_node(graph):
    """
    Determine the node with the maximum degree irrespective of its color

    Args:
        graph (networkx.Graph): 
            The input graph to use.
    Returns:
        max_degree_node (int): 
            index of the node with the maximum degree 
    """

    nodes = list(graph.nodes(data=True))
    max_degree_node = nodes[0][0]

    # Iterate over the nodes and find the most connected node
    for node in nodes:
        if graph.degree[node[0]] > graph.degree[max_degree_node]:
            max_degree_node = node[0]
        elif graph.degree[node[0]] == graph.degree[max_degree_node]:
            # settle a tie by choosing the node with greater area
            if node[1]['pixel count'] > \
                graph.nodes(data=True)[max_degree_node]['pixel count']:
                max_degree_node = node[0]

    return max_degree_node




def get_node_color_sign(node_color):
    """
    Returns -1 for black color (node_color = 0) and 
    1 for white (node_color = 1 or 255)

    Args:
        node_color (int): 
            node color value should be 0, 1 or 255
    
    Returns:
        sign (int): -1 or 1 based in pixel value

    Raises:
        AssertionError: 
            node_color needs to be either black or white.
    """
    assert node_color in [0,1,255], "node_color can only be 0, 1 or 255"

    if node_color < 2:
        # when node color value is 0 or 1
        return -1 ** (node_color+1)
    else:
        # 255 is always white
        return 1
        



def priority_bfs(graph, root, return_traversal_order=False):
    """
    Implementation of the priority BFS algorithm

    Args:
        graph (networkx.Graph): 
            The input graph to use.
        root (int):
            index of the node to be considered as the root
        return_traversal_order (bool): 
            Whether to return traversal order of the nodes.
            (default=False)

    Returns:
        vector (list): 
            vector representation of the graph
        traversal_order (list): 
            A list containing the indices of the nodes in the order they
            were traversed. Only returned when return_traversal_order is
            True.

        
    """
    vector  = []
    visited = []
    queue   = []

    visited.append(root)
    # Queue element storage format 
    # [ (<node>, <node_signature>) , (<node>, <node_signature>), ... ]
    queue.append((root,graph.nodes[root]['weight']))

    while queue:

        # Step A: Dequeue it to the vector
        current_node_index, current_node_signature = queue.pop(0)
        current_node_color = graph.nodes[current_node_index]['mean color'][0]
        visited.append(current_node_index)


        # Step B: Append it to the vector
        vector.append(get_node_color_sign(current_node_color) *
                      current_node_signature)


        # Step C: Get all of elements children
        current_node_neighbors = []
        for neighbor in graph.neighbors(current_node_index):
            current_node_neighbors.append(
                (neighbor, graph.nodes[neighbor]['weight']))


        # Step D: Sort them by their signature and enqueue them
        current_node_neighbors.sort(key = lambda x: x[1])
        # enqueueing - make sure that node has not been visited first
        # althugh that should not happen since the graph is always
        # acyclic
        for neighbor in current_node_neighbors:
            if neighbor[0] not in visited:
                queue.append(neighbor)

    vector = np.array(vector)

    if return_traversal_order:
        return vector, visited
    else:
        return vector




def generate_bfs_vector(graph, return_traversal_order=False):
    """
    Vecotorize a given graph using the priority BFS algorithm
    
    Args:
        graph (networkx.Graph): 
            The input graph to use
        return_traversal_order (bool): 
            Whether to return traversal order of the nodes.
            (default=False)

    Returns:
        vector (list): 
            vector representation of the graph
        traversal_order (list): 
            A list containing the indices of the nodes in the order they
            were traversed. Only returned when return_traversal_order is
            True.
    """
    # determine the root node
    root = get_max_degree_node(graph)

    # generate BFS vector
    return priority_bfs(
        graph, 
        root,
        return_traversal_order=return_traversal_order)