from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import zipfile
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the uploads and static directories exist
for dir_path in ['uploads', 'static/img']:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_THEMES = ['modern', 'minimal', 'creative', 'neon', 'terminal']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Create a default avatar if it doesn't exist
    default_avatar = os.path.join('static', 'img', 'default-avatar.png')
    if not os.path.exists(default_avatar):
        with open(default_avatar, 'w') as f:
            f.write('')  # Create an empty file as placeholder
    return render_template('index.html')

def process_form_data():
    data = {
        'name': request.form.get('name'),
        'title': request.form.get('title'),
        'about': request.form.get('about'),
        'email': request.form.get('email'),
        'skills': request.form.getlist('skills[]'),
        'projects': [],
        'education': [],
        'experience': [],
        'social_links': {},
        'theme': request.form.get('theme', 'modern')
    }
    
    # Handle profile image
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            data['profile_image'] = filename
    
    # Process projects
    project_titles = request.form.getlist('project_title[]')
    project_descriptions = request.form.getlist('project_description[]')
    project_links = request.form.getlist('project_link[]')
    
    for i in range(len(project_titles)):
        if project_titles[i]:
            data['projects'].append({
                'title': project_titles[i],
                'description': project_descriptions[i],
                'link': project_links[i]
            })
    
    # Process education
    edu_schools = request.form.getlist('edu_school[]')
    edu_degrees = request.form.getlist('edu_degree[]')
    edu_years = request.form.getlist('edu_year[]')
    edu_grades = request.form.getlist('edu_grade[]')
    
    for i in range(len(edu_schools)):
        if edu_schools[i]:
            data['education'].append({
                'school': edu_schools[i],
                'degree': edu_degrees[i],
                'year': edu_years[i],
                'grade': edu_grades[i]
            })
    
    # Process experience
    exp_companies = request.form.getlist('exp_company[]')
    exp_positions = request.form.getlist('exp_position[]')
    exp_durations = request.form.getlist('exp_duration[]')
    exp_descriptions = request.form.getlist('exp_description[]')
    
    for i in range(len(exp_companies)):
        if exp_companies[i]:
            data['experience'].append({
                'company': exp_companies[i],
                'position': exp_positions[i],
                'duration': exp_durations[i],
                'description': exp_descriptions[i]
            })
    
    # Process social links
    social_platforms = ['linkedin', 'github', 'twitter']
    for platform in social_platforms:
        link = request.form.get(f'social_{platform}')
        if link:
            data['social_links'][platform] = link
    
    # Process custom social links
    custom_social_urls = request.form.getlist('social_custom[]')
    for url in custom_social_urls:
        if url:
            data['social_links']['custom'] = url
    
    return data

@app.route('/preview', methods=['POST'])
def preview_portfolio():
    data = process_form_data()
    theme = request.form.get('theme', 'modern')
    
    if theme not in ALLOWED_THEMES:
        theme = 'modern'
    
    return render_template(f'themes/{theme}.html', data=data, now=datetime.now())

@app.route('/generate', methods=['POST'])
def generate_portfolio():
    data = process_form_data()
    theme = request.form.get('theme', 'modern')
    
    if theme not in ALLOWED_THEMES:
        theme = 'modern'
    
    rendered_html = render_template(f'themes/{theme}.html', data=data, now=datetime.now())
    
    # Create ZIP file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        # Add main HTML file
        zf.writestr('index.html', rendered_html)
        
        # Add profile image if exists
        if 'profile_image' in data:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], data['profile_image'])
            if os.path.exists(image_path):
                zf.write(image_path, f'images/{data["profile_image"]}')
        
        # Add CSS and other static files
        static_dir = os.path.join(app.static_folder, 'css', data['theme'])
        if os.path.exists(static_dir):
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.join('css', file)
                    zf.write(file_path, arc_name)
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'portfolio_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    )

if __name__ == '__main__':
    app.run(debug=True)
