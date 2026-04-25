import os
import subprocess
import tempfile
from flask import Flask, request, render_template, send_file, after_this_request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    if not url:
        return "❌ No URL provided", 400

    # Create a temporary directory to store the video
    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    try:
        # yt-dlp command: download best MP4, no playlist, no live
        result = subprocess.run([
            'yt-dlp',
            '-f', 'best[ext=mp4]/best',
            '-o', output_template,
            '--no-playlist',
            '--no-live',
            url
        ], check=True, capture_output=True, text=True)

        # Find the downloaded file
        video_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
        if not video_files:
            return ("❌ Download failed. The video might be private, "
                    "age‑restricted, or not downloadable."), 400

        video_path = os.path.join(temp_dir, video_files[0])

        # Clean up after sending
        @after_this_request
        def cleanup(response):
            try:
                os.remove(video_path)
                os.rmdir(temp_dir)
            except OSError:
                pass
            return response

        return send_file(video_path, as_attachment=True,
                         download_name=video_files[0])

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or "Unknown download error"
        return f"❌ yt-dlp error: {error_msg}", 500
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}", 500

# Required for Render / production
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
