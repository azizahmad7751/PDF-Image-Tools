from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import os
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger
from zipfile import ZipFile

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
MERGED_FOLDER = 'merged'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MERGED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MERGED_FOLDER'] = MERGED_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pdf_to_images', methods=['GET', 'POST'])
def pdf_to_images():
    if request.method == 'POST':
        file = request.files['pdf_file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        doc = fitz.open(filepath)
        image_paths = []

        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            pix = page.get_pixmap()
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"page_{page_number + 1}.jpg")
            pix.save(output_path)
            image_paths.append(output_path)

        zip_path = os.path.join(app.config['MERGED_FOLDER'], 'converted_images.zip')
        with ZipFile(zip_path, 'w') as zipf:
            for img_path in image_paths:
                zipf.write(img_path, arcname=os.path.basename(img_path))

        return render_template('download.html', file_path=zip_path, file_name='converted_images.zip')
    return render_template('pdf_to_images.html')

@app.route('/images_to_pdf', methods=['GET', 'POST'])
def images_to_pdf():
    if request.method == 'POST':
        images = request.files.getlist('image_files')
        image_list = []

        for img in images:
            image = Image.open(img).convert('RGB')
            image_list.append(image)

        output_pdf_path = os.path.join(app.config['MERGED_FOLDER'], 'converted.pdf')
        image_list[0].save(output_pdf_path, save_all=True, append_images=image_list[1:])

        return render_template('download.html', file_path=output_pdf_path, file_name='converted.pdf')
    return render_template('images_to_pdf.html')

@app.route('/merge_pdfs', methods=['GET', 'POST'])
def merge_pdfs():
    if request.method == 'POST':
        files = request.files.getlist('pdf_files')
        merger = PdfMerger()

        for file in files:
            merger.append(file)

        output_path = os.path.join(app.config['MERGED_FOLDER'], 'merged.pdf')
        merger.write(output_path)
        merger.close()
        return render_template('download.html', file_path=output_path, file_name='merged.pdf')
    return render_template('merge_pdfs.html')

@app.route('/merge_images', methods=['GET', 'POST'])
def merge_images():
    if request.method == 'POST':
        images = request.files.getlist('image_files')
        pil_images = [Image.open(img) for img in images]

        total_height = sum(img.height for img in pil_images)
        max_width = max(img.width for img in pil_images)

        merged_image = Image.new('RGB', (max_width, total_height))
        y_offset = 0
        for img in pil_images:
            merged_image.paste(img, (0, y_offset))
            y_offset += img.height

        merged_path = os.path.join(app.config['MERGED_FOLDER'], 'merged_image.jpg')
        merged_image.save(merged_path)
        return render_template('download.html', file_path=merged_path, file_name='merged_image.jpg')
    return render_template('merge_images.html')

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(app.config['MERGED_FOLDER'], filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
