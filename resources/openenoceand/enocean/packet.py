import globals
import json
from enocean import utils
from enocean.devices import vld, rps, bs4, bs1,response, rawhandler
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import RadioPacket, UTETeachIn

try:
	from jeedom.jeedom import *
except ImportError:
	print "Error: importing module from jeedom folder"
	sys.exit(1)

def packet_get_eep(packet):
	packet_id = str(packet.sender_hex).replace(":","")
	packet_rorg = str(jeedom_utils.dec2hex(packet.rorg))
	if packet_id in globals.KNOWN_DEVICES:
		for info in globals.KNOWN_DEVICES[packet_id]:
			if str(info['rorg']) == packet_rorg:
				return info

	if packet.contains_eep:
		try:
			rorg = jeedom_utils.dec2hex(packet.rorg_of_eep)
		except:
			rorg = packet_rorg
		return {'rorg' : rorg, 'func' : str(jeedom_utils.dec2hex(packet.rorg_func)).zfill(2) , 'type' : str(jeedom_utils.dec2hex(packet.rorg_type)).zfill(2)}
	
	if packet.rorg == RORG.BS4:
		return {'rorg' : packet_rorg, 'func' : '02' , 'type' : '05'}

	if packet.rorg == RORG.BS1:
		return {'rorg' : packet_rorg, 'func' : '00' , 'type' : '01'}

	if packet.rorg == RORG.RPS:
		return {'rorg' : packet_rorg, 'func' : '02' , 'type' : '02'}

	if packet.rorg == RORG.VLD:
		return {'rorg' : packet_rorg, 'func' : '01' , 'type' : '01'}

	return None
	
def decode_packet(packet):
	action = {}
	if packet.packet_type == PACKET.RESPONSE:
		response.parse(packet)
		return
	if packet.packet_type == PACKET.EVENT:
		logging.debug('Receive event packet : ' + str(packet))
		return
	if packet.packet_type <> PACKET.RADIO:
		logging.debug('Not decode because it\'s not radio package : ' + str(packet.packet_type))
		return
	if packet.sender[0:3] == globals.COMMUNICATOR.base_id[0:3]:
		logging.debug('Ignore this is an echo')
		return
	eep = packet_get_eep(packet)
	if eep is None:
		logging.debug('No eep found, no decoded')
		return
	try: 
		repeat = str(hex(packet.data[-1:][0]))[-1:]
	except Exception, e:
		logging.debug(str(e))
		repeat = '0'
	logging.debug('Message is repeated ' + repeat + ' times')
	action['id'] = str(packet.sender_hex).replace(":","")
	action['rorg'] = eep['rorg']
	action['packet_type'] = str(packet.packet_type)
	action['dBm'] = str(packet.dBm)
	action['func'] = eep['func']
	action['type'] = eep['type']
	action['repeat'] = repeat
	action['manufacturer'] = str(jeedom_utils.dec2hex(packet.rorg_manufacturer)).zfill(2)
	if packet.learn and globals.EXCLUDE_MODE:
		if packet.rorg == RORG.VLD and eep['func'] == '01':
			logging.debug('It\'s should be a UTE packet for exclusion, i ignore')
			return
		globals.EXCLUDE_MODE = False
		logging.debug('It\'s learn packet and I am in exclude mode, i delete the device')
		globals.JEEDOM_COM.send_change_immediate({'exclude_mode' : 0, 'deviceId' : str(packet.sender_hex).replace(":","") });
		return
	if action['id'] not in globals.KNOWN_DEVICES:
		if not packet.learn or not globals.LEARN_MODE:
			#logging.debug('Not decode because it\'s an unknown device or I\'am not in learn mode')
			return
		elif packet.learn and globals.LEARN_MODE:
			if packet.rorg == RORG.VLD and eep['func'] == '01':
				logging.debug('It\'s should be a UTE packet for learn, i ignore')
				return
			logging.debug('It\'s learn packet and I don\'t known this device so I learn')
			try:
				if utils.profile_from_action(action) in globals.LEARN_PROCEDURE['BS4VAR3']:
					logging.debug('It\'s a BS4VAR3 learn device')
					packet.parse_eep(utils.from_hex_string(eep['func']),utils.from_hex_string(eep['type']))
					if packet.parsed['LRNB']['raw_value'] == 0 :
						logging.debug('It\'s really a BS4VAR3 learn packet let\'s respond')
						bs4.response_learn_BS4VAR3(packet)
					else:
						logging.debug('It\'s not really a BS4VAR3 learn packet ignoring')
						return
				action['learn'] = 1
				globals.JEEDOM_COM.add_changes('devices::'+action['id'],action)
				globals.JEEDOM_COM.send_change_immediate({'learn_mode' : 0});
				globals.LEARN_MODE = False
			except Exception, e:
				logging.debug(str(e))	
		return
	
	if packet.cmd :
		logging.debug("Its a VLD message with command : " + str(packet.cmd))
	if eep['func'] == '38' and eep['type']=='08':
		packet.cmd = 2
	packet.parse_eep(utils.from_hex_string(eep['func']),utils.from_hex_string(eep['type']) , command = packet.cmd )
	parse_packet(action,packet)

