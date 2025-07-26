#!/usr/bin/env python3
"""
Dependency Installation Script
Installs and configures all required dependencies for the AI PKM Tool
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Optional


class DependencyInstaller:
    """Manages installation of system and application dependencies"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.system = platform.system().lower()
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
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
            if check:
                raise
            return e
            
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            result = subprocess.run([command, "--version"], 
                                  capture_output=True, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False
            
    def install_python_dependencies(self):
        """Install Python backend dependencies"""
        self.log("Installing Python dependencies...")
        
        # Check Python version
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            raise RuntimeError("Python 3.9+ is required")
        self.log(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        
        # Create virtual environment if it doesn't exist
        venv_dir = self.backend_dir / "venv"
        if not venv_dir.exists():
            self.log("Creating virtual environment...")
            self.run_command([sys.executable, "-m", "venv", "venv"], cwd=self.backend_dir)
            
        # Get Python executable in venv
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
            self.log("Installing from requirements.txt...")
            self.run_command([str(pip_exe), "install", "-r", "requirements.txt"], cwd=self.backend_dir)
        else:
            self.log("Installing core dependencies...")
            core_deps = [
                "fastapi>=0.104.1",
                "uvicorn[standard]>=0.24.0",
                "sqlalchemy>=2.0.23",
                "chromadb>=0.4.18",
                "celery>=5.3.4",
                "redis>=5.0.1",
                "raganything>=0.1.0",
                "lightrag-hku>=0.1.0",
                "mineru>=0.2.0",
                "openai>=1.0.0",
                "torch>=2.5.1",
                "torchvision>=0.20.1",
                "torchaudio>=2.5.1",
                "python-dotenv>=1.0.0",
                "pydantic>=2.7.1,<3.0.0",
                "httpx>=0.25.2",
                "aiofiles>=23.2.1",
                "networkx>=3.2.1",
                "Pillow>=10.0.0",
                "PyMuPDF>=1.23.0",
                "pdfplumber>=0.9.0",
                "numpy>=1.22.5,<2.0.0"
            ]
            
            for dep in core_deps:
                try:
                    self.run_command([str(pip_exe), "install", dep], cwd=self.backend_dir)
                except subprocess.CalledProcessError as e:
                    self.log(f"Failed to install {dep}: {e}", "WARNING")
                    
        self.log("Python dependencies installed")
        
    def install_nodejs_dependencies(self):
        """Install Node.js frontend dependencies"""
        if not self.check_command_exists("node"):
            self.log("Node.js not found - skipping frontend dependencies", "WARNING")
            self.log("Please install Node.js 18+ from https://nodejs.org/", "INFO")
            return
            
        # Check Node.js version
        result = self.run_command(["node", "--version"], check=False)
        if result.returncode == 0:
            version_str = result.stdout.strip().lstrip('v')
            major_version = int(version_str.split('.')[0])
            if major_version < 18:
                self.log(f"Node.js {version_str} found - version 18+ recommended", "WARNING")
            else:
                self.log(f"Node.js {version_str} - OK")
        
        # Install frontend dependencies
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            self.log("Installing frontend dependencies...")
            self.run_command(["npm", "install"], cwd=self.frontend_dir)
            self.log("Frontend dependencies installed")
        else:
            self.log("No package.json found - skipping frontend dependencies", "WARNING")
            
    def install_redis(self):
        """Install Redis based on the operating system"""
        # First check if Redis is already available
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0)
            client.ping()
            self.log("Redis already available and running")
            return True
        except:
            pass
            
        self.log("Installing Redis...")
        
        if self.system == "windows":
            self.log("For Windows, Redis installation options:", "INFO")
            self.log("1. Use Docker: docker run -d -p 6379:6379 redis:7-alpine", "INFO")
            self.log("2. Use WSL2 and install Redis in Linux", "INFO")
            self.log("3. Download from https://github.com/microsoftarchive/redis/releases", "INFO")
            return False
            
        elif self.system == "darwin":  # macOS
            if self.check_command_exists("brew"):
                try:
                    self.run_command(["brew", "install", "redis"])
                    self.run_command(["brew", "services", "start", "redis"])
                    self.log("Redis installed and started with Homebrew")
                    return True
                except subprocess.CalledProcessError:
                    self.log("Failed to install Redis with Homebrew", "ERROR")
            else:
                self.log("Homebrew not found. Please install Redis manually.", "WARNING")
                self.log("Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"", "INFO")
            return False
            
        elif self.system == "linux":
            # Try different package managers
            package_managers = [
                (["sudo", "apt-get", "update"], ["sudo", "apt-get", "install", "-y", "redis-server"]),
                (["sudo", "yum", "update"], ["sudo", "yum", "install", "-y", "redis"]),
                (["sudo", "dnf", "update"], ["sudo", "dnf", "install", "-y", "redis"]),
                (["sudo", "pacman", "-Sy"], ["sudo", "pacman", "-S", "--noconfirm", "redis"])
            ]
            
            for update_cmd, install_cmd in package_managers:
                try:
                    self.run_command(update_cmd, check=False)
                    result = self.run_command(install_cmd, check=False)
                    if result.returncode == 0:
                        # Start and enable Redis
                        self.run_command(["sudo", "systemctl", "start", "redis-server"], check=False)
                        self.run_command(["sudo", "systemctl", "enable", "redis-server"], check=False)
                        # Alternative service names
                        self.run_command(["sudo", "systemctl", "start", "redis"], check=False)
                        self.run_command(["sudo", "systemctl", "enable", "redis"], check=False)
                        self.log("Redis installed and started")
                        return True
                except subprocess.CalledProcessError:
                    continue
                    
            self.log("Could not install Redis automatically", "ERROR")
            self.log("Please install Redis manually for your Linux distribution", "INFO")
            return False
            
        return False
        
    def install_docker(self):
        """Install Docker (guidance only)"""
        if self.check_command_exists("docker"):
            result = self.run_command(["docker", "--version"], check=False)
            if result.returncode == 0:
                self.log(f"Docker already installed: {result.stdout.strip()}")
                return True
                
        self.log("Docker not found. Installation guidance:", "INFO")
        
        if self.system == "windows":
            self.log("Install Docker Desktop from https://www.docker.com/products/docker-desktop", "INFO")
        elif self.system == "darwin":
            self.log("Install Docker Desktop from https://www.docker.com/products/docker-desktop", "INFO")
            if self.check_command_exists("brew"):
                self.log("Or use Homebrew: brew install --cask docker", "INFO")
        elif self.system == "linux":
            self.log("Install Docker using your package manager or:", "INFO")
            self.log("curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh", "INFO")
            
        return False
        
    def install_system_dependencies(self):
        """Install system-level dependencies"""
        self.log("Checking system dependencies...")
        
        if self.system == "linux":
            # Common system packages needed for Python packages
            system_packages = [
                "build-essential",
                "python3-dev",
                "libffi-dev",
                "libssl-dev",
                "libjpeg-dev",
                "libpng-dev",
                "libfreetype6-dev",
                "pkg-config"
            ]
            
            # Try to install with apt-get
            try:
                self.run_command(["sudo", "apt-get", "update"], check=False)
                for package in system_packages:
                    self.run_command(["sudo", "apt-get", "install", "-y", package], check=False)
                self.log("System dependencies installed (apt-get)")
            except:
                self.log("Could not install system dependencies automatically", "WARNING")
                
        elif self.system == "darwin":
            # macOS usually has what we need, but check for Xcode tools
            try:
                self.run_command(["xcode-select", "--install"], check=False)
                self.log("Xcode command line tools check completed")
            except:
                pass
                
        elif self.system == "windows":
            self.log("For Windows, ensure you have:", "INFO")
            self.log("- Microsoft C++ Build Tools", "INFO")
            self.log("- Git for Windows", "INFO")
            
    def configure_cuda(self):
        """Configure CUDA for MinerU acceleration (optional)"""
        self.log("Checking CUDA availability...")
        
        try:
            import torch
            if torch.cuda.is_available():
                cuda_version = torch.version.cuda
                device_count = torch.cuda.device_count()
                self.log(f"CUDA {cuda_version} available with {device_count} device(s)")
                
                # Update MinerU configuration
                config_file = self.backend_dir / "magic-pdf.json"
                if config_file.exists():
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    # Update device configuration
                    if 'device-mode' in config:
                        config['device-mode'] = 'cuda'
                        
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                        
                    self.log("Updated MinerU configuration for CUDA")
                else:
                    self.log("MinerU configuration file not found", "WARNING")
                    
            else:
                self.log("CUDA not available - using CPU mode")
                
        except ImportError:
            self.log("PyTorch not installed - cannot check CUDA", "WARNING")
        except Exception as e:
            self.log(f"Error checking CUDA: {e}", "WARNING")
            
    def verify_installation(self):
        """Verify that all dependencies are properly installed"""
        self.log("Verifying installation...")
        
        # Check Python packages
        venv_dir = self.backend_dir / "venv"
        if self.system == "windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            
        if python_exe.exists():
            test_imports = [
                "fastapi",
                "uvicorn",
                "celery",
                "redis",
                "sqlalchemy",
                "chromadb",
                "openai",
                "torch",
                "lightrag",
                "raganything"
            ]
            
            for module in test_imports:
                try:
                    result = self.run_command([
                        str(python_exe), "-c", f"import {module}; print(f'{module} - OK')"
                    ], check=False)
                    if result.returncode != 0:
                        self.log(f"{module} import failed", "WARNING")
                except:
                    self.log(f"Error testing {module}", "WARNING")
                    
        # Check Redis
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0)
            client.ping()
            self.log("Redis connection - OK")
        except:
            self.log("Redis connection failed", "WARNING")
            
        # Check Node.js
        if self.check_command_exists("node"):
            self.log("Node.js - OK")
        else:
            self.log("Node.js not found", "WARNING")
            
        # Check Docker
        if self.check_command_exists("docker"):
            self.log("Docker - OK")
        else:
            self.log("Docker not found", "WARNING")
            
    def run(self, skip_system: bool = False, skip_redis: bool = False, 
            skip_frontend: bool = False, cuda: bool = False):
        """Run the complete dependency installation"""
        self.log("Starting dependency installation...")
        
        try:
            if not skip_system:
                self.install_system_dependencies()
                
            self.install_python_dependencies()
            
            if not skip_frontend:
                self.install_nodejs_dependencies()
                
            if not skip_redis:
                self.install_redis()
                
            self.install_docker()
            
            if cuda:
                self.configure_cuda()
                
            self.verify_installation()
            
            self.log("Dependency installation completed!", "SUCCESS")
            self.log("Next steps:", "INFO")
            self.log("1. Run 'python setup.py' to complete setup", "INFO")
            self.log("2. Edit .env file with your configuration", "INFO")
            self.log("3. Start the application with scripts/start-dev.py", "INFO")
            
        except Exception as e:
            self.log(f"Installation failed: {e}", "ERROR")
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Install AI PKM Tool dependencies")
    parser.add_argument("--skip-system", action="store_true",
                       help="Skip system package installation")
    parser.add_argument("--skip-redis", action="store_true",
                       help="Skip Redis installation")
    parser.add_argument("--skip-frontend", action="store_true",
                       help="Skip frontend dependencies")
    parser.add_argument("--cuda", action="store_true",
                       help="Configure CUDA acceleration")
    
    args = parser.parse_args()
    
    installer = DependencyInstaller()
    installer.run(
        skip_system=args.skip_system,
        skip_redis=args.skip_redis,
        skip_frontend=args.skip_frontend,
        cuda=args.cuda
    )