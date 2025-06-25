from flask import Flask, render_template_string, request, redirect, jsonify
import json
import os

app = Flask(__name__)

TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks():
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f)

tasks = load_tasks()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>To-Do List</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background-color: #111;
    color: white;
    font-family: Arial, sans-serif;
    padding-bottom: 100px; /* space for footer */
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100vw;
    min-height: 100vh;
}

h1 {
    font-size: 1.8em;
    font-weight: bold;
    margin: 24px 0;
    text-align: center;
}

#task-list {
    list-style: none;
    width: 100%;
    max-width: 500px;
    padding: 0 16px;
}

.task {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #1e1e1e;
    padding: 12px 16px;
    margin: 10px 0;
    border-radius: 10px;
    cursor: grab;
}

.task span {
    flex-grow: 1;
    margin-right: 10px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.delete-btn {
    background: none;
    border: none;
    color: turquoise;
    font-size: 18px;
    cursor: pointer;
    min-width: 32px;
    min-height: 32px;
}

/* Fixed footer input bar */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #111;
    padding: 12px 16px;
    box-shadow: 0 -4px 12px rgba(0,0,0,0.3);
    display: flex;
    justify-content: center;
}

.footer form {
    display: flex;
    width: 100%;
    max-width: 500px;
}

input[type="text"] {
    flex-grow: 1;
    padding: 12px;
    font-size: 16px;
    border: none;
    border-radius: 8px 0 0 8px;
    background-color: #222;
    color: white;
}

button[type="submit"] {
    padding: 12px 20px;
    font-size: 16px;
    background-color: turquoise;
    border: none;
    color: black;
    cursor: pointer;
    border-radius: 0 8px 8px 0;
    min-width: 64px;
}
html, body {
    overscroll-behavior: none;
    touch-action: manipulation;
}
#task-list {
    user-select: none;
    -webkit-user-drag: none;
}
    </style>
</head>
<body>
    <h1>Bruh's To-Do List</h1>
    <ul id="task-list">
        {% for i, task in enumerate(tasks) %}
        <li class="task" draggable="true" data-index="{{ i }}">
    <span class="task-text">{{ task }}</span>
    <button class="delete-btn" onclick="document.getElementById('form-{{ i }}').submit()">X</button>
    <form id="form-{{ i }}" method="POST" action="/delete/{{ i }}" style="display: none;"></form>
    <div class="footer">
  <form method="POST" action="/add">
      <input type="text" name="task" placeholder="Enter a task" required>
      <button type="submit">Add</button>
  </form>
</div>
</li>
        {% endfor %}
    </ul>

    <script>
        const taskList = document.getElementById("task-list");
        let dragSrcIndex = null;

        taskList.addEventListener("dragstart", (e) => {
            dragSrcIndex = +e.target.getAttribute("data-index");
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", ""); // suppress ghost drag text

        });

        taskList.addEventListener("dragover", (e) => {
            e.preventDefault();
        });

        taskList.addEventListener("drop", (e) => {
    e.preventDefault();
    const li = e.target.closest("li");
    if (!li) return;

    const dropIndex = +li.getAttribute("data-index");
    if (dragSrcIndex !== null && dropIndex !== dragSrcIndex) {
        fetch("/reorder", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ from: dragSrcIndex, to: dropIndex })
        }).then(() => {
            location.reload();
        });
    }
});
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, tasks=tasks, enumerate=enumerate)

@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task")
    if task:
        tasks.append(task)
        save_tasks()
    return redirect("/")

@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    if 0 <= index < len(tasks):
        tasks.pop(index)
        save_tasks()
    return redirect("/")

@app.route("/reorder", methods=["POST"])
def reorder():
    data = request.get_json()
    from_index = data.get("from")
    to_index = data.get("to")
    if 0 <= from_index < len(tasks) and 0 <= to_index < len(tasks):
        task = tasks.pop(from_index)
        tasks.insert(to_index, task)
        save_tasks()
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
