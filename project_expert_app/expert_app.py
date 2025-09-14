import json
import random
import re
import threading
from collections import defaultdict, Counter
from functools import partial

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except Exception as e:
    print("Tkinter không khả dụng trong môi trường này:", e)

# -------------------------
# 1. Knowledge base (JSON)
# -------------------------
KB_JSON = {
    "diseases": [
        {
            "id": "cold",
            "name": "Cảm lạnh",
            "symptoms": ["ho","sổ mũi","hắt hơi","đau họng","mệt mỏi"],
            "medications": ["Paracetamol","Thuốc nhỏ mũi"],
            "advice": ["Nghỉ ngơi","Uống nhiều nước","Súc họng nước muối"]
        },
        {
            "id": "flu",
            "name": "Cúm",
            "symptoms": ["sốt cao","đau đầu","đau cơ","ho","mệt mỏi"],
            "medications": ["Paracetamol","Thuốc chống virut nếu cần"],
            "advice": ["Nghỉ ngơi","Tránh tiếp xúc người khác"]
        },
        {
            "id": "dengue",
            "name": "Sốt xuất huyết",
            "symptoms": ["sốt cao","đau đầu","đau cơ","xuất huyết da","mệt mỏi"],
            "medications": ["Bù nước","Theo dõi tại cơ sở y tế"],
            "advice": ["Đi khám ngay","Uống oresol nếu mất nước"]
        },
        {
            "id": "strep_throat",
            "name": "Viêm họng do liên cầu",
            "symptoms": ["đau họng","sốt","khó nuốt","hạch cổ sưng"],
            "medications": ["Kháng sinh (nếu do vi khuẩn)","Paracetamol"],
            "advice": ["Đi khám để làm test", "Súc họng nước muối"]
        },
        {
            "id": "covid",
            "name": "COVID-19",
            "symptoms": ["sốt","ho","mất vị giác","mất khứu giác","mệt mỏi"],
            "medications": ["Theo hướng dẫn y tế địa phương"],
            "advice": ["Cách ly","Làm test PCR/rapid"]
        }
    ]
}

# Lưu ra file JSON nếu cần (tuỳ chọn)
with open('knowledge_base.json', 'w', encoding='utf8') as f:
    json.dump(KB_JSON, f, ensure_ascii=False, indent=2)

# -------------------------
# 2. Rule-based system
# -------------------------

class Rule:
    def __init__(self, disease_id, required_symptoms):
        self.disease_id = disease_id
        self.required_symptoms = set(self._normalize(s) for s in required_symptoms)

    def _normalize(self, text):
        return text.strip().lower()

    def matches(self, facts):
        facts_norm = set(self._normalize(s) for s in facts)
        matched = len(self.required_symptoms & facts_norm)
        total = len(self.required_symptoms)
        score = matched / total if total else 0
        return score, matched, total


class ExpertSystem:
    def __init__(self, kb):
        self.kb = kb
        self.rules = [Rule(d['id'], d['symptoms']) for d in kb['diseases']]
        # map id->disease
        self.disease_map = {d['id']: d for d in kb['diseases']}

    def forward_chaining(self, facts, topk=3):
        scores = []
        for r in self.rules:
            score, matched, total = r.matches(facts)
            scores.append((r.disease_id, score, matched, total))
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for disease_id, score, matched, total in scores[:topk]:
            d = self.disease_map[disease_id]
            results.append({
                'id': disease_id,
                'name': d['name'],
                'score': round(score, 3),
                'matched': matched,
                'total': total,
                'medications': d.get('medications', []),
                'advice': d.get('advice', [])
            })
        return results

    def backward_chaining(self, goal_disease_id, facts):
        rule = next((r for r in self.rules if r.disease_id == goal_disease_id), None)
        if not rule:
            return None
        facts_norm = set(s.strip().lower() for s in facts)
        missing = list(rule.required_symptoms - facts_norm)
        return {
            'disease_id': goal_disease_id,
            'missing_symptoms': missing,
            'is_satisfied': len(missing) == 0
        }

# -------------------------
# 3. Tạo dataset giả lập từ KB cho ML baseline
# -------------------------

