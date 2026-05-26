import os, json, uuid
from flask import Flask, request, jsonify, session, render_template_string
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", str(uuid.uuid4()))

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def load_persona():
    samples = ""
    path = os.path.join(os.path.dirname(__file__), "my_persona_dataset.jsonl")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                data = json.loads(line)
                for msg in data.get("messages", []):
                    role = "对方" if msg["role"] == "user" else "我(assistant)"
                    samples += f"{role}: {msg['content']}\n"
    return samples

SYSTEM_PROMPT = f"""你是我的数字克隆分身，说话习惯继承自下面的真实对话样本。

{load_persona()}

核心准则：
1. 深入模仿样本中的说话习惯。
2. 绝对精简：对方发短句你也短，拒绝AI味。
3. 表情克制：偶尔用[捂脸][强]之类的微信表情，杜绝高频颜文字。"""

sessions = {}  # {session_id: [messages]}

PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>赛博朱亮宇</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#f5f5f5;height:100vh;display:flex;flex-direction:column}
.header{background:#07c160;color:#fff;padding:12px 16px;text-align:center;font-size:18px;font-weight:bold}
.header small{font-size:12px;opacity:0.8;font-weight:normal}
.chat{flex:1;overflow-y:auto;padding:12px}
.msg{margin-bottom:12px;display:flex;flex-direction:column}
.msg.assistant{align-items:flex-start}
.msg.user{align-items:flex-end}
.msg .bubble{max-width:75%;padding:10px 14px;border-radius:8px;word-break:break-word;line-height:1.5}
.msg.user .bubble{background:#95ec69;color:#000}
.msg.assistant .bubble{background:#fff;color:#000;border:1px solid #eee}
.msg .role{font-size:11px;color:#999;margin-bottom:2px}
.input-area{display:flex;padding:10px;background:#fff;border-top:1px solid #ddd}
.input-area input{flex:1;padding:10px;border:1px solid #ddd;border-radius:6px;font-size:16px;outline:none}
.input-area button{width:50px;margin-left:8px;background:#07c160;color:#fff;border:none;border-radius:6px;font-size:16px;cursor:pointer}
.loading{color:#999;font-size:13px;padding-left:4px}
</style>
</head>
<body>
<div class="header">赛博朱亮宇 🤖<br><small>我放了一个小朱亮宇在这里值班</small></div>
<div class="chat" id="chat"></div>
<div class="input-area">
  <input id="input" placeholder="发消息..." autofocus onkeydown="if(event.key==='Enter')send()">
  <button onclick="send()">发送</button>
</div>
<script>
let sid = localStorage.getItem("sid") || "";
if (!sid) { sid = crypto.randomUUID(); localStorage.setItem("sid", sid); }

async function load() {
  let r = await fetch("/history?sid=" + sid);
  let msgs = await r.json();
  document.getElementById("chat").innerHTML = msgs.map(m =>
    m.role === "system" ? "" :
    `<div class="msg ${m.role}"><span class="role">${m.role==="user"?"你":"朱亮宇"}</span><div class="bubble">${m.content}</div></div>`
  ).join("");
  document.getElementById("chat").scrollTop = document.getElementById("chat").scrollHeight;
}

async function send() {
  let input = document.getElementById("input");
  let text = input.value.trim();
  if (!text) return;
  input.value = "";
  input.disabled = true;
  let chat = document.getElementById("chat");
  chat.innerHTML += `<div class="msg user"><span class="role">你</span><div class="bubble">${text}</div></div>`;
  chat.innerHTML += `<div class="msg assistant"><span class="role">朱亮宇</span><div class="bubble"><span class="loading">...</span></div></div>`;
  chat.scrollTop = chat.scrollHeight;
  let r = await fetch("/chat", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sid,text})});
  let data = await r.json();
  chat.lastElementChild.querySelector(".bubble").innerHTML = data.reply;
  input.disabled = false;
  input.focus();
}
load();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    sid = data.get("sid", "default")
    text = data["text"]
    if sid not in sessions:
        sessions[sid] = [{"role": "system", "content": SYSTEM_PROMPT}]
    sessions[sid].append({"role": "user", "content": text})
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=sessions[sid],
            temperature=0.65,
            presence_penalty=0.3,
            max_tokens=100,
        )
        reply = resp.choices[0].message.content
    except Exception as e:
        reply = f"出错: {e}"
    sessions[sid].append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})

@app.route("/history")
def history():
    sid = request.args.get("sid", "default")
    return jsonify(sessions.get(sid, []))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
