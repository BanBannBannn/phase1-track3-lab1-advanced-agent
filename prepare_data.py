import json
from datasets import load_dataset

print("Đang tải dữ liệu gốc từ HuggingFace (chờ một chút nhé)...")
# Tải tập validation của HotpotQA (bản chuẩn)
dataset = load_dataset("hotpot_qa", "distractor", split="validation")

formatted_data = []

# Chỉ lấy đúng 100 câu đầu tiên cho đủ KPI bài Lab
for i in range(100):
    row = dataset[i]
    
    # Xử lý Context: HotpotQA gốc chia thành từng câu nhỏ, 
    # mình gom lại thành đoạn văn cho khớp với QAExample của bạn
    context_chunks = []
    titles = row['context']['title']
    sentences_list = row['context']['sentences']
    
    for title, sentences in zip(titles, sentences_list):
        context_chunks.append({
            "title": title,
            "text": " ".join(sentences)
        })
        
    # Tạo object khớp 100% với file hotpot_mini.json
    item = {
        "qid": row["id"],
        "difficulty": row["level"],
        "question": row["question"],
        "gold_answer": row["answer"],
        "context": context_chunks
    }
    formatted_data.append(item)

# Lưu ra thư mục data/
output_path = "data/hotpot_100.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(formatted_data, f, ensure_ascii=False, indent=2)

print(f"🎉 Xong! Đã tạo thành công file: {output_path} với 100 câu hỏi chuẩn.")