from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def dashboard():
    return render_template("index.html")


@app.get("/health-dashboard")
def health_dashboard():
    return render_template("health.html")


@app.get("/traffic-dashboard")
def traffic_dashboard():
    return render_template("traffic.html")


@app.get("/load-test")
def load_test_dashboard():
    return render_template("loadtest.html")


@app.get("/system-info")
def system_info_dashboard():
    return render_template("system.html")


@app.get("/dependency-graph")
def dependency_graph_dashboard():
    return render_template("graph.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
