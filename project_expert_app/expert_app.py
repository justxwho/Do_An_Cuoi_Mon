# expert_system.py
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from collections import defaultdict

KB_FILE = "knowledge_base.json"

class KnowledgeBase:
    def __init__(self, kb_file=KB_FILE):
        with open(kb_file, "r", encoding="utf-8") as f:
            self.rules = json.load(f)
        # index rules by consequent for backward chaining
        self.rules_by_consequent = defaultdict(list)
        for r in self.rules:
            self.rules_by_consequent[r["then"]].append(r)

class InferenceEngine:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def forward_chain(self, facts):
        """
        Simple forward chaining:
        - For each rule, if all antecedents in facts -> conclude consequent.
        - Return list of (conclusion, confidence, rule_id, explanation)
        """
        conclusions = []
        for r in self.kb.rules:
            antecedents = r.get("if", [])
            if all(a in facts for a in antecedents):
                conclusions.append({
                    "conclusion": r["then"],
                    "confidence": r.get("confidence", 1.0),
                    "rule_id": r.get("id"),
                    "explanation": r.get("explanation", "")
                })
        # aggregate by conclusion (take max confidence if multiple rules)
        agg = {}
        for c in conclusions:
            key = c["conclusion"]
            if key not in agg or c["confidence"] > agg[key]["confidence"]:
                agg[key] = c
        # sort by confidence desc
        return sorted(agg.values(), key=lambda x: x["confidence"], reverse=True)

    def backward_chain(self, goal, known_facts, trace=None, visited=None):
        """
        Backward chaining attempt to prove 'goal' from known_facts using rules.
        Returns (proved:bool, confidence:float, trace:list)
        - confidence is product of confidences along the proof path (approximation).
        - trace collects steps.
        """
        if trace is None:
            trace = []
        if visited is None:
            visited = set()

        # If goal already in known_facts
        if goal in known_facts:
            trace.append(f"Goal '{goal}' is in known facts.")
            return True, 1.0, trace

        if goal in visited:
            trace.append(f"Already tried '{goal}', avoid loop.")
            return False, 0.0, trace
        visited.add(goal)

        rules = self.kb.rules_by_consequent.get(goal, [])
        if not rules:
            trace.append(f"No rules conclude '{goal}'. Cannot prove.")
            return False, 0.0, trace

        # try each rule that can conclude goal
        best_conf = 0.0
        best_trace = None
        proved_any = False
        for r in rules:
            trace_local = trace.copy()
            trace_local.append(f"Trying rule {r.get('id')}: if {r.get('if')} then {r.get('then')} (c={r.get('confidence')})")
            antecedents = r.get("if", [])
            all_proved = True
            conf_product = r.get("confidence", 1.0)
            # prove each antecedent
            for ant in antecedents:
                proved, conf, trace_ant = self.backward_chain(ant, known_facts, trace=[], visited=visited)
                trace_local.extend(["  "+t for t in trace_ant])
                if not proved:
                    all_proved = False
                    break
                else:
                    conf_product *= conf
            if all_proved:
                trace_local.append(f"Rule {r.get('id')} proves '{goal}' with confidence approx {conf_product:.3f}")
                proved_any = True
                if conf_product > best_conf:
                    best_conf = conf_product
                    best_trace = trace_local

        if proved_any:
            return True, best_conf, best_trace
        else:
            trace.append(f"No rule could prove '{goal}' with given facts.")
            return False, 0.0, trace

