from pathlib import Path
from PIL import Image

def convert_images_to_l(input_dir_path, output_dir_path):
    # フォルダのパスをPathオブジェクトとして定義
    input_dir = Path(input_dir_path)
    output_dir = Path(output_dir_path)
    
    # 出力先フォルダが存在しない場合は自動で作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 処理対象とする画像の拡張子
    extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'}
    
    # 入力フォルダ内のすべてのファイルをループ処理
    for file_path in input_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                # 1. 画像を開く（記事の変数名に合わせて `alpha` としています）
                alpha = Image.open(file_path)
                
                # 2. グレースケールに変換 (アルファ値を考慮しない変換)
                l_img = alpha.convert("L")
                
                # 3. 出力フォルダへの保存パスを組み立てて保存
                save_path = output_dir / file_path.name
                l_img.save(save_path)
                
                print(f"変換完了: {file_path.name}")
                
            except Exception as e:
                print(f"エラー ({file_path.name}): {e}")

if __name__ == "__main__":
    # --- 実行設定 ---
    # 変換したい画像が入っているフォルダのパス
    INPUT_FOLDER = "3手詰ハンドブック 新版" 
    # 変換後の画像を保存するフォルダのパス
    OUTPUT_FOLDER = "output_images"
    
    # 変換の実行
    convert_images_to_l(INPUT_FOLDER, OUTPUT_FOLDER)