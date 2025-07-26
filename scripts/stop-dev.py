#!/usr/bin/env python3
"""
Development Server Shutdown Script
Stops all development services and cleans up resources
"""

import os
import sys
import subprocess
import signal
import psutil
from pathlib import Path


class DevServerStopper:
    """Manages stopping development servers and services"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def find_processes_by_port(self, port: int):
        """Find processes using a specific port"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == port:
                        processes.append(proc)
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes
        
    def find_processes_by_name(self, name_patterns):
        """Find processes by command line patterns"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.cmdline())
                for pattern in name_patterns:
                    if pattern in cmdline:
                        processes.append(proc)
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes
        
    def stop_process(self, proc, name: str):
        """Stop a single process gracefully"""
        try:
            self.log(f"Stopping {name} (PID: {proc.pid})...")
            proc.terminate()
            
            # Wait for graceful shutdown
            try:
                proc.wait(timeout=5)
                self.log(f"Stopped {name}")
            except psutil.TimeoutExpired:
                self.log(f"Force killing {name}...")
                proc.kill()
                proc.wait()
                self.log(f"Force killed {name}")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.log(f"Could not stop {name}: {e}", "WARNING")
            
    def stop_backend_services(self):
        """Stop FastAPI backend and Celery workers"""
        self.log("Stopping backend services...")
        
        # Stop processes on port 8000 (FastAPI)
        backend_processes = self.find_processes_by_port(8000)
        for proc in backend_processes:
            self.stop_process(proc, "Backend server")
            
        # Stop Celery workers
        celery_patterns = [
            "celery worker",
            "celery -A app.core.celery_app worker",
            "app.core.celery_app"
        ]
        celery_processes = self.find_processes_by_name(celery_patterns)
        for proc in celery_processes:
            self.stop_process(proc, "Celery worker")
            
    def stop_frontend_services(self):
        """Stop React development server"""
        self.log("Stopping frontend services...")
        
        # Stop processes on port 3000 (React dev server)
        frontend_processes = self.find_processes_by_port(3000)
        for proc in frontend_processes:
            self.stop_process(proc, "Frontend server")
            
        # Stop npm/node processes related to the project
        npm_patterns = [
            "npm run dev",
            "vite",
            f"node_modules/.bin/vite"
        ]
        npm_processes = self.find_processes_by_name(npm_patterns)
        for proc in npm_processes:
            # Check if it's related to our project
            try:
                if str(self.root_dir) in ' '.join(proc.cmdline()):
                    self.stop_process(proc, "Frontend process")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
    def stop_redis_docker(self):
        """Stop Redis Docker container if running"""
        self.log("Stopping Redis Docker container...")
        try:
            # Check if container exists and is running
            result = subprocess.run([
                "docker", "ps", "--filter", "name=ai-pkm-redis", "--format", "{{.Names}}"
            ], capture_output=True, text=True, check=False)
            
            if "ai-pkm-redis" in result.stdout:
                subprocess.run(["docker", "stop", "ai-pkm-redis"], check=True)
                self.log("Stopped Redis container")
            else:
                self.log("Redis container not running")
                
        except subprocess.CalledProcessError as e:
            self.log(f"Error stopping Redis container: {e}", "WARNING")
        except FileNotFoundError:
            self.log("Docker not found - skipping Redis container stop", "WARNING")
            
    def cleanup_temp_files(self):
        """Clean up temporary files and caches"""
        self.log("Cleaning up temporary files...")
        
        temp_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/node_modules/.cache",
            "**/dist",
            "**/.vite"
        ]
        
        import glob
        for pattern in temp_patterns:
            for path in glob.glob(str(self.root_dir / pattern), recursive=True):
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    self.log(f"Cleaned: {path}")
                except Exception as e:
                    self.log(f"Could not clean {path}: {e}", "WARNING")
                    
    def run(self, cleanup: bool = False):
        """Stop all development services"""
        self.log("Stopping AI PKM Tool development environment...")
        
        try:
            # Stop all services
            self.stop_backend_services()
            self.stop_frontend_services()
            self.stop_redis_docker()
            
            if cleanup:
                self.cleanup_temp_files()
                
            self.log("All services stopped successfully!")
            
        except Exception as e:
            self.log(f"Error during shutdown: {e}", "ERROR")
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stop AI PKM Tool development services")
    parser.add_argument("--cleanup", action="store_true", 
                       help="Clean up temporary files and caches")
    
    args = parser.parse_args()
    
    stopper = DevServerStopper()
    stopper.run(cleanup=args.cleanup)