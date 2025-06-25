from flask import Flask, render_template_string, request, redirect, jsonify
from flask_socketio import SocketIO, emit
import json
import os

app = Flask(__name__)
socketio = SocketIO(app)

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
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>/* [unchanged CSS — keep existing styles] */</style>
</head>
<body>
    <h1>Bruh's To-Do List</h1>
    <ul id="task-list">
        {% for i, task in enumerate(tasks) %}
        <li class="task" draggable="true" data-index="{{ i }}">
            <span class="task-text">{{ task }}</span>
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

        // Handle new task
        socket.on("new_task", function(data) {
            const li = document.createElement("li");
            li.className = "task";
            li.setAttribute("draggable", "true");
            li.setAttribute("data-index", taskList.children.length);
            li.innerHTML = `
                <span class="task-text">${data.task}</span>
                <button class="delete-btn" onclick="deleteTask(${taskList.children.length})">X</button>
            `;
            taskList.appendChild(li);
        });

        // Handle delete
        socket.on("task_deleted", function(data) {
            const items = document.querySelectorAll("#task-list li");
            if (data.index >= 0 && data.index < items.length) {
                items[data.index].remove();
                updateTaskIndices();
            }
        });

        // Handle full reorder sync
        socket.on("tasks_reordered", function(data) {
            taskList.innerHTML = "";
            data.tasks.forEach((task, i) => {
                const li = document.createElement("li");
                li.className = "task";
                li.setAttribute("draggable", "true");
                li.setAttribute("data-index", i);
                li.innerHTML = `
                    <span class="task-text">${task}</span>
                    <button class="delete-btn" onclick="deleteTask(${i})">X</button>
                `;
                taskList.appendChild(li);
            });
        });

        function deleteTask(index) {
            fetch(`/delete/${index}`, {
                method: "POST"
            });
        }

        function updateTaskIndices() {
            document.querySelectorAll("#task-list li").forEach((li, i) => {
                li.setAttribute("data-index", i);
                li.querySelector("button").setAttribute("onclick", `deleteTask(${i})`);
            });
        }

        let dragSrcIndex = null;

        taskList.addEventListener("dragstart", (e) => {
            dragSrcIndex = +e.target.getAttribute("data-index");
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", "");
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
        socketio.emit("new_task", {"task": task})
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
        socketio.emit("tasks_reordered", {"tasks": tasks})
    return jsonify(success=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050)
