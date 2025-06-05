import json
import os
import subprocess
import tempfile
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    try:
        # Validate input
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        data = request.get_json()
        if not data or "script" not in data:
            return jsonify({"error": "Missing 'script' field in request"}), 400
        
        script = data["script"]
        
        # Create a temporary file for the script
        script_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, f"{script_id}.py")
        
        with open(script_path, "w") as f:
            f.write(script)
        
        # Create a wrapper script to capture the output and validate the main function
        wrapper_path = os.path.join(temp_dir, f"{script_id}_wrapper.py")
        with open(wrapper_path, "w") as f:
            f.write("""
import json
import sys
import traceback
from importlib.util import spec_from_file_location, module_from_spec

# Redirect stdout to capture print statements
class StdoutCapture:
    def __init__(self):
        self.content = ""
    
    def write(self, text):
        self.content += text
    
    def flush(self):
        pass

stdout_capture = StdoutCapture()
original_stdout = sys.stdout
sys.stdout = stdout_capture

try:
    # Import the user script
    spec = spec_from_file_location("user_script", sys.argv[1])
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Check if main function exists
    if not hasattr(module, "main"):
        print(json.dumps({
            "error": "No main() function found in the script"
        }))
        sys.exit(1)
    
    # Execute the main function
    result = module.main()
    
    # Restore stdout
    sys.stdout = original_stdout
    
    # Validate that the result is JSON serializable
    try:
        json.dumps(result)
    except (TypeError, OverflowError):
        print(json.dumps({
            "error": "The main() function must return a JSON serializable object"
        }))
        sys.exit(1)
    
    # Return the result and captured stdout
    print(json.dumps({
        "result": result,
        "stdout": stdout_capture.content
    }))
    
except Exception as e:
    sys.stdout = original_stdout
    print(json.dumps({
        "error": str(e),
        "traceback": traceback.format_exc()
    }))
    sys.exit(1)
""")
        
        # Execute the script using NSJail for security
        nsjail_cmd = [
            "nsjail",
            "--config", "/nsjail.config",
            "--cwd", temp_dir,
            "--",
            "/usr/bin/python3",
            wrapper_path,
            script_path
        ]
        
        process = subprocess.Popen(
            nsjail_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        try:
            # Try to parse stdout as JSON
            result = json.loads(stdout.decode('utf-8').strip())
            if "error" in result:
                return jsonify({"error": result["error"], "traceback": result.get("traceback", "")}), 400
            return jsonify(result), 200
        except json.JSONDecodeError:
            # If stdout is not valid JSON, return the error
            return jsonify({
                "error": "Failed to execute script",
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8')
            }), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 