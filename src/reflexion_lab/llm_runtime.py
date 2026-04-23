import json
import ollama
from .schemas import QAExample, JudgeResult, ReflectionEntry

MODEL_NAME = "qwen2.5-coder:7b" 

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> str:
    # 1. Ghép Context từ danh sách các chunk
    context_text = "\n".join([f"- {chunk.title}: {chunk.text}" for chunk in example.context])
    
    # 2. Xây dựng Prompt
    prompt = f"Question: {example.question}\n\nContext:\n{context_text}\n"
    
    # Nếu có bài học từ lần sai trước, nhắc LLM đừng lặp lại
    if reflection_memory:
        prompt += "\nWARNING - PREVIOUS MISTAKES TO AVOID:\n"
        for mem in reflection_memory:
            prompt += f"- {mem}\n"
            
    prompt += "\nBased strictly on the context, provide a short and accurate final answer."

    # 3. Gọi Local LLM
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': 'You are an intelligent AI agent solving complex questions using step-by-step logic.'},
        {'role': 'user', 'content': prompt}
    ])
    
    return response['message']['content']

def evaluator(example: QAExample, answer: str) -> JudgeResult:
    prompt = f"""
    Question: {example.question}
    Gold Answer (Correct Answer): {example.gold_answer}
    Predicted Answer (Agent's Answer): {answer}
    
    Evaluate if the predicted answer is correct based on the gold answer.
    You MUST return ONLY a JSON object with this exact structure:
    {{"score": 1, "is_perfect": true, "reason": "Perfect match"}} 
    OR 
    {{"score": 0, "is_perfect": false, "reason": "Explain why it is wrong"}}
    """
    
    # Ép Ollama trả về định dạng JSON
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': 'You are a strict evaluator. Only output valid JSON.'},
        {'role': 'user', 'content': prompt}
    ], format='json')
    
    try:
        # Parse chuỗi JSON LLM trả về thành Dictionary
        data = json.loads(response['message']['content'])
        return JudgeResult(
            score=data.get('score', 0),
            is_perfect=data.get('is_perfect', False),
            reason=data.get('reason', 'Không rõ lý do do lỗi parse JSON.')
        )
    except Exception as e:
        # Fallback an toàn nếu LLM trả về rác
        return JudgeResult(score=0, is_perfect=False, reason=f"Lỗi parse JSON từ LLM: {str(e)}")

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> ReflectionEntry:
    prompt = f"""
    Question: {example.question}
    The previous answer was WRONG.
    Evaluator's critique: {judge.reason}
    
    Analyze the mistake. You MUST return ONLY a JSON object with this exact structure:
    {{"lesson": "The root cause of the mistake", "strategy": "What the agent should do differently next time"}}
    """
    
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': 'You are a critical thinker diagnosing logic failures. Only output valid JSON.'},
        {'role': 'user', 'content': prompt}
    ], format='json')
    
    try:
        data = json.loads(response['message']['content'])
        return ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=judge.reason,
            lesson=data.get('lesson', 'Cần đọc kỹ context hơn.'),
            strategy=data.get('strategy', 'Thực hiện tư duy từng bước rõ ràng.')
        )
    except Exception:
        return ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=judge.reason,
            lesson="Lỗi parse logic",
            strategy="Thử lại với cách tiếp cận đơn giản hơn."
        )