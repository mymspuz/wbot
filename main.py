import configparser
from pathlib import Path
import logging
import sqlite3
from pyrogram import Client, filters, emoji
from pyrogram.types import InlineKeyboardMarkup
import datetime

from bot_db import BotDB, BotUsers, BotItemsExpenses, BotMeters, BotPurchases, BotPayments, BotReports
import bot_menu


def get_users_ini():
    result = {}
    path = Path('config.ini')
    if not path.exists() or not path.is_file():
        logging.error('No file config.ini')
        return {}
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        admins = config.get('admins', 'users')
    except configparser.NoSectionError:
        logging.error('No section: "admins"')
        return {}
    except configparser.NoOptionError:
        logging.error('No option "users" in section: "admins"')
        return {}
    for i in admins.split(';'):
        result[i] = True
    return result


def get_users_db():
    result = {}
    current_users = BotUsers(conn=conn)
    for i in current_users.get_list('bot_users', ['telegram_name', 'user_access']):
        result[i[0]] = i[1]
    del current_users
    return result


def get_cur_db():
    path = Path('wbot.db')
    if not path.exists() or not path.is_file():
        logging.error('No file DB')
        return False
    try:
        conn = sqlite3.connect('wbot.db', check_same_thread=False)
    except Exception:
        logging.error('Error connect DB')
        return False
    return conn


def get_user_access(user_name):
    return users.get(user_name, 'not')


def check_candidate(data):
    if len(data) != 3 or not data[2].upper() in ['Y', 'N']:
        return False
    if not data[0]:
        return False
    return True


def check_date_value(data):
    if len(data) == 0 or len(data) > 2:
        return {'result': False, 'msg': 'Incorrect data!!!'}
    if len(data) == 2:
        v_date = data[0]
        v_meter = data[1].replace(',', '.')
    else:
        v_date = False
        v_meter = data[0].replace(',', '.')
    if v_date:
        try:
            v_date = datetime.datetime.strptime(v_date, '%d.%m.%y')
            v_date = datetime.date(v_date.year, v_date.month, v_date.day)
        except:
            return {'result': False, 'msg': 'Incorrect Date!!!'}
    else:
        v_date = datetime.date.today()
    try:
        v_meter = round(float(v_meter), 2)
    except:
        return {'result': False, 'msg': 'Incorrect Meter!!!'}
    return {'result': True, 'date':v_date, 'value': v_meter}


