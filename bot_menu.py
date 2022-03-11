from pyrogram import emoji, filters
from pyrogram.types import InlineKeyboardButton

from bot_db import BotUsers, BotItemsExpenses


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data
    )


def get_main_menu(access):
    result = []
    for i in MAIN_MENU:
        if not access and i['admin']:
            continue
        result.append([InlineKeyboardButton(f"{i['emoji']} {i['name']}", callback_data=i['data'])])
    return result


def get_users_menu(conn, meter=''):
    list_users = BotUsers(conn=conn)
    result = []
    num = 0
    row = []
    for i in list_users.get_list('bot_users', ['id', 'name', 'telegram_name', 'user_access']):
        temp = emoji.POLICE_OFFICER if i[3] else emoji.CONSTRUCTION_WORKER
        row.append(InlineKeyboardButton(f'{temp} {i[1].upper()}', callback_data=f'user_{meter}{i[0]}'))
        num += 1
        if num == 2:
            result.append(row.copy())
            row.clear()
            num = 0
    if len(row):
        result.append(row)
    if not meter:
        result.append([InlineKeyboardButton(f"{emoji.PLUS}", callback_data='add_user')])
    return result


def get_user_menu(user_id, conn):
    item_user = BotUsers(conn=conn)
    user = item_user.get_item('bot_users', user_id, ['name'])[0]
    del item_user
    btns = [
            InlineKeyboardButton(emoji.PENCIL, callback_data=f'user_edit_{user_id}'),
            InlineKeyboardButton(emoji.WASTEBASKET, callback_data=f'user_remove_{user_id}'),
            ]
    return user.upper(), btns


def get_items_expenses_menu(conn, purchase=''):
    list_iexp = BotItemsExpenses(conn=conn)
    result = []
    for i in list_iexp.get_list('bot_items_expenses'):
        result.append([InlineKeyboardButton(f'{emoji.GEM_STONE} {i[1].upper()}', callback_data=f'iexp_{purchase}{i[0]}')])
    if not purchase:
        result.append([InlineKeyboardButton(f'{emoji.PLUS}', callback_data='add_iexp')])
    return result


def get_item_expenses_menu(iexp_id, conn):
    item_iexp = BotItemsExpenses(conn=conn)
    iexp = item_iexp.get_item('bot_items_expenses', iexp_id, ['name'])[0]
    del item_iexp
    btns = [
            InlineKeyboardButton(emoji.PENCIL, callback_data=f'iexp_edit_{iexp_id}'),
            InlineKeyboardButton(emoji.WASTEBASKET, callback_data=f'iexp_remove_{iexp_id}'),
            ]
    return iexp.upper(), btns


def get_meters_menu(conn):
    return get_users_menu(conn, 'meter_')


def get_purchases_menu(conn):
    return get_items_expenses_menu(conn, 'purchase_')


def get_payments_menu(conn):
    return get_users_menu(conn, 'payment_')


def get_reports_menu():
    result = []
    for i in REPORT_MENU:
        result.append([InlineKeyboardButton(f"{i['emoji']} {i['name']}", callback_data=i['data'])])
    return result


MAIN_MENU = [
    {'name': 'Users', 'emoji': emoji.BUST_IN_SILHOUETTE, 'data': 'users', 'admin': True},
    {'name': 'Items Expenses', 'emoji': emoji.MONEY_BAG, 'data': 'items_expenses', 'admin': True},
    {'name': 'Meters', 'emoji': emoji.PAGER, 'data': 'meters', 'admin': True},
    {'name': 'Purchases', 'emoji': emoji.SHOPPING_BAGS, 'data': 'purchases', 'admin': True},
    {'name': 'Payments', 'emoji': emoji.DOLLAR_BANKNOTE, 'data': 'payments', 'admin': True},
    {'name': 'Reports', 'emoji': emoji.BAR_CHART, 'data': 'reports', 'admin': False},
]

REPORT_MENU = [
    {'name': 'Debts', 'emoji': emoji.BALANCE_SCALE, 'data': 'report_debts'},
    {'name': 'Meters', 'emoji': emoji.PAGER, 'data': 'report_meters'},
    {'name': 'Сonsumption', 'emoji': emoji.POTABLE_WATER, 'data': 'report_consumption'},
    {'name': 'Expenses', 'emoji': emoji.MONEY_BAG, 'data': 'report_expenses'},
]
