#!/usr/bin/env python3
"""
AI PKM Tool Setup Script
Automated setup for local development environment
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import List, Optional


class SetupManager:
    """Manages the setup process for the AI PKM Tool"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.data_dir = self.root_dir / "data"
        self.system = platform.system().lower()
        
    def log(self, message: str, level: str = "INFO"):
        """Log setup messages"""
        print(f"[{level}] {message}")
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command"""
        self.log(f"Running: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.root_dir,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr.strip()}", "ERROR")
            raise
            
    def check_python_version(self):
        """Check if Python version is compatible"""
        self.log("Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            raise RuntimeError("Python 3.9+ is required")
        self.log(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        
    def check_node_version(self):
        """Check if Node.js version is compatible"""
        self.log("Checking Node.js version...")
        try:
            result = self.run_command(["node", "--version"], check=False)
            if result.returncode != 0:
                self.log("Node.js not found - please install Node.js 18+", "WARNING")
                return False
            
            version_str = result.stdout.strip().lstrip('v')
            major_version = int(version_str.split('.')[0])
            if major_version < 18:
                self.log(f"Node.js {version_str} found - version 18+ recommended", "WARNING")
            else:
                self.log(f"Node.js {version_str} - OK")
            return True
        except Exception as e:
            self.log(f"Error checking Node.js: {e}", "WARNING")
            return False
            
    def check_redis(self):
        """Check if Redis is available"""
        self.log("Checking Redis availability...")
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0)
            client.ping()
            self.log("Redis connection - OK")
            return True
        except Exception as e:
            self.log(f"Redis not available: {e}", "WARNING")
            return False
            
    def install_redis(self):
        """Install Redis based on the operating system"""
        self.log("Installing Redis...")
        
        if self.system == "windows":
            self.log("For Windows, please install Redis manually or use Docker:", "INFO")
            self.log("Option 1: Use Docker - docker run -d -p 6379:6379 redis:7-alpine", "INFO")
            self.log("Option 2: Install from https://github.com/microsoftarchive/redis/releases", "INFO")
            return False
            
        elif self.system == "darwin":  # macOS
            try:
                # Check if Homebrew is available
                self.run_command(["brew", "--version"], check=False)
                self.run_command(["brew", "install", "redis"])
                self.run_command(["brew", "services", "start", "redis"])
                return True
            except:
                self.log("Homebrew not found. Please install Redis manually.", "ERROR")
                return False
                
        elif self.system == "linux":
            try:
                # Try apt-get first (Ubuntu/Debian)
                self.run_command(["sudo", "apt-get", "update"], check=False)
                result = self.run_command(["sudo", "apt-get", "install", "-y", "redis-server"], check=False)
                if result.returncode == 0:
                    self.run_command(["sudo", "systemctl", "start", "redis-server"])
                    self.run_command(["sudo", "systemctl", "enable", "redis-server"])
                    return True
                    
                # Try yum (CentOS/RHEL)
                result = self.run_command(["sudo", "yum", "install", "-y", "redis"], check=False)
                if result.returncode == 0:
                    self.run_command(["sudo", "systemctl", "start", "redis"])
                    self.run_command(["sudo", "systemctl", "enable", "redis"])
                    return True
                    
                self.log("Could not install Redis automatically. Please install manually.", "ERROR")
                return False
            except Exception as e:
                self.log(f"Error installing Redis: {e}", "ERROR")
                return False
        
        return False
        
    def create_directories(self):
        """Create necessary directories"""
        self.log("Creating directories...")
        directories = [
            self.data_dir,
            self.data_dir / "uploads",
            self.data_dir / "processed",
            self.data_dir / "chroma_db",
            self.data_dir / "rag_storage",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {directory}")
            
    def setup_environment(self):
        """Setup environment variables"""
        self.log("Setting up environment variables...")
        env_file = self.root_dir / ".env"
        env_example = self.root_dir / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
            self.log("Created .env file from template")
            self.log("Please edit .env file with your configuration", "INFO")
        elif env_file.exists():
            self.log(".env file already exists")
        else:
            self.log("No .env.example found - creating basic .env", "WARNING")
            with open(env_file, 'w') as f:
                f.write("""# AI PKM Tool Environment Variables
