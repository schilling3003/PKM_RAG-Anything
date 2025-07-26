#!/usr/bin/env python3
"""
Development Server Startup Script
Starts all services required for local development
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from typing import List, Optional


class DevServerManager:
    """Manages development servers and services"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.processes: List[subprocess.Popen] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_redis(self) -> bool:
        """Check if Redis is running"""
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0)
            client.ping()
            return True
        except Exception:
            return False
            
    def start_redis_docker(self):
        """Start Redis using Docker if not running"""
        self.log("Starting Redis with Docker...")
        try:
            # Check if Redis container already exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=ai-pkm-redis", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if "ai-pkm-redis" in result.stdout:
                # Container exists, start it
                subprocess.run(["docker", "start", "ai-pkm-redis"], check=True)
                self.log("Started existing Redis container")
            else:
                # Create and start new container
                subprocess.run([
                    "docker", "run", "-d",
                    "--name", "ai-pkm-redis",
                    "-p", "6379:6379",
                    "redis:7-alpine",
                    "redis-server", "--appendonly", "yes"
                ], check=True)
                self.log("Created and started new Redis container")
                
            # Wait for Redis to be ready
            for i in range(10):
                if self.check_redis():
                    self.log("Redis is ready")
                    return True
                time.sleep(1)
                
            self.log("Redis failed to start", "ERROR")
            return False
            
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to start Redis with Docker: {e}", "ERROR")
            return False
        except FileNotFoundError:
            self.log("Docker not found - please install Docker or Redis manually", "ERROR")
            return False
            
    def get_python_executable(self) -> Path:
        """Get the Python executable from virtual environment"""
        venv_dir = self.backend_dir / "venv"
        if os.name == 'nt':  # Windows
            return venv_dir / "Scripts" / "python.exe"
        else:
            return venv_dir / "bin" / "python"
            
    def start_backend(self):
        """Start the FastAPI backend server"""
        self.log("Starting backend server...")
        python_exe = self.get_python_executable()
        
        if not python_exe.exists():
            self.log("Virtual environment not found. Run setup.py first.", "ERROR")
            return None
            
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.backend_dir)
        
        process = subprocess.Popen([
            str(python_exe), "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=self.backend_dir, env=env)
        
        self.processes.append(process)
        self.log("Backend server started (PID: {})".format(process.pid))
        return process
        
    def start_celery_worker(self):
        """Start the Celery worker"""
        self.log("Starting Celery worker...")
        python_exe = self.get_python_executable()
        
        if not python_exe.exists():
            self.log("Virtual environment not found. Run setup.py first.", "ERROR")
            return None
            
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.backend_dir)
        
        process = subprocess.Popen([
            str(python_exe), "-m", "celery",
            "-A", "app.core.celery_app",
            "worker",
            "--loglevel=info"
        ], cwd=self.backend_dir, env=env)
        
        self.processes.append(process)
        self.log("Celery worker started (PID: {})".format(process.pid))
        return process
        
    def start_frontend(self):
        """Start the React frontend development server"""
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            self.log("Frontend not found - skipping", "WARNING")
            return None
            
        self.log("Starting frontend server...")
        
        try:
            process = subprocess.Popen([
                "npm", "run", "dev"
            ], cwd=self.frontend_dir)
            
            self.processes.append(process)
            self.log("Frontend server started (PID: {})".format(process.pid))
            return process
            
        except FileNotFoundError:
            self.log("npm not found - please install Node.js", "ERROR")
            return None
            
    def cleanup(self):
        """Stop all running processes"""
        self.log("Stopping all services...")
        
        for process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    self.log(f"Stopped process (PID: {process.pid})")
            except Exception as e:
                self.log(f"Error stopping process: {e}", "ERROR")
                
        self.processes.clear()
        
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.log("Received interrupt signal - shutting down...")
        self.cleanup()
        sys.exit(0)
        
    def wait_for_services(self):
        """Wait for all services to be ready"""
        self.log("Waiting for services to be ready...")
        
        # Wait for backend
        for i in range(30):
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    self.log("Backend is ready")
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.log("Backend failed to start", "WARNING")
            
        # Wait for frontend (if running)
        if any("npm" in str(p.args) for p in self.processes if p.poll() is None):
            self.log("Frontend starting... (this may take a moment)")
            time.sleep(5)  # Give frontend time to compile
            
    def run(self):
        """Start all development services"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            self.log("Starting AI PKM Tool development environment...")
            
            # Check and start Redis
            if not self.check_redis():
                self.log("Redis not running - attempting to start with Docker...")
                if not self.start_redis_docker():
                    self.log("Failed to start Redis. Please start it manually.", "ERROR")
                    return
                    
            # Start backend services
            backend_process = self.start_backend()
            if not backend_process:
                self.log("Failed to start backend", "ERROR")
                return
                
            # Start Celery worker
            celery_process = self.start_celery_worker()
            if not celery_process:
                self.log("Failed to start Celery worker", "ERROR")
                
            # Start frontend
            frontend_process = self.start_frontend()
            
            # Wait for services to be ready
            self.wait_for_services()
            
            self.log("All services started successfully!")
            self.log("Backend API: http://localhost:8000")
            self.log("API Documentation: http://localhost:8000/docs")
            if frontend_process:
                self.log("Frontend: http://localhost:3000")
            self.log("Press Ctrl+C to stop all services")
            
            # Keep the script running
            while True:
                # Check if any process has died
                for process in self.processes[:]:  # Copy list to avoid modification during iteration
                    if process.poll() is not None:
                        self.log(f"Process (PID: {process.pid}) has stopped", "WARNING")
                        self.processes.remove(process)
                        
                if not self.processes:
                    self.log("All processes have stopped", "ERROR")
                    break
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.log("Interrupted by user")
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
        finally:
            self.cleanup()


if __name__ == "__main__":
    manager = DevServerManager()
    manager.run()