# XML Variable Extractor and Relationship Network Illustrator - XMLVERNIv1
# Developed by Partha Pratim Ray, ALl Copyright Reserved 2024
# GitHub | Contact: parthapratimray1986@gmail.com
# Available for commercial license. 
# Unauthorized use of this software without permission is a punishable offence.
# app.py

import xml.etree.ElementTree as ET
from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
from Levenshtein import distance as levenshtein_distance
from pyvis.network import Network
import networkx as nx
import os
import webbrowser
import gradio as gr

# Default sample XML file content
DEFAULT_XML = """<?xml version="1.0"?>
<root>
    <variable name="alpha_var1">Value 1</variable>
    <variable name="alpha_var2">Value 2</variable>
    <variable name="alpha_variable">Value 3</variable>
    <variable name="beta_var1">Data A</variable>
    <variable name="beta_var2">Data B</variable>
    <variable name="gamma_val1">Output X</variable>
    <variable name="gamma_value">Output Y</variable>
    <variable name="gamma_output">Output Z</variable>
    <variable name="delta_var1">Config 1</variable>
    <variable name="delta_var2">Config 2</variable>
    <variable name="unrelated_var1">Random Data 1</variable>
    <variable name="unrelated_var2">Random Data 2</variable>
    <variable name="independent_value">Unique Value</variable>
    <variable name="standalone_var">Standalone</variable>
    <variable name="epsilon_variable">Extra Data</variable>
    <variable name="theta_data">Theta Information</variable>
    <variable name="zeta_config">Zeta Config</variable>
</root>
"""

# Save the default XML file
with open("example.xml", "w") as f:
    f.write(DEFAULT_XML)

# Function to parse XML
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    variables = []
    for elem in root.iter():
        if elem.text and elem.text.strip():
            variables.append(elem.text.strip())
        for attr_value in elem.attrib.values():
            variables.append(attr_value.strip())
    return variables

# Function for Jaccard similarity
def jaccard_similarity_method(variables, threshold=0.5):
    def jaccard_similarity(str1, str2):
        set1, set2 = set(str1), set(str2)
        return len(set1 & set2) / len(set1 | set2)

    similar_pairs = []
    similarity_scores = []
    for var1, var2 in combinations(variables, 2):
        score = jaccard_similarity(var1, var2)
        if score > threshold:
            similar_pairs.append((var1, var2))
            similarity_scores.append(score)
    return similar_pairs, similarity_scores

# Function for Levenshtein similarity
def levenshtein_similarity_method(variables, max_distance=3):
    similar_pairs = []
    similarity_scores = []
    for var1, var2 in combinations(variables, 2):
        dist = levenshtein_distance(var1, var2)
        if dist <= max_distance:
            similar_pairs.append((var1, var2))
            similarity_scores.append(1 / (1 + dist))  # Normalize score
    return similar_pairs, similarity_scores

# Function for cosine similarity
def cosine_similarity_method(variables, threshold=0.6):
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    tfidf_matrix = vectorizer.fit_transform(variables)
    similarity_matrix = cosine_similarity(tfidf_matrix)

    similar_pairs = []
    similarity_scores = []
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            if similarity_matrix[i][j] > threshold:
                similar_pairs.append((variables[i], variables[j]))
                similarity_scores.append(similarity_matrix[i][j])
    return similar_pairs, similarity_scores

# Function for semantic similarity
def semantic_similarity_method(variables, threshold=0.7):
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    embeddings = model.encode(variables, convert_to_tensor=True)
    similarity_matrix = util.cos_sim(embeddings, embeddings)

    similar_pairs = []
    similarity_scores = []
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            if similarity_matrix[i][j] > threshold:
                similar_pairs.append((variables[i], variables[j]))
                similarity_scores.append(similarity_matrix[i][j].item())
    return similar_pairs, similarity_scores

# Visualization function
def visualize_interactive(similar_pairs, similarity_scores):
    G = nx.Graph()

    for i, (var1, var2) in enumerate(similar_pairs):
        G.add_edge(var1, var2, weight=similarity_scores[i])

    communities = list(nx.community.greedy_modularity_communities(G))
    net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black", notebook=False)
    cluster_colors = ["#%06X" % (i * 100000 % 0xFFFFFF) for i in range(len(communities))]

    for idx, community in enumerate(communities):
        color = cluster_colors[idx]
        for node in community:
            net.add_node(node, label=node, color=color, title=f"Variable: {node}")

    for i, (var1, var2) in enumerate(similar_pairs):
        score = f"Similarity: {similarity_scores[i]:.2f}"
        net.add_edge(var1, var2, value=similarity_scores[i], title=score)

    file_name = "interactive_network.html"
    net.save_graph(file_name)
    webbrowser.open(f"file://{os.path.abspath(file_name)}")

# Slider updater
def update_slider(technique):
    if technique == "Levenshtein Distance":
        return gr.update(value=3, minimum=1, maximum=10, step=1, label="Max Distance")
    elif technique == "Jaccard Similarity":
        return gr.update(value=0.5, minimum=0.0, maximum=1.0, step=0.05, label="Threshold")
    elif technique == "Cosine Similarity":
        return gr.update(value=0.6, minimum=0.0, maximum=1.0, step=0.05, label="Threshold")
    elif technique == "Semantic Similarity":
        return gr.update(value=0.7, minimum=0.0, maximum=1.0, step=0.05, label="Threshold")

# Processing function
def process_input(file, technique, threshold):
    variables = parse_xml(file.name)
    if technique == "Jaccard Similarity":
        similar_pairs, similarity_scores = jaccard_similarity_method(variables, threshold)
    elif technique == "Levenshtein Distance":
        similar_pairs, similarity_scores = levenshtein_similarity_method(variables, int(threshold))
    elif technique == "Cosine Similarity":
        similar_pairs, similarity_scores = cosine_similarity_method(variables, threshold)
    elif technique == "Semantic Similarity":
        similar_pairs, similarity_scores = semantic_similarity_method(variables, threshold)
    visualize_interactive(similar_pairs, similarity_scores)
    return variables, similar_pairs

# Gradio Interface
def gradio_interface(file, technique, threshold):
    if file is None:
        file = open("example.xml", "r")
    variables, similar_pairs = process_input(file, technique, threshold)
    return variables, similar_pairs

# Define Gradio components
techniques = ["Cosine Similarity", "Semantic Similarity", "Jaccard Similarity", "Levenshtein Distance"]

with gr.Blocks() as demo:
    gr.Markdown(
        """
        # XML Variable Extractor and Relationship Network Illustrator - XMLVERNIv1
        ## Developed by Partha Pratim Ray
        [GitHub](https://github.com/ParthaPRay) | Contact: parthapratimray1986@gmail.com
        ### Available for commercial license. Unauthorized use of this software without permission is punishable offence. 
        """
    )
    file = gr.File(label="Upload XML File (or use default 'example.xml')", file_types=[".xml"])
    technique = gr.Radio(techniques, label="Select Technique", value="Cosine Similarity")
    slider = gr.Slider(0.6, 1.0, step=0.05, value=0.6, label="Threshold")

    def update_slider_visibility(selected_technique):
        return update_slider(selected_technique)

    technique.change(fn=update_slider_visibility, inputs=technique, outputs=slider)

    submit = gr.Button("Submit")
    output_vars = gr.Textbox(label="Extracted Variables")
    output_pairs = gr.Textbox(label="Similar Variable Pairs")

    submit.click(
        gradio_interface,
        inputs=[file, technique, slider],
        outputs=[output_vars, output_pairs]
    )

if __name__ == "__main__":
    demo.launch()

