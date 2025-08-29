"""
Instance Check Script - Detect if another SS6 instance is running
"""
import psutil
import os
import sys

def check_for_running_instances():
    """Check if another instance of SS6 is already running."""
    current_pid = os.getpid()
    current_process_name = "python.exe"
    ss6_instances = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('main.py' in arg or 'SS6' in arg for arg in cmdline):
                        if proc.info['pid'] != current_pid:
                            ss6_instances.append({
                                'pid': proc.info['pid'],
                                'cmdline': ' '.join(cmdline) if cmdline else 'N/A'
                            })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    except Exception as e:
        print(f"Error checking for instances: {e}")
        return []
    
    return ss6_instances

def terminate_other_instances():
    """Terminate other SS6 instances."""
    instances = check_for_running_instances()
    
    if not instances:
        print("No other SS6 instances found.")
        return True
    
    print(f"Found {len(instances)} other SS6 instance(s):")
    for instance in instances:
        print(f"  PID: {instance['pid']} - {instance['cmdline']}")
    
    response = input("Terminate other instances? (y/n): ").lower()
    if response == 'y':
        for instance in instances:
            try:
                proc = psutil.Process(instance['pid'])
                proc.terminate()
                print(f"Terminated instance {instance['pid']}")
            except Exception as e:
                print(f"Failed to terminate instance {instance['pid']}: {e}")
        return True
    
    return False

if __name__ == "__main__":
    print("SS6 Instance Check")
    print("=" * 20)
    
    instances = check_for_running_instances()
    
    if instances:
        print(f"WARNING: Found {len(instances)} other SS6 instance(s) running:")
        for instance in instances:
            print(f"  PID: {instance['pid']} - {instance['cmdline']}")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--terminate":
            terminate_other_instances()
        else:
            print("\nRun with --terminate to close other instances.")
    else:
        print("No other SS6 instances found. Safe to run.")
