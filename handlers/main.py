from aiogram import types
from aiogram.fsm.context import FSMContext

from keyboards import main_menu, delete_keyboard, country_menu
import emoji
import database.sql_queries as db
from aiogram.filters import CommandStart, or_f
import aiogram.utils.markdown as markdown
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from aiogram.fsm.state import StatesGroup, State

'''main commands'''


async def echo_handler(message: types.Message) -> None:
    await message.answer("Sorry, didn't understand what do you want to know, could you choose again?",
                         reply_markup=main_menu)


# answer to command /start with turning on keyboard
async def command_start_handler(message: types.Message):
    await message.delete()
    await message.answer(f"Hello, {markdown.hbold(message.from_user.full_name)}!, what would you like to know?" +
                         emoji.emojize(':eyes:'), reply_markup=main_menu)


# command useful links, getting data from SQL and giving back list of links which is turing into inline keyboard buttons
async def command_useful_links(message: types.Message):
    data = await db.sql_find_links()
    builder = InlineKeyboardBuilder()
    if data == {}:
        await message.answer("Sorry, can't find information")
    else:
        for i in data.items():
            builder.row(types.InlineKeyboardButton(text=i[0], url=i[1], callback_data=i[0]))
    await message.answer(
        "Here what I've found: ",
        reply_markup=builder.as_markup()
    )
    await message.answer("Would you like to know anything else?", reply_markup=main_menu)


# command for getting feedback which using FSM to get message and then sending it to SQL
async def command_feedback(message: types.Message, state: FSMContext):
    await message.answer("You can write feedback here and I'll send it to my developer", reply_markup=delete_keyboard)
    await state.set_state(WriteFeedback.feedback)


class WriteFeedback(StatesGroup):
    feedback = State()


async def command_get_feedback(message: types.Message, state: FSMContext):
    await db.sql_send_feedback(message.text)
    await message.answer("Thank you for your feedback", reply_markup=delete_keyboard)
    await state.clear()


# command country info which uses fsm to write country and user in sql, then use this data for giving detailed
# information about specific country to specific user
async def command_country_info(message: types.Message, state: FSMContext):
    await message.answer("Type country about which you wanna know more", reply_markup=delete_keyboard)
    await state.set_state(WriteCountry.country)


class WriteCountry(StatesGroup):
    country = State()


async def get_country_info(message: types.Message, state: FSMContext):
    country = message.text
    await state.clear()
    await message.answer("I'm searching data about " + country + ", wait")
    data, img = await db.get_country_with_data(country, message.from_user.id)
    if img != "":
        await message.answer_photo(img)
    if data != "":
        await message.answer(data, parse_mode='Markdown')
        await message.answer("Choose what else do you want to know?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, can't find any information about such country, could you try to write again",
                             reply_markup=main_menu)


'''Commands for getting detailed info about specific country'''


async def command_back(message: types.Message):
    await message.answer("What would you like to know?", reply_markup=main_menu)


async def command_climate(message: types.Message):
    data = await db.sql_find_climate(message.from_user.id)
    if data != "":
        await message.answer("*Climate in chosen country * \n" + data, parse_mode='Markdown')
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text='weather and climate',
                                               url='https://weather-and-climate.com/'))
        await message.answer(
            "For more info u can check this: ",
            reply_markup=builder.as_markup())
        await message.answer("Would you like to know anything else?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, didn't find info about climate in chosen country")


async def command_main_cities(message: types.Message):
    data = await db.sql_find_main_cities(message.from_user.id)
    if data != "":
        await message.answer("*Main cities:*" + data, parse_mode='Markdown')
        await message.answer("Would you like to know anything else?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, didn't find info about climate in chosen country")


class WriteJob(StatesGroup):
    job = State()


async def command_job_opportunities(message: types.Message, state: FSMContext):
    country = await db.sql_get_user_country(message.from_user.id)
    if country != "":
        await message.answer("Type job title about which you wanna know more", reply_markup=delete_keyboard)
        await state.set_state(WriteJob.job)
    else:
        await message.answer("Sorry, didn't find info about chosen country, please choose it again",
                             reply_markup=main_menu)


async def command_job_opportunities_details(message: types.Message, state: FSMContext):
    job_title = message.text
    await state.clear()
    await message.answer("I'm searching for data, wait")
    data = await db.sql_find_jobs(message.from_user.id, job_title)
    if data != "":
        builder = InlineKeyboardBuilder()
        for i in data.items():
            builder.row(types.InlineKeyboardButton(text=i[0], url=i[1], callback_data=i[0]))
        await message.answer(
            "Here what I've found: ",
            reply_markup=builder.as_markup()
        )
        await message.answer("Would you like to know anything else?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, didn't find info about chosen country")


async def command_visas(message: types.Message):
    country = await db.sql_get_user_country(message.from_user.id)
    if country != "":
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Visas",
                                               url="https://visaguide.world/europe/" + country + "-visa/"))
        await message.answer("You can read about visa regimes here: ", reply_markup=builder.as_markup())
        await message.answer("Would you like to know anything else?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, didn't find info about chosen country, please choose it again",
                             reply_markup=main_menu)


async def command_expanses(message: types.Message):
    data = await db.sql_find_expanses(message.from_user.id)
    if data != "":
        await message.answer("Here what I've found about expanses in chosen country: \n" + data,
                             reply_markup=country_menu)
        await message.answer("Would you like to know anything else?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, didn't find info about chosen country")


async def command_taxes(message: types.Message):
    data = await db.sql_find_taxes(message.from_user.id)
    if data != "":
        await message.answer("Here what I've found about taxes in chosen country: \n" + data, reply_markup=country_menu)
        await message.answer("Would you like to know anything else?", reply_markup=country_menu)
    else:
        await message.answer("Sorry, didn't find info about chosen country")


async def command_rent(message: types.Message):
    data = await db.sql_find_rent(message.from_user.id)
    if data != "":
        builder = InlineKeyboardBuilder()
        for i in data.items():
            builder.row(types.InlineKeyboardButton(text=i[0], url=i[1], callback_data=i[0]))
        await message.answer(
            "Here what I've found: ",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer("Sorry, can't find information")
    await message.answer("Would you like to know anything else?", reply_markup=country_menu)


def register_handlers_main(router):
    router.message.register(command_start_handler, CommandStart())
    router.message.register(command_useful_links, F.text.casefold() == 'useful links')
    router.message.register(command_feedback, or_f(F.text.casefold() == 'give feedback',
                                                   F.text.casefold() == 'feedback'))
    router.message.register(command_get_feedback, WriteFeedback.feedback, F.text)
    router.message.register(command_country_info, F.text.casefold() == 'country info')
    router.message.register(get_country_info, WriteCountry.country, F.text)
    router.message.register(command_back, F.text.casefold() == 'back')
    router.message.register(command_climate, F.text.casefold() == 'climate')
    router.message.register(command_main_cities, F.text.casefold() == 'main cities')
    router.message.register(command_job_opportunities, F.text.casefold() == 'job opportunities')
    router.message.register(command_job_opportunities_details, WriteJob.job, F.text)
    router.message.register(command_visas, F.text.casefold() == 'visas')
    router.message.register(command_expanses, F.text.casefold() == 'expanses')
    router.message.register(command_taxes, F.text.casefold() == 'taxes')
    router.message.register(command_rent, F.text.casefold() == 'rent')
    router.message.register(echo_handler, )
