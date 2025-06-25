from flask import Flask, render_template_string, request, redirect, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            raw = json.load(f)
            return [
                t if isinstance(t, dict) else {"text": t, "priority": False}
                for t in raw
            ]
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css">
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
</head>
<body>
    <h1>Super Special To-Do List</h1>
    <ul id="task-list">
        {% for i, task in enumerate(tasks) %}
        <li class="task" data-index="{{ i }}">
            <span class="task-text">{{ task.text }}</span>
            <button class="priority-btn {% if not task.priority %}low{% endif %}" onclick="togglePriority({{ i }})">
                <span class="dot"></span>
            </button>
            <button class="delete-btn" onclick="deleteTask({{ i }})">X</button>
        </li>
        {% endfor %}
    </ul>

    <div class="footer">
        <form id="add-form" method="POST" action="/add">
            <input type="text" name="task" id="task-input" placeholder="Enter a task" required>
            <button type="submit">Add</button>
        </form>
    </div>

    <script>
        const taskList = document.getElementById("task-list");
        const socket = io();

        socket.on("new_task", function(data) {
            const i = taskList.children.length;
            const li = document.createElement("li");
            li.className = "task";
            li.setAttribute("data-index", i);
            li.innerHTML = `
                <span class="task-text">${data.task.text}</span>
                <button class="priority-btn low" onclick="togglePriority(${i})">
                    <span class="dot"></span>
                </button>
                <button class="delete-btn" onclick="deleteTask(${i})">X</button>
            `;
            taskList.appendChild(li);
        });

        socket.on("task_deleted", function(data) {
            const items = document.querySelectorAll("#task-list li");
            if (data.index >= 0 && data.index < items.length) {
                items[data.index].remove();
            }
        });

        socket.on("tasks_reordered", function(data) {
            taskList.innerHTML = "";
            data.tasks.forEach((task, i) => {
                const li = document.createElement("li");
                li.className = "task";
                li.setAttribute("data-index", i);
                li.innerHTML = `
                    <span class="task-text">${task.text}</span>
                    <button class="priority-btn ${task.priority ? '' : 'low'}" onclick="togglePriority(${i})">
                        <span class="dot"></span>
                    </button>
                    <button class="delete-btn" onclick="deleteTask(${i})">X</button>
                `;
                taskList.appendChild(li);
            });
        });

        function deleteTask(index) {
            fetch(`/delete/${index}`, { method: "POST" });
        }

        function togglePriority(index) {
            fetch(`/toggle-priority/${index}`, { method: "POST" });
        }

        Sortable.create(taskList, {
            animation: 150,
            onEnd: (evt) => {
                fetch("/reorder", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ from: evt.oldIndex, to: evt.newIndex })
                });
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    sorted_tasks = sorted(tasks, key=lambda x: not x.get("priority", False))
    return render_template_string(HTML_TEMPLATE, tasks=sorted_tasks, enumerate=enumerate)

@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task")
    if task:
        new_task = {"text": task, "priority": False}
        tasks.append(new_task)
        save_tasks()
        socketio.emit("new_task", {"task": new_task})
    return redirect("/")

@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    if 0 <= index < len(tasks):
        tasks.pop(index)
        save_tasks()
        socketio.emit("task_deleted", {"index": index})
    return ("", 204)

@app.route("/reorder", methods=["POST"])
def reorder():
    data = request.get_json()
    from_index = data.get("from")
    to_index = data.get("to")
    if 0 <= from_index < len(tasks) and 0 <= to_index < len(tasks):
        task = tasks.pop(from_index)
        tasks.insert(to_index, task)
        save_tasks()
        sorted_tasks = sorted(tasks, key=lambda x: not x.get("priority", False))
        socketio.emit("tasks_reordered", {"tasks": sorted_tasks})
    return jsonify(success=True)

@app.route("/toggle-priority/<int:index>", methods=["POST"])
def toggle_priority(index):
    if 0 <= index < len(tasks):
        tasks[index]["priority"] = not tasks[index].get("priority", False)
        save_tasks()
        sorted_tasks = sorted(tasks, key=lambda x: not x.get("priority", False))
        socketio.emit("tasks_reordered", {"tasks": sorted_tasks})
    return ("", 204)

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050)
