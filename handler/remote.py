#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import json
import requests
from config import *


def get_products():
	"""
	Queries the products from the intranet and returns a dict containing
	tuples. The dict keys are the ids of the objects (db id). The values
	are tuples of names and prices - {obj_id: (name, price)}, obj_id: int,
	name: String, price: ??.
	"""
	logger = logging.getLogger("remote:get_products")
	try:
		r = requests.get(URL_SYNC, auth=(AUTH_USER, AUTH_PASSWORD))
		json_data = r.json()
		logger.info("successfully read json data")
		data = decode_product_list(json_data)
		logger.info("successfully decoded json data")
		return data
	except Exception, e:
		logger.error("fetching failed; %s: %s" % (type(e).__name__, e))
		return {}

def get_user(user):
	logger = logging.getLogger("remote:get_user")
	try:
		r = requests.get(URL_USER + '/' + user + '.json', auth=(AUTH_USER, AUTH_PASSWORD))
		logger.info("successfully read json data")
		return r.json()
	except Exception, e:
		logger.error("fetching failed; %s: %s" % (type(e).__name__, e))
		return {}

def buy(user, *products):
	"""
	Takes a user id (sci login name) and a list of products
	(db id, may still require casting) and adds the bill to the intranet.

	In case of a communication error this method blocks and retries to
	add the bill to the intranet.

	If the bill was added successfully True is returned. Otherwise,
	if the given user is not allowed to purchase things or a products
	is unknown, False is returned.
	"""
	logger = logging.getLogger("remote:buy")
	beverages = encode_buy(products)
	payload = {'buy': {'beverages': beverages, 'user': user}}
	headers = {'content-type': 'application/json'}
	# HTTP-200 -> ok
	# HTTP-422 -> scanned user is not allowed to buy stuff
	# HTTP-otherwise -> something went wrong, retry
	logger.info("init buy sequence")
	try_sync = True
	while True:
		try:
			r = requests.put(URL_BUY, data=json.dumps(payload), headers=headers, auth=(AUTH_USER, AUTH_PASSWORD))
			if r.status_code == 200:
				logger.info("...everything worked fine")
				return True
			elif r.status_code == 422:
				# sync
				if not try_sync:
					logger.critical("...did not work (user or product unknown by FSIntra)")
					return False
				else:
					logger.error("...did not work (user or product unknown by FSIntra) -> syncing")
					try_sync = True
					from product_list import PRODUCT_LIST
					PRODUCT_LIST.update()
			else:
				# something went terribly wrong, retry
				logger.critical("...worked perfectly wrong")
				LCD.message_on(**MSG_BUY_RETRY)
				time.sleep(MSG_BUY_RETRY_WAIT)
		except requests.ConnectionError:
			logger.critical("connection refused. Are you online")
			LCD.message_on(**MSG_BUY_RETRY)
			time.sleep(MSG_BUY_RETRY_WAIT)
