#!/usr/bin/env python3
"""
Docker Shutdown Script
Stops Docker Compose services and cleans up resources
"""

import os
import sys
import subprocess
from pathlib import Path


class DockerStopper:
    """Manages stopping Docker Compose services"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.compose_dev = self.root_dir / "docker-compose.dev.yml"
        self.compose_prod = self.root_dir / "docker-compose.yml"
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
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
        
    def stop_services(self, compose_file: Path):
        """Stop Docker services"""
        if not compose_file.exists():
            self.log(f"Compose file not found: {compose_file}", "WARNING")
            return
            
        self.log(f"Stopping services from {compose_file.name}...")
        
        compose_cmd = self.get_compose_command()
        result = subprocess.run(
            compose_cmd + ["-f", str(compose_file), "down"],
            cwd=self.root_dir
        )
        
        if result.returncode == 0:
            self.log(f"Services from {compose_file.name} stopped")
        else:
            self.log(f"Error stopping services from {compose_file.name}", "ERROR")
            
    def remove_volumes(self, compose_file: Path):
        """Remove Docker volumes"""
        if not compose_file.exists():
            return
            
        self.log(f"Removing volumes from {compose_file.name}...")
        
        compose_cmd = self.get_compose_command()
        result = subprocess.run(
            compose_cmd + ["-f", str(compose_file), "down", "-v"],
            cwd=self.root_dir
        )
        
        if result.returncode == 0:
            self.log(f"Volumes from {compose_file.name} removed")
        else:
            self.log(f"Error removing volumes from {compose_file.name}", "ERROR")
            
    def remove_images(self, compose_file: Path):
        """Remove Docker images"""
        if not compose_file.exists():
            return
            
        self.log(f"Removing images from {compose_file.name}...")
        
        compose_cmd = self.get_compose_command()
        result = subprocess.run(
            compose_cmd + ["-f", str(compose_file), "down", "--rmi", "all"],
            cwd=self.root_dir
        )
        
        if result.returncode == 0:
            self.log(f"Images from {compose_file.name} removed")
        else:
            self.log(f"Error removing images from {compose_file.name}", "ERROR")
            
    def cleanup_docker_system(self):
        """Clean up Docker system resources"""
        self.log("Cleaning up Docker system resources...")
        
        # Remove unused containers
        subprocess.run(["docker", "container", "prune", "-f"], check=False)
        
        # Remove unused images
        subprocess.run(["docker", "image", "prune", "-f"], check=False)
        
        # Remove unused volumes
        subprocess.run(["docker", "volume", "prune", "-f"], check=False)
        
        # Remove unused networks
        subprocess.run(["docker", "network", "prune", "-f"], check=False)
        
        self.log("Docker system cleanup completed")
        
    def show_status(self):
        """Show current Docker status"""
        self.log("Current Docker status:")
        
        # Show running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout)
        else:
            self.log("No running containers")
            
    def run(self, mode: str = "both", remove_volumes: bool = False, 
            remove_images: bool = False, cleanup: bool = False):
        """Stop Docker services"""
        
        try:
            compose_cmd = self.get_compose_command()
            self.log("Stopping AI PKM Tool Docker services...")
            
            if mode in ["dev", "both"]:
                if remove_volumes:
                    self.remove_volumes(self.compose_dev)
                elif remove_images:
                    self.remove_images(self.compose_dev)
                else:
                    self.stop_services(self.compose_dev)
                    
            if mode in ["prod", "both"]:
                if remove_volumes:
                    self.remove_volumes(self.compose_prod)
                elif remove_images:
                    self.remove_images(self.compose_prod)
                else:
                    self.stop_services(self.compose_prod)
                    
            if cleanup:
                self.cleanup_docker_system()
                
            self.show_status()
            self.log("Docker services stopped successfully!")
            
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stop AI PKM Tool Docker services")
    parser.add_argument("--mode", choices=["dev", "prod", "both"], default="both",
                       help="Which services to stop (default: both)")
    parser.add_argument("--remove-volumes", action="store_true",
                       help="Remove volumes (WARNING: deletes data)")
    parser.add_argument("--remove-images", action="store_true",
                       help="Remove images (forces rebuild)")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up unused Docker resources")
    
    args = parser.parse_args()
    
    if args.remove_volumes:
        response = input("WARNING: This will delete all data in Docker volumes. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
            
    stopper = DockerStopper()
    stopper.run(
        mode=args.mode,
        remove_volumes=args.remove_volumes,
        remove_images=args.remove_images,
        cleanup=args.cleanup
    )