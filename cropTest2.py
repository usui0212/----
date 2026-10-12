import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw

class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("画像複数切り抜きツール (ウィンドウフィット版)")
        self.root.geometry("800x600")
        
        self.pil_image = None       # 元のオリジナル画像
        self.display_image = None   # ウィンドウ表示用にリサイズした画像
        self.tk_image = None
        self.scale = 1.0            # 元画像と表示画像の倍率
        self.offset_x = 0           # 中央配置時のオフセット
        self.offset_y = 0
        
        self.shape_type = tk.StringVar(value="rect")
        self.shapes = []            # 保存データ: (shape_type, (orig_x1, orig_y1, orig_x2, orig_y2))
        self.canvas_shapes = []     # キャンバス上の描画要素IDリスト
        
        self.start_x = None
        self.start_y = None
        self.current_shape_id = None
        
        self.setup_ui()

    def setup_ui(self):
        # コントロールパネル
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Button(control_frame, text="画像を開く", command=self.open_image).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(control_frame, text="四角", variable=self.shape_type, value="rect").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(control_frame, text="丸 (楕円)", variable=self.shape_type, value="oval").pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="選択枠をすべてクリア", command=self.clear_shapes).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="切り抜いて保存", command=self.crop_and_save).pack(side=tk.LEFT, padx=5)
        
        # 画像表示用キャンバス（ウィンドウサイズに合わせて自動伸縮）
        self.canvas = tk.Canvas(self.root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # イベントバインド
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        if not file_path:
            return
        
        self.pil_image = Image.open(file_path)
        self.shapes.clear()
        self.redraw_image()

    def on_resize(self, event):
        """ウィンドウサイズ変更時に画像を再描画"""
        if self.pil_image:
            self.redraw_image()

    def redraw_image(self):
        """アスペクト比を維持してキャンバスサイズに合わせて描画"""
        if not self.pil_image:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        img_w, img_h = self.pil_image.size
        
        # 縮小・拡大倍率の計算 (アスペクト比維持)
        self.scale = min(canvas_w / img_w, canvas_h / img_h)
        new_w = int(img_w * self.scale)
        new_h = int(img_h * self.scale)
        
        # 中央配置のためのオフセット
        self.offset_x = (canvas_w - new_w) // 2
        self.offset_y = (canvas_h - new_h) // 2

        # リサイズと表示
        self.display_image = self.pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=self.tk_image)
        
        # 既存の選択枠を新しいスケールに合わせて描き直す
        for stype, orig_bbox in self.shapes:
            canvas_bbox = self.orig_to_canvas_coords(orig_bbox)
            if stype == "rect":
                self.canvas.create_rectangle(*canvas_bbox, outline="blue", width=2)
            else:
                self.canvas.create_oval(*canvas_bbox, outline="blue", width=2)

    def canvas_to_orig_coords(self, x, y):
        """キャンバス座標を元画像のピクセル座標に変換"""
        orig_x = (x - self.offset_x) / self.scale
        orig_y = (y - self.offset_y) / self.scale
        # 元画像の範囲内に収める
        orig_x = max(0, min(self.pil_image.width, orig_x))
        orig_y = max(0, min(self.pil_image.height, orig_y))
        return orig_x, orig_y

    def orig_to_canvas_coords(self, orig_bbox):
        """元画像のピクセル座標をキャンバス座標に変換"""
        x1, y1, x2, y2 = orig_bbox
        cx1 = x1 * self.scale + self.offset_x
        cy1 = y1 * self.scale + self.offset_y
        cx2 = x2 * self.scale + self.offset_x
        cy2 = y2 * self.scale + self.offset_y
        return cx1, cy1, cx2, cy2

    def on_button_press(self, event):
        if not self.pil_image:
            return
        self.start_x, self.start_y = event.x, event.y
        
        shape = self.shape_type.get()
        if shape == "rect":
            self.current_shape_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2
            )
        else:
            self.current_shape_id = self.canvas.create_oval(
                self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2
            )

    def on_move_press(self, event):
        if not self.current_shape_id:
            return
        self.canvas.coords(self.current_shape_id, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        if not self.current_shape_id:
            return
        
        # キャンバス上の座標を取得
        cx1 = min(self.start_x, event.x)
        cy1 = min(self.start_y, event.y)
        cx2 = max(self.start_x, event.x)
        cy2 = max(self.start_y, event.y)
        
        if (cx2 - cx1) > 5 and (cy2 - cy1) > 5:
            # キャンバス座標を元画像のピクセル座標に変換して保存
            ox1, oy1 = self.canvas_to_orig_coords(cx1, cy1)
            ox2, oy2 = self.canvas_to_orig_coords(cx2, cy2)
            
            self.shapes.append((self.shape_type.get(), (ox1, oy1, ox2, oy2)))
            self.canvas.itemconfig(self.current_shape_id, outline="blue")
        else:
            self.canvas.delete(self.current_shape_id)
            
        self.current_shape_id = None

    def clear_shapes(self):
        self.shapes.clear()
        self.redraw_image()

    def crop_and_save(self):
        if not self.pil_image or not self.shapes:
            messagebox.showwarning("警告", "画像を開くか、1つ以上の領域を指定してください。")
            return
        
        save_dir = filedialog.askdirectory(title="保存先のフォルダを選択")
        if not save_dir:
            return
            
        for i, (shape_type, bbox) in enumerate(self.shapes, 1):
            # 元画像の座標範囲でクロップ
            crop_bbox = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
            cropped = self.pil_image.crop(crop_bbox)
            save_path = os.path.join(save_dir, f"crop_{i}.png")
            
            if shape_type == "oval":
                mask = Image.new("L", cropped.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, cropped.width, cropped.height), fill=255)
                
                cropped_rgba = cropped.convert("RGBA")
                cropped_rgba.putalpha(mask)
                cropped_rgba.save(save_path)
            else:
                cropped.save(save_path)
                
        messagebox.showinfo("完了", f"{len(self.shapes)}枚の画像をオリジナル画質で保存しました。")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCropperApp(root)
    root.mainloop()