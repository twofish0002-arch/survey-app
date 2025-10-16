from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import requests

# --- Configuration ---
USE_MOCK_DATA = False 
SHEETDB_URL = "https://sheetdb.io/api/v1/7fida3dgawvel"

app = Flask(__name__)

# ==============================================================================
# 1. PRESENTATION LAYER (HTML TEMPLATE - with target="_top" fix)
# ==============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Your Archetype Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --accent-color: {{ role_info.color }}; }
        body{font-family:'Inter',sans-serif;background-color:#fff;color:#4a5568;margin:0;padding:24px;box-sizing: border-box;}
        
        .dashboard-grid{ display: grid; grid-template-columns: 1fr 2fr; gap: 24px; width: 100%; max-width: 1600px; margin: 0 auto; }
        .left-column, .right-column{display:flex;flex-direction:column;gap:24px;}
        .card{border: 1px solid #e2e8f0; border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05),0 2px 4px -1px rgba(0,0,0,0.04);padding:24px;position:relative;overflow:hidden;}
        .card-header{font-size:0.85rem;font-weight:600;color:#1a202c;margin-top:0;margin-bottom:16px;border-bottom:1px solid #e2e8f0;padding-bottom:10px; text-transform: uppercase; letter-spacing: 0.5px;}
        .archetype-card{border-top:5px solid var(--accent-color);text-align:center;padding-top:32px;}
        .archetype-card h2{margin:0;font-size:1.8rem;color:#1a202c;}
        .archetype-card p{margin:4px 0 0 0;font-size:1.0rem;color:var(--accent-color);font-weight:600;}
        .pupil-warning { background-color: #fffbeb; border-left: 5px solid #f59e0b; padding: 16px; border-radius: 8px; font-size: 0.95rem; line-height: 1.6; color: #b45309; margin-bottom: 0;}
        .pupil-warning strong { color: #92400e; }
        .kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
        .kpi-card{padding:16px;text-align:center;}
        .kpi-card .value{font-size:1.8rem;font-weight:700;color:#1a202c;line-height:1;}
        .kpi-card .label{font-size:0.65rem;color:#718096;text-transform:uppercase;margin-top:8px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
        .journey-section h4, .validation-card h3 {margin:16px 0 6px 0;font-weight:600;color:#2d3748; font-size:0.9rem;}
        .journey-section p, .validation-card p {margin:0 0 12px 0;line-height:1.6; font-size:0.9rem;}
        .traits-list ul {list-style:none;padding:0;margin:0;}
        .traits-list li {margin-bottom:8px;display:flex;align-items:center;font-weight:500; font-size:0.9rem;}
        .traits-list li::before{content:'\\25CF';color:var(--accent-color);margin-right:10px;font-size:1rem;line-height:1;}
        .qa-list { margin-top: 30px; }
        .qa-list h4{margin:0 0 4px 0;font-size:0.85rem;font-weight:600;}
        .qa-list p {margin:0 0 16px 0;font-style:italic; font-size:0.9rem;}
        .graph-card { height: 600px; padding: 24px 24px 0 24px; display: flex; flex-direction: column; }
        .graph-card #plotly-graph {flex-grow:1; width:100%; height:100%;}
        .slider-control-card { padding: 20px 40px; }
        .html-slider-container { margin-top: 8px; }
        input[type=range] { width: 100%; margin: 7px 0; background-color: transparent; -webkit-appearance: none; }
        input[type=range]:focus { outline: none; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 5px; cursor: pointer; background: #ddd; border-radius: 3px; }
        input[type=range]::-webkit-slider-thumb { box-shadow: 0 1px 3px rgba(0,0,0,0.2); border: 2px solid white; height: 18px; width: 18px; border-radius: 50%; background: var(--accent-color); cursor: pointer; -webkit-appearance: none; margin-top: -6.5px; }
        .slider-labels { display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 500; color: #718096; margin: 0 4px; }
        .metric-slider{display:grid;grid-template-columns:auto 1fr;align-items:center;margin-bottom:10px;gap:8px;}
        .metric-slider .metric-name{font-weight:500;font-size:0.75rem;text-align:left;}
        .metric-slider .track-container{display:flex;align-items:center;flex-grow:1;gap:8px;}
        .metric-slider .label{font-size:0.65rem;color:#666;}
        .metric-slider .track{position:relative;height:3px;flex-grow:1;background-color:#ccc;border-radius:2px;}
        .metric-slider .dot{position:absolute;top:-5px;width:13px;height:13px;background-color:var(--accent-color);border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.2);transition:left 0.3s ease-in-out;}
        .validation-card ul { list-style-position: inside; padding-left: 0; font-size: 0.9rem; }
        .validation-card li { margin-bottom: 8px; }
        .validate-button { display: inline-block; background-color: #007bff; color: #fff; padding: 12px 24px; font-size: 0.9rem; font-weight: 600; text-decoration: none; border-radius: 8px; transition: background-color 0.2s ease; margin-top: 10px; }
        .validate-button:hover { background-color: #0056b3; }
        @media (max-width: 768px) { .dashboard-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="dashboard-grid">
        <div class="left-column">
            <div class="card archetype-card"><h2>{{ role }}</h2><p>{{ role_info.title }}</p><p style="font-size:0.9rem; font-weight:400; color:#718096; margin-top:12px;">User ID: {{ user_id }}</p></div>
            <div class="pupil-warning" id="pupil-warning-message" style="display: {% if k_band == 0 %}block{% else %}none{% endif %};"><strong>Warning:</strong> There is a threat in the environment. All players must do exactly as instructed. Stay with the group.</div>
            <div class="kpi-grid"><div class="card kpi-card"><div class="value">{{ f_score }}</div><div class="label">Freedom</div></div><div class="card kpi-card"><div class="value">{{ s_score }}</div><div class="label">Security</div></div><div class="card kpi-card"><div class="value">{{ r_score }}</div><div class="label">Responsibility</div></div></div>
            <div class="card"><h3 class="card-header">Player Dynamic Characteristics</h3>{% for metric in display_metrics[:3] %}<div class="metric-slider"><div class="metric-name">{{ metric.metric }}</div><div class="track-container"><span class="label">{{ metric.start_label }}</span><div class="track"><div class="dot" id="dot-{{ metric.metric.lower() }}" style="left: calc({{ k_band }} / 5 * 100% - 7.5px);"></div></div><span class="label">{{ metric.end_label }}</span></div></div>{% endfor %}</div>
            <div class="card"><h3 class="card-header">Game Static Characteristics</h3>{% for metric in display_metrics[3:] %}<div class="metric-slider"><div class="metric-name">{{ metric.metric }}</div><div class="track-container"><span class="label">{{ metric.start_label }}</span><div class="track"><div class="dot" id="dot-{{ metric.metric.lower() }}" style="left: calc({{ k_band }} / 5 * 100% - 7.5px);"></div></div><span class="label">{{ metric.end_label }}</span></div></div>{% endfor %}</div>
            <div class="card"><h3 class="card-header">At a Glance</h3><div class="traits-list"><ul>{% for trait in role_info.traits %}<li>{{ trait }}</li>{% endfor %}</ul></div><div class="qa-list">{% for item in role_info.q_and_a %}<h4>{{ item.q }}</h4><p>{{ item.a }}</p>{% endfor %}</div></div>
            <div class="card validation-card">
                <h3>Validate your result: one token, one signal</h3>
                <p>For 1 euro, you validate yourself and everyone who has not yet. Each validation adds your data to a growing dataset, sending a clear signal: it is safe and wise to differentiate beyond “Pupil.” With validation, you also receive the full SI Paper.</p>
                <h3>What the Paper reveals</h3>
                <ul>
                    <li>The reality beyond standardised education.</li>
                    <li>A new language for growth.</li>
                    <li>Why some thrive as Founders while others flourish as Scholars.</li>
                    <li>How the five games are designed and why they feel different.</li>
                    <li>Why Responsibility matters most.</li>
                    <li>Proof: 10 years of practice, thousands of reflections.</li>
                </ul>
                <h3>Privacy</h3>
                <p>Your results are stored anonymously. Only validated results can send a clear signal for change.</p>
                <!-- THIS IS THE ONE-LINE FIX -->
                <a href="https://thequantumfamily.com/store" class="validate-button" target="_top">Validate results &amp; receive the paper →</a>
            </div>
        </div>
        <div class="right-column">
            <div class="card graph-card">{{graph_html|safe}}</div>
            <div class="card slider-control-card"><h3 class="card-header" id="slider-title">Role: {{ role }}</h3><div class="html-slider-container"><input type="range" min="0" max="5" value="{{ k_band }}" id="archetype-slider"><div class="slider-labels">{% for d in cube_definitions %}<span>{{ d.label }}</span>{% endfor %}</div></div></div>
            <div class="card">
                <h3 class="card-header">Your Journey</h3>
                <div class="journey-section"><h4>Start</h4><p>{{role_info.start_text}}</p><h4>Play</h4><p>{{role_info.play_text}}</p><h4>Quest</h4><p>{{role_info.quest_text}}</p><h4>Legacy</h4><p>{{role_info.legacy_text}}</p></div>
            </div>
        </div>
    </div>
    <script>
        const sliderStepsData = {{ slider_steps_json|safe }};
        const metrics = {{ display_metrics|map(attribute='metric')|list|tojson }};
        window.addEventListener('load', function() {
            const graphDiv = document.getElementById('plotly-graph');
            const archetypeSlider = document.getElementById('archetype-slider');
            const sliderTitle = document.getElementById('slider-title');
            const warningMessage = document.getElementById('pupil-warning-message');
            if (!graphDiv || !archetypeSlider || !warningMessage) return;
            archetypeSlider.addEventListener('input', function(event) {
                const kValue = parseInt(event.target.value, 10);
                const stepInfo = sliderStepsData[kValue];
                const visibility = stepInfo.args[0].visible;
                const titleText = stepInfo.args[1]['title.text'];
                const roleName = stepInfo.label;
                Plotly.update(graphDiv, { visible: visibility }, { 'title.text': titleText });
                sliderTitle.innerText = "Role: " + roleName;
                if (kValue === 0) { warningMessage.style.display = 'block'; } else { warningMessage.style.display = 'none'; }
                const newPosition = `calc(${kValue} / 5 * 100% - 7.5px)`;
                metrics.forEach(metric => {
                    const dot = document.getElementById(`dot-${metric.toLowerCase()}`);
                    if (dot) dot.style.left = newPosition;
                });
            });
        });
    </script>
</body>
</html>
"""

# ==============================================================================
# 2. DATA & CONFIGURATION (Full text restored)
# ==============================================================================
# All the full text dictionaries and python logic follow here, unchanged...
# The rest of the file is identical to the last one I sent. I am including it
# here so you have a single file to copy and paste for deployment.
role_details = { "Pupil": { "game_name": "Standardised Game", "color": "#8d99ae", "title": "A Classroom Leader", "start_text": "You are the Pupil...", "play_text": "...", "quest_text": "...", "legacy_text": "...", "traits": ["Follows rules", "Seeks approval", "Dislikes mistakes", "Likes clear steps", "Waits for instructions"], "q_and_a": [ {"q": "What excites you?", "a": "Doing the task exactly right and getting approval."}]}, "Scholar": { "game_name": "Academic Game", "color": "#0077b6", "title": "An Academic Leader", "start_text": "You are matched with the Scholar...", "play_text": "...", "quest_text": "...", "legacy_text": "...", "traits": ["Asks questions", "Seeks truth", "Dislikes rushing", "Studies deeply", "Shares knowledge"], "q_and_a": [ {"q": "What excites you?", "a": "Asking big questions and finding answers."}]}, "Servant": { "game_name": "Neoclassical Game", "color": "#2a9d8f", "title": "A Community Leader", "start_text": "You are matched with the Servant...", "play_text": "...", "quest_text": "...", "legacy_text": "...", "traits": ["Helps others", "Keeps order", "Dislikes chaos", "Builds trust", "Bonds groups"], "q_and_a": [ {"q": "What excites you?", "a": "Helping people feel safe, welcome, and treated fairly."}]}, "Engineer": { "game_name": "Progressive Game", "color": "#e9c46a", "title": "A Project Leader", "start_text": "You are matched with the Engineer...", "play_text": "...", "quest_text": "...", "legacy_text": "...", "traits": ["Solves problems", "Wants results", "Dislikes worksheets", "Builds with team", "Makes ideas real"], "q_and_a": [ {"q": "What excites you?", "a": "Solving problems with tools and teamwork."}]}, "Founder": { "game_name": "Neotraditional Game", "color": "#f4a261", "title": "A Visionary Leader", "start_text": "You are matched with the Founder...", "traits": ["Chases ideas", "Breaks rules", "Dislikes limits", "Takes risks", "Sees future"], "q_and_a": [ {"q": "What excites you?", "a": "Chasing big ideas and trying new things."}]}, "Artist": { "game_name": "Democratic Game", "color": "#e76f51", "title": "A Philosophical Leader", "start_text": "You are matched with the Artist...", "traits": ["Creates freely", "Loves beauty", "Dislikes rules", "Shares feelings", "Pursues meaning"], "q_and_a": [ {"q": "What excites you?", "a": "Drawing, singing, writing, or creating something new."}]} }
cube_definitions=[{'label':role,'size':(i,i,i),'color':details['color']} for i,(role,details) in enumerate(role_details.items())]; cube_definitions[0]['size']=(0.3,0.3,0.3)
display_slider_metrics = [{'metric':"Freedom",'start_label':"Follow",'end_label':"Lead"},{'metric':"Security",'start_label':"Known",'end_label':"Unknown"},{'metric':"Responsibility",'start_label':"Social",'end_label':"Personal"},{'metric':"Control",'start_label':"Zero",'end_label':"Full"},{'metric':"Attention",'start_label':"Narrow",'end_label':"Broad"},{'metric':"Information",'start_label':"Consume",'end_label':"Create"}]
def make_cube(origin,size,color,visible=False):
    x0,y0,z0=origin; dx,dy,dz=size; vertices=np.array([[x0,y0,z0],[x0+dx,y0,z0],[x0+dx,y0+dy,z0],[x0,y0+dy,z0],[x0,y0,z0+dz],[x0+dx,y0,z0+dz],[x0+dx,y0+dy,z0+dz],[x0,y0+dy,z0+dz]]); edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    return [go.Scatter3d(x=[vertices[e[0],0],vertices[e[1],0]],y=[vertices[e[0],1],vertices[e[1],1]],z=[vertices[e[0],2],vertices[e[1],2]],mode="lines",line=dict(color=color,width=4),showlegend=False,visible=visible) for e in edges]
def make_sphere(center,radius,color, visible=False):
    u=np.linspace(0,2*np.pi,40); v=np.linspace(0,np.pi,20); x=center[0]+radius*np.outer(np.cos(u),np.sin(v)); y=center[1]+radius*np.outer(np.sin(u),np.sin(v)); z=center[2]+radius*np.outer(np.ones(np.size(u)),np.cos(v))
    return go.Mesh3d(x=x.flatten(),y=y.flatten(),z=z.flatten(),color=color,opacity=0.5,alphahull=0,showlegend=False,name="Player Sphere",lighting=dict(ambient=0.4,diffuse=0.8,specular=0.2,roughness=0.5),lightposition=dict(x=100,y=200,z=50), visible=visible)
@app.route("/")
def index():
    if USE_MOCK_DATA:
        mock_data={'user_id':['user_alpha'],'Freedom':[12],'Security':[13],'Responsibility':[15],'k_band':[0]}; df=pd.DataFrame(mock_data); df.columns=[c.lower().replace(' ','_') for c in df.columns]
    else:
        try:
            response=requests.get(SHEETDB_URL); response.raise_for_status(); data=response.json(); df=pd.DataFrame(data); df.columns=[c.lower().replace(' ','_') for c in df.columns]
        except Exception as e: return f"<p style='color:red;'>An error occurred: {e}</p>"
    user_id=request.args.get("user_id");
    if not user_id: return "<p style='color:red;'>No user_id provided.</p>"
    user_rows=df[df['user_id']==user_id]
    if user_rows.empty: return f"<p style='color:red;'>No results for user: {user_id}</p>"
    latest=user_rows.iloc[-1]
    try: f_score=int(latest['freedom']);s_score=int(latest['security']);r_score=int(latest['responsibility']);k_band=int(latest['k_band']);role=list(role_details.keys())[k_band]
    except (ValueError,KeyError,IndexError) as e: return f"<p style='color:red;'>Data processing error: {e}</p>"
    fig=go.Figure();
    for d in cube_definitions:
        for trace in make_cube((0,0,0), d['size'], d['color'], visible=False): fig.add_trace(trace)
    for i, d in enumerate(cube_definitions):
        if i > 0: r = i / 2.0; fig.add_trace(make_sphere((r,r,r), r, d['color'], visible=False))
    initial_visible_list = [False] * len(fig.data)
    for i in range(k_band*12, k_band*12+12): initial_visible_list[i] = True
    if k_band > 0:
        num_cube_traces = len(cube_definitions) * 12
        sphere_index = num_cube_traces + (k_band - 1)
        initial_visible_list[sphere_index] = True
    for i, visible in enumerate(initial_visible_list): fig.data[i].visible = visible
    slider_steps_data = []
    num_cube_traces = len(cube_definitions) * 12
    for i, d in enumerate(cube_definitions):
        visibility_list = [False] * len(fig.data)
        for j in range(i*12, i*12+12): visibility_list[j] = True
        if i > 0:
            sphere_index = num_cube_traces + (i - 1)
            visibility_list[sphere_index] = True 
        step_args = [ {"visible": visibility_list}, {"title.text": f"<b>{'Growth' if i>0 else 'Survival'} Game - {d['label']}</b>"} ]
        slider_steps_data.append({"label": d['label'], "method": "update", "args": step_args})
    initial_title=f"<b>{'Growth' if k_band > 0 else 'Survival'} Game - {role}</b>"
    axis_style=dict(range=[-0.5,5.5],tickvals=[0,1,2,3,4,5],gridcolor='#e0e0e0',zerolinecolor='rgba(0,0,0,0.3)',showbackground=False)
    fig.update_layout(title=dict(text=initial_title,y=0.98,x=0.5,xanchor='center',yanchor='top',font=dict(size=22,color='#2c3e50')), paper_bgcolor='white', plot_bgcolor='white', showlegend=False, scene=dict(xaxis={**axis_style, 'title': 'Control'}, yaxis={**axis_style, 'title': 'Attention'}, zaxis={**axis_style, 'title': 'Information'}, camera=dict(eye=dict(x=1.5,y=-1.5,z=1.3)), aspectmode='cube'), margin=dict(l=0, r=0, b=0, t=60), autosize=True)
    graph_html=fig.to_html(full_html=False,config={'displayModeBar':False, 'responsive': True},include_plotlyjs='cdn', div_id='plotly-graph')
    return render_template_string(HTML_TEMPLATE, user_id=user_id,role=role, f_score=f_score,s_score=s_score,r_score=r_score, role_info=role_details[role], graph_html=graph_html, display_metrics=display_slider_metrics, k_band=k_band, cube_definitions=cube_definitions, slider_steps_json=jsonify(slider_steps_data).get_data(as_text=True))

if __name__ == "__main__":
    port=int(os.environ.get("PORT",8080)); app.run(host="0.0.0.0",port=port,debug=False)
