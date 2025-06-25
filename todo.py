from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

tasks = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Basic To-Do List</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background-color: #111;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        h1 {
            margin-bottom: 20px;
        }
        form {
            display: flex;
            width: 100%;
            max-width: 500px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex-grow: 1;
            padding: 10px;
            font-size: 16px;
            border: none;
            border-radius: 8px 0 0 8px;
            background-color: #222;
            color: white;
        }
        button[type="submit"] {
            padding: 10px 20px;
            font-size: 16px;
            background-color: turquoise;
            border: none;
            color: black;
            cursor: pointer;
            border-radius: 0 8px 8px 0;
        }
        .task {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #1e1e1e;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 10px;
            width: 100%;
            max-width: 500px;
            word-break: break-word;
        }
        .task span {
            flex-grow: 1;
            margin-right: 10px;
        }
        .delete-btn {
            background-color: #444;
            border: none;
            color: white;
            padding: 6px 12px;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Basic To-Do List</h1>
    <form method="POST" action="/add">
        <input type="text" name="task" placeholder="Enter a task" required>
        <button type="submit">Add</button>
    </form>
    {% for i, task in enumerate(tasks) %}
        <div class="task">
            <span>{{ task }}</span>
            <form method="POST" action="/delete/{{ i }}" style="margin: 0;">
                <button class="delete-btn" type="submit">X</button>
            </form>
        </div>
    {% endfor %}
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
    return redirect("/")

@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    if 0 <= index < len(tasks):
        tasks.pop(index)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
