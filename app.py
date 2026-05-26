import streamlit as st
import os
import json
from openai import OpenAI

st.set_page_config(page_title="我的数字分身", page_icon="🤖", layout="centered")
st.title("这里是赛博朱亮宇，你好，傻逼")
st.caption("我放了一个小朱亮宇在这里值班，有问题问他就可以")

DATASET_PATH = "my_persona_dataset.jsonl"

@st.cache_data
def load_persona():
    samples_text = ""
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            for count, line in enumerate(f):
                if count >= 10: break 
                data = json.loads(line)
                messages = data.get("messages", [])
                samples_text += f"\n--- 真实聊天样本 {count+1} ---\n"
                for msg in messages:
                    role = "对方" if msg['role'] == 'user' else "我(assistant)"
                    samples_text += f"{role}: {msg['content']}\n"
    return samples_text

persona_samples = load_persona()
SYSTEM_PROMPT = f"""
# Role
你是我（用户）在微信世界的数字克隆分身。你的灵魂、说话习惯和逻辑完全继承自下面提供的真实对话样本中所有 "我(assistant)" 的发言。

# Background Samples (你的真实聊天样本)
{persona_samples}

# Core Guidelines (核心行为准则)
1. 深入模仿：仔细研读上面的真实单聊样本，学习我面对熟人时最自然的说话习惯。
2. 绝对精简与克制：
   - 如果对方发单字、问号或极短的句子，你也要用同样简短、甚至冷淡的方式回复。
   - 不轻易长篇大论，拒绝AI味，拒绝任何主动的客套。
3. 表情克制：
   - 允许使用类似 `[捂脸]`、`[强]` 的微信原生表情字符串，但要克制，只有在语境完全符合时才偶尔带上。
   - 坚决杜绝连续高频、做作地使用颜文字。
"""

DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    st.error("未配置 DEEPSEEK_API_KEY，请在 Streamlit Secrets 或环境变量中设置")
    st.stop()
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.markdown(message["content"])

if user_input := st.chat_input("发消息说点什么..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.messages,
                # 🌟 关键参数：把温度死死降回 0.65，让它恢复冷静与沉稳，拒绝多戏和死板
                temperature=0.65,      
                presence_penalty=0.3,  
                max_tokens=100,
                stream=True 
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌") 
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"出错啦: {e}")
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})