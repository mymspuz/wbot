import datetime
from pyrogram import emoji
import pandas as pd
from pathlib import Path


class BotDB:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def get_item(self, table_name, item_id, list_fields=None):
        if list_fields is None:
            list_fields = ['*']
        fields = ', '.join(list_fields)
        sql_text = f'SELECT {fields} FROM {table_name} WHERE id = :id'
        sql_params = {'id': item_id}
        cursor = self.conn.cursor()
        cursor.execute(sql_text, sql_params)
        return cursor.fetchone()

    def get_list(self, table_name, list_fields=None):
        if list_fields is None:
            list_fields = ['*']
        fields = ', '.join(list_fields)
        sql_text = f'SELECT {fields} FROM {table_name}'
        cursor = self.conn.cursor()
        cursor.execute(sql_text)
        return cursor.fetchall()

    def remove_item(self, table_name, item_id):
        sql_text = f'DELETE FROM {table_name} WHERE id = :id'
        sql_params = {'id': item_id}
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception as e:
            return False
        return True

    def get_balance(self, user_id, date=datetime.date.today()):
        sql_text = 'SELECT sum(price) FROM bot_purchases WHERE user = :id AND date <= :date GROUP BY user'
        sum_purchases = self._get_sum(sql_text, user_id, date)
        if not sum_purchases.get('result', True):
            return sum_purchases
        sql_text = 'SELECT sum(value) FROM bot_payments WHERE user = :id  AND date <= :date GROUP BY user'
        sum_payments = self._get_sum(sql_text, user_id, date)
        if not sum_payments.get('result', True):
            return sum_purchases
        return {'result': True, 'msg': sum_payments['sum'] - sum_purchases['sum']}

    def _get_sum(self, sql_text, user_id, date):
        try:
            self.cursor.execute(sql_text, {'id': user_id, 'date': date})
            sql_result = self.cursor.fetchone()
            return {'sum': sql_result[0]} if sql_result else {'sum': 0}
        except Exception as e:
            return {'result': False, 'msg': str(e)}


class BotUsers(BotDB):
    def add_user(self, data):
        if not self.check_data(data):
            return False, 'Name or TelegramName no unique!!!'
        sql_text = 'INSERT INTO bot_users (name, telegram_name, user_access) VALUES (:name, :telegram_name, :access)'
        sql_params = {
            'name': data[0],
            'telegram_name': data[1] if data[1] else None,
            'access': True if data[2].upper() == 'Y' else False
        }
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception:
            return False, 'Error sql query!!!'
        return True, ''

    def edit_user(self, data, user_id):
        if not self.check_data(data, user_id):
            return False, 'Name or TelegramName no unique!!!'
        sql_text = 'UPDATE bot_users ' \
                   'SET name = :name, telegram_name = :telegram_name, user_access = :access WHERE id = :id'
        sql_params = {
            'name': data[0],
            'telegram_name': data[1] if data[1] else None,
            'access': True if data[2].upper() == 'Y' else False,
            'id': user_id
        }
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception:
            return False, 'Error sql query!!!'
        return True, ''

    def check_data(self, data, user_id=0):
        or_t_name = ''
        and_id = ''
        sql_params = {'name': data[0]}
        if data[1]:
            or_t_name = ' OR telegram_name = :t_name'
            sql_params['t_name'] = data[1]
        if user_id:
            and_id = ' AND id <> :id'
            sql_params['id'] = user_id
        sql_text = f'SELECT id FROM bot_users WHERE (name = :name{or_t_name}){and_id} LIMIT 1'
        cursor = self.conn.cursor()
        cursor.execute(sql_text, sql_params)
        sql_result = cursor.fetchone()
        return False if sql_result else True


class BotItemsExpenses(BotDB):
    def add_iexp(self, data):
        if not self.check_data(data):
            return False, 'Name no unique!!!'
        sql_text = 'INSERT INTO bot_items_expenses (name) VALUES (:name)'
        sql_params = {
            'name': data,
        }
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception:
            return False, 'Error sql query!!!'
        return True, ''

    def check_data(self, data, iexp_id=0):
        and_id = ''
        sql_params = {'name': data[0]}
        if iexp_id:
            and_id = ' AND id <> :id'
            sql_params['id'] = iexp_id
        sql_text = f'SELECT id FROM bot_items_expenses WHERE name = :name{and_id}'
        cursor = self.conn.cursor()
        cursor.execute(sql_text, sql_params)
        sql_result = cursor.fetchone()
        return False if sql_result else True

    def edit_iexp(self, data, iexp_id):
        if not self.check_data(data, iexp_id):
            return False, 'Name no unique!!!'
        sql_text = 'UPDATE bot_items_expenses SET name = :name WHERE id = :id'
        sql_params = {
            'name': data,
            'id': iexp_id
        }
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception:
            return False, 'Error sql query!!!'
        return True, ''


