import os
import sys
import subprocess

# Set development database URL
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///retailsight_dev.db')

# Run Streamlit as a subprocess using the same Python interpreter
cmd = [sys.executable, '-m', 'streamlit', 'run', 'Retailsights/app.py']
print('Starting Streamlit with command:', ' '.join(cmd))
subprocess.run(cmd, check=True)
