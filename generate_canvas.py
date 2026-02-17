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
            # Line format: - [status] Content | Key: Value | ...
            # Clean start
            clean = line[2:] # remove '- '
            
            parts = clean.split('|')
            content_part = parts[0].strip()
            
            # Remove [status] from content
            content_text = re.sub(r'^\[.*?\] ', '', content_part).replace('**', '').strip()
            
            if current_section == 'metrics':
                 # Special case: **Name**: Value Unit
                 if ':' in content_text:
                     content_text = content_text # Keep Name: Value
            
            # Clean content for display (strip metadata from full text)
            display_text = content_text.split('|')[0].strip()
            short_text = display_text[:30] + "..." if len(display_text) > 30 else display_text
            
            nodes.append({"id": short_text, "group": current_section[:-1], "full": display_text, "radius": 10})
            
            # Parse attributes
            attrs = {}
            for p in parts[1:]:
                if ':' in p:
                    k, v = p.split(':', 1)
                    attrs[k.strip()] = v.strip()
            
            # Link logic
            # 1. Explicit From -> To
            if 'From' in attrs and '->' in attrs['From']:
                 src, tgt = attrs['From'].split('->')
                 # Clean "Name (ID: ...)" -> "Name"
                 src = re.sub(r' \(ID: .*?\)', '', src).strip()
                 tgt = re.sub(r' \(ID: .*?\)', '', tgt).strip()
                 
                 links.append({"source": src, "target": short_text, "value": 1})
            
            # 2. Actor field
            elif 'Actor' in attrs:
                actor = attrs['Actor']
                actor = re.sub(r' \(ID: .*?\)', '', actor).strip()
                links.append({"source": actor, "target": short_text, "value": 1})
            
            # 3. Fallback to old hardcoded logic if no attrs found (for old entries)
            else:
                if "actor-owner" in line or "Valekk" in line:
                    links.append({"source": "Valekk_17", "target": short_text, "value": 1})
                elif "actor-arisha" in line or "Arisha" in line:
                    links.append({"source": "Arisha", "target": short_text, "value": 1})

    # Ensure all link sources/targets exist as nodes
    node_ids = {n['id'] for n in nodes}
    for l in links:
        src = l['source']
        if src not in node_ids:
            nodes.append({"id": src, "group": "actor", "radius": 15})
            node_ids.add(src)
        tgt = l['target']
        if tgt not in node_ids:
             # Should be rare as target is usually the node we just created
             pass

    # ORPHAN CONTROL: Link everything to Valekk_17 if not linked
    linked_nodes = set()
    for l in links:
        linked_nodes.add(l['source'])
        linked_nodes.add(l['target'])
    
    for n in nodes:
        if n['id'] != "Valekk_17" and n['id'] not in linked_nodes:
            # Default link
            links.append({"source": "Valekk_17", "target": n['id'], "value": 1, "type": "owns"})

    # Hardcoded Family Links (Ensure existence)
    # Family Node
    if not any(n['id'] == "Family" for n in nodes):
        nodes.append({"id": "Family", "group": "actor", "radius": 15})
    
    links.append({"source": "Family", "target": "Valekk_17", "value": 3, "type": "member"})
    links.append({"source": "Family", "target": "Arisha", "value": 3, "type": "member"})

    # Valekk <-> Arisha
    links.append({"source": "Valekk_17", "target": "Arisha", "value": 5, "type": "spouse"})
    # Valekk <-> Andrey
    links.append({"source": "Valekk_17", "target": "Andrey Kovalkov", "value": 3, "type": "brother"})
    # Valekk <-> Evgeniya
    links.append({"source": "Valekk_17", "target": "Evgeniya Kovalkova", "value": 3, "type": "mother"})
    # Valekk <-> Alexey
    links.append({"source": "Valekk_17", "target": "Alexey Kosenko", "value": 3, "type": "friend"})
    # Valekk <-> JARVIS
    links.append({"source": "Valekk_17", "target": "JARVIS", "value": 3, "type": "assistant"})

    # Link Pregnancy to Family
    for n in nodes:
        if "pregnancy" in n['id'].lower() or "беременность" in n['id'].lower():
            links.append({"source": "Family", "target": n['id'], "value": 2, "type": "shared"})

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
        .attr("fill", d => {{
            // Systems
            if (d.group === "system" || d.id === "JARVIS" || d.id === "cybos") return "#4444ff";
            // Humans (Family, Friends, Owner)
            if (d.group === "owner" || d.group === "actor" || d.id === "Family") return "#ff4444";
            // Tasks/Promises
            if (d.group === "plan") return "#44ffff";
            if (d.group === "promise") return "#ffff44";
            return color(d.group);
        }})
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

const edgeLabel = g.append("g")
    .selectAll("text")
    .data(data.links)
    .join("text")
    .attr("dy", -5)
    .text(d => d.type || "")
    .attr("fill", "#666")
    .style("font-size", "8px")
    .style("pointer-events", "none");

simulation.on("tick", () => {{
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    edgeLabel
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);

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