# Database Configuration
DATABASE_URL=sqlite:///./data/pkm.db
CHROMA_DB_PATH=./data/chroma_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# File Storage Configuration
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
RAG_STORAGE_DIR=./data/rag_storage
MAX_FILE_SIZE=104857600

# Server Configuration
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# AI Configuration (optional)
# OPENAI_API_KEY=your_key_here
# LLM_MODEL=gpt-4o-mini
# EMBEDDING_MODEL=text-embedding-3-large

# MinerU Configuration
MINERU_DEVICE=cpu
MINERU_BACKEND=pipeline
MINERU_LANG=en
""")
            
    def install_backend_dependencies(self):
        """Install Python backend dependencies"""
        self.log("Installing backend dependencies...")
        
        # Check if virtual environment exists
        venv_dir = self.backend_dir / "venv"
        if not venv_dir.exists():
            self.log("Creating virtual environment...")
            self.run_command([sys.executable, "-m", "venv", "venv"], cwd=self.backend_dir)
            
        # Determine Python executable in venv
        if self.system == "windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"
            
        # Upgrade pip
        self.run_command([str(pip_exe), "install", "--upgrade", "pip"], cwd=self.backend_dir)
        
        # Install requirements
        requirements_file = self.backend_dir / "requirements.txt"
        if requirements_file.exists():
            self.run_command([str(pip_exe), "install", "-r", "requirements.txt"], cwd=self.backend_dir)
        else:
            self.log("requirements.txt not found", "ERROR")
            
    def install_frontend_dependencies(self):
        """Install Node.js frontend dependencies"""
        if not self.check_node_version():
            self.log("Skipping frontend setup - Node.js not available", "WARNING")
            return
            
        self.log("Installing frontend dependencies...")
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            self.run_command(["npm", "install"], cwd=self.frontend_dir)
        else:
            self.log("package.json not found - skipping frontend setup", "WARNING")
            
    def test_setup(self):
        """Test the setup by running basic checks"""
        self.log("Testing setup...")
        
        # Test Redis connection
        if not self.check_redis():
            self.log("Redis test failed", "WARNING")
            
        # Test backend imports
        try:
            venv_dir = self.backend_dir / "venv"
            if self.system == "windows":
                python_exe = venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = venv_dir / "bin" / "python"
                
            test_script = """
import sys
sys.path.append('.')
try:
    from app.main import app
    print("Backend imports - OK")
except Exception as e:
    print(f"Backend import error: {e}")
    sys.exit(1)
"""
            result = self.run_command([str(python_exe), "-c", test_script], cwd=self.backend_dir, check=False)
            if result.returncode == 0:
                self.log("Backend imports - OK")
            else:
                self.log("Backend import test failed", "WARNING")
                
        except Exception as e:
            self.log(f"Backend test error: {e}", "WARNING")
            
    def run_setup(self):
        """Run the complete setup process"""
        self.log("Starting AI PKM Tool setup...")
        
        try:
            # Check prerequisites
            self.check_python_version()
            self.check_node_version()
            
            # Create directories
            self.create_directories()
            
            # Setup environment
            self.setup_environment()
            
            # Install dependencies
            self.install_backend_dependencies()
            self.install_frontend_dependencies()
            
            # Check/install Redis
            if not self.check_redis():
                self.log("Redis not available - attempting installation...")
                if not self.install_redis():
                    self.log("Please install Redis manually or use Docker", "WARNING")
                    
            # Test setup
            self.test_setup()
            
            self.log("Setup completed successfully!", "SUCCESS")
            self.log("Next steps:", "INFO")
            self.log("1. Edit .env file with your configuration", "INFO")
            self.log("2. Run './scripts/start-dev.py' to start development servers", "INFO")
            self.log("3. Access the application at http://localhost:3000", "INFO")
            
        except Exception as e:
            self.log(f"Setup failed: {e}", "ERROR")
            sys.exit(1)


if __name__ == "__main__":
    setup = SetupManager()
    setup.run_setup()