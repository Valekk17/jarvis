import json
import os

JSON_FILE = "/root/.openclaw/workspace/_archive/system_b/knowledge_graph.json"

def parse_system_b():
    if not os.path.exists(JSON_FILE):
        return {"nodes": [], "links": []}
    
    with open(JSON_FILE) as f:
        data = json.load(f)
    
    # Extract nodes
    nodes = []
    # Map id to index or keep id? D3 forceLink needs id.
    # The JSON uses integer IDs.
    
    for n in data.get("nodes", []):
        # Flatten
        # D3 expects 'id', 'group'.
        # n already has id, name, group.
        # Add radius based on group
        group = n.get("group", "Node")
        radius = 10
        if group == "Actor": radius = 15
        if group == "Skill": radius = 8
        
        nodes.append({
            "id": n["id"], # integer
            "label": n.get("name", "Unknown"), # for display
            "group": group,
            "radius": radius,
            "full": n.get("context") or n.get("source_quote") or n.get("name")
        })

    # Extract edges -> links
    links = []
    for e in data.get("edges", []):
        links.append({
            "source": e["source"],
            "target": e["target"],
            "value": 1,
            "type": e.get("relation", "LINK")
        })
        
    return {"nodes": nodes, "links": links}

data = parse_system_b()

html = f"""
<!DOCTYPE html>
<style>
body {{ margin: 0; background: #111; color: #eee; font-family: sans-serif; overflow: hidden; }}
#graph {{ width: 100vw; height: 100vh; }}
</style>
<div id="graph"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {json.dumps(data)};
const width = window.innerWidth;
const height = window.innerHeight;

const color = d3.scaleOrdinal()
    .domain(["Actor", "Promise", "Plan", "Decision", "Metric", "Skill", "Person"])
    .range(["#44ff44", "#ffff44", "#44ffff", "#ff44ff", "#888888", "#aaaaaa", "#ff4444"]);

const svg = d3.select("#graph").append("svg")
    .attr("width", width)
    .attr("height", height)
    .call(d3.zoom().on("zoom", (event) => g.attr("transform", event.transform)))
    .append("g");

const g = svg.append("g");

// Arrow marker
svg.append("defs").selectAll("marker")
    .data(["end"])
    .enter().append("marker")
    .attr("id", String)
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 25)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999");

const simulation = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(120))
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(d => d.radius + 10));

const link = g.append("g")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(data.links)
    .join("line")
    .attr("marker-end", "url(#end)");

const node = g.append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(data.nodes)
    .join("circle")
    .attr("r", d => d.radius)
    .attr("fill", d => color(d.group))
    .call(drag(simulation));

node.append("title").text(d => d.full || d.label);

const label = g.append("g")
    .selectAll("text")
    .data(data.nodes)
    .join("text")
    .attr("dx", 15)
    .attr("dy", 4)
    .text(d => d.label)
    .attr("fill", "#ddd")
    .style("font-size", "12px")
    .style("pointer-events", "none");

// Edge labels
const edgeLabel = g.append("g")
    .selectAll("text")
    .data(data.links)
    .join("text")
    .text(d => d.type)
    .attr("fill", "#666")
    .style("font-size", "8px");

simulation.on("tick", () => {{
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
        
    label
        .attr("x", d => d.x)
        .attr("y", d => d.y);
        
    edgeLabel
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);
}});

function drag(simulation) {{
  function dragstarted(event) {{
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }}
  
  function dragged(event) {{
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }}
  
  function dragended(event) {{
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }}
  
  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}}
</script>
"""
print(html)
