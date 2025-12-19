import csv
import json
import os
import tkinter as tk
import argparse
import configparser
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any
import stats_utils

# Імена очікуваних колонок (case-insensitive)
EXPECTED_COLUMNS = {"timestamp", "temperature", "humidity", "pressure"}


class SmartHomeApp(tk.Tk):
    def __init__(self, thresholds=None):
        super().__init__()
        self.custom_thresholds = thresholds if thresholds else {}
        self.title("Smart Home — Statistical Processor")
        self.geometry("1000x700")

        # Дата структури
        self.data: Dict[str, Dict[str, float]] = {
            "temperature": {},
            "humidity": {},
            "pressure": {}
        }
        self.timestamps: List[str] = []

        # UI
        self.create_widgets()
        
        # Автозавантаження конфігурації
        if os.path.exists('config.ini'):
           self.load_config()

    def create_widgets(self):
        # Верхня панель: кнопки
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        btn_load = ttk.Button(top_frame, text="Відкрити CSV", command=self.load_csv)
        btn_load.pack(side=tk.LEFT, padx=4)

        btn_process = ttk.Button(top_frame, text="Запустити обробку", command=self.run_processing)
        btn_process.pack(side=tk.LEFT, padx=4)

        btn_save = ttk.Button(top_frame, text="Зберегти результати (JSON)", command=self.save_results)
        btn_save.pack(side=tk.LEFT, padx=4)

        # Розділювач
        ttk.Frame(top_frame, width=20).pack(side=tk.LEFT)

        # Кнопки налаштувань
        btn_save_cfg = ttk.Button(top_frame, text="Зберегти налаштування", command=self.save_config)
        btn_save_cfg.pack(side=tk.LEFT, padx=4)

        btn_load_cfg = ttk.Button(top_frame, text="Завантажити налаштування", command=self.load_config)
        btn_load_cfg.pack(side=tk.LEFT, padx=4)

        # Центр: розділений на ліву (таблиця) і праву (налаштування + результати)
        center = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        center.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Ліва частина — таблиця даних
        left_frame = ttk.Labelframe(center, text="Вхідні дані (CSV)", width="400")
        center.add(left_frame, weight=3)

        self.tree = ttk.Treeview(left_frame, show="headings")
        
        vsb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Права частина — налаштування та результати
        right_frame = ttk.Labelframe(center, text="Налаштування / Результати", width="200")
        center.add(right_frame, weight=1)

        # Налаштування: чекбокси
        settings_frame = ttk.Frame(right_frame)
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        ttk.Label(settings_frame, text="Обрати характеристики:").pack(anchor=tk.W)

        self.check_vars: Dict[str, Dict[str, tk.BooleanVar]] = {}
        stats = ["average", "min", "max", "median", "jumps"]
        for param in ["temperature", "humidity", "pressure"]:
            frm = ttk.LabelFrame(settings_frame, text=param.capitalize())
            frm.pack(fill=tk.X, padx=4, pady=4)
            self.check_vars[param] = {}
            for s in stats:
                val = (s in ["average", "min", "max"] if param != "humidity" else s in ["average"])
                var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(frm, text=s, variable=var)
                cb.pack(side=tk.LEFT, padx=2, pady=2)
                self.check_vars[param][s] = var

        # Результати (Вкладки)
        result_frame = ttk.Frame(right_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        ttk.Label(result_frame, text="Результати:").pack(anchor=tk.W)
        
        self.res_notebook = ttk.Notebook(result_frame)
        self.res_notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка 1: Текстовий Звіт
        tab_report = ttk.Frame(self.res_notebook)
        self.res_notebook.add(tab_report, text="Звіт")

        self.report_text = tk.Text(tab_report, height=15, width=40, font=("Consolas", 10))
        rep_vsb = ttk.Scrollbar(tab_report, orient="vertical", command=self.report_text.yview)
        rep_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_text.configure(yscrollcommand=rep_vsb.set)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Вкладка 2: JSON
        tab_json = ttk.Frame(self.res_notebook)
        self.res_notebook.add(tab_json, text="JSON")

        self.result_json = tk.Text(tab_json, height=15, wrap=tk.WORD)
        json_vsb = ttk.Scrollbar(tab_json, orient="vertical", command=self.result_json.yview)
        json_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_json.configure(yscrollcommand=json_vsb.set)
        self.result_json.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Статусбар
        self.status_var = tk.StringVar(value="Готово")
        status = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        self.after(100, lambda: center.sashpos(0, int(self.winfo_width() * 5/9)))

    def set_status(self, text: str):
        self.status_var.set(text)
        self.update_idletasks()

    def clear_table(self):
        for c in self.tree.get_children():
            self.tree.delete(c)
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Виберіть CSV файл",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                col_map = {}
                if reader.fieldnames:
                    for h in reader.fieldnames:
                        clean_name = h.strip().lower()
                        if clean_name in EXPECTED_COLUMNS:
                            col_map[clean_name] = h

                self.data = {"temperature": {}, "humidity": {}, "pressure": {}}
                self.timestamps = []

                for row in reader:
                    ts_key = col_map.get("timestamp")
                    if not ts_key or ts_key not in row:
                        continue
                        
                    ts = row[ts_key].strip()
                    if not ts:
                        continue

                    has_data = False
                    for field in ("temperature", "humidity", "pressure"):
                        field_key = col_map.get(field)
                        if field_key and field_key in row:
                            raw = row[field_key].strip()
                            if raw:
                                try:
                                    val = float(raw)
                                    self.data[field][ts] = val
                                    has_data = True
                                except ValueError:
                                    pass
                    
                    if has_data:
                        self.timestamps.append(ts)

            self.display_table()
            self.set_status(f"Завантажено: {os.path.basename(path)} — записів: {len(self.timestamps)}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося прочитати файл:\n{e}")
            self.set_status("Помилка при завантаженні")

    def display_table(self):
        cols = ["timestamp", "temperature", "humidity", "pressure"]
        self.clear_table()
        self.tree["columns"] = cols
        for col in cols:
            self.tree.column(col, width=120, anchor=tk.CENTER)
            self.tree.heading(col, text=col)

        timestamps_unique = self.timestamps

        for ts in timestamps_unique:
            vals = []
            for key in cols:
                if key == "timestamp":
                    vals.append(ts)
                else:
                    v = self.data.get(key, {}).get(ts, "")
                    vals.append("" if v is None else str(v))
            self.tree.insert("", tk.END, values=vals)

    def collect_stats_config(self) -> Dict[str, List[str]]:
        cfg: Dict[str, List[str]] = {}
        for param, checks in self.check_vars.items():
            chosen = [name for name, var in checks.items() if var.get()]
            cfg[param] = chosen
        return cfg

    def generate_simple_report(self, results: Dict[str, Any]):
        """Генерує текстовий звіт."""
        self.report_text.delete("1.0", tk.END)
        
        report_lines = []
        report_lines.append("=== ЗВІТ ОБРОБКИ ДАНИХ ===\n")
        
        for param, stats in results.items():
            if not stats:
                continue
            
            report_lines.append(f"[{param.upper()}]")
            
            if "average" in stats:
                report_lines.append(f"  Середнє:  {stats['average']}")
            if "min" in stats and "max" in stats:
                report_lines.append(f"  Діапазон: {stats['min']} ... {stats['max']}")
            if "median" in stats:
                report_lines.append(f"  Медіана:  {stats['median']}")
            if "jumps" in stats:
                jumps = stats['jumps']
                count = len(jumps) if isinstance(jumps, list) else 0
                report_lines.append(f"  Стрибків: {count}")
            
            report_lines.append("-" * 30 + "\n")
        
        self.report_text.insert(tk.END, "\n".join(report_lines))

    def run_processing(self):
        if not self.timestamps:
            messagebox.showwarning("Немає даних", "Спочатку завантажте CSV з даними.")
            return

        cfg = self.collect_stats_config()
        results: Dict[str, Any] = {}
        timestamps = self.timestamps

        for param in ("temperature", "humidity", "pressure"):
            values = [self.data.get(param, {}).get(ts) for ts in timestamps]
            res = stats_utils.compute_stats_for_parameter(
                timestamps, 
                values, 
                cfg.get(param, []), 
                param,
                thresholds=self.custom_thresholds
            )
            results[param] = res

        self.generate_simple_report(results)

        self.result_json.delete("1.0", tk.END)
        pretty = json.dumps(results, ensure_ascii=False, indent=4)
        self.result_json.insert(tk.END, pretty)
        
        self.res_notebook.select(0)
        
        self.current_results = results
        self.set_status("Обробка завершена")

    def save_results(self):
        if not hasattr(self, "current_results") or not self.current_results:
            messagebox.showwarning("Немає результатів", "Спочатку виконайте обробку.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Зберегти результати"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.current_results, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Збережено", f"Файл збережено:\n{path}")
            self.set_status(f"Збережено: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти:\n{e}")

    def save_config(self):
        config = configparser.ConfigParser()

        current_thresholds = self.custom_thresholds if self.custom_thresholds else stats_utils.DEFAULT_THRESHOLDS
        config['Thresholds'] = {
            'temperature': str(current_thresholds.get('temperature', 7.0)),
            'humidity': str(current_thresholds.get('humidity', 20.0)),
            'pressure': str(current_thresholds.get('pressure', 5000.0))
        }

        for param, vars_dict in self.check_vars.items():
            section_name = f"Stats_{param}"
            config[section_name] = {}
            for stat_name, var in vars_dict.items():
                config[section_name][stat_name] = str(var.get())

        try:
            with open('config.ini', 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            messagebox.showinfo("Налаштування", "Збережено у config.ini")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти:\n{e}")

    def load_config(self):
        if not os.path.exists('config.ini'):
            messagebox.showwarning("Налаштування", "Файл config.ini не знайдено.")
            return

        config = configparser.ConfigParser()
        try:
            config.read('config.ini', encoding='utf-8')

            if 'Thresholds' in config:
                if not self.custom_thresholds: self.custom_thresholds = {}
                th = config['Thresholds']
                if 'temperature' in th: self.custom_thresholds['temperature'] = float(th['temperature'])
                if 'humidity' in th: self.custom_thresholds['humidity'] = float(th['humidity'])
                if 'pressure' in th: self.custom_thresholds['pressure'] = float(th['pressure'])

            for param, vars_dict in self.check_vars.items():
                section_name = f"Stats_{param}"
                if section_name in config:
                    for stat_name, var in vars_dict.items():
                        val = config.getboolean(section_name, stat_name, fallback=var.get())
                        var.set(val)
            
            messagebox.showinfo("Налаштування", "Налаштування завантажено.")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка зчитування:\n{e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Home App", add_help=False)
    
    parser.add_argument("-t", type=float, default=7.0, help="Поріг температури")
    parser.add_argument("-h", type=float, default=20.0, help="Поріг вологості")
    parser.add_argument("-p", type=float, default=5000.0, help="Поріг тиску")
    
    args = parser.parse_args()
    
    cli_thresholds = {
        "temperature": args.t,
        "humidity": args.h,
        "pressure": args.p
    }
    
    app = SmartHomeApp(thresholds=cli_thresholds)
    app.mainloop()