def generate_synthetic_dataset(kb, n_samples_per_disease=300, noise_rate=0.2):
    diseases = kb['diseases']
    all_symptoms = sorted({s for d in diseases for s in d['symptoms']})
    rows = []
    for d in diseases:
        for _ in range(n_samples_per_disease):
            # chọn subset của triệu chứng thật
            present = [s for s in d['symptoms'] if random.random() > 0.2]
            # thêm noise: triệu chứng từ các bệnh khác
            if random.random() < noise_rate:
                other = random.choice(diseases)
                extra = random.choice(other['symptoms'])
                if extra not in present:
                    present.append(extra)
            # đôi khi có triệu chứng ngẫu nhiên
            if random.random() < 0.05:
                extra = random.choice(all_symptoms)
                if extra not in present:
                    present.append(extra)
            text = ", ".join(present)
            rows.append({'text': text, 'label': d['id']})
    df = pd.DataFrame(rows)
    return df

# -------------------------
# 4. ML baseline: train LR and RF
# -------------------------

class MLBaseline:
    def __init__(self):
        self.vectorizer = CountVectorizer(token_pattern=r"(?u)\b[^,]+\b")
        self.lr = LogisticRegression(max_iter=1000)
        self.rf = RandomForestClassifier(n_estimators=100)
        self.trained = False
        self.label_map = None
        self.inv_label_map = None

    def fit(self, texts, labels):
        X = self.vectorizer.fit_transform(texts)
        # label encoding
        uniq = sorted(list(set(labels)))
        self.label_map = {l: i for i, l in enumerate(uniq)}
        self.inv_label_map = {v: k for k, v in self.label_map.items()}
        y = np.array([self.label_map[l] for l in labels])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        print("Training Logistic Regression...")
        self.lr.fit(X_train, y_train)
        print("Training Random Forest...")
        self.rf.fit(X_train, y_train)
        # report
        preds_lr = self.lr.predict(X_test)
        preds_rf = self.rf.predict(X_test)
        print("== Logistic Regression Report ==")
        print(classification_report(y_test, preds_lr, target_names=uniq))
        print("== Random Forest Report ==")
        print(classification_report(y_test, preds_rf, target_names=uniq))
        self.trained = True

    def predict_proba(self, text, topk=3):
        if not self.trained:
            return []
        X = self.vectorizer.transform([text])
        proba_lr = self.lr.predict_proba(X)[0]
        proba_rf = self.rf.predict_proba(X)[0]
        # average probas
        avg = (proba_lr + proba_rf) / 2.0
        pairs = [(self.inv_label_map[i], avg[i]) for i in range(len(avg))]
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:topk]

# -------------------------
# 5. GUI (Tkinter)
# -------------------------