def parse_packet(action,packet):
	logging.debug("Parsing Packet")
	if packet.rorg == RORG.VLD:
		action = vld.parse(action,packet)
	if packet.rorg == RORG.RPS:
		action = rps.parse(action,packet)
	if packet.rorg == RORG.BS4:
		action = bs4.parse(action,packet)
	if packet.rorg == RORG.BS1:
		action = bs1.parse(action,packet)
	logging.debug('Decode data : '+json.dumps(action))
	try:
		if len(action) > 7 and (not 'ignore' in action or action['ignore'] <> 1):
			globals.JEEDOM_COM.add_changes('devices::'+action['id'],action)
	except Exception, e:
		pass
	return

def send_command(message,learn=False, immediate=False):
	kwargs={}
	command = None
	generic = ''
	direction = None
	delay = False
	learn = False
	type = ''
	raw = ''
	sender = globals.COMMUNICATOR.base_id
	commandRorg = int(message['profile']['rorg'],16)
	commandFunc = utils.from_hex_string(message['profile']['func'])
	commandType = utils.from_hex_string(message['profile']['type'])
	commandDestination = utils.destination_sender_to_list(message['dest'])
	for data in message['command']:
		if data == 'command' :
			command = int(message['command'][data])
		elif data == 'direction' :
			direction = int(message['command'][data])
		elif data == 'type':
			type = message['command'][data]
		elif data == 'delay':
			delay = message['command'][data]
		elif data == 'generic':
			generic = message['command'][data]
		elif data == 'learn':
			learn = message['command'][data]
		elif data == 'profil':
			profil = message['command'][data]
		elif data == 'raw':
			raw = message['command'][data]
		else:
			try :
				kwargs[data] = int(message['command'][data])
			except :
				kwargs[data] = message['command'][data]
	if learn <> False and learn <> '1':
		send_learn(learn,message)
		return
	if learn == '1':
		learn = True
	if delay and not immediate:
		globals.STORAGE_MESSAGE[message['dest']] = message
		logging.debug('Storing message')
		return
	logging.debug(str(kwargs) +' on command ' + str(command) + ' ' + str(commandRorg)+ ' '+ str(commandFunc) + ' ' + str(commandType))
	if generic <> '':
		if type == 'switch':
			sender = utils.destination_sender_to_list(generic)
			commandDestination = None
			globals.COMMUNICATOR.send(RadioPacket.create(rorg=commandRorg, rorg_func =commandFunc, rorg_type =commandType, destination=commandDestination, sender=sender, learn = learn, command = command, direction = direction, EB = 1, **kwargs))
			globals.COMMUNICATOR.send(RadioPacket.create(rorg=commandRorg, rorg_func =commandFunc, rorg_type =commandType, destination=commandDestination, sender=sender, learn = learn, command = command, direction = direction, EB = 0, **kwargs))
			return
		else :
			sender = utils.destination_sender_to_list(generic)
			commandDestination = None
	if raw <> '':
		rawhandler.send(commandRorg,raw,sender)
		return
	globals.COMMUNICATOR.send(RadioPacket.create(rorg=commandRorg, rorg_func =commandFunc, rorg_type =commandType, destination=commandDestination, sender=sender, learn = learn, command = command, direction = direction, **kwargs))

def send_learn(learn,message):
	if learn == 'BS4':
		bs4.send_learn(message)
	return