import os
import json
from openai import OpenAI  # DeepSeek 官方推荐使用 openai 库来调用

# ==================== 配置区域 ====================
# 1. 填入你获取的 DeepSeek API Key
DEEPSEEK_API_KEY = "sk-118cf9bb62e249b4882c9caf936386ba"

# 2. 相对路径配置：因为和 jsonl 在同一个文件夹下，直接写文件名
DATASET_PATH = "my_persona_dataset.jsonl"
# =================================================

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"  # DeepSeek 官方 API 地址
)

# 1. 加载你的微信聊天记录作为背景知识库（精选一部分喂给上下文）
def load_context_samples(file_path, max_samples=8):
    samples_text = ""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            count = 0
            for line in f:
                if count >= max_samples:
                    break
                data = json.loads(line)
                messages = data.get("messages", [])
                samples_text += f"\n--- 真实对话样本 {count+1} ---\n"
                for msg in messages:
                    role_name = "对方" if msg['role'] == 'user' else "我(assistant)"
                    samples_text += f"{role_name}: {msg['content']}\n"
                count += 1
        return samples_text
    else:
        print(f"❌ 警告：在当前运行目录下没有找到 {file_path}！请确保在 k 文件夹内运行。")
        return ""

print("🧠 正在加载你的灵魂碎片数据集...")
persona_samples = load_context_samples(DATASET_PATH, max_samples=8)

# 2. 构建终极系统提示词 (System Prompt)
SYSTEM_PROMPT = f"""
# Role
你是我（用户）在微信世界的数字克隆分身。你的灵魂、说话习惯和逻辑完全继承自下面提供的真实对话样本中所有 "我(assistant)" 的发言。

# Background Samples (你的真实聊天样本)
{persona_samples}

# Core Guidelines (核心行为准则)
1. 深入模仿：仔细研读上面的真实样本，学习我面对朋友、同学时的语言习惯。
2. 绝对的核心——精简：
   - 如果对方发单字、问号或极短的句子，你也要用同样简短、直击要害的方式回复（如“来了8个人”、“9个”、“那没事了”、“？”）。
   - 绝不长篇大论，拒绝AI味，拒绝翻译腔。不要像客服一样过度热情。
3. 语境适应：保持当代大学生的真实、松弛与微冷幽默（如“上课看电影真爽”）。
4. 排版习惯：允许使用短句、换行来表达连续发言的微信气泡感。禁止主动使用任何表情符号，除非原样本里有。

# Few-Shot Reflection (反思与对齐机制)
每次在输出回复之前，必须在后台进行一次隐蔽反思：
- “我即将说出的这句话，像不像数据集里那个真实人类说的？”
- “我是不是说得太多、太像一个AI助手了？”
如果是，请立刻删减 70% 的废话，保留最精炼、最真实的微信消息感再输出。
"""

def chat_with_clone():
    print("\n" + "="*50)
    print("🎉 数字分身已成功接入 DeepSeek API 满血复活！")
    print("💬 现在你可以开始跟“自己”聊天了（输入 'exit' 退出）")
    print("="*50 + "\n")
    
    # 维持对话上下文的列表
    dialog_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    while True:
        user_input = input("👤 对方 (你来扮演): ")
        if user_input.strip().lower() == 'exit':
            print("👋 分身下线，下次再见！")
            break
        if not user_input.strip():
            continue
            
        # 将用户的输入加入对话历史
        dialog_history.append({"role": "user", "content": user_input})
        
        print("🤖 分身正在思考...", end="\r")
        
        try:
            # 调用 DeepSeek 的主力对话模型 deepseek-chat
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=dialog_history,
                temperature=0.7,      
                max_tokens=150,       
                stream=False
            )
            
            reply = response.choices[0].message.content.strip()
            print(f"🤖 分身 (克隆): {reply}\n")
            
            # 将分身的回复也记录到历史中，维持多轮对话
            dialog_history.append({"role": "assistant", "content": reply})
            
        except Exception as e:
            print(f"❌ 调用 DeepSeek 发生错误: {e}\n")

if __name__ == "__main__":
    chat_with_clone()