# --- GUI ---
class ExpertSystemApp:
    def __init__(self, master):
        self.master = master
        master.title("Hệ chuyên gia chẩn đoán bệnh - Demo")
        master.geometry("800x520")

        self.kb = KnowledgeBase()
        self.engine = InferenceEngine(self.kb)

        # collect all symptoms from KB
        self.symptoms = sorted({s for r in self.kb.rules for s in r.get("if", [])})

        left = ttk.Frame(master, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Chọn triệu chứng (tích nhiều):").pack(anchor="w")
        self.vars = {}
        self.checkbuttons = []
        cb_frame = ttk.Frame(left)
        cb_frame.pack(fill=tk.Y, expand=True)
        for s in self.symptoms:
            v = tk.IntVar(value=0)
            cb = ttk.Checkbutton(cb_frame, text=s, variable=v)
            cb.pack(anchor="w")
            self.vars[s] = v
            self.checkbuttons.append(cb)

        btn_frame = ttk.Frame(left, padding=(0,10))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Gợi ý (Suy diễn tiến)", command=self.on_forward).pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Kiểm tra bệnh (Suy diễn lùi)", command=self.on_backward_popup).pack(fill=tk.X)

        # Right panel: results and trace
        right = ttk.Frame(master, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Kết quả gợi ý:").pack(anchor="w")
        self.result_box = ttk.Treeview(right, columns=("conf", "rule"), show="headings", height=6)
        self.result_box.heading("conf", text="Độ tin cậy")
        self.result_box.heading("rule", text="Rule ID")
        self.result_box.pack(fill=tk.X)

        ttk.Label(right, text="Giải thích / Trace:").pack(anchor="w", pady=(8,0))
        self.trace = scrolledtext.ScrolledText(right, height=18)
        self.trace.pack(fill=tk.BOTH, expand=True)

        # bottom actions
        bottom = ttk.Frame(master, padding=6)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(bottom, text="Xóa chọn", command=self.clear_all).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Thoát", command=master.quit).pack(side=tk.RIGHT)

    def get_selected_symptoms(self):
        return [s for s,v in self.vars.items() if v.get()==1]

    def on_forward(self):
        facts = self.get_selected_symptoms()
        self.trace.delete("1.0", tk.END)
        self.result_box.delete(*self.result_box.get_children())
        if not facts:
            messagebox.showinfo("Chú ý", "Vui lòng chọn ít nhất 1 triệu chứng.")
            return
        self.trace.insert(tk.END, f"Facts (triệu chứng): {facts}\n\n")
        results = self.engine.forward_chain(facts)
        if not results:
            self.trace.insert(tk.END, "Không tìm thấy chẩn đoán phù hợp với luật hiện có.\n")
            return
        self.trace.insert(tk.END, "Kết luận tìm được (theo độ tin cậy giảm dần):\n")
        for r in results:
            self.result_box.insert("", tk.END, values=(f"{r['confidence']:.2f}", r['rule_id']))
            self.trace.insert(tk.END, f"- {r['conclusion']} (conf={r['confidence']:.2f}) bằng {r['rule_id']}: {r['explanation']}\n")

    def on_backward_popup(self):
        popup = tk.Toplevel(self.master)
        popup.title("Suy diễn lùi - Kiểm tra một chẩn đoán")
        popup.geometry("360x160")
        ttk.Label(popup, text="Nhập tên chẩn đoán cần kiểm tra (ví dụ: cam_cum):").pack(padx=8, pady=(8,4), anchor="w")
        entry = ttk.Entry(popup)
        entry.pack(fill=tk.X, padx=8)
        def do_check():
            goal = entry.get().strip()
            if not goal:
                messagebox.showinfo("Chú ý", "Nhập tên chẩn đoán.")
                return
            facts = self.get_selected_symptoms()
            self.trace.delete("1.0", tk.END)
            self.result_box.delete(*self.result_box.get_children())
            self.trace.insert(tk.END, f"Known facts: {facts}\n\n")
            proved, conf, trace = self.engine.backward_chain(goal, set(facts))
            self.trace.insert(tk.END, f"Backward chaining result for '{goal}':\n")
            self.trace.insert(tk.END, "\n".join(trace) + "\n\n")
            if proved:
                self.trace.insert(tk.END, f"--> Có thể chứng minh '{goal}' (độ tin cậy xấp xỉ {conf:.3f})\n")
            else:
                self.trace.insert(tk.END, f"--> Không chứng minh được '{goal}' với các dữ kiện hiện có.\n")
            popup.destroy()
        ttk.Button(popup, text="Kiểm tra", command=do_check).pack(pady=10)

    def clear_all(self):
        for v in self.vars.values():
            v.set(0)
        self.result_box.delete(*self.result_box.get_children())
        self.trace.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpertSystemApp(root)
    root.mainloop()
