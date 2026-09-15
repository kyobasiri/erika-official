import os
import json
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
from PIL import Image

class WebPConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Erika Project - WebP 一括変換ツール")
        self.root.geometry("600x450")
        self.root.configure(bg="#1e1e2e")
        
        # プロジェクトのルートディレクトリ（現在の作業ディレクトリ）をデフォルトに
        self.base_dir = tk.StringVar(value=os.path.abspath(os.getcwd()))
        
        # UI Setup
        title_label = tk.Label(root, text="WebP 一括変換 & JSON自動更新ツール", font=("Helvetica", 14, "bold"), bg="#1e1e2e", fg="#cdd6f4")
        title_label.pack(pady=15)
        
        frame = tk.Frame(root, bg="#1e1e2e")
        frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(frame, text="プロジェクトルート (assets等がある場所):", bg="#1e1e2e", fg="#cdd6f4").pack(anchor=tk.W, pady=(0, 5))
        
        path_frame = tk.Frame(frame, bg="#1e1e2e")
        path_frame.pack(fill=tk.X)
        tk.Entry(path_frame, textvariable=self.base_dir, width=55, bg="#313244", fg="#cdd6f4", insertbackground="white").pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        tk.Button(path_frame, text=" 参照 ", command=self.browse_folder, bg="#45475a", fg="white", relief=tk.FLAT).pack(side=tk.LEFT)
        
        self.log_text = tk.Text(root, height=12, width=70, state=tk.DISABLED, bg="#11111b", fg="#a6e3a1", font=("Consolas", 9))
        self.log_text.pack(pady=10, padx=20)
        
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=560, mode='determinate')
        self.progress.pack(pady=5)
        
        self.start_btn = tk.Button(root, text="変換スタート", command=self.start_conversion, bg="#f39c12", fg="#111", font=("Helvetica", 12, "bold"), relief=tk.FLAT, padx=20, pady=5)
        self.start_btn.pack(pady=10)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.base_dir.get())
        if folder:
            self.base_dir.set(folder)
            
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_conversion(self):
        self.start_btn.config(state=tk.DISABLED, bg="#555")
        self.progress['value'] = 0
        self.log("変換処理を開始します...")
        
        # GUIがフリーズしないように別スレッドで実行
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        project_dir = Path(self.base_dir.get())
        gallery_dir = project_dir / "assets" / "images" / "gallery"
        
        if not gallery_dir.exists():
            self.log(f"[エラー] ギャラリーフォルダが見つかりません。\n{gallery_dir}\n正しいプロジェクトルートを選択してください。")
            self.reset_btn()
            return

        # 1. 画像ファイルの収集 (再帰的)
        png_files = list(gallery_dir.rglob("*.png")) + list(gallery_dir.rglob("*.jpg")) + list(gallery_dir.rglob("*.jpeg"))
        total = len(png_files)
        
        if total == 0:
            self.log("[情報] 変換対象の画像(.png, .jpg)が見つかりません。すでにWebP化されている可能性があります。")
            
            # 念のためJSONの更新だけ回す
            self.update_jsons(project_dir)
            self.reset_btn()
            return
            
        self.log(f"{total}件の画像をWebPに変換します...")
        self.progress['maximum'] = total
        
        # 2. WebP変換 & 元ファイル削除
        for i, img_path in enumerate(png_files, 1):
            webp_path = img_path.with_suffix('.webp')
            try:
                # PillowでWebP変換（品質85）
                with Image.open(img_path) as img:
                    img.save(webp_path, 'webp', quality=85)
                # 変換成功したら元ファイルを削除
                os.remove(img_path)
                self.log(f"[{i}/{total}] 変換完了: {img_path.name} -> {webp_path.name}")
            except Exception as e:
                self.log(f"[エラー] {img_path.name}: {e}")
                
            self.progress['value'] = i

        # 3. JSONファイルの更新 (gallery.json & alt_cache.json)
        self.update_jsons(project_dir)

        self.log("すべての処理が完了しました！")
        messagebox.showinfo("完了", "WebPへの一括変換とJSONの更新が完了しました。")
        self.reset_btn()
        
    def update_jsons(self, project_dir):
        self.log("JSONファイルの拡張子を更新中...")
        self.update_json_file(project_dir / "assets" / "gallery.json")
        self.update_json_file(project_dir / "alt_cache.json")
        
    def update_json_file(self, json_path):
        if not json_path.exists():
            self.log(f"[スキップ] {json_path.name} が見つかりません")
            return
            
        try:
            content = json_path.read_text(encoding='utf-8')
            # .png や .jpg という文字列を .webp に置換する
            content = content.replace('.png"', '.webp"').replace('.jpg"', '.webp"').replace('.jpeg"', '.webp"')
            json_path.write_text(content, encoding='utf-8')
            self.log(f"[更新完了] {json_path.name} 内の拡張子を.webpに書き換えました")
        except Exception as e:
            self.log(f"[エラー] JSON更新失敗 ({json_path.name}): {e}")

    def reset_btn(self):
        self.start_btn.config(state=tk.NORMAL, bg="#f39c12")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebPConverterApp(root)
    root.mainloop()
