#!/usr/bin/env python3
"""
Docker Deployment Script
Starts the AI PKM Tool using Docker Compose
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional


class DockerManager:
    """Manages Docker Compose deployment"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.compose_dev = self.root_dir / "docker-compose.dev.yml"
        self.compose_prod = self.root_dir / "docker-compose.yml"
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                self.log(f"Docker available: {result.stdout.strip()}")
                return True
            return False
        except FileNotFoundError:
            return False
            
    def check_docker_compose(self) -> bool:
        """Check if Docker Compose is available"""
        try:
            # Try docker compose (newer version)
            result = subprocess.run(["docker", "compose", "version"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                self.log(f"Docker Compose available: {result.stdout.strip()}")
                return True
                
            # Try docker-compose (older version)
            result = subprocess.run(["docker-compose", "--version"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                self.log(f"Docker Compose available: {result.stdout.strip()}")
                return True
                
            return False
        except FileNotFoundError:
            return False
            
    def get_compose_command(self) -> list:
        """Get the appropriate docker compose command"""
        # Try docker compose first (newer)
        try:
            result = subprocess.run(["docker", "compose", "version"], 
                                  capture_output=True, check=False)
            if result.returncode == 0:
                return ["docker", "compose"]
        except FileNotFoundError:
            pass
            
        # Fall back to docker-compose
        try:
            result = subprocess.run(["docker-compose", "--version"], 
                                  capture_output=True, check=False)
            if result.returncode == 0:
                return ["docker-compose"]
        except FileNotFoundError:
            pass
            
        raise RuntimeError("Docker Compose not found")
        
    def setup_environment(self):
        """Ensure environment file exists"""
        env_file = self.root_dir / ".env"
        env_example = self.root_dir / ".env.example"
        
        if not env_file.exists():
            if env_example.exists():
                import shutil
                shutil.copy(env_example, env_file)
                self.log("Created .env file from template")
            else:
                self.log("No .env file found - creating basic configuration", "WARNING")
                with open(env_file, 'w') as f:
                    f.write("""# Docker Environment Configuration
DATABASE_URL=sqlite:///./data/pkm.db
CHROMA_DB_PATH=./data/chroma_db
REDIS_URL=redis://redis:6379/0
RAG_STORAGE_DIR=./data/rag_storage
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
MAX_FILE_SIZE=104857600
DEBUG=false
LOG_LEVEL=INFO
""")
        else:
            self.log(".env file exists")
            
    def build_images(self, compose_file: Path, no_cache: bool = False):
        """Build Docker images"""
        self.log("Building Docker images...")
        
        compose_cmd = self.get_compose_command()
        cmd = compose_cmd + ["-f", str(compose_file), "build"]
        
        if no_cache:
            cmd.append("--no-cache")
            
        result = subprocess.run(cmd, cwd=self.root_dir)
        if result.returncode != 0:
            raise RuntimeError("Failed to build Docker images")
            
        self.log("Docker images built successfully")
        
    def start_services(self, compose_file: Path, detached: bool = True):
        """Start Docker services"""
        self.log("Starting Docker services...")
        
        compose_cmd = self.get_compose_command()
        cmd = compose_cmd + ["-f", str(compose_file), "up"]
        
        if detached:
            cmd.append("-d")
            
        result = subprocess.run(cmd, cwd=self.root_dir)
        if result.returncode != 0:
            raise RuntimeError("Failed to start Docker services")
            
        if detached:
            self.log("Docker services started in background")
        else:
            self.log("Docker services started")
            
    def wait_for_services(self):
        """Wait for services to be healthy"""
        self.log("Waiting for services to be ready...")
        
        # Wait for backend health check
        for i in range(60):  # Wait up to 60 seconds
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    self.log("Backend is healthy")
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.log("Backend health check timeout", "WARNING")
            
        # Check Redis
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0)
            client.ping()
            self.log("Redis is healthy")
        except Exception as e:
            self.log(f"Redis health check failed: {e}", "WARNING")
            
    def show_status(self, compose_file: Path):
        """Show service status"""
        self.log("Service status:")
        
        compose_cmd = self.get_compose_command()
        subprocess.run(compose_cmd + ["-f", str(compose_file), "ps"], cwd=self.root_dir)
        
    def show_logs(self, compose_file: Path, service: Optional[str] = None, follow: bool = False):
        """Show service logs"""
        compose_cmd = self.get_compose_command()
        cmd = compose_cmd + ["-f", str(compose_file), "logs"]
        
        if follow:
            cmd.append("-f")
            
        if service:
            cmd.append(service)
            
        subprocess.run(cmd, cwd=self.root_dir)
        
    def run_development(self, build: bool = False, no_cache: bool = False):
        """Run development environment"""
        self.log("Starting development environment with Docker...")
        
        if not self.compose_dev.exists():
            raise RuntimeError(f"Development compose file not found: {self.compose_dev}")
            
        self.setup_environment()
        
        if build:
            self.build_images(self.compose_dev, no_cache=no_cache)
            
        self.start_services(self.compose_dev, detached=True)
        self.wait_for_services()
        self.show_status(self.compose_dev)
        
        self.log("Development environment started successfully!")
        self.log("Backend API: http://localhost:8000")
        self.log("API Documentation: http://localhost:8000/docs")
        self.log("Redis: localhost:6379")
        self.log("")
        self.log("Useful commands:")
        self.log("  View logs: python scripts/start-docker.py --logs")
        self.log("  Stop services: python scripts/stop-docker.py")
        
    def run_production(self, build: bool = False, no_cache: bool = False):
        """Run production environment"""
        self.log("Starting production environment with Docker...")
        
        if not self.compose_prod.exists():
            raise RuntimeError(f"Production compose file not found: {self.compose_prod}")
            
        self.setup_environment()
        
        if build:
            self.build_images(self.compose_prod, no_cache=no_cache)
            
        self.start_services(self.compose_prod, detached=True)
        self.wait_for_services()
        self.show_status(self.compose_prod)
        
        self.log("Production environment started successfully!")
        self.log("Application: http://localhost")
        self.log("Backend API: http://localhost:8000")
        
    def run(self, mode: str = "dev", build: bool = False, no_cache: bool = False, 
            logs: bool = False, service: Optional[str] = None, follow: bool = False):
        """Main execution method"""
        
        if not self.check_docker():
            self.log("Docker not found. Please install Docker.", "ERROR")
            sys.exit(1)
            
        if not self.check_docker_compose():
            self.log("Docker Compose not found. Please install Docker Compose.", "ERROR")
            sys.exit(1)
            
        try:
            if logs:
                compose_file = self.compose_dev if mode == "dev" else self.compose_prod
                self.show_logs(compose_file, service=service, follow=follow)
            elif mode == "dev":
                self.run_development(build=build, no_cache=no_cache)
            elif mode == "prod":
                self.run_production(build=build, no_cache=no_cache)
            else:
                raise ValueError(f"Invalid mode: {mode}")
                
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start AI PKM Tool with Docker")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev",
                       help="Deployment mode (default: dev)")
    parser.add_argument("--build", action="store_true",
                       help="Build images before starting")
    parser.add_argument("--no-cache", action="store_true",
                       help="Build without cache")
    parser.add_argument("--logs", action="store_true",
                       help="Show service logs")
    parser.add_argument("--service", type=str,
                       help="Show logs for specific service")
    parser.add_argument("--follow", action="store_true",
                       help="Follow log output")
    
    args = parser.parse_args()
    
    manager = DockerManager()
    manager.run(
        mode=args.mode,
        build=args.build,
        no_cache=args.no_cache,
        logs=args.logs,
        service=args.service,
        follow=args.follow
    )