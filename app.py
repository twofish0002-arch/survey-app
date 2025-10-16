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
# 1. PRESENTATION LAYER (HTML TEMPLATE - with icon and JS fixes)
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
        .card-header{font-size:0.85rem;font-weight:600;color:#1a202c;margin-top:0;margin-bottom:16px;border-bottom:1px solid #e2e8f0;padding-bottom:10px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center;}
        .card-header svg { width: 16px; height: 16px; margin-right: 8px; stroke-width: 2; }
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
        .graph-card { height: 600px; padding: 0; display: flex; flex-direction: column; position: relative; }
        .graph-card #plotly-graph {flex-grow:1; width:100%; height:100%;}
        #growth-text-display { position: absolute; bottom: 0; left: 0; right: 0; background-color: rgba(248, 249, 250, 0.9); border-top: 1px solid #e2e8f0; padding: 12px 20px; text-align: center; font-size: 0.8rem; font-style: italic; color: #4a5568; backdrop-filter: blur(2px); }
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
            <div class="card">
                <h3 class="card-header">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                        <defs><radialGradient id="grad1" cx="40%" cy="40%" r="65%"><stop offset="0%" style="stop-color:rgb(220,220,220)" /><stop offset="100%" style="stop-color:rgb(100,100,100)" /></radialGradient></defs>
                        <circle cx="12" cy="12" r="10" fill="url(#grad1)" />
                    </svg>
                    <span>Player Dynamic Characteristics</span>
                </h3>
                {% for metric in display_metrics[:3] %}<div class="metric-slider"><div class="metric-name">{{ metric.metric }}</div><div class="track-container"><span class="label">{{ metric.start_label }}</span><div class="track"><div class="dot" id="dot-{{ metric.metric.lower() }}" style="left: calc({{ k_band }} / 5 * 100% - 7.5px);"></div></div><span class="label">{{ metric.end_label }}</span></div></div>{% endfor %}
            </div>
            <div class="card">
                <h3 class="card-header">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                    <span>Game Static Characteristics</span>
                </h3>
                {% for metric in display_metrics[3:] %}<div class="metric-slider"><div class="metric-name">{{ metric.metric }}</div><div class="track-container"><span class="label">{{ metric.start_label }}</span><div class="track"><div class="dot" id="dot-{{ metric.metric.lower() }}" style="left: calc({{ k_band }} / 5 * 100% - 7.5px);"></div></div><span class="label">{{ metric.end_label }}</span></div></div>{% endfor %}
            </div>
            <div class="card"><h3 class="card-header">At a Glance</h3><div class="traits-list"><ul>{% for trait in role_info.traits %}<li>{{ trait }}</li>{% endfor %}</ul></div><div class="qa-list">{% for item in role_info.q_and_a %}<h4>{{ item.q }}</h4><p>{{ item.a }}</p>{% endfor %}</div></div>
            <div class="card validation-card">
                <h3>Validate your result: one token, one signal</h3><p>For 1 euro, you validate yourself and everyone who has not yet. Each validation adds your data to a growing dataset, sending a clear signal: it is safe and wise to differentiate beyond “Pupil.” With validation, you also receive the full SI Paper.</p>
                <h3>What the Paper reveals</h3><ul><li>The reality beyond standardised education.</li><li>A new language for growth.</li><li>Why some thrive as Founders while others flourish as Scholars.</li><li>How the five games are designed and why they feel different.</li><li>Why Responsibility matters most.</li><li>Proof: 10 years of practice, thousands of reflections.</li></ul>
                <h3>Privacy</h3><p>Your results are stored anonymously. Only validated results can send a clear signal for change.</p>
                <a href="https://thequantumfamily.com/store" class="validate-button" target="_top">Validate results &amp; receive the paper →</a>
            </div>
        </div>
        <div class="right-column">
            <div class="card graph-card">
                {{graph_html|safe}}
                <div id="growth-text-display">{{ role_info.growth_text }}</div>
            </div>
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
        const growthTexts = {{ growth_texts_json|safe }}; 
        window.addEventListener('load', function() {
            const graphDiv = document.getElementById('plotly-graph');
            const archetypeSlider = document.getElementById('archetype-slider');
            const sliderTitle = document.getElementById('slider-title');
            const warningMessage = document.getElementById('pupil-warning-message');
            const growthTextDisplay = document.getElementById('growth-text-display'); 
            if (!graphDiv || !archetypeSlider || !warningMessage || !growthTextDisplay) return;
            archetypeSlider.addEventListener('input', function(event) {
                const kValue = parseInt(event.target.value, 10);
                const stepInfo = sliderStepsData[kValue];
                const visibility = stepInfo.args[0].visible;
                const titleText = stepInfo.args[1]['title.text'];
                const roleName = stepInfo.label;
                Plotly.update(graphDiv, { visible: visibility }, { 'title.text': titleText });
                sliderTitle.innerText = "Role: " + roleName;
                growthTextDisplay.innerText = growthTexts[kValue];
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
# 2. DATA & CONFIGURATION
# ==============================================================================
role_details = {
    "Pupil": { "game_name": "Standardised Game", "color": "#8d99ae", "title": "A Classroom Leader", "growth_text": "This is the space all pupils are mandated to occupy.", "start_text": "You are the Pupil, a potential Classroom Leader trained to listen, copy, and perform until the score says you’re enough. The Standardised Game promises safety and success if you comply, fit its pattern and adopt its values, yet it measures only what can be counted, not what truly ignites you.", "play_text": "You may feel pressure to please, to stay within the narrow lines that others drew. That tension isn’t failure; it’s proof that you still have a self. The game feels serious, but it is not the world; its walls are a temporary Hollywood set, and you are the world outside.", "quest_text": "Hold on to your values; they are assets the world wants and rewards. Remember what excites you, what feels true, what matters when nobody’s watching. When the noise of grinding tests grows loud, look for the edge of the stage because it’s all a game, a big temporary act.", "legacy_text": "One day, the bell will ring and the stage lights will fade. You’ll step beyond this script and carry forward what the game could never grade: your curiosity, your courage, your heart. Knowing your value is where a great education truly begins.", "traits": ["Follows rules", "Seeks approval", "Dislikes mistakes", "Likes clear steps", "Waits for instructions"], "q_and_a": [ {"q": "What excites you?", "a": "Doing the task exactly right and getting approval."}, {"q": "What matters?", "a": "Safety, clear instructions, and meeting expectations."}, {"q": "A great day looks like…", "a": "The plan is clear and there are no surprises. You follow instructions and feel proud when you finish with a tick."}, {"q": "What you don’t like…", "a": "Feeling like you’re in a perpetual state of emergency."}, {"q": "Secret power", "a": "You are excellent at following orders in an emergency."}, {"q": "Leadership style", "a": "As a classroom leader, you enjoy being at the top of your class and setting the standard for the other pupils."} ] },
    "Scholar": { "game_name": "Academic Game", "color": "#0077b6", "title": "An Academic Leader", "growth_text": "This is the space an academic needs to grow.", "start_text": "You are matched with the Scholar, a potential Academic Leader devoted to truth and understanding. Your gift is to discover, test, and preserve knowledge in a world that rewards depth, focus, and disciplined curiosity. You look beneath the surface and connect the past to the future through clear reasoning.", "play_text": "The Academic Game fits you because it matches your need for clarity and structure while respecting your independence of thought. Guided by mentors, you progress steadily from curiosity to comprehension in a world where patience and precision lead to mastery.", "quest_text": "You ask and resolve “What’s this?” questions, the kind that seek truth and understanding. Resolution comes when knowledge feels complete, sharpening thought and strengthening community. Each time you clarify something for yourself, you make it clearer for others.", "legacy_text": "You are trusted to question deeply, verify carefully, and teach what endures. Scholars guard truth, refine knowledge through honest inquiry, and pass it forward so others can build wisely upon it. Without them, civilisation forgets what it has learned.", "traits": ["Asks questions", "Seeks truth", "Dislikes rushing", "Studies deeply", "Shares knowledge"], "q_and_a": [ {"q": "What excites you?", "a": "Asking big questions and finding answers."}, {"q": "What matters?", "a": "Clear thinking, careful work, and learning."}, {"q": "A great day looks like…", "a": "You wake up with a puzzle in your head. You spend hours reading, testing, and writing until the answer starts to shine."}, {"q": "What you don’t like…", "a": "Being rushed to finish before you’re ready."}, {"q": "Secret power", "a": "You help the world remember what is true."}, {"q": "Leadership style", "a": "As an academic leader, you enjoy teaching others and showing them what’s real and worth knowing."} ] },
    "Servant": { "game_name": "Neoclassical Game", "color": "#2a9d8f", "title": "A Community Leader", "growth_text": "This is the space a servant needs to grow.", "start_text": "You are matched with the Servant, a potential Community Leader devoted to care, order, and trust. Your gift is to create stability so others can thrive together. You thrive in the Neoclassical Game, where shared goals and mutual respect keep groups strong.", "play_text": "The Neoclassical Game fits you because it reflects your respect for structure and your instinct to serve. It offers clear expectations, shared responsibility, and opportunity for social contribution. You prefer a world of fairness and well-kept promises.", "quest_text": "You ask and resolve “Can I?” and “What’s this?” questions, seeking both permission and understanding. You find fulfilment in improving systems and processes, making them more humane. You’re motivated to maintain order and strengthen communities.", "legacy_text": "You are trusted to organise, mediate, and safeguard collective wellbeing. Servants are the glue that keeps us together, transforming ability into stability and care into cohesion. Servants are the foundations of entire communities.", "traits": ["Helps others", "Keeps order", "Dislikes chaos", "Builds trust", "Bonds groups"], "q_and_a": [ {"q": "What excites you?", "a": "Helping people feel safe, welcome, and treated fairly."}, {"q": "What matters?", "a": "Rules, fairness, and making sure groups stay connected."}, {"q": "A great day looks like…", "a": "You quietly make sure everyone has what they need. By the end, the group has worked well together because of you."}, {"q": "What you don’t like…", "a": "Chaos, unfairness, or people breaking promises."}, {"q": "Secret power", "a": "You are the glue that holds people together."}, {"q": "Leadership style", "a": "As a community leader, you enjoy caring for people and creating relationships and harmony."} ] },
    "Engineer": { "game_name": "Progressive Game", "color": "#e9c46a", "title": "A Project Leader", "growth_text": "This is the space an engineer needs to grow.", "start_text": "You are matched with the Engineer, a potential Project Leader devoted to solving problems and making ideas real. Your gift is to design, build, test and innovate. You thrive in the Progressive Game, where you can choose your goals and find the best solution.", "play_text": "The Progressive Game fits you because it rewards initiative and practical thinking. It provides clear objectives and the trust to experiment until you find what works best. You prefer a balance of structure and freedom that keeps challenge and order in balance.", "quest_text": "You ask and resolve “How can I?”, “Can I?”, and “What’s this?” questions, seeking better ways to turn plans into reality. You find fulfilment when an idea functions flawlessly. Your curiosity optimises and strengthens the systems people rely on.", "legacy_text": "You are trusted to build, innovate, and deliver results others depend on. Engineers are the world’s problem solvers, turning imagination into solutions and ideas into everyday products and services. They make the modern world function.", "traits": ["Solves problems", "Wants results", "Dislikes worksheets", "Builds with team", "Makes ideas real"], "q_and_a": [ {"q": "What excites you?", "a": "Solving problems with tools and teamwork."}, {"q": "What matters?", "a": "Making things that work and last."}, {"q": "A great day looks like…", "a": "You carefully decide who to serve and which problem to solve. You test, fix, and by the end, you can proudly say, “It works!”"}, {"q": "What you don’t like…", "a": "Endless worksheets that don’t matter in real life."}, {"q": "Secret power", "a": "You make ideas real."}, {"q": "Leadership style", "a": "As a project leader, you enjoy helping everyone on the team to solve really challenging problems together."} ] },
    "Founder": { "game_name": "Neotraditional Game", "color": "#f4a261", "title": "A Visionary Leader", "growth_text": "This is the space a founder needs to grow.", "start_text": "You are matched with the Founder, a potential Visionary Leader who creates what has never existed before. Your gift is to see possibilities where others see risk, turning ideas into opportunities that shape the future. You thrive in the Neotraditional Game, where freedom and uncertainty open new paths to growth and discovery.", "play_text": "The Neotraditional Game fits you because it gives you ownership and the freedom to take calculated risks. It provides open space, autonomy, and the chance to act before certainty exists. You prefer the unknown, where opportunities can emerge.", "quest_text": "You ask and resolve “What if?”, “How can I?”, “Can I?”, and “What’s this?” questions, exploring potential from every angle. You find fulfilment when your vision becomes real and others begin to follow it. Your curiosity generates opportunity and gives others new space to grow.", "legacy_text": "You are trusted to imagine boldly, act decisively, and build ventures that change the game. Founders are the architects of the future, expanding economies and creating markets. They shape the future through courage and creation.", "traits": ["Chases ideas", "Breaks rules", "Dislikes limits", "Takes risks", "Sees future"], "q_and_a": [ {"q": "What excites you?", "a": "Chasing big ideas and trying new things."}, {"q": "What matters?", "a": "Freedom to experiment and take risks."}, {"q": "A great day looks like…", "a": "A spark hits: you sketch, test, and tinker until your idea begins to take shape."}, {"q": "What you don’t like…", "a": "Being stuck in rules that stop you from exploring."}, {"q": "Secret power", "a": "You see the future before others do."}, {"q": "Leadership style", "a": "As a visionary leader, you enjoy the thrill of imagining the unimaginable and inviting others to follow."} ] },
    "Artist": { "game_name": "Democratic Game", "color": "#e76f51", "title": "A Philosophical Leader", "growth_text": "This is the space an artist needs to grow.", "start_text": "You are matched with the Artist, a potential Philosophical Leader who pursues meaning where others pursue objectivity. Your gift is to create beauty and express truth, revealing what words alone cannot reach. You thrive in the Democratic Game, where freedom and authenticity encourage creation.", "play_text": "The Democratic Game fits you because it celebrates individuality and expression. It offers total creative control and the freedom to follow intuition wherever it leads. You prefer open space, where imagination and emotion can move without boundaries.", "quest_text": "You can ask and resolve “Why?” and move through “What if?”, “How can I?”, “Can I?”, and “What’s this?” questions, exploring every layer of meaning. You find fulfilment when your work reveals why something matters. Your curiosity connects hearts and restores meaning to others.", "legacy_text": "You are trusted to imagine freely, challenge norms, and reveal truth through creation. Artists are the voice of humanity, showing what is possible when feeling becomes form. They remind the world not just how to live, but why.", "traits": ["Creates freely", "Loves beauty", "Dislikes rules", "Shares feelings", "Pursues meaning"], "q_and_a": [ {"q": "What excites you?", "a": "Drawing, singing, writing, or creating something new."}, {"q": "What matters?", "a": "Freedom, beauty, and sharing your heart."}, {"q": "A great day looks like…", "a": "A picture, sound, or feeling comes to you. You follow it until it becomes real, then share it with others."}, {"q": "What you don’t like…", "a": "Being told there’s only one right way to do things."}, {"q": "Secret power", "a": "You remind people what really matters."}, {"q": "Leadership style", "a": "As a philosophical leader, you enjoy exploring boundaries and expressing meaning, beauty, and truth."} ] }
}
cube_definitions=[{'label':role,'size':(i,i,i),'color':details['color']} for i,(role,details) in enumerate(role_details.items())]; cube_definitions[0]['size']=(0.3,0.3,0.3)
display_slider_metrics = [{'metric':"Freedom",'start_label':"Follow",'end_label':"Lead"},{'metric':"Security",'start_label':"Known",'end_label':"Unknown"},{'metric':"Responsibility",'start_label':"Social",'end_label':"Personal"},{'metric':"Control",'start_label':"Zero",'end_label':"Full"},{'metric':"Attention",'start_label':"Narrow",'end_label':"Broad"},{'metric':"Information",'start_label':"Consume",'end_label':"Create"}]

# ==============================================================================
# 3. PLOTTING HELPER FUNCTIONS & FLASK ROUTE
# ==============================================================================
def make_cube(origin,size,color,visible=False):
    x0,y0,z0=origin; dx,dy,dz=size; vertices=np.array([[x0,y0,z0],[x0+dx,y0,z0],[x0+dx,y0+dy,z0],[x0,y0+dy,z0],[x0,y0,z0+dz],[x0+dx,y0,z0+dz],[x0+dx,y0+dy,z0+dz],[x0,y0+dy,z0+dz]]); edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    return [go.Scatter3d(x=[vertices[e[0],0],vertices[e[1],0]],y=[vertices[e[0],1],vertices[e[1],1]],z=[vertices[e[0],2],vertices[e[1],2]],mode="lines",line=dict(color=color,width=4),showlegend=False,visible=visible, hoverinfo='none') for e in edges]
def make_sphere(center,radius,color, visible=False):
    u=np.linspace(0,2*np.pi,40); v=np.linspace(0,np.pi,20); x=center[0]+radius*np.outer(np.cos(u),np.sin(v)); y=center[1]+radius*np.outer(np.sin(u),np.sin(v)); z=center[2]+radius*np.outer(np.ones(np.size(u)),np.cos(v))
    return go.Mesh3d(x=x.flatten(),y=y.flatten(),z=z.flatten(),color=color,opacity=0.5,alphahull=0,showlegend=False,name="Player Sphere",lighting=dict(ambient=0.4,diffuse=0.8,specular=0.2,roughness=0.5),lightposition=dict(x=100,y=200,z=50), visible=visible, hoverinfo='none')

@app.route("/")
def index():
    if USE_MOCK_DATA:
        mock_data={'user_id':['user_alpha'],'Freedom':[12],'Security':[13],'Responsibility':[15],'k_band':[3]}; df=pd.DataFrame(mock_data); df.columns=[c.lower().replace(' ','_') for c in df.columns]
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
    # Create all cube and sphere traces upfront
    for d in cube_definitions:
        for trace in make_cube((0,0,0), d['size'], d['color'], visible=False): fig.add_trace(trace)
    for i, d in enumerate(cube_definitions):
        if i > 0: r = i / 2.0; fig.add_trace(make_sphere((r,r,r), r, d['color'], visible=False))
    
    # Set initial visibility
    initial_visible_list = [False] * len(fig.data)
    for i in range(k_band*12, k_band*12+12): initial_visible_list[i] = True
    if k_band > 0:
        num_cube_traces = len(cube_definitions) * 12
        sphere_index = num_cube_traces + (k_band - 1)
        initial_visible_list[sphere_index] = True
    for i, visible in enumerate(initial_visible_list): fig.data[i].visible = visible
        
    # Prepare slider data for Javascript (robust method)
    slider_steps_data = []
    num_cube_traces = len(cube_definitions) * 12
    for i, d in enumerate(cube_definitions):
        visibility_list = [False] * len(fig.data)
        for j in range(i*12, i*12+12): visibility_list[j] = True
        if i > 0:
            sphere_index = num_cube_traces + (i - 1)
            visibility_list[sphere_index] = True 
        step_args = [ {"visible": visibility_list}, {"title.text": f"<b>{'Growth' if i>0 else 'Survival'} Game - {d['label']}</b>"} ]
        slider_steps_data.append({"label": d['label'], "args": step_args})

    growth_texts = [details['growth_text'] for role, details in role_details.items()]
    initial_title=f"<b>{'Growth' if k_band > 0 else 'Survival'} Game - {role}</b>"
    axis_style=dict(range=[-0.5,5.5],tickvals=[0,1,2,3,4,5],gridcolor='#e0e0e0',zerolinecolor='rgba(0,0,0,0.3)',showbackground=False)
    
    # Final camera and margin settings
    fig.update_layout(
        title=dict(text=initial_title,y=0.98,x=0.5,xanchor='center',yanchor='top',font=dict(size=20,color='#2c3e50')),
        paper_bgcolor='white', plot_bgcolor='white', showlegend=False,
        scene=dict(
            xaxis={**axis_style, 'title': 'Control'}, yaxis={**axis_style, 'title': 'Attention'}, zaxis={**axis_style, 'title': 'Information'},
            camera=dict(
                eye=dict(x=1.9, y=-1.9, z=1.6), # Final camera position
            ),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=20, t=40), # Minimal margins
        autosize=True
    )
    
    graph_html=fig.to_html(full_html=False,config={'displayModeBar':False, 'responsive': True},include_plotlyjs='cdn', div_id='plotly-graph')
    return render_template_string(
        HTML_TEMPLATE, user_id=user_id,role=role, f_score=f_score,s_score=s_score,r_score=r_score, 
        role_info=role_details[role], graph_html=graph_html, 
        display_metrics=display_slider_metrics, k_band=k_band, 
        cube_definitions=cube_definitions, 
        slider_steps_json=jsonify(slider_steps_data).get_data(as_text=True),
        growth_texts_json=jsonify(growth_texts).get_data(as_text=True)
    )

if __name__ == "__main__":
    port=int(os.environ.get("PORT",8080)); app.run(host="0.0.0.0",port=port,debug=False)
