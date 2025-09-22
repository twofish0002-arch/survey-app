from flask import Flask, request, render_template_string
import pandas as pd, numpy as np, plotly.graph_objects as go
import os, json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# --- Google Sheets setup (Render secret) ---
service_account_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
gc = gspread.authorize(creds)

sheet = gc.open("Imaginative Survey - Responses").sheet1
df = pd.DataFrame(sheet.get_all_records())

@app.route("/")
def index():
    # Get user’s email (user_id) from URL
    user_id = request.args.get("user_id")
    if not user_id:
        return "Please provide ?user_id=email in the URL"

    # Filter the sheet data for this user
    user_rows = df[df['user_id'] == user_id]
    if user_rows.empty:
        return f"No results found for {user_id}"

    # Get their most recent submission
    latest = user_rows.iloc[-1]
    k_band = int(latest['K Band'])
    band = k_band

    # --- Plotly Visualisation (Working Block) ---
    def cube_vertices(size):
        coords = [-size/2, size/2]
        return np.array([[x,y,z] for x in coords for y in coords for z in coords])

    vertices_ref = cube_vertices(2)
    edges = []
    for i in range(8):
        for j in range(i+1, 8):
            if np.sum(np.abs(vertices_ref[i] - vertices_ref[j])) == 2:
                edges.append((i,j))

    sizes = [1,2,3,4,5]
    roles = ["Scholar", "Servant", "Engineer", "Founder", "Artist"]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#d62728"]
    cubes = [cube_vertices(s) for s in sizes]

    fig = go.Figure()

    # Plot cubes as wireframes
    for c_idx, cube in enumerate(cubes):
        for i,j in edges:
            fig.add_trace(go.Scatter3d(
                x=[cube[i,0], cube[j,0]],
                y=[cube[i,1], cube[j,1]],
                z=[cube[i,2], cube[j,2]],
                mode="lines",
                line=dict(color=colors[c_idx], width=3),
                showlegend=False,
                visible=True
            ))

    # Join edges between cubes
    for k in range(len(sizes)-1):
        cube_small = cubes[k]
        cube_large = cubes[k+1]
        for v in range(8):
            fig.add_trace(go.Scatter3d(
                x=[cube_small[v,0], cube_large[v,0]],
                y=[cube_small[v,1], cube_large[v,1]],
                z=[cube_small[v,2], cube_large[v,2]],
                mode="lines",
                line=dict(color="black", width=1),
                showlegend=False,
                visible=True
            ))

    # Sphere generator
    def sphere(radius, n=60):
        u = np.linspace(0, 2*np.pi, n)
        v = np.linspace(0, np.pi, n)
        x = radius * np.outer(np.cos(u), np.sin(v))
        y = radius * np.outer(np.sin(u), np.cos(v))
        z = radius * np.outer(np.ones_like(u), np.cos(v))
        return x, y, z

    radii = [0, 0.5, 1, 1.5, 2, 2.5]
    sphere_traces = []
    label_traces = []

	for step, r in enumerate(radii):
	    if step == 0:
		# Small central black sphere for "Pupil"
		u = np.linspace(0, 2*np.pi, 40)
		v = np.linspace(0, np.pi, 20)
		x = (0.3 * np.outer(np.cos(u), np.sin(v))).flatten()
		y = (0.3 * np.outer(np.sin(u), np.sin(v))).flatten()
		z = (0.3 * np.outer(np.ones_like(u), np.cos(v))).flatten()

		fig.add_trace(go.Mesh3d(
		    x=x, y=y, z=z,
		    alphahull=0,
		    opacity=0.9,
		    color="black",
		    visible=(band == 0),
		    showscale=False
		))

		fig.add_trace(go.Scatter3d(
		    x=[0], y=[0], z=[0.5],
		    mode="text",
		    text=["Pupil"],
		    textfont=dict(color="black", size=18),
		    visible=(band == 0)
		))

	    else:
		# Larger blue spheres for Scholar–Artist
		u = np.linspace(0, 2*np.pi, 40)
		v = np.linspace(0, np.pi, 20)
		x = (r * np.outer(np.cos(u), np.sin(v))).flatten()
		y = (r * np.outer(np.sin(u), np.sin(v))).flatten()
		z = (r * np.outer(np.ones_like(u), np.cos(v))).flatten()

		fig.add_trace(go.Mesh3d(
		    x=x, y=y, z=z,
		    alphahull=0,
		    opacity=0.5,
		    color="#088cff",
		    visible=(band == step),
		    showscale=False
		))

		fig.add_trace(go.Scatter3d(
		    x=[0], y=[0], z=[r*1.2],
		    mode="text",
		    text=[roles[step-1]],
		    textfont=dict(color="black", size=18),
		    visible=(band == step)
		))


    fig.update_layout(
        scene=dict(xaxis=dict(visible=False),
                   yaxis=dict(visible=False),
                   zaxis=dict(visible=False)),
        width=900, height=900,
        title=f"Survey Result → K Band {band}"
    )

    # --- End Working Block ---

    graph_html = fig.to_html(full_html=False)

    return render_template_string("""
	<html>
	<body>
	  <h2>Survey Result for {{ user_id }} → K Band {{ k_band }}</h2>
	  {{ graph_html | safe }}
	  <hr>
	  <p><b>Validate your result:</b></p>
	  <a href="https://your-stripe-checkout-link" target="_blank">
	    <button style="font-size:18px;padding:10px 20px;">Validate & Join Dataset</button>
	  </a>
	</body>
	</html>
	""", user_id=user_id, k_band=k_band, graph_html=graph_html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


