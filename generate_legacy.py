import os
import re
import json

LEGACY_DIR = "legacy_data"

def parse_legacy():
    nodes = []
    links = []
    
    # Actors
    actors_map = {} # id -> canonical
    if os.path.exists(f"{LEGACY_DIR}/actors.md"):
        with open(f"{LEGACY_DIR}/actors.md") as f:
            content = f.read()
            # Split by ##
            blocks = content.split("## ")
            for b in blocks[1:]:
                lines = b.strip().split('\n')
                aid = lines[0].strip() # actor-andrey
                props = {}
                for l in lines[1:]:
                    if l.startswith('- '):
                        if ':' in l:
                            k, v = l[2:].split(':', 1)
                            props[k.strip()] = v.strip()
                
                name = props.get('canonical_name', aid)
                role = props.get('role', 'actor')
                actors_map[aid] = name
                nodes.append({"id": name, "group": "actor", "role": role, "radius": 15})

    # Plans, Promises, etc.
    for kind in ['plans', 'promises', 'decisions', 'metrics']:
        if not os.path.exists(f"{LEGACY_DIR}/{kind}.md"):
            continue
            
        with open(f"{LEGACY_DIR}/{kind}.md") as f:
            content = f.read()
            blocks = content.split("## ")
            for b in blocks[1:]:
                lines = b.strip().split('\n')
                props = {}
                for l in lines[1:]:
                    if l.startswith('- '):
                        if ':' in l:
                            k, v = l[2:].split(':', 1)
                            props[k.strip()] = v.strip()
                
                content_text = props.get('content') or props.get('name') or "Unknown"
                short = content_text[:30] + "..." if len(content_text)>30 else content_text
                
                nodes.append({"id": short, "group": kind[:-1], "full": content_text, "radius": 10})
                
                # Links
                # If plan has actor_id (implied ownership)
                # Old system didn't always link plans to actors in MD?
                # Let's check props for 'from', 'to', 'actor'
                if 'from_actor' in props:
                    src = actors_map.get(props['from_actor'], props['from_actor'])
                    links.append({"source": src, "target": short, "value": 1})
                if 'to_actor' in props:
                    tgt = actors_map.get(props['to_actor'], props['to_actor'])
                    # If promise, from -> promise -> to?
                    # Visualizer supports simple links.
                    # We link promise to 'to' as well
                    links.append({"source": short, "target": tgt, "value": 1})
                
                # Default link to Valekk if orphan?
                if not 'from_actor' in props and not 'to_actor' in props:
                     links.append({"source": "Valekk_17", "target": short, "value": 1})

    return {"nodes": nodes, "links": links}

data = parse_legacy()

# Reuse HTML template
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