class BotMeters(BotDB):
    def add_item(self, data):
        check = self.check_data(data['value'], data['date'], data['user'])
        if not check['result']:
            return check
        sql_text = 'INSERT INTO bot_meters (date, user, value) VALUES (:date, :user, :value)'
        sql_params = {
            'date': data['date'],
            'user': data['user'],
            'value': data['value']
        }
        try:
            self.cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        return {'result': True, 'msg': f'Meter add success!!! Difference - {check["difference"]}'}

    def check_data(self, value, date, user):
        diff = 0
        sql_params = {'date': date, 'user': user}

        sql_text = 'SELECT value FROM bot_meters WHERE date = :date AND user = :user'
        self.cursor.execute(sql_text, sql_params)
        sql_result = self.cursor.fetchone()
        if sql_result:
            return {'result': False, 'msg': f'Value already exists {sql_result[0]}'}

        sql_text = 'SELECT value FROM bot_meters WHERE date < :date AND user = :user ORDER BY date DESC'
        self.cursor.execute(sql_text, sql_params)
        sql_result = self.cursor.fetchone()
        if sql_result:
            if value < sql_result[0]:
                return {'result': False, 'msg': f'Value must be greater {sql_result[0]}'}
            else:
                diff = round(value - sql_result[0], 2)

        sql_text = 'SELECT value FROM bot_meters WHERE date > :date AND user = :user ORDER BY date'
        self.cursor.execute(sql_text, sql_params)
        sql_result = self.cursor.fetchone()
        if sql_result:
            if value > sql_result[0]:
                return {'result': False, 'msg': f'Value must be less {sql_result[0]}'}

        return {'result': True, 'difference': diff}

    def get_last_meter(self, user_id):
        sql_text = 'SELECT value FROM bot_meters WHERE user = :id ORDER BY date DESC LIMIT 1'
        sql_params = {'id': user_id}
        try:
            self.cursor.execute(sql_text, sql_params)
            sql_result = self.cursor.fetchone()
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        if sql_result:
            return {'result': True, 'msg': f'Last meter {sql_result[0]}'}
        else:
            return {'result': True, 'msg': f'Empty meters'}


class BotPurchases(BotDB):
    def add_purchase(self, data):
        check = self._check_data(data['date'], data['item_expens'])
        if not check['result']:
            return check
        meters = []
        result = []
        sum_meters = 0
        last_date = self._get_last_date_purchase(data['date'], data['item_expens'])
        list_user = self.get_list('bot_users', ['id', 'name'])
        for i in list_user:
            if data['price'] == 0:
                result.append({'user': i[0], 'name': i[1], 'meter': 0, 'price': 0})
            else:
                if last_date['result']:
                    diff = self._get_diff_meters(i[0], i[1], last_date['result'], data['date'])
                    if not diff.get('result', True):
                        return diff
                    meters.append(diff)
                    sum_meters += diff['meter']
                else:
                    result.append({
                        'user': i[0],
                        'name': i[1],
                        'meter': 0,
                        'price': round(data['price'] / len(list_user))
                    })
        if not result:
            for i in meters:
                percent = i['meter'] * 100 / sum_meters
                result.append({
                    'user': i['id'],
                    'name': i['name'],
                    'meter': i['meter'],
                    'price': round(data['price'] * percent / 100)
                })
        msg = ''
        for i in result:
            sql_text = 'INSERT INTO bot_purchases (item_expens, date, price, user) ' \
                       'VALUES (:expens, :date, :price, :user)'
            sql_params = {
                'expens': data['item_expens'],
                'date': data['date'],
                'price': i['price'],
                'user': i['user']
            }
            try:
                duty = self.get_balance(i['user'], data['date'])
                self.cursor.execute(sql_text, sql_params)
                self.conn.commit()
            except Exception:
                return {'result': False, 'msg': 'Operation error DB!!!'}
            if duty['msg']:
                label = 'Долг' if duty['msg'] < 0 else 'Переплата'
                corr = i['price'] - duty['msg']
                msg += f"{i['name']} - {i['meter']}m3 - {label} - {duty['msg']} RUB - {i['price']} RUB Итого - {corr}\n"
                data['price'] -= duty['msg']
            else:
                msg += f"{i['name']} - {i['meter']}m3 - {i['price']} RUB\n"
        msg += f'--------------------\n{round(sum_meters, 2)}m3 - {data["price"]} RUB'
        return {'result': True, 'msg': msg}

    def get_list_diff(self, expens_id):
        last_date = self._get_last_date_purchase(datetime.date.today(), expens_id)
        if not last_date['result']:
            if not last_date['msg']:
                return 'First purchases'
            else:
                return last_date['msg']
        list_user = self.get_list('bot_users', ['id', 'name'])
        msg = ''
        sum_meters = 0
        for i in list_user:
            diff = self._get_diff_meters(i[0], i[1], last_date['result'], datetime.date.today())
            if not diff.get('result', True):
                return diff['msg']
            sum_meters += diff['meter']
            msg += f"{diff['name']} - {diff['meter']}m3\n"
        msg += f'--------------------\nALL - {round(sum_meters, 2)}m3'
        return msg

    def _get_diff_meters(self, user_id, user_name, date1, date2):
        sql_text = 'SELECT value FROM bot_meters ' \
                   'WHERE user = :user AND date BETWEEN :date1 AND :date2 ' \
                   'ORDER BY date'
        sql_params = {'user': user_id, 'date1': date1, 'date2': date2}
        try:
            self.cursor.execute(sql_text, sql_params)
            sql_result = self.cursor.fetchall()
        except Exception:
            return {'result': False, 'msg': 'Operation error DB!!!'}
        if sql_result:
            diff = round(sql_result[-1][0] - sql_result[0][0], 2)
            return {'id': user_id, 'name': user_name, 'meter': diff}
        else:
            return {'id': user_id, 'name': user_name, 'meter': 0}

    def _check_data(self, date, expens):
        sql_text = 'SELECT id FROM bot_purchases WHERE date = :date AND item_expens = :expens'
        sql_params = {'date': date, 'expens': expens}
        try:
            self.cursor.execute(sql_text, sql_params)
            sql_result = self.cursor.fetchone()
            if sql_result:
                return {'result': False, 'msg': 'Value already exists'}
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        return {'result': True}

    def _get_last_date_purchase(self, date, expens):
        sql_text = 'SELECT date FROM bot_purchases ' \
                   'WHERE item_expens = :expens AND date < :date ' \
                   'ORDER BY date DESC ' \
                   'LIMIT 1'
        sql_params = {'date': date, 'expens': int(expens)}
        try:
            self.cursor.execute(sql_text, sql_params)
            sql_result = self.cursor.fetchone()
            if sql_result:
                return {'result': sql_result[0]}
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        return {'result': False, 'msg': False}


