
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sys
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pdf_interaction import PDFInteraction

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

pdf_system = PDFInteraction()

# Helper to check allowed file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            result = pdf_system.load_pdf(filepath)
            return render_template('result.html', result=result, filename=filename)
        else:
            flash('Invalid file type. Only PDF allowed.')
            return redirect(request.url)
    return render_template('index.html')

@app.route('/process/<filename>')
def process(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.process_pdf()
    return render_template('result.html', result=result, filename=filename)

@app.route('/analyze/<filename>')
def analyze(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.analyze_pdf()
    return render_template('result.html', result=result, filename=filename)

@app.route('/toc/<filename>')
def toc(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.extract_toc()
    return render_template('result.html', result=result, filename=filename)

@app.route('/index/<filename>')
def index_cmd(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.extract_index()
    return render_template('result.html', result=result, filename=filename)

@app.route('/components/<filename>')
def components(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.extract_components()
    return render_template('result.html', result=result, filename=filename)

@app.route('/component_tabs/<filename>')
def component_tabs(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.extract_components()
    components = result.get('components', [])
    # If result is a list, use it directly; if dict, try to extract list
    if isinstance(result, list):
        components = result
    elif isinstance(result, dict) and 'components' in result:
        components = result['components']
    return render_template('component_tabs.html', components=components, filename=filename)

@app.route('/upload_component_pdf/<filename>/<component_number>', methods=['POST'])
def upload_component_pdf(filename, component_number):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.extract_components()
    components = result.get('components', [])
    
    # Find the component by number - Fixed the duplicate get() call
    component = None
    for comp in components:
        if str(comp.get('number', '')) == str(component_number):
            component = comp
            break
    
    if not component:
        flash('Component not found.')
        return redirect(url_for('component_tabs', filename=filename))
    
    # Handle file upload
    if 'component_pdf' not in request.files:
        flash('No file part')
        return redirect(url_for('component_tabs', filename=filename))
    
    file = request.files['component_pdf']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('component_tabs', filename=filename))
    
    if file and allowed_file(file.filename):
        # Save in uploads/<component_number>_<component_title>/
        safe_title = component.get('title', 'component').replace(' ', '_').replace('/', '_')
        comp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"{component_number}_{safe_title}")
        os.makedirs(comp_dir, exist_ok=True)
        filename_secure = secure_filename(file.filename)
        file.save(os.path.join(comp_dir, filename_secure))
        flash(f'PDF uploaded for component {component_number}: {component.get("title", "")}')
    else:
        flash('Invalid file type. Only PDF allowed.')
    
    return redirect(url_for('component_tabs', filename=filename))

@app.route('/summary/<filename>')
def summary(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.get_pdf_summary()
    return render_template('result.html', result=result, filename=filename)

@app.route('/analysis/<filename>')
def analysis(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf_system.load_pdf(filepath)
    result = pdf_system.get_full_analysis()
    return render_template('result.html', result=result, filename=filename)

if __name__ == '__main__':
    app.run(debug=True)