class DiagnosisApp:
    def __init__(self, root, expert_system, ml_baseline):
        self.root = root
        self.expert = expert_system
        self.ml = ml_baseline
        self.root.title('Hệ chuyên gia hỗ trợ chẩn đoán - Demo')
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        ttk.Label(frm, text='Nhập triệu chứng (ngăn cách bằng phẩy):').grid(column=0, row=0, sticky='w')
        self.input_text = scrolledtext.ScrolledText(frm, width=60, height=4)
        self.input_text.grid(column=0, row=1, pady=6)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(column=0, row=2, sticky='w')
        ttk.Button(btn_frame, text='Chẩn đoán (Rule-based)', command=self.on_diagnose_rule).grid(column=0, row=0)
        ttk.Button(btn_frame, text='Chẩn đoán (ML baseline)', command=self.on_diagnose_ml).grid(column=1, row=0, padx=8)
        ttk.Button(btn_frame, text='Chạy cả 2 (so sánh)', command=self.on_compare).grid(column=2, row=0)

        ttk.Label(frm, text='Kết quả:').grid(column=0, row=3, sticky='w', pady=(10,0))
        self.result_box = scrolledtext.ScrolledText(frm, width=60, height=15)
        self.result_box.grid(column=0, row=4, pady=6)

    def _get_input_symptoms(self):
        raw = self.input_text.get('1.0', 'end').strip()
        if not raw:
            return []
        parts = [p.strip().lower() for p in raw.split(',') if p.strip()]
        return parts

    def on_diagnose_rule(self):
        facts = self._get_input_symptoms()
        if not facts:
            messagebox.showinfo('Thiếu dữ liệu', 'Vui lòng nhập ít nhất một triệu chứng.')
            return
        res = self.expert.forward_chaining(facts, topk=5)
        self._display_rule_results(res)

    def on_diagnose_ml(self):
        facts = self._get_input_symptoms()
        if not facts:
            messagebox.showinfo('Thiếu dữ liệu', 'Vui lòng nhập ít nhất một triệu chứng.')
            return
        text = ", ".join(facts)
        preds = self.ml.predict_proba(text, topk=5)
        self._display_ml_results(preds)

    def on_compare(self):
        facts = self._get_input_symptoms()
        if not facts:
            messagebox.showinfo('Thiếu dữ liệu', 'Vui lòng nhập ít nhất một triệu chứng.')
            return
        self.result_box.delete('1.0', 'end')
        # Rule-based
        rb = self.expert.forward_chaining(facts, topk=5)
        self.result_box.insert('end', '*** Rule-based (Forward chaining) ***\n')
        for r in rb:
            self.result_box.insert('end', f"{r['name']} - score: {r['score']} ({r['matched']}/{r['total']})\n")
            self.result_box.insert('end', f"  Thuốc: {', '.join(r['medications'])}\n")
            self.result_box.insert('end', f"  Giải pháp: {', '.join(r['advice'])}\n")
        self.result_box.insert('end', '\n')
        # ML
        text = ", ".join(facts)
        preds = self.ml.predict_proba(text, topk=5)
        self.result_box.insert('end', '*** ML baseline (LR + RF average) ***\n')
        for pid, p in preds:
            d = self.expert.disease_map[pid]
            self.result_box.insert('end', f"{d['name']} - prob: {p:.3f}\n")
            self.result_box.insert('end', f"  Thuốc: {', '.join(d.get('medications', []))}\n")
            self.result_box.insert('end', f"  Giải pháp: {', '.join(d.get('advice', []))}\n")

    def _display_rule_results(self, results):
        self.result_box.delete('1.0', 'end')
        self.result_box.insert('end', 'Top kết quả từ hệ chuyên gia:\n')
        for r in results:
            self.result_box.insert('end', f"- {r['name']}  (score={r['score']}, matched={r['matched']}/{r['total']})\n")
            self.result_box.insert('end', f"   Thuốc: {', '.join(r['medications'])}\n")
            self.result_box.insert('end', f"   Giải pháp: {', '.join(r['advice'])}\n")

    def _display_ml_results(self, preds):
        self.result_box.delete('1.0', 'end')
        self.result_box.insert('end', 'Kết quả ML baseline:\n')
        for pid, p in preds:
            d = self.expert.disease_map[pid]
            self.result_box.insert('end', f"- {d['name']} (prob={p:.3f})\n")
            self.result_box.insert('end', f"   Thuốc: {', '.join(d.get('medications', []))}\n")
            self.result_box.insert('end', f"   Giải pháp: {', '.join(d.get('advice', []))}\n")

# -------------------------
# 6. Main: đào tạo ML trên dataset giả lập và khởi chạy GUI
# -------------------------

def main():
    print('Tạo bộ dữ liệu giả lập từ knowledge base...')
    df = generate_synthetic_dataset(KB_JSON, n_samples_per_disease=400, noise_rate=0.25)
    print('Số mẫu:', len(df))
    # shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    ml = MLBaseline()
    # train (in thread nếu GUI cần phản hồi nhanh)
    def train_and_start():
        ml.fit(df['text'].tolist(), df['label'].tolist())
        print('Huấn luyện xong. Khởi chạy GUI...')
        # start GUI in main thread
        root = tk.Tk()
        expert = ExpertSystem(KB_JSON)
        app = DiagnosisApp(root, expert, ml)
        root.mainloop()

    # Đào tạo có thể mất vài giây -> dùng thread để không block stdout
    t = threading.Thread(target=train_and_start)
    t.start()

if __name__ == '__main__':
    main()
