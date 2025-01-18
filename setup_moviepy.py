import os
from pathlib import Path

# Create .moviepy directory in user's home directory
moviepy_dir = Path.home() / ".moviepy"
moviepy_dir.mkdir(exist_ok=True)

# Create the configuration file
config_content = """
IMAGEMAGICK_BINARY = r"C:\\Program Files\\ImageMagick-7.1.1-Q16\\magick.exe"
"""

config_file = moviepy_dir / "config_defaults.py"
with open(config_file, "w") as f:
    f.write(config_content)

print(f"Created MoviePy config at: {config_file}") 