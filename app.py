from flask import Flask, request, render_template_string
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import json
import requests

app = Flask(__name__)

# --- FINAL, ROBUST API Setup (Works Everywhere) ---
SHEETDB_URL = "https://sheetdb.io/api/v1/7fida3dgawvel"


# --- Final, Leadership-Focused Role Content with All Text Updates ---
role_details = {
    "Scholar": {
        "leadership_title": "As an academic leader, you enjoy teaching others and showing them what’s real and worth knowing.",
        "game_name": "Academic Game",
        "definition": "A scholar is an individual who creates value by seeking truth and curating knowledge. Driven by the foundational question, “What’s this?”, their leadership begins with the pursuit of clarity. Their strength lies in connecting generations by preserving and building upon essential ideas.",
        "game_description": "Your profile suggests a preference for clear guidance and a world of knowns, allowing you to master a subject with precision. The Academic Game matches this perfectly. It gives you a mentor-led path where you can ask and resolve 'What's this?' questions, focus your attention on a single, deep line of inquiry, and have the space to precisely curate and understand existing knowledge.",
        "bullets": ["Asks questions", "Seeks truth", "Dislikes rushing", "Studies deeply", "Shares knowledge"],
        "profile": {
            "What makes you excited?": "Asking big questions and finding answers.",
            "What matters?": "Clear thinking, careful work, and learning.",
            "A great day looks like…": "You wake up with a puzzle in your head. You spend hours reading, testing, and writing until the answer starts to shine.",
            "What you don’t like…": "Being rushed to finish before you’re ready.",
            "Secret power": "You help the world remember what is true."
        }
    },
    "Servant": {
        "leadership_title": "As a community leader, you enjoy caring for people and creating relationships and harmony.",
        "game_name": "Neoclassical Game",
        "definition": "A servant is an individual who creates value by building trust and ensuring systems run smoothly. Driven by the question, “Can I?”, which honours established boundaries, their leadership strength is creating the stability and psychological safety that empowers a group to succeed together.",
        "game_description": "Your profile suggests you thrive within a trusted community with clear rules, where you can take on and manage important tasks for the group. The Neoclassical Game matches this perfectly. It provides clear institutional boundaries where you can ask and resolve 'Can I?' questions, focus your attention on improving systems and processes that serve the entire community.",
        "bullets": ["Helps others", "Keeps order", "Dislikes chaos", "Builds trust", "Bonds groups"],
        "profile": {
            "What makes you excited?": "Helping people feel safe, welcome, and treated fairly.",
            "What matters?": "Rules, fairness, and making sure groups stay connected.",
            "A great day looks like…": "You quietly make sure everyone has what they need. By the end, the group has worked well together because of you.",
            "What you don’t like…": "Chaos, unfairness, or people breaking promises.",
            "Secret power": "You are the glue that holds people together."
        }
    },
    "Engineer": {
        "leadership_title": "As a project leader, you enjoy helping everyone on the team to solve really challenging problems together.",
        "game_name": "Progressive Game",
        "definition": "An engineer is an individual who creates value by turning ideas into reality. Driven by the practical question, “How can I?”, their leadership strength is planning, building, and delivering reliable results that move a team forward. This role is broader than just a technical profession; it is about taking ownership of the 'how.'",
        "game_description": "Your profile suggests a desire for clear objectives and the freedom to solve real problems, balancing knowns and unknowns. The Progressive Game matches this perfectly. It gives you a clear path to follow, where the directive is \"I must.\" It allows you to focus your attention on a predictable schedule and provides the opportunity to master given material with precision.",
        "bullets": ["Solves problems", "Wants results", "Dislikes worksheets", "Builds with team", "Makes ideas real"],
        "profile": {
            "What makes you excited?": "Solving problems with tools and teamwork.",
            "What matters?": "Making things that work and last.",
            "A great day looks like…": "You carefully decide who to serve and which problem to solve. You test, fix, and by the end, you can proudly say, “It works!”",
            "What you don’t like…": "Endless worksheets that don’t matter in real life.",
            "Secret power": "You make ideas real."
        }
    },
    "Founder": {
        "leadership_title": "As a visionary leader, you enjoy the thrill of imagining the unimaginable and inviting others to follow.",
        "game_name": "Neotraditional Game",
        "definition": "A founder is an individual who creates value by reimagining what is possible and pursuing new opportunities. Driven by the expansive question, “What if?”, their leadership strength is the ability to sustain uncertainty and inspire others to help build a new future.",
        "game_description": "Your profile suggests a high level of self-trust and a comfort with the unknown, along with a strong desire to take ownership of your own ideas and their outcomes. The Neotraditional Game matches this perfectly. It gives you full control to ask and resolve 'What if?' questions, focus your attention on a wide-open space for experimentation, and have the permission to create new value from your own vision.",
        "bullets": ["Chases ideas", "Breaks rules", "Dislikes limits", "Takes risks", "Sees future"],
        "profile": {
            "What makes you excited?": "Chasing big ideas and trying new things.",
            "What matters?": "Freedom to experiment and taking risks.",
            "A great day looks like…": "A spark hits: you sketch, test, and tinker until your idea begins to take shape.",
            "What you don’t like…": "Being stuck in rules that stop you from exploring.",
            "Secret power": "You see the future before others do."
        }
    },
    "Artist": {
        "leadership_title": "As a philosophical leader, you enjoy exploring boundaries and expressing meaning, beauty, and truth.",
        "game_name": "Democratic Game",
        "definition": "An artist is an individual who creates value by exploring authenticity and giving form to the unknown. Driven by the ultimate question, “Why?”, their leadership strength is serving as a moral and aesthetic compass for society, creating works that connect us to beauty and eternal truths.",
        "game_description": "Your profile suggests a deep trust in your own intuition and a need for unstructured freedom, where you are the ultimate judge of your own work. The Democratic Game matches this perfectly. It provides a blank canvas with near-total control where you can ask and resolve 'Why?' questions, direct your own attention without external goals, and have the freedom to create something based on your own standard of authentic expression.",
        "bullets": ["Creates freely", "Loves beauty", "Dislikes rules", "Shares feelings", "Shows meaning"],
        "profile": {
            "What makes you excited?": "Drawing, singing, writing, or creating something new.",
            "What matters?": "Freedom, beauty, and sharing your heart.",
            "A great day looks like…": "A picture, sound, or feeling comes to you. You follow it until it becomes real, then share it with others.",
            "What you don’t like…": "Being told there’s only one right way to do things.",
            "Secret power": "You remind people what really matters."
        }
    },
    "Pupil": {
        "leadership_title": "As an excellent pupil, you enjoy being an exemplary student and reliable follower.",
        "game_name": "Standardised Game",
        "definition": "A pupil is the foundational role for learning within a highly structured environment. A Pupil creates value by demonstrating excellence in compliance. Guided by the directive, “I must,” their core strength is following instructions with precision, a necessary skill before a player discovers their leadership style.",
        "game_description": "Your profile suggests a need for a safe, predictable environment with clear, step-by-step guidance, where success comes from following instructions perfectly. The Standardised Game matches this perfectly. It gives you a clear path to follow, where the directive is 'I must,' allows you to focus your attention on a predictable schedule, and provides the opportunity to master given material with precision.",
        "bullets": ["Follows rules", "Seeks approval", "Dislikes mistakes", "Likes clear steps", "Waits for instructions"],
        "profile": {
            "What makes you excited?": "Doing the task exactly right and getting approval.",
            "What matters?": "Safety, clear instructions, and meeting expectations.",
            "A great day looks like…": "The plan is clear and there are no surprises. You follow instructions and feel proud when you finish with a tick.",
            "What you don’t like…": "Uncertainty, unclear instructions, or self-direction.",
            "Secret power": "You are excellent at following orders in an emergency."
        }
    }
}

