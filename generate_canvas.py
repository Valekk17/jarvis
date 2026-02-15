import re
import json
import os

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"

def parse_graph():
    nodes = []
    links = []
    
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": [], "links": []}
    
    with open(GRAPH_FILE) as f:
        content = f.read()
    
    current_section = None
    
    # Pre-add key actors to ensure they exist
    nodes.append({"id": "Valekk_17", "group": "owner", "radius": 20})
    nodes.append({"id": "JARVIS", "group": "system", "radius": 15})
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('## '):
            current_section = line[3:].strip().lower() # actors, promises, etc.
            continue
        
        if not line.startswith('- '):
            continue
            
        # Parse based on section
        if current_section == 'actors':
            # - **Name** | Role: role | ...
            m = re.match(r'- \*\*(.+?)\*\* \| Role: (.+?) (\||$)', line)
            if m:
                name = m.group(1)
                role = m.group(2).replace('|', '').strip()
                if not any(n['id'] == name for n in nodes):
                    nodes.append({"id": name, "group": "actor", "role": role, "radius": 15})
                
                # Relations
                if "Relations:" in line:
                    rel_part = line.split("Relations:")[1].split("|")[0].strip()
                    # e.g. "Brother of Valekk_17"
                    # Try to find target
                    for target in ["Valekk_17", "Arisha", "Alexey Kosenko"]:
                        if target in rel_part:
                            links.append({"source": name, "target": target, "value": 2, "type": "relation"})
        
        elif current_section in ['promises', 'plans', 'decisions', 'metrics']:
            # - [status] Content | ...
            # Clean md
            clean = line[2:] # remove '- '
            
            # Extract content
            if current_section == 'metrics':
                # - **Name**: Value Unit | ...
                m = re.match(r'\*\*(.+?)\*\*: (.+?) \|', clean)
                if m:
                    label = f"{m.group(1)}: {m.group(2)}"
                    nodes.append({"id": label, "group": "metric", "radius": 8})
                    links.append({"source": "Valekk_17", "target": label, "value": 1})
            else:
                # - [status] Content | ... OR - Content | ...
                content_part = clean.split('|')[0].strip()
                # Remove [status] if present
                content_text = re.sub(r'^\[.*?\] ', '', content_part)
                content_text = content_text.replace('**', '')
                
                # Truncate
                short_text = content_text[:30] + "..." if len(content_text) > 30 else content_text
                
                nodes.append({"id": short_text, "group": current_section[:-1], "full": content_text, "radius": 10})
                
                # Try to find actor link
                if "From: actor-owner" in line or "From: Valekk" in line:
                    links.append({"source": "Valekk_17", "target": short_text, "value": 1})
                elif "From: actor-arisha" in line:
                    links.append({"source": "Arisha", "target": short_text, "value": 1})
                else:
                    # Link to owner default
                    links.append({"source": "Valekk_17", "target": short_text, "value": 1})

    return {"nodes": nodes, "links": links}

data = parse_graph()

html = f"""
<!DOCTYPE html>
<style>
body {{ margin: 0; background: #111; color: #eee; font-family: sans-serif; overflow: hidden; }}
#graph {{ width: 100vw; height: 100vh; }}
.tooltip {{ position: absolute; background: #333; padding: 5px; border-radius: 4px; pointer-events: none; opacity: 0; transition: 0.2s; }}
</style>
<div id="graph"></div>
<div class="tooltip"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {json.dumps(data)};
const width = window.innerWidth;
const height = window.innerHeight;

const color = d3.scaleOrdinal()
    .domain(["owner", "system", "actor", "promise", "plan", "decision", "metric"])
    .range(["#ff4444", "#4444ff", "#44ff44", "#ffff44", "#44ffff", "#ff44ff", "#888888"]);

const svg = d3.select("#graph").append("svg")
    .attr("width", width)
    .attr("height", height)
    .call(d3.zoom().on("zoom", (event) => g.attr("transform", event.transform)))
    .append("g");

const g = svg.append("g");

const simulation = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(d => d.radius + 5));

const link = g.append("g")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(data.links)
    .join("line");

const node = g.append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(data.nodes)
    .join("circle")
    .attr("r", d => d.radius)
    .attr("fill", d => color(d.group))
    .call(drag(simulation));

node.append("title").text(d => d.full || d.id);

const label = g.append("g")
    .selectAll("text")
    .data(data.nodes)
    .join("text")
    .attr("dx", 12)
    .attr("dy", 4)
    .text(d => d.id)
    .attr("fill", "#ddd")
    .style("font-size", "10px")
    .style("pointer-events", "none");

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
