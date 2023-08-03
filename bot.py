from pyrogram import filters
from pyrogram.types import KeyboardButton, ReplyKeyboardMarkup
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot_settings import bot, url_request
import db_functions as db
from languages import languages
from transliterate import translit
import requests
import re 



########################################## Доп. Функции #######################################################


################## Проверка наличия кириллицы #################

def has_cyrillic(text):
    return bool(re.search(r'[а-яА-Я]', text))

###############################################################



########## Словарь перевода из латиницы в кириллицу ###########

en_to_ru = dict(zip(map(ord, "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
                           'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~'),
                           "йцукенгшщзхъфывапролджэячсмитьбю.ё"
                           'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'))

###############################################################



########## Словарь перевода из кириллицы в латиницу ###########

ru_to_en = dict(zip(map(ord, "йцукенгшщзхъфывапролджэячсмитьбю.ё"
                           'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'),
                           "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
                           'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~')) 

###############################################################



################## Запрос GET /shop_search/ ###################

def api_request(shop_name):
	try:
		resp =  requests.get(f'{url_request}/shop_search/?q={shop_name}', timeout = 30)
		if resp.status_code == 200:
			return resp

		return resp.text

	except Exception as e:
		return e

###############################################################


###############################################################################################################




###################### Кнопка start ###########################

@bot.on_message(filters.command('start') & filters.private & filters.incoming)
def start(_, message):
	db.new_user(message.chat.id)
	db.state_change(message.chat.id, 'menu')
	language = db.lang_get(message.chat.id)
	if language is None:
		bot.send_message(
			chat_id  = message.chat.id,
			text = '🌐 Выберите язык',
			reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('🇷🇺 Русский язык', callback_data  = 'ru')], [InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data  = 'uz')], [InlineKeyboardButton('🇬🇧 English', callback_data = 'en')]])
			)
		db.state_change(message.chat.id, 'change_language')
		return

	bot.send_message(
		chat_id = message.chat.id,
		text  = languages[language]['enter_store_name'],
		reply_markup = ReplyKeyboardMarkup([[KeyboardButton(languages[language]['lang_choose'])]], resize_keyboard = True)
		)

###############################################################




########### Выдача информации по названию магазина ############

@bot.on_message(filters.private & filters.text)
def shop_info_sender(_, message):
	language = db.lang_get(message.chat.id)
	state = db.state_get(message.chat.id)

	if state == 'menu':
		if message.text == languages[language]['lang_choose']:
			db.lang_change(message.chat.id, None)
			start(_, message)
			return

		resp = api_request(message.text)
		try:
			shops = resp.json()
			shop = shops['data']['items'][language]
			if len(shop) == 0:
				resp = api_request(translit(message.text, 'ru', reversed = has_cyrillic(message.text)))
				shops = resp.json()
				shop = shops['data']['items'][language]
				if len(shop) == 0:
					if has_cyrillic(message.text):
						resp = api_request(message.text.translate(ru_to_en))
					else:
						resp = api_request(message.text.translate(en_to_ru))
					shops = resp.json()
					shop = shops['data']['items'][language]
					if len(shop) == 0:
						bot.send_message(
							chat_id = message.chat.id,
							text = languages[language]['not_found']
							)
						return

			shop = shop[0]
			try:
				bot.send_photo(
					chat_id = message.chat.id,
					photo = f"http:{shop['picture']}", 
					caption = f"<b>{shop['name']}</b>\n\n<b>SAP ID: </b>{shop['id']}\n<b>Code: </b>{db.code_get(shop['id'])}\n<b>{languages[language]['legal_address']}</b>{shop['address']}\n<b>Google Maps: </b><a href = 'https://www.google.com/maps/dir//{shop['location']['lat']},{shop['location']['lon']}/@{shop['location']['lat']},{shop['location']['lon']},18z?entry=ttu'>{shop['name']}</a>"
					)
			except:
				bot.send_message(
					chat_id = message.chat.id,
					text = f"<b>{shop['name']}</b>\n\n<b>SAP ID: </b>{shop['id']}\n<b>Code: </b>{db.code_get(shop['id'])}\n<b>{languages[language]['legal_address']}</b>{shop['address']}\n<b>Google Maps: </b><a href = 'https://www.google.com/maps/dir//{shop['location']['lat']},{shop['location']['lon']}/@{shop['location']['lat']},{shop['location']['lon']},18z?entry=ttu'>{shop['name']}</a>",
					disable_web_page_preview = True
					)

			bot.send_location(
				chat_id = message.chat.id, 
				latitude = float(shop['location']['lat']),
				longitude = float(shop['location']['lon'])
				)
		
		except:
			bot.send_message(
				chat_id = message.chat.id,
				text = resp
				)

###############################################################




############### Обработка нажатий Inline кнопок ###############

@bot.on_callback_query()
def callback_handler(_, callback_query):
	state = db.state_get(callback_query.message.chat.id)

	if state == 'change_language':
		db.lang_change(callback_query.message.chat.id, callback_query.data)
		language = db.lang_get(callback_query.message.chat.id)
		bot.send_message(
			chat_id = callback_query.message.chat.id,
			text = languages[language]['lang_changed']
			)
		bot.delete_messages(
			chat_id = callback_query.message.chat.id,
			message_ids = callback_query.message.id
			)
		start(_, callback_query.message)
		return

	language = db.lang_get(callback_query.message.chat.id)

###############################################################







bot.run()
