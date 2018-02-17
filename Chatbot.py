#!/bin/env python3
# Autor: Xavi Beltran
# Date: 17/02/2018

# Chatbot

import socket
import threading
import re
import requests
import subprocess
from subprocess import Popen,PIPE

# vars
bind_ip = '0.0.0.0'
bind_port = 9200

file = 'config.ini'

# declare a list of dictionaries
rule = {'regex':'',
'bot_command':'',
'parameters':''}
db = []

# socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)
subprocess.call('clear', shell=True)
print ("##### Chatbox Server: #####\n")
print ("[+] Listening on %s:%d" % (bind_ip, bind_port))

def handle_client(client_socket):
	client_socket.send(str.encode("##### Welcome to ChatBot #####\n"))
	request = client_socket.recv(1024)
	print("[+] Received: %s" % request)
	name = request.split(':')[0]
        command = request.split(':')[1].rstrip('\n')
	welcome(client_socket, name)

	# single client loop
	while command != 'exit':
		bot_command = ''
		# read config.ini
		del db[:]
		f = open (file,'r')
		for line in f:
			rule = {}
			rule['regex'] = line.split('#')[0][1:]
			rule['bot_command'] = line.split('#')[1].split('(')[0]
			rule['parameters'] = line.split('#')[1].split('(')[1][:-2].split(',')
			db.append(rule)
		f.close()

		request = client_socket.recv(1024)
		print("[+] Received: %s" % request)
		name = request.split(':')[0]
		command = request.split(':')[1].rstrip('\n')

		# look for a regex match
		for rule in db:
			#print(rule.get('regex'))
			match = re.search(rule.get('regex'), command)
			if match:
				print('[+] Match found: '+ match.group(0))
				bot_command = rule.get('bot_command')
				found = match
				print('[+] Command: ' + bot_command)

		if bot_command == 'FETCH_URL':
			#print(found.group(1))
			fetch_url(client_socket, found.group(1))
		elif bot_command == 'GREP':
			#print(found.group(1))
			#print(found.group(2))
			grep(client_socket, found.group(1), found.group(2))
		elif bot_command == 'EXTERNAL':
			print(found.group(1))
			external(client_socket, found.group(1))
		elif command == 'exit':
			close_socket(client_socket)
		else:
			client_socket.send(str.encode("Chatbot: Command not recognized\n"))

def welcome (client_socket, name):
        client_socket.send(str.encode("Chatbot: Hi %s, how can I help you?\n" % name))

def close_socket (client_socket):
	client_socket.send(str.encode("Chatbot: Closing connection. Bye!\n"))
	client_socket.close()

def fetch_url (client_socket, incident_number):
	URL = "http://127.0.0.1/incidents/" + incident_number
	print("[+] Sending GET request to: "+ URL)
	incident = requests.get(URL)
	client_socket.send(str.encode("Chatbot: This is what I found:\n"))
	client_socket.send(str.encode(incident.content))

def grep (client_socket, word, log_name):
	print("[+] Searching %s in log %s" % (word, log_name))
	# directory traversal protection
	path='/var/log/logstore/%s' % log_name.rstrip('..')
	p1 = Popen(["cat", path], stdout=PIPE)
	p2 = Popen(["grep", word], stdin=p1.stdout, stdout=PIPE)
	p3 = Popen(["head", "-3"], stdin=p2.stdout, stdout=PIPE)
	output = p3.communicate()[0]
	print(output)
	client_socket.send(str.encode("Chatbot: Here are the 3 first matching lines of the log:\n"))
	client_socket.send(str.encode(output))

def external(client_socket, parameters):
	output = subprocess.call('bash external.sh %s' % parameters, shell=True)
        client_socket.send(str.encode("Chatbot: External command executed.\n"))

# main loop
while True:
	client, addr = server.accept()
	print("[+] Accepted connection from: %s:%d" % (addr[0], addr[1]))
	# threads
	client_handler = threading.Thread(target=handle_client, args=(client,))
	client_handler.start()
