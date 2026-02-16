import socket
import time
import random
import argparse

# UDP syslog sender (RFC 5424 basic; mimics VMs/apps)[web:47]
def send_log(msg, host='127.0.0.1', port=514):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Syslog format: <PRI>timestamp host msg (simple)
    syslog_msg = f"<13>{time.strftime('%Y-%m-%dT%H:%M:%S')} localhost {msg}"
    sock.sendto(syslog_msg.encode(), (host, port))
    sock.close()
    print(f"Sent: {msg}")

def simulate_brute_force(ip='192.168.1.100', fails=6):
    print("Simulating brute force: 5+ fails → success (T1110)")
    for i in range(fails):
        send_log(f"auth failed user=admin ip={ip} action=login status=fail")
        time.sleep(0.5)
    send_log(f"auth success user=admin ip={ip} action=login status=success")
    print("Brute force sim done—check rules!")

def simulate_admin_create():
    print("Simulating off-hours admin (T1136)")
    send_log("user created user=newadmin ip=10.0.0.50 action=create_user status=success")
    print("Admin sim done—check off-hours rule!")

def continuous_vm_logs():
    actions = ['login', 'file_access', 'sudo', 'ssh']
    statuses = ['success', 'fail']
    ips = ['192.168.1.10', '10.0.0.5', '172.16.0.100']
    users = ['user1', 'admin', 'root']
    for _ in range(20):
        msg = f"auth {random.choice(actions)} user={random.choice(users)} ip={random.choice(ips)} status={random.choice(statuses)}"
        send_log(msg)
        time.sleep(random.uniform(0.2, 1.5))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--brute', action='store_true', help="Run brute force test")
    parser.add_argument('--admin', action='store_true', help="Run admin create test")
    parser.add_argument('--continuous', action='store_true', help="Run VM log burst")
    args = parser.parse_args()

    if args.brute:
        simulate_brute_force()
    elif args.admin:
        simulate_admin_create()
    elif args.continuous:
        continuous_vm_logs()
    else:
        print("Use: python test_sender.py --brute | --admin | --continuous")
        simulate_brute_force()  # Default demo
