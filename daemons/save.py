	old_wideopen=[
		"iptables -F",
		"iptables -t nat -F",
		"iptables -P INPUT ACCEPT",
		"iptables -P OUTPUT ACCEPT",
		"iptables -P FORWARD ACCEPT",
		"iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
		"iptables -I INPUT 1 -i wlan0 -j ACCEPT",
		"iptables -I INPUT 1 -i lo -j ACCEPT",
		"iptables -A INPUT -p UDP --dport bootps ! -i wlan0 -j REJECT",
		"iptables -A INPUT -p UDP --dport domain ! -i wlan0 -j REJECT",
		"iptables -A INPUT -p TCP ! -i wlan0 -d 0/0 --dport 0:1023 -j ACCEPT",
		"iptables -A INPUT -p UDP ! -i wlan0 -d 0/0 --dport 0:1023 -j ACCEPT",
	]
	old_output=[
	"""
-P INPUT ACCEPT
-P FORWARD ACCEPT
-P OUTPUT ACCEPT
-N DOCKER
-N DOCKER-ISOLATION
-A INPUT -i lo -j ACCEPT
-A INPUT -i wlan1 -j ACCEPT
-A INPUT -i eth0 -j ACCEPT
-A INPUT ! -i eth0 -p udp -m udp --dport 67 -j REJECT --reject-with icmp-port-unreachable
-A INPUT ! -i wlan1 -p udp -m udp --dport 67 -j REJECT --reject-with icmp-port-unreachable
-A INPUT ! -i eth0 -p udp -m udp --dport 53 -j REJECT --reject-with icmp-port-unreachable
-A INPUT ! -i wlan1 -p udp -m udp --dport 53 -j REJECT --reject-with icmp-port-unreachable
-A INPUT -i wlan0 -p tcp -m tcp --dport 22 -j ACCEPT
-A FORWARD -j DOCKER-ISOLATION
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
-A FORWARD -d 192.168.0.0/16 -i wlan1 -j ACCEPT
-A FORWARD -d 192.168.0.0/16 -i eth0 -j ACCEPT
-A FORWARD -s 192.168.0.0/16 -i eth0 -j ACCEPT
-A FORWARD -s 192.168.0.0/16 -i wlan1 -j ACCEPT
-A FORWARD -d 192.168.0.0/16 -i wlan0 -j ACCEPT
-A DOCKER-ISOLATION -j RETURN
	"""
	]