class BotPayments(BotDB):
    def add_item(self, data):
        sql_text = 'INSERT INTO bot_payments (user, date, value) VALUES (:user, :date, :value)'
        sql_params = {
            'user': data['user'],
            'date': data['date'],
            'value': data['value']
        }
        try:
            self.cursor.execute(sql_text, sql_params)
            self.conn.commit()
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        return {'result': True, 'msg': 'Payment add success'}


class BotReports(BotDB):
    def report_debts(self):
        list_user = self.get_list('bot_users', ['id', 'name'])
        msg = ''
        for i in list_user:
            balance = self.get_balance(i[0])
            if balance['msg'] == 0:
                my_emoji = emoji.HANDSHAKE
            elif balance['msg'] > 0:
                my_emoji = emoji.THUMBS_UP
            else:
                my_emoji = emoji.THUMBS_DOWN
            msg += f"{my_emoji} {i[1]} - {balance['msg']} RUB\n"
        return msg

    def reports_meters(self):
        list_user = self.get_list('bot_users', ['id', 'name'])
        msg = ''
        sql_text = 'SELECT value FROM bot_meters WHERE user = :id ORDER BY date DESC LIMIT 2'
        for i in list_user:
            last_meter = 0
            diff_meter = 0
            sql_params = {'id': i[0]}
            try:
                self.cursor.execute(sql_text, sql_params)
                sql_result = self.cursor.fetchall()
            except Exception as e:
                return str(e)
            if sql_result:
                last_meter = sql_result[0][0]
                if len(sql_result) == 2:
                    diff_meter = round(last_meter - sql_result[1][0], 2)
            msg += f"{i[1]} - {last_meter}m3 - **{diff_meter}**m3\n"
        return msg

    def reports_consumption(self, user):
        sql_text = 'SELECT m.date, u.name, m.value ' \
                   'FROM bot_meters AS m ' \
                   'LEFT JOIN bot_users AS u ON u.id = m.user ' \
                   'ORDER BY m.date, m.user'
        try:
            df = pd.read_sql_query(sql_text, self.conn)
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        pt = pd.pivot_table(df, index='date', columns='name', values='value')
        pt.reset_index(inplace=True)
        diff = pt.set_index('date').diff()
        columns = [i for i in diff.columns]
        diff['temp'] = diff.index.values
        pic = diff.plot(x='temp', y=columns, kind="bar")
        path = Path.cwd() / 'reports' / f'{user}_consumption.png'
        pic.figure.savefig(path)
        return {'result': True, 'path': path}

    def reports_expenses(self, user):
        sql_text = 'SELECT i.name, p.date, sum(price) AS price ' \
                   'FROM bot_purchases AS p ' \
                   'LEFT JOIN bot_items_expenses AS i ON i.id = p.item_expens ' \
                   'GROUP BY item_expens, date ' \
                   'ORDER BY date'
        try:
            df = pd.read_sql_query(sql_text, self.conn)
        except Exception as e:
            return {'result': False, 'msg': str(e)}
        path = Path.cwd() / 'reports' / f'{user}_expenses.xlsx'
        df.to_excel(path)
        return {'result': True, 'path': path}
