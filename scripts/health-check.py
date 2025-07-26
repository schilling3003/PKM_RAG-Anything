#!/usr/bin/env python3
"""
Health Check Script
Verifies that all services and dependencies are working correctly
"""

import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, Any


class HealthChecker:
    """Performs comprehensive health checks on all system components"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0)
            client.ping()
            info = client.info()
            return {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except ImportError:
            return {"status": "error", "message": "redis package not installed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def check_backend(self) -> Dict[str, Any]:
        """Check backend API health"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "details": data
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                }
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Backend not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def check_celery(self) -> Dict[str, Any]:
        """Check Celery worker health"""
        try:
            response = requests.get(f"{self.backend_url}/health/celery", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "details": data
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                }
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Backend not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def check_frontend(self) -> Dict[str, Any]:
        """Check frontend availability"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Frontend not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            response = requests.get(f"{self.backend_url}/health/database", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "details": data
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                }
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Backend not running"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def check_ai_services(self) -> Dict[str, Any]:
        """Check AI service availability"""
        services = {}
        
        # Check OpenAI
        try:
            response = requests.get(f"{self.backend_url}/health/openai", timeout=5)
            if response.status_code == 200:
                services["openai"] = {"status": "healthy", "details": response.json()}
            else:
                services["openai"] = {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            services["openai"] = {"status": "error", "message": str(e)}
            
        # Check LightRAG
        try:
            response = requests.get(f"{self.backend_url}/health/lightrag", timeout=5)
            if response.status_code == 200:
                services["lightrag"] = {"status": "healthy", "details": response.json()}
            else:
                services["lightrag"] = {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            services["lightrag"] = {"status": "error", "message": str(e)}
            
        # Check RAG-Anything
        try:
            response = requests.get(f"{self.backend_url}/health/raganything", timeout=5)
            if response.status_code == 200:
                services["raganything"] = {"status": "healthy", "details": response.json()}
            else:
                services["raganything"] = {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            services["raganything"] = {"status": "error", "message": str(e)}
            
        return services
        
    def check_storage(self) -> Dict[str, Any]:
        """Check storage directories and permissions"""
        directories = [
            self.root_dir / "data",
            self.root_dir / "data" / "uploads",
            self.root_dir / "data" / "processed",
            self.root_dir / "data" / "chroma_db",
            self.root_dir / "data" / "rag_storage"
        ]
        
        results = {}
        for directory in directories:
            try:
                if directory.exists():
                    if directory.is_dir():
                        # Test write permissions
                        test_file = directory / ".health_check_test"
                        test_file.write_text("test")
                        test_file.unlink()
                        results[str(directory.name)] = {"status": "healthy", "writable": True}
                    else:
                        results[str(directory.name)] = {"status": "error", "message": "Not a directory"}
                else:
                    results[str(directory.name)] = {"status": "error", "message": "Directory does not exist"}
            except PermissionError:
                results[str(directory.name)] = {"status": "error", "message": "Permission denied"}
            except Exception as e:
                results[str(directory.name)] = {"status": "error", "message": str(e)}
                
        return results
        
    def check_docker_services(self) -> Dict[str, Any]:
        """Check Docker container status"""
        try:
            import subprocess
            
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return {"status": "error", "message": "Docker not available"}
                
            # Check running containers
            result = subprocess.run([
                "docker", "ps", "--format", 
                "{{.Names}}\t{{.Status}}\t{{.Ports}}"
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                containers = {}
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name = parts[0]
                            status = parts[1]
                            ports = parts[2] if len(parts) > 2 else ""
                            containers[name] = {
                                "status": "healthy" if "Up" in status else "error",
                                "details": status,
                                "ports": ports
                            }
                return {"status": "healthy", "containers": containers}
            else:
                return {"status": "error", "message": "Could not list containers"}
                
        except FileNotFoundError:
            return {"status": "error", "message": "Docker not installed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all health checks"""
        self.log("Starting comprehensive health check...")
        
        checks = {
            "redis": self.check_redis,
            "backend": self.check_backend,
            "celery": self.check_celery,
            "frontend": self.check_frontend,
            "database": self.check_database,
            "ai_services": self.check_ai_services,
            "storage": self.check_storage,
            "docker": self.check_docker_services
        }
        
        results = {}
        for check_name, check_func in checks.items():
            self.log(f"Checking {check_name}...")
            try:
                results[check_name] = check_func()
                status = results[check_name].get("status", "unknown")
                if isinstance(results[check_name], dict) and "status" not in results[check_name]:
                    # For complex checks like ai_services, determine overall status
                    statuses = [v.get("status", "unknown") for v in results[check_name].values() 
                              if isinstance(v, dict)]
                    status = "healthy" if all(s == "healthy" for s in statuses) else "partial"
                    
                self.log(f"{check_name}: {status}")
            except Exception as e:
                results[check_name] = {"status": "error", "message": str(e)}
                self.log(f"{check_name}: error - {e}", "ERROR")
                
        return results
        
    def print_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of health check results"""
        print("\n" + "="*60)
        print("HEALTH CHECK SUMMARY")
        print("="*60)
        
        healthy_count = 0
        total_count = 0
        
        for service, result in results.items():
            print(f"\n{service.upper()}:")
            
            if isinstance(result, dict):
                if "status" in result:
                    status = result["status"]
                    total_count += 1
                    if status == "healthy":
                        healthy_count += 1
                        print(f"  ✅ Status: {status}")
                    else:
                        print(f"  ❌ Status: {status}")
                        
                    if "message" in result:
                        print(f"  📝 Message: {result['message']}")
                    if "details" in result:
                        print(f"  📊 Details: {result['details']}")
                        
                else:
                    # Complex result like ai_services
                    for sub_service, sub_result in result.items():
                        if isinstance(sub_result, dict) and "status" in sub_result:
                            total_count += 1
                            status = sub_result["status"]
                            if status == "healthy":
                                healthy_count += 1
                                print(f"  ✅ {sub_service}: {status}")
                            else:
                                print(f"  ❌ {sub_service}: {status}")
                                if "message" in sub_result:
                                    print(f"     📝 {sub_result['message']}")
                                    
        print(f"\n{'='*60}")
        print(f"OVERALL: {healthy_count}/{total_count} services healthy")
        
        if healthy_count == total_count:
            print("🎉 All services are running correctly!")
            return True
        else:
            print("⚠️  Some services need attention.")
            return False
            
    def run(self, detailed: bool = False):
        """Run health checks and display results"""
        results = self.run_comprehensive_check()
        
        if detailed:
            import json
            print(json.dumps(results, indent=2))
        else:
            success = self.print_summary(results)
            
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI PKM Tool Health Check")
    parser.add_argument("--detailed", action="store_true",
                       help="Show detailed JSON output")
    parser.add_argument("--service", type=str,
                       help="Check specific service only")
    
    args = parser.parse_args()
    
    checker = HealthChecker()
    
    if args.service:
        # Check specific service
        service_methods = {
            "redis": checker.check_redis,
            "backend": checker.check_backend,
            "celery": checker.check_celery,
            "frontend": checker.check_frontend,
            "database": checker.check_database,
            "ai": checker.check_ai_services,
            "storage": checker.check_storage,
            "docker": checker.check_docker_services
        }
        
        if args.service in service_methods:
            result = service_methods[args.service]()
            if args.detailed:
                import json
                print(json.dumps(result, indent=2))
            else:
                print(f"{args.service}: {result.get('status', 'unknown')}")
        else:
            print(f"Unknown service: {args.service}")
            print(f"Available services: {', '.join(service_methods.keys())}")
            sys.exit(1)
    else:
        # Run comprehensive check
        results = checker.run(detailed=args.detailed)
        
        # Exit with error code if any service is unhealthy
        if not all(
            result.get("status") == "healthy" 
            for result in results.values() 
            if isinstance(result, dict) and "status" in result
        ):
            sys.exit(1)