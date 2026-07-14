"""
Planet Influence Graph: Model chart as a directed graph of relationships.
Enables reasoning about cascading influences and synthesis.
"""

from typing import Any
from collections import defaultdict


class PlanetInfluenceGraph:
    """Models chart as a network of planetary relationships."""

    def __init__(self, chart: dict):
        self.chart = chart
        self.nodes = {}  # planet -> properties
        self.edges = []  # (source, target, relationship_type, weight)
        self._build_graph()

    def _build_graph(self):
        """Build nodes and edges from chart data."""
        planets = self.chart.get("planets", {})
        dasha = self.chart.get("dasha", {})
        house_lords = self.chart.get("house_lords", {})
        yogas = self.chart.get("yogas", [])

        # Create nodes
        for planet, data in planets.items():
            self.nodes[planet] = {
                "sign": data.get("sign"),
                "house": data.get("house"),
                "nakshatra": data.get("nakshatra"),
                "dignity": data.get("dignity"),
                "strength": self.chart.get("analysis", {})
                    .get("planet_strength_ranking", {})
                    .get(planet, {})
                    .get("strength", 50),
            }

        # Create edges: conjunctions (same house)
        planet_list = list(planets.keys())
        for i, p1 in enumerate(planet_list):
            for p2 in planet_list[i + 1 :]:
                if planets[p1]["house"] == planets[p2]["house"]:
                    self._add_edge(p1, p2, "conjunct", weight=25)

        # Create edges: aspects
        for planet, data in planets.items():
            for aspected_house in data.get("aspects", []):
                for other, other_data in planets.items():
                    if other != planet and other_data["house"] == aspected_house:
                        self._add_edge(planet, other, "aspects", weight=15)

        # Create edges: rulership
        for house_num, lord_info in house_lords.items():
            lord = lord_info["planet"]
            placed_in = lord_info["placed_in_house"]
            # Lord of house → placement house
            self._add_edge(
                lord, f"House{house_num}", f"rules_{house_num}", weight=20
            )

        # Create edges: dasha activation
        if dasha.get("mahadasha"):
            maha_lord = dasha["mahadasha"]
            for planet in planets.keys():
                if planet == maha_lord:
                    self._add_edge("TIME", maha_lord, "mahadasha_active", weight=30)
                elif planet == dasha.get("antardasha"):
                    self._add_edge("TIME", planet, "antardasha_active", weight=20)

        # Create edges: yoga relationships
        for yoga in yogas:
            yoga_planets = yoga.get("planets", [])
            if len(yoga_planets) >= 2:
                for i, p1 in enumerate(yoga_planets):
                    for p2 in yoga_planets[i + 1 :]:
                        self._add_edge(p1, p2, f"yoga_{yoga['name']}", weight=22)

    def _add_edge(self, source: str, target: str, rel_type: str, weight: float):
        """Add directed edge (can be bidirectional in representation)."""
        self.edges.append({
            "source": source,
            "target": target,
            "type": rel_type,
            "weight": weight,
        })

    def get_neighbors(self, planet: str) -> list[dict]:
        """Return all planets connected to a given planet."""
        neighbors = []
        for edge in self.edges:
            if edge["source"] == planet:
                neighbors.append({
                    "planet": edge["target"],
                    "relationship": edge["type"],
                    "weight": edge["weight"],
                })
            elif edge["target"] == planet:
                neighbors.append({
                    "planet": edge["source"],
                    "relationship": f"←{edge['type']}",
                    "weight": edge["weight"],
                })
        return sorted(neighbors, key=lambda x: x["weight"], reverse=True)

    def get_subgraph(self, center_planet: str, depth: int = 2) -> dict:
        """Get subgraph centered on a planet with given depth."""
        visited = set()
        nodes = {center_planet: self.nodes.get(center_planet, {})}
        edges = []

        def traverse(planet, d):
            if d == 0 or planet in visited:
                return
            visited.add(planet)
            for neighbor in self.get_neighbors(planet):
                n_planet = neighbor["planet"]
                if n_planet not in nodes:
                    nodes[n_planet] = self.nodes.get(n_planet, {})
                edges.append({
                    "source": planet,
                    "target": n_planet,
                    "type": neighbor["relationship"],
                    "weight": neighbor["weight"],
                })
                traverse(n_planet, d - 1)

        traverse(center_planet, depth)
        return {"nodes": nodes, "edges": edges, "center": center_planet}

    def get_influence_paths(self, source: str, target: str, max_depth: int = 3) -> list[list[str]]:
        """Find all paths of influence from source to target planet."""
        paths = []

        def dfs(current, goal, path, depth):
            if depth == 0:
                return
            if current == goal:
                paths.append(path + [current])
                return
            for neighbor in self.get_neighbors(current):
                n_planet = neighbor["planet"]
                if n_planet not in path:
                    dfs(n_planet, goal, path + [current], depth - 1)

        dfs(source, target, [], max_depth)
        return paths

    def to_dict(self) -> dict:
        """Export graph as serializable dict."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
        }


def build_graph_visualization(chart: dict) -> dict:
    """
    Create a visualization-ready graph with positions and styling.
    """
    graph = PlanetInfluenceGraph(chart)
    nodes_dict = graph.nodes
    edges_list = graph.edges

    # Assign positions using a simple circular layout
    import math
    planet_list = list(nodes_dict.keys())
    n = len(planet_list)
    positioned_nodes = {}

    for i, planet in enumerate(planet_list):
        angle = (2 * math.pi * i) / n
        x = 100 * math.cos(angle)
        y = 100 * math.sin(angle)
        positioned_nodes[planet] = {
            **nodes_dict[planet],
            "x": x,
            "y": y,
            "id": planet,
            "label": planet,
        }

    return {
        "nodes": list(positioned_nodes.values()),
        "edges": edges_list,
    }
