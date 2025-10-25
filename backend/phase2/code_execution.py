from flask import Blueprint, request, jsonify
import subprocess
import os
import time

code_execution_bp = Blueprint('code_execution', __name__)

# Whitelist for allowed script paths
ALLOWED_DIR = 'src/'
EXECUTION_TIMEOUT = 10  # seconds

def validate_script_path(script_path):
    """
    Validate that the script path is within the allowed directory.
    """
    # Normalize the path to prevent directory traversal attacks
    normalized_path = os.path.normpath(script_path)
    
    # Check if the path starts with the allowed directory
    if not normalized_path.startswith(ALLOWED_DIR):
        return False
    
    # Additional check to prevent absolute paths
    if os.path.isabs(normalized_path):
        return False
    
    return True

def execute_code(script_path, code_content):
    """
    Execute code in a subprocess with security checks and timeout.
    """
    try:
        # Create a temporary file with the code content
        temp_file = f"/tmp/exec_{int(time.time() * 1000)}.py"
        
        with open(temp_file, 'w') as f:
            f.write(code_content)
        
        # Execute the code in a subprocess with timeout
        result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            # Security: Don't allow shell execution
            shell=False,
            # Security: Run with limited environment
            env={'PATH': os.environ.get('PATH', '/usr/bin:/bin')}
        )
        
        # Clean up temporary file
        os.remove(temp_file)
        
        return {
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    except subprocess.TimeoutExpired:
        # Clean up temporary file on timeout
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return {
            'success': False,
            'error': f'Execution timed out after {EXECUTION_TIMEOUT} seconds',
            'stdout': '',
            'stderr': ''
        }
    
    except Exception as e:
        # Clean up temporary file on error
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
        return {
            'success': False,
            'error': str(e),
            'stdout': '',
            'stderr': ''
        }

@code_execution_bp.route('/execute', methods=['POST'])
def execute():
    """
    Execute code endpoint.
    Expects JSON payload with 'script_path' and 'code_content' fields.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        script_path = data.get('script_path')
        code_content = data.get('code_content')
        
        # Validate required fields
        if not script_path or not code_content:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: script_path and code_content'
            }), 400
        
        # Validate script path against whitelist
        if not validate_script_path(script_path):
            return jsonify({
                'success': False,
                'error': f'Invalid script path. Only scripts in {ALLOWED_DIR} directory are allowed'
            }), 403
        
        # Execute the code
        execution_result = execute_code(script_path, code_content)
        
        if execution_result['success']:
            return jsonify(execution_result), 200
        else:
            return jsonify(execution_result), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500