if __name__ == "__main__":
    user_status = {}
    logging.basicConfig(filename='bot.log', level=logging.ERROR)
    conn = get_cur_db()
    if conn:
        users = get_users_ini()
        users.update(get_users_db())
        app = Client(session_name='mspuz_bot', config_file='config.ini')


        @app.on_message(filters.command(["start"]))
        def menu_main(_, message):
            user_access = get_user_access(message.chat.username)
            if user_access == 'not':
                message.reply('Access is closed')
                return
            message.reply(
                f'{emoji.HOUSE} MAIN MENU',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_main_menu(user_access))
            )


        @app.on_callback_query(bot_menu.dynamic_data_filter('users'))
        def menu_list_users(_, query):
            query.message.reply(
                f'{emoji.BUST_IN_SILHOUETTE} LIST USERS',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_users_menu(conn=conn))
            )


        @app.on_callback_query(bot_menu.dynamic_data_filter('items_expenses'))
        def menu_list_items_expenses(_, query):
            query.message.reply(
                f'{emoji.MONEY_BAG} LIST ITEMS EXPENSES',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_items_expenses_menu(conn=conn))
            )


        @app.on_callback_query(bot_menu.dynamic_data_filter('meters'))
        def menu_meters(_, query):
            query.message.reply(
                f'{emoji.PAGER} LIST USERS METERS',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_meters_menu(conn=conn))
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('purchases'))
        def menu_purchases(_, query):
            query.message.reply(
                f'{emoji.SHOPPING_BAGS} LIST PURCHASES',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_purchases_menu(conn=conn))
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('payments'))
        def menu_payments(_, query):
            query.message.reply(
                f'{emoji.DOLLAR_BANKNOTE} LIST PAYMENTS',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_payments_menu(conn=conn))
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('reports'))
        def menu_reports(_, query):
            query.message.reply(
                f'{emoji.BAR_CHART} REPORTS',
                reply_markup=InlineKeyboardMarkup(bot_menu.get_reports_menu())
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('report_debts'))
        def report_debts(_, query):
            debts = BotReports(conn=conn)
            query.message.reply(
                debts.report_debts()
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('report_meters'))
        def report_meters(_, query):
            meters = BotReports(conn=conn)
            query.message.reply(
                meters.reports_meters()
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('report_consumption'))
        def report_consumption(_, query):
            consumption = BotReports(conn=conn)
            consumption = consumption.reports_consumption(query.from_user.username)
            if not consumption['result']:
                query.message.reply(
                    consumption['msg']
                )
            else:
                query.message.reply_photo(consumption['path'])

        @app.on_callback_query(bot_menu.dynamic_data_filter('report_expenses'))
        def report_expenses(_, query):
            expenses = BotReports(conn=conn)
            expenses = expenses.reports_expenses(query.from_user.username)
            if not expenses['result']:
                query.message.reply(
                    expenses['msg']
                )
            else:
                query.message.reply_document(expenses['path'])

        @app.on_callback_query(bot_menu.dynamic_data_filter('add_user'))
        def status_add_user(_, query):
            user_status[query.from_user.username] = 'add_user'
            query.message.reply(
                'Input UserName;TelegramName;Admin(Y/N)'
            )

        @app.on_callback_query(bot_menu.dynamic_data_filter('add_iexp'))
        def status_add_items_expenses(_, query):
            user_status[query.from_user.username] = 'add_iexp'
            query.message.reply(
                'Input NameItemsExpenses'
            )

        @app.on_message(filters.text)
        def input_text(_, message):
            status = user_status.get(message.from_user.username, False)
            if not status:
                message.reply('Wrong data')
                return
            if status.startswith('iexp_purchase_'):
                purchase = check_date_value(message.text.strip().split('-'))
                if not purchase['result']:
                    message.reply(purchase['msg'])
                    return
                new_purchase = BotPurchases(conn=conn)
                result = new_purchase.add_purchase({
                                                'date': purchase['date'],
                                                'item_expens': int(status.split('_')[-1]),
                                                'price': purchase['value']
                                            })
                del new_purchase
                user_status.pop(message.from_user.username)
                message.reply(result['msg'])
                return
            if status.startswith('user_payment_') or status.startswith('user_meter_'):
                item = check_date_value(message.text.strip().split('-'))
                if not item['result']:
                    message.reply(item['msg'])
                    return
                if status.startswith('user_payment_'):
                    new_item = BotPayments(conn=conn)
                elif status.startswith('user_meter_'):
                    new_item = BotMeters(conn=conn)
                result = new_item.add_item({
                                            'date': item['date'],
                                            'user': int(status.split('_')[-1]),
                                            'value': item['value']
                                            })
                del new_item
                user_status.pop(message.from_user.username)
                message.reply(result['msg'])
                return
            if status == 'add_user' or status.startswith('edit_user_'):
                candidate = message.text.strip().split(';')
                if not check_candidate(candidate):
                    message.reply('Incorrect data')
                    return
                new_user = BotUsers(conn=conn)
                if status == 'add_user':
                    result, msg_error = new_user.add_user(candidate)
                if status.startswith('edit_user_'):
                    result, msg_error = new_user.edit_user(candidate, status.split("_")[-1])
                del new_user
                if not result:
                    message.reply(msg_error)
                    return
                user_status.pop(message.from_user.username)
                message.reply('User operation success')
            if status == 'add_iexp' or status.startswith('edit_iexp_'):
                candidate = message.text.strip()
                if not candidate:
                    message.reply('Incorrect data')
                    return
                new_iexp = BotItemsExpenses(conn=conn)
                if status == 'add_iexp':
                    result, msg_error = new_iexp.add_iexp(candidate)
                if status.startswith('edit_iexp_'):
                    result, msg_error = new_iexp.edit_iexp(candidate, status.split('_')[-1])
                del new_iexp
                if not result:
                    message.reply(msg_error)
                    return
                user_status.pop(message.from_user.username)
                message.reply('ItemsExpenses operation success')


        @app.on_callback_query()
        def input_callback(_, query):
            if query.data.startswith('iexp_purchase_'):
                user_status[query.from_user.username] = query.data
                diffs = BotPurchases(conn=conn)
                query.message.reply(
                    diffs.get_list_diff(query.data.split('_')[-1])
                )
                query.message.reply(
                    'Input DD.MM.YY-Price'
                )
                return

            if query.data.startswith('user_edit_'):
                user_status[query.from_user.username] = f'edit_user_{query.data.split("_")[-1]}'
                query.message.reply(
                    'Input new UserName;TelegramName;Admin(Y/N)'
                )
                return

            if query.data.startswith('user_remove_'):
                user = BotUsers(conn=conn)
                if user.remove_item('bot_users', query.data.split('_')[-1]):
                    query.message.reply('User remove success')
                else:
                    query.message.reply('Operation error!!!')
                return

            if query.data.startswith('user_meter_'):
                user_status[query.from_user.username] = query.data
                meter = BotMeters(conn=conn)
                meter = meter.get_last_meter(int(query.data.split('_')[-1]))
                query.message.reply(meter['msg'])
                query.message.reply('Input DD.MM.YY-Value')
                return

            if query.data.startswith('user_payment_'):
                user_status[query.from_user.username] = query.data
                query.message.reply('Input DD.MM.YY-Payment')
                duty = BotDB(conn=conn)
                balance = duty.get_balance(int(query.data.split('_')[-1]))
                query.message.reply(f"Duty - {balance['msg']}")
                return

            if query.data.startswith('user_'):
                name, btns = bot_menu.get_user_menu(query.data.split('_')[-1], conn)
                query.message.reply(name, reply_markup=InlineKeyboardMarkup([btns]))
                return

            if query.data.startswith('iexp_edit_'):
                user_status[query.from_user.username] = f'edit_iexp_{query.data.split("_")[-1]}'
                query.message.reply(
                    'Input new ItemExpensesName'
                )
                return

            if query.data.startswith('iexp_remove_'):
                iexp = BotItemsExpenses(conn=conn)
                if iexp.remove_item('bot_items_expenses', query.data.split('_')[-1]):
                    query.message.reply('ItemExpenses remove success')
                else:
                    query.message.reply('Operation error!!!')
                return

            if query.data.startswith('iexp_'):
                name, btns = bot_menu.get_item_expenses_menu(query.data.split('_')[-1], conn)
                query.message.reply(name, reply_markup=InlineKeyboardMarkup([btns]))
                return


        app.run()
