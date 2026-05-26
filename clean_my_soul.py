import pandas as pd
import json
import re
import os

# ==================== 配置区域 ====================
# 已经为你填入绝对正确的本地真实路径
CSV_FILE_PATH = r"C:\Users\20953\Desktop\n\messages.csv"

# 挑选出最能体现你个人硬核逻辑与高频社交的 TalkerId
# 2:A猪, 4:点子生产车间, 29:互联网+创赛群, 37:z, 68:Sail
TARGET_TALKERS = [2, 4, 29, 37, 68]
# =================================================

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).strip()
    
    # 彻底过滤腾讯新闻等 XML 杂音
    if text.startswith("<?xml") or "<mmreader>" in text:
        return ""
    
    # 过滤微信特有的非文本占位符与系统提示
    invalid_patterns = [
        r'^\[图片\]$', r'^\[表情\]$', r'^\[视频\]$', r'^\[语音\]$', 
        r'^\[文件\]$', r'^\[位置\]$', r'^\[链接\]$', r'拍了拍', r'撤回了一条消息', r'加入了群聊'
    ]
    for pattern in invalid_patterns:
        if re.search(pattern, text):
            return ""
            
    return text

def main():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ 错误：在指定路径找不到你的 CSV 文件，请确认文件是否在桌面的 n 文件夹下：\n👉 {CSV_FILE_PATH}")
        return

    print("📊 正在读取微信原始 CSV 数据，开始精准剥离你的说话风格...")
    
    # 兼容微信导出可能存在的不同编码格式
    try:
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_FILE_PATH, encoding='gbk')
    
    # 筛选：只要纯文本 (Type == 1)，且在我们指定的活跃联系人/群聊里
    df = df[df['TalkerId'].isin(TARGET_TALKERS) & (df['Type'] == 1)]
    
    # 按时间严格排序，确保对话逻辑不颠倒
    df = df.sort_values(by=['TalkerId', 'CreateTime']).reset_index(drop=True)
    
    dataset = []
    
    # 按会话独立切分，防止不同群聊、不同好友的语料交叉“串味”
    for talker_id, group in df.groupby('TalkerId'):
        print(f"🔍 正在提取会话 ID [{talker_id}] 中属于你的独特语气...")
        
        current_turns = []
        last_role = None
        last_content = ""
        
        for _, row in group.iterrows():
            content = clean_text(row['StrContent'])
            if not content:
                continue
            
            # 🌟 IsSender == 1 是你自己（大模型要模仿的 assistant）
            role = "assistant" if int(row['IsSender']) == 1 else "user"
            
            if last_role is None:
                last_role = role
                last_content = content
            elif last_role == role:
                # 同一个人连续发多条气泡，用换行拼接，完美保留你连续发言的习惯
                last_content += "\n" + content
            else:
                # 换人说话了，把上一轮的记录下来
                current_turns.append({"role": last_role, "content": last_content})
                last_role = role
                last_content = content
                
            # 当你（assistant）回复完对方（user），形成了一次完整的闭环互动时
            if len(current_turns) >= 1 and role == "assistant" and current_turns[-1]["role"] == "user":
                full_turns = list(current_turns) + [{"role": "assistant", "content": last_content}]
                
                # 确保是对方先说/问（user），你负责回（assistant）的标准微调格式
                if full_turns[0]["role"] == "user":
                    dataset.append({"messages": full_turns})
                
                # 清空上下文缓存，滚动进入下一轮对话捕捉
                current_turns = []
                last_role = None
                last_content = ""

    # 在 CSV 文件同级目录下生成标准的 JSONL 数据集
    output_path = os.path.join(os.path.dirname(CSV_FILE_PATH), "my_persona_dataset.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print("\n" + "="*50)
    print(f"🎉 🎉 🎉【你自己的数字分身语料库】清洗大功告成！！！")
    print(f"✨ 成功捕捉到 {len(dataset)} 组带有你真实说话习惯和硬核逻辑的多轮对话！")
    print(f"💾 专属微调数据集已完美保存至：\n👉 {output_path}")
    print("="*50)

if __name__ == "__main__":
    main()