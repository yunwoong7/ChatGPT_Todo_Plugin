import sqlite3
import quart
import quart_cors
from quart import request

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

DATABASE = "todos.db"


def init_db():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS todos
                       (username TEXT PRIMARY KEY, todos TEXT)''')
        con.commit()


@app.post("/todos/<string:username>")
async def add_todo(username):
    request_data = await quart.request.get_json(force=True)
    todo = request_data["todo"]

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT todos FROM todos WHERE username=?", (username,))
        existing_todos = cur.fetchone()

        if existing_todos:
            todos_list = existing_todos[0].split('|')
            todos_list.append(todo)
            cur.execute("UPDATE todos SET todos=? WHERE username=?", ('|'.join(todos_list), username))
        else:
            cur.execute("INSERT INTO todos (username, todos) VALUES (?, ?)", (username, todo))

        con.commit()

    return quart.Response(response='OK', status=200)


@app.get("/todos/<string:username>")
async def get_todos(username):
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT todos FROM todos WHERE username=?", (username,))
        todos = cur.fetchone()

    if todos:
        return quart.Response(response='|'.join(todos), status=200)
    else:
        return quart.Response(response='', status=200)


@app.delete("/todos/<string:username>")
async def delete_todo(username):
    request_data = await quart.request.get_json(force=True)
    todo_idx = request_data["todo_idx"]

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT todos FROM todos WHERE username=?", (username,))
        todos = cur.fetchone()

        if todos:
            todos_list = todos[0].split('|')
            if 0 <= todo_idx < len(todos_list):
                todos_list.pop(todo_idx)
                cur.execute("UPDATE todos SET todos=? WHERE username=?", ('|'.join(todos_list), username))
                con.commit()

    return quart.Response(response='OK', status=200)


@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")


@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")


def main():
    init_db()  # 데이터베이스 초기화
    app.run(debug=True, host="localhost", port=5001)


if __name__ == "__main__":
    main()