# --- Cube helper functions and Plotly setup ---
def cube_vertices(size):
    coords = [-size / 2, size / 2]
    return np.array([[x, y, z] for x in coords for y in coords for z in coords])

vertices_ref = cube_vertices(2)
edges = []
for i in range(8):
    for j in range(i + 1, 8):
        if np.sum(np.abs(vertices_ref[i] - vertices_ref[j])) == 2:
            edges.append((i, j))

sizes = [1, 2, 3, 4, 5]
colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#d62728"]
radii = [0, 0.5, 1, 1.5, 2, 2.5]


@app.route("/")
def index():
    try:
        response = requests.get(SHEETDB_URL)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching data from the API: {e}"
    except Exception as e:
        return f"An error occurred while processing the data: {e}"

    user_id = request.args.get("user_id")
    if not user_id:
        return "<p style='color:red; text-align:center;'>No user_id provided in the URL.</p>"

    user_rows = df[df['user_id'] == user_id]
    if user_rows.empty:
        return f"<p style='color:red; text-align:center;'>No results found for user: {user_id}</p>"

    latest = user_rows.iloc[-1]
    
    try:
        f_score = int(latest['freedom'])
        s_score = int(latest['security'])
        r_score = int(latest['responsibility'])
        k_band = int(latest['k_band'])
        
        role_name_map = {0: "Pupil", 1: "Scholar", 2: "Servant", 3: "Engineer", 4: "Founder", 5: "Artist"}
        role = role_name_map.get(k_band, "Pupil")
        details = role_details.get(role, role_details["Pupil"])
    except (ValueError, KeyError) as e:
        return f"There was an error processing your data. Please check the sheet for correct column headers. The script could not find the column: {e}"
        
    band = k_band

    # --- 3D VISUAL GENERATION ---
    fig = go.Figure()
    
    cubes = [cube_vertices(s) for s in sizes]
    for c_idx, cube in enumerate(cubes):
        for i, j in edges:
            fig.add_trace(go.Scatter3d(x=[cube[i, 0], cube[j, 0]], y=[cube[i, 1], cube[j, 1]], z=[cube[i, 2], cube[j, 2]], mode="lines", line=dict(color=colors[c_idx], width=2), showlegend=False))
            
    role_radius = radii[band]
    if band > 0:
        u, v = np.mgrid[0:2*np.pi:40j, 0:np.pi:20j]
        x, y, z = role_radius * np.cos(u) * np.sin(v), role_radius * np.sin(u) * np.sin(v), role_radius * np.cos(v)
        fig.add_trace(go.Mesh3d(x=x.flatten(), y=y.flatten(), z=z.flatten(), alphahull=0, opacity=0.6, color="#088cff", showscale=False))

    u, v = np.mgrid[0:2*np.pi:40j, 0:np.pi:20j]
    x, y, z = 0.2 * np.cos(u) * np.sin(v), 0.2 * np.sin(u) * np.sin(v), 0.2 * np.cos(v)
    fig.add_trace(go.Mesh3d(x=x.flatten(), y=y.flatten(), z=z.flatten(), alphahull=0, opacity=0.5, color="grey", showscale=False))
    
    label_z = (role_radius + 0.5) if band > 0 else 0.5
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[label_z], mode="text", text=[role], textfont=dict(color="black", size=16, family="Arial, sans-serif")))
    
    fig.update_layout(
        autosize=True,
        scene=dict(
            xaxis=dict(visible=False), 
            yaxis=dict(visible=False), 
            zaxis=dict(visible=False), 
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ), 
        margin=dict(l=0, r=0, b=0, t=0)
    )
    graph_html = fig.to_html(full_html=False, config={'displayModeBar': False}, include_plotlyjs='cdn')
    
    # This is the final, cleaned HTML template. It ONLY contains the results content.
    html_template = """
    <!-- Final content block. Does not include "Validate" button or "Journey Ahead" text. -->

    <div class="content-box reveal-box">
        <h1>{{ role }}!!</h1>
        <h2>Congratulations!</h2>
        <p>Your survey suggests the {{ details.game_name }}.</p>
    </div>

    <p style="text-align: left;">In a growth game like TwoFish, your suggested starting point is the role of {{ role }} in the {{ details.game_name }}. {{ details.definition }}</p>
    
    <div class="strengths-container">
        <div class="strength-item"><h4>Freedom (F = {{ f_score }})</h4><div class="bar-bg"><div class="bar-fill" style="width:{{ (f_score / 5) * 100 }}%;"></div></div></div>
        <div class="strength-item"><h4>Security (S = {{ s_score }})</h4><div class="bar-bg"><div class="bar-fill" style="width:{{ (s_score / 5) * 100 }}%;"></div></div></div>
        <div class="strength-item"><h4>Responsibility (R = {{ r_score }})</h4><div class="bar-bg"><div class="bar-fill" style="width:{{ (r_score / 5) * 100 }}%;"></div></div></div>
    </div>

    <div class="content-box">
        <h3 style="margin-top:0; text-align: left;">What your choices revealed.</h3>
        <p style="margin-bottom:0;">{{ details.game_description }}</p>
    </div>

    <h3 style="text-align: left;">The space you need to grow.</h3>
    <div class="info-box visual-column" style="margin: 0 auto;"> <!-- Centering the visual box -->
        <div class="graph-container">{{ graph_html | safe }}</div>
        <p class="visual-note">The grey sphere indicates the space a pupil is permitted to occupy.</p>
    </div>

    <!-- All other content from the original screenshot has been removed -->
    <!-- as it belongs in the main HTML file. -->

    <script>
        window.onload = function() {
            var height = document.documentElement.scrollHeight;
            parent.postMessage(height, "https://thequantumfamily.com");
        };
    </script>
    """
    
    return render_template_string(
        html_template, user_id=user_id, role=role, f_score=f_score, s_score=s_score, r_score=r_score, details=details, graph_html=graph_html
    )

@app.after_request
def add_headers(response):
    response.headers["X-Frame-Options"] = "ALLOW-FROM https://thequantumfamily.com"
    response.headers["Content-Security-Policy"] = "frame-ancestors https://thequantumfamily.com"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
