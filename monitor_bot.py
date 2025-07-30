#!/usr/bin/env python3
"""
Real-time Crypto Scalping Bot Monitor
Monitors all 3 timeframe workflows and provides live status updates
"""

import requests
import time
import json
from datetime import datetime, timedelta
import os

class BotMonitor:
    def __init__(self):
        self.repo_owner = "GInv3st"
        self.repo_name = "CSB-new"
        self.branch = "cursor/deep-repo-analysis-for-malfunction-9e4f"
        self.workflows = {
            "crypto-3m.yml": {"name": "3m Scalping", "interval": 3},
            "crypto-5m.yml": {"name": "5m Scalping", "interval": 5}, 
            "crypto-15m.yml": {"name": "15m Scalping", "interval": 15},
            "health-check.yml": {"name": "Health Check", "interval": 10},
            "storage-cleanup.yml": {"name": "Storage Cleanup", "interval": 10080}  # Weekly
        }
        
    def get_workflow_runs(self, workflow_file, per_page=5):
        """Get recent workflow runs for a specific workflow"""
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow_file}/runs"
        params = {
            "per_page": per_page,
            "branch": self.branch
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"workflow_runs": [], "total_count": 0}
        except Exception as e:
            print(f"❌ API Error for {workflow_file}: {e}")
            return {"workflow_runs": [], "total_count": 0}
    
    def format_time_ago(self, timestamp_str):
        """Convert timestamp to human readable time ago"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            diff = now - dt
            
            if diff.total_seconds() < 60:
                return f"{int(diff.total_seconds())}s ago"
            elif diff.total_seconds() < 3600:
                return f"{int(diff.total_seconds() / 60)}m ago"
            elif diff.total_seconds() < 86400:
                return f"{int(diff.total_seconds() / 3600)}h ago"
            else:
                return f"{int(diff.total_seconds() / 86400)}d ago"
        except:
            return "unknown"
    
    def get_status_emoji(self, status, conclusion):
        """Get appropriate emoji for workflow status"""
        if status == "in_progress" or status == "queued":
            return "🔄"
        elif status == "completed":
            if conclusion == "success":
                return "✅"
            elif conclusion == "failure":
                return "❌"
            elif conclusion == "cancelled":
                return "⚠️"
            else:
                return "❓"
        else:
            return "⏸️"
    
    def check_workflow_health(self, workflow_file, config):
        """Check the health of a specific workflow"""
        runs_data = self.get_workflow_runs(workflow_file)
        runs = runs_data.get("workflow_runs", [])
        
        if not runs:
            return {
                "status": "❓ No Runs",
                "last_run": "Never",
                "health": "unknown",
                "next_expected": "Unknown"
            }
        
        latest_run = runs[0]
        status = latest_run.get("status", "unknown")
        conclusion = latest_run.get("conclusion", "unknown")
        created_at = latest_run.get("created_at", "")
        
        emoji = self.get_status_emoji(status, conclusion)
        time_ago = self.format_time_ago(created_at)
        
        # Calculate next expected run
        if config["interval"] < 60:  # Minutes
            next_run = f"~{config['interval']}m"
        elif config["interval"] < 1440:  # Hours  
            next_run = f"~{config['interval']//60}h"
        else:  # Days
            next_run = f"~{config['interval']//1440}d"
        
        # Determine health based on interval
        try:
            last_run_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(last_run_time.tzinfo)
            minutes_since = (now - last_run_time).total_seconds() / 60
            
            expected_interval = config["interval"]
            if minutes_since > expected_interval * 2:  # More than 2x expected interval
                health = "⚠️ DELAYED"
            elif status == "completed" and conclusion == "success":
                health = "✅ HEALTHY"
            elif status == "in_progress":
                health = "🔄 RUNNING"
            else:
                health = "❌ ISSUE"
        except:
            health = "❓ UNKNOWN"
        
        return {
            "status": f"{emoji} {status.upper()}",
            "conclusion": conclusion,
            "last_run": time_ago,
            "health": health,
            "next_expected": next_run,
            "run_number": latest_run.get("run_number", "?"),
            "html_url": latest_run.get("html_url", "")
        }
    
    def display_status(self):
        """Display comprehensive status of all workflows"""
        print("\n" + "="*80)
        print("🚀 CRYPTO SCALPING BOT - REAL-TIME MONITORING")
        print(f"📊 Repository: {self.repo_owner}/{self.repo_name}")
        print(f"🌿 Branch: {self.branch}")
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("="*80)
        
        overall_health = "✅ ALL SYSTEMS OPERATIONAL"
        
        for workflow_file, config in self.workflows.items():
            health_data = self.check_workflow_health(workflow_file, config)
            
            print(f"\n📈 {config['name']} ({workflow_file})")
            print(f"   Status: {health_data['status']}")
            print(f"   Health: {health_data['health']}")
            print(f"   Last Run: {health_data['last_run']} (#{health_data['run_number']})")
            print(f"   Next Expected: {health_data['next_expected']}")
            
            if "ISSUE" in health_data['health'] or "DELAYED" in health_data['health']:
                overall_health = "⚠️ REQUIRES ATTENTION"
                print(f"   🔗 Debug: {health_data['html_url']}")
        
        print("\n" + "="*80)
        print(f"🎯 OVERALL STATUS: {overall_health}")
        print("="*80)
    
    def run_continuous_monitoring(self, interval_seconds=30):
        """Run continuous monitoring with specified interval"""
        print("🔍 Starting continuous bot monitoring...")
        print(f"🔄 Refresh rate: every {interval_seconds} seconds")
        print("💡 Press Ctrl+C to stop")
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
                self.display_status()
                
                print(f"\n⏳ Next update in {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n\n❌ Monitoring error: {e}")

def main():
    monitor = BotMonitor()
    
    print("🚀 Crypto Scalping Bot Monitor")
    print("Choose monitoring mode:")
    print("1. Single status check")
    print("2. Continuous monitoring (30s intervals)")
    print("3. Continuous monitoring (60s intervals)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        monitor.display_status()
    elif choice == "2":
        monitor.run_continuous_monitoring(30)
    elif choice == "3":
        monitor.run_continuous_monitoring(60)
    else:
        print("Invalid choice. Running single status check...")
        monitor.display_status()

if __name__ == "__main__":
    main()