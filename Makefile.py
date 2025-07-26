#!/usr/bin/env python3
"""
Makefile-style Task Runner
Provides common development tasks for the AI PKM Tool
"""

import os
import sys
import subprocess
from pathlib import Path


class TaskRunner:
    """Runs common development tasks"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages"""
        print(f"[{level}] {message}")
        
    def run_command(self, command: list, cwd: Path = None):
        """Run a command"""
        self.log(f"Running: {' '.join(command)}")
        result = subprocess.run(command, cwd=cwd or self.root_dir)
        return result.returncode == 0
        
    def install(self):
        """Install all dependencies"""
        self.log("Installing dependencies...")
        return self.run_command([sys.executable, "scripts/install-deps.py"])
        
    def setup(self):
        """Run initial setup"""
        self.log("Running setup...")
        return self.run_command([sys.executable, "setup.py"])
        
    def dev(self):
        """Start development environment"""
        self.log("Starting development environment...")
        return self.run_command([sys.executable, "scripts/start-dev.py"])
        
    def stop(self):
        """Stop development environment"""
        self.log("Stopping development environment...")
        return self.run_command([sys.executable, "scripts/stop-dev.py"])
        
    def docker_dev(self):
        """Start development environment with Docker"""
        self.log("Starting Docker development environment...")
        return self.run_command([sys.executable, "scripts/start-docker.py", "--mode", "dev", "--build"])
        
    def docker_prod(self):
        """Start production environment with Docker"""
        self.log("Starting Docker production environment...")
        return self.run_command([sys.executable, "scripts/start-docker.py", "--mode", "prod", "--build"])
        
    def docker_stop(self):
        """Stop Docker environment"""
        self.log("Stopping Docker environment...")
        return self.run_command([sys.executable, "scripts/stop-docker.py"])
        
    def health(self):
        """Run health checks"""
        self.log("Running health checks...")
        return self.run_command([sys.executable, "scripts/health-check.py"])
        
    def test(self):
        """Run tests"""
        self.log("Running tests...")
        # Backend tests
        backend_success = self.run_command([
            sys.executable, "-m", "pytest", "tests/"
        ], cwd=self.root_dir / "backend")
        
        # Frontend tests (if available)
        frontend_success = True
        package_json = self.root_dir / "frontend" / "package.json"
        if package_json.exists():
            frontend_success = self.run_command([
                "npm", "test", "--", "--run"
            ], cwd=self.root_dir / "frontend")
            
        return backend_success and frontend_success
        
    def clean(self):
        """Clean up temporary files"""
        self.log("Cleaning up...")
        return self.run_command([sys.executable, "scripts/stop-dev.py", "--cleanup"])
        
    def reset(self):
        """Reset the environment (clean + setup)"""
        self.log("Resetting environment...")
        self.clean()
        return self.setup()
        
    def help(self):
        """Show available tasks"""
        tasks = {
            "install": "Install all dependencies",
            "setup": "Run initial setup",
            "dev": "Start development environment",
            "stop": "Stop development environment",
            "docker-dev": "Start development with Docker",
            "docker-prod": "Start production with Docker",
            "docker-stop": "Stop Docker environment",
            "health": "Run health checks",
            "test": "Run tests",
            "clean": "Clean up temporary files",
            "reset": "Reset environment (clean + setup)",
            "help": "Show this help message"
        }
        
        print("Available tasks:")
        for task, description in tasks.items():
            print(f"  {task:<15} - {description}")
            
    def run(self, task: str):
        """Run a specific task"""
        task_methods = {
            "install": self.install,
            "setup": self.setup,
            "dev": self.dev,
            "stop": self.stop,
            "docker-dev": self.docker_dev,
            "docker-prod": self.docker_prod,
            "docker-stop": self.docker_stop,
            "health": self.health,
            "test": self.test,
            "clean": self.clean,
            "reset": self.reset,
            "help": self.help
        }
        
        if task in task_methods:
            try:
                success = task_methods[task]()
                if success is not None and not success:
                    self.log(f"Task '{task}' failed", "ERROR")
                    sys.exit(1)
                else:
                    self.log(f"Task '{task}' completed successfully")
            except KeyboardInterrupt:
                self.log(f"Task '{task}' interrupted", "WARNING")
                sys.exit(1)
            except Exception as e:
                self.log(f"Task '{task}' failed: {e}", "ERROR")
                sys.exit(1)
        else:
            self.log(f"Unknown task: {task}", "ERROR")
            self.help()
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Makefile.py <task>")
        TaskRunner().help()
        sys.exit(1)
        
    task = sys.argv[1]
    runner = TaskRunner()
    runner.run(task)