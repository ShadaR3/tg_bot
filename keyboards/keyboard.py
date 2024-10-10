from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


main_kb = [[KeyboardButton(text='Country info'),
           KeyboardButton(text='Useful links')],
           [KeyboardButton(text='Give feedback')]]

county_kb = [[KeyboardButton(text='Climate'),
             KeyboardButton(text='Main cities'),
             KeyboardButton(text='Job opportunities')],
             [KeyboardButton(text='Visas'),
             KeyboardButton(text='Expanses'),
             KeyboardButton(text='Taxes')],
             [KeyboardButton(text='Rent'),
             KeyboardButton(text='Back')]]


main_menu = ReplyKeyboardMarkup(keyboard=main_kb, resize_keyboard=True)
delete_keyboard = ReplyKeyboardRemove()
country_menu = ReplyKeyboardMarkup(keyboard=county_kb, resize_keyboard=True)
