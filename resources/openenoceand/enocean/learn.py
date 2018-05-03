import globals
import json
import time
from enocean import utils
from enocean.devices import vld, rps, bs4, bs1,response
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import RadioPacket, UTETeachIn

try:
	from jeedom.jeedom import *
except ImportError:
	print "Error: importing module from jeedom folder"
	sys.exit(1)
	
def learn_packet_message(message):
	if message['type'] == 'repeater':
		repeater(message['dest'],message['level'])
	
def remote_learnin(remoteid):
	logging.debug('Sending learnin remote message')
	data = [0xC5,0x40,0x01,0x7F,0xF2,0x20] + \
		[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00] 
	optional = [0x03] + utils.destination_sender_to_list(remoteid) + [0xFF, 0x00,0xE4]
	globals.COMMUNICATOR.send(RadioPacket(PACKET.RADIO, data=data, optional=optional))
	return
def remote_learnout(remoteid):
	logging.debug('Sending learnout remote message')
	data = [0xC5,0xC0,0x01,0x7F,0xF2,0x20] + \
		[0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x8F] 
	optional = [0x03] + utils.destination_sender_to_list(remoteid) + [0xFF, 0x00]
	globals.COMMUNICATOR.send(RadioPacket(PACKET.RADIO, data=data, optional=optional))
	return
def remote_learnexit(remoteid):
	logging.debug('Sending learnexit remote message')
	data = [0xC5,0x40,0x01,0x7F,0xF2,0x20] + \
		[0x80,0x00,0x00,0x00,0x00,0x00,0x00,0x8F] 
	optional = [0x03] + utils.destination_sender_to_list(remoteid) + [0xFF, 0x00]
	globals.COMMUNICATOR.send(RadioPacket(PACKET.RADIO, data=data, optional=optional))
	return
def remote_co(packet):
	return
def repeater(remoteid,level):
	logging.debug('Sending Repeater remote message')
	frelevel=0x01
	if level == '1':
		relevel= 0x01
	elif level == '2':
		relevel= 0x02
	else:
		relevel= 0x00
		frelevel=0x00
	data = [0xD1,0x46,0x00,0x08,frelevel,relevel] + \
		globals.COMMUNICATOR.base_id + [0x00]
	optional = [0x03] + utils.destination_sender_to_list(remoteid) + [0xFF, 0x00]
	globals.COMMUNICATOR.send(RadioPacket(PACKET.RADIO, data=data, optional=optional))
	time.sleep(0.3)
	data = [0xD1,0x00,0x46,0x08,frelevel,relevel] + \
		globals.COMMUNICATOR.base_id + [0x00]
	optional = [0x03] + utils.destination_sender_to_list(remoteid) + [0xFF, 0x00]
	globals.COMMUNICATOR.send(RadioPacket(PACKET.RADIO, data=data, optional=optional))
	return