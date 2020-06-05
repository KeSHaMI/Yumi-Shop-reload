import telebot
from telebot import types
import json
import requests
import re
from config import *
import pymongo
from collections import Counter

bot = telebot.TeleBot(Token)

cluster = pymongo.MongoClient(f'mongodb+srv://Kesha:{password}@shop-ocoyn.mongodb.net/test?retryWrites=true&w=majority')

db = cluster['Shop']
collection = db['Tovars']

collection_user = db['Users']


def get_user(call, key):
    try:
        return  list(collection_user.find({'_id' : call.message.chat.id}))[0][key]
    except:
        return list(collection_user.find({'_id': call.chat.id}))[0][key]
def get_tovar(call, key, index='index'):

    tovar = list(collection.find({'category': get_user(call, 'category')}))[int(get_user(call, index))]

    return tovar[key]

def get_bucket(call):
    return sorted(Counter(get_user(call, 'tovar_id')).keys())[int(get_user(call, 'index_buck'))]

@bot.message_handler(commands=['start'])
def start(message):
    if not collection_user.find_one({'_id': message.chat.id}):
        collection_user.insert_one({'_id': message.chat.id,
                                    'name': None,
                                    'number': 0,
                                    'index': 0,
                                    'index_buck': 0,
                                    'category': 0,
                                    'tovar_id': [],

                                    })
    else:

        collection_user.update_one({'_id': message.chat.id},
                                   {'$set' : {'index' : 0,
                                              'category' : 0,
                                              'index_buck': 0,
                                              'tovar_id' : []
                                              }})

    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('🛍 Товари', callback_data='tovars')
    but2 = types.InlineKeyboardButton('🛒 Кошик', callback_data='bucket')
    but3 = types.InlineKeyboardButton('📒 Історія замовлень', callback_data='orders')

    markup.add(but1, but2, but3)

    bot.send_message(message.chat.id, 'Вітаю!\n'
                                      'Я бот для замовлень продукції YUMI Lashes \n' 
                                      'Оберіть товари та добавте їх у кошик. \n'
                                      'Після замовлення менеджер зв\'яжеться з Вами для узгодження деталей.\n'
                                      'Що ви хочете переглянути?:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'back')
def startscreen(call):
    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('🛍 Товари', callback_data='tovars')
    but2 = types.InlineKeyboardButton('🛒 Кошик', callback_data='bucket')
    but3 = types.InlineKeyboardButton('📒 Історія замовлень', callback_data='orders')

    markup.add(but1, but2, but3)

    bot.send_message(call.message.chat.id, 'Оберіть дію:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'tovars')
def categories(call):

    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('Основні продукти', callback_data='14')
    but2 = types.InlineKeyboardButton('Аксесуари', callback_data='13')
    but3 = types.InlineKeyboardButton('🔙  Повернутися назад', callback_data='back')

    markup.add(but1, but2, but3)


    bot.send_message(call.message.chat.id, 'Оберіть категорію товару', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['13', '14', 'cancel'])
def tovars(call):
    markup = types.InlineKeyboardMarkup()
    if  call.data in ['13', '14']:
        collection_user.update_one({'_id':call.message.chat.id}, {'$set': {'category': call.data}})
        collection_user.update_one({'_id': call.message.chat.id}, {'$set': {'index': 0}})

        markup.row(types.InlineKeyboardButton('✔Замовити на {} грн.'.format(get_tovar(call, 'price')[:-3]),
                                          callback_data='add{}'.format(get_tovar(call, '_id'))))


        but1 = types.InlineKeyboardButton('⬅', callback_data='minus')
        but2 = types.InlineKeyboardButton('{}/{}'.format(int(get_user(call, 'index'))+1,
                                                         len(list(collection.find({'category': get_tovar(call, 'category')})))),
                                          callback_data='Noooooooooo')
        but3 =  types.InlineKeyboardButton('➡', callback_data='plus')

        markup.row(but1, but2, but3)

        markup.row(types.InlineKeyboardButton('🛒  Кошик', callback_data='bucket'))

        markup.row(types.InlineKeyboardButton('🔙  Повернутися назад', callback_data='tovars'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='<a href="{1}">{0}</a>'.format(get_tovar(call, 'name'), get_tovar(call, 'image')),
                              parse_mode='HTML', reply_markup=markup
                              )

    else:
        if Counter(get_user(call, 'tovar_id')).get(get_tovar(call, '_id')):
            markup.row(types.InlineKeyboardButton('✔Замовити на {} грн. - {} шт.'.format(get_tovar(call, 'price')[:-3],
                                                    Counter(get_user(call, 'tovar_id')).get(get_tovar(call, '_id'))),
                                                  callback_data='add{}'.format(get_tovar(call, '_id'))))


        else:
            markup.row(types.InlineKeyboardButton('✔Замовити на {} грн.'.format(get_tovar(call, 'price')[:-3]),
                                                  callback_data='add{}'.format(get_tovar(call, '_id'))))


        but1 = types.InlineKeyboardButton('⬅', callback_data='minus')
        but2 = types.InlineKeyboardButton('{}/{}'.format(int(get_user(call, 'index')) + 1,
                                                         len(list(collection.find(
                                                             {'category': get_tovar(call, 'category')})))),
                                          callback_data='Noooooooooo')
        but3 = types.InlineKeyboardButton('➡', callback_data='plus')

        markup.row(but1, but2, but3)
        markup.row(types.InlineKeyboardButton('🛒  Кошик', callback_data='bucket'))
        markup.row(types.InlineKeyboardButton('🔙  Повернутися назад', callback_data='tovars'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup,
                              text='<a href="{1}">{0}</a>'.format(get_tovar(call, 'name'), get_tovar(call, 'image')), parse_mode='HTML'
                              )


@bot.callback_query_handler(func=lambda call: call.data.startswith('ad'))
def add_tovar(call):
    if call.data[2] == '-':
        prods = get_user(call, 'tovar_id')
        i = 0
        while prods[i] != call.data[3:]:
            i += 1
            continue
        prods.pop(i)
        collection_user.update_one({'_id' : call.message.chat.id},
                                   {'$set': {'tovar_id' : prods}})
        if call.data[3:] not in prods:
            collection_user.update_one({'_id': call.message.chat.id},
                                       {'$set': {'index_buck': 0}})

    else:
        collection_user.update_one({'_id' : call.message.chat.id},
                                   {'$push' : {'tovar_id' : call.data[3:]},})
    if (call.data[2] == 'b' )or (call.data[2] == '-'):
        bucket_upd(call)
    else:
        tovars(call)

@bot.callback_query_handler(func=lambda call: call.data in ['plus', 'minus'])
def change_tovar(call):
    index = int(get_user(call, 'index'))
    if call.data == 'plus':
        if index == len(list(collection.find({'category': get_tovar(call, 'category')})))-1:
            index = -1
        collection_user.update_one({'_id' : call.message.chat.id},
                                   {'$set': {'index' : index+1}})

    else:
        if index == 0:
            index = len(list(collection.find({'category': get_tovar(call, 'category')})))
        collection_user.update_one({'_id': call.message.chat.id},
                                   {'$set': {'index': index-1}})
    tovars(call)


@bot.callback_query_handler(func=lambda call: call.data == 'bucket')
def bucket_upd(call):
    try:
        markup = types.InlineKeyboardMarkup(row_width=4)

        but1 = types.InlineKeyboardButton('❌', callback_data='delete{}'.format(get_bucket(call)))
        but2 = types.InlineKeyboardButton('🔻', callback_data='ad-{}'.format(get_bucket(call)))
        but3 = types.InlineKeyboardButton('{}шт'.format(Counter(get_user(call, 'tovar_id')).get(get_bucket(call))), callback_data='None')
        but4 = types.InlineKeyboardButton('🔺', callback_data='adb{}'.format(get_bucket(call)))
        but5 = types.InlineKeyboardButton('⬅', callback_data='prev')
        but6 = types.InlineKeyboardButton('{}/{}'.format(int(get_user(call, 'index_buck'))+1, len(Counter(get_user(call, 'tovar_id')).keys())), callback_data='None')
        but7 = types.InlineKeyboardButton('➡', callback_data='next')
        but8 = types.InlineKeyboardButton('✅ Замовлення на {} грн. Оформити?'.format(sum([int(list(collection.find({'_id' : key}))[0]['price'][:-3])*value
                                                                                        for key, value
                                                                                        in Counter(get_user(call, 'tovar_id')).items()])),
                                          callback_data='confirm')

        but9 = types.InlineKeyboardButton('🔙  Продовжити покупки', callback_data='tovars')

        markup.row(but1, but2, but3, but4)
        markup.row(but5, but6, but7)
        markup.row(but8)
        markup.row(but9)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Ваш кошик:\n'
                                    '<a href="{1}">{0}</a>'.format(list(collection.find({'_id': get_bucket(call)}))[0]['name'],
                                                                   list(collection.find({'_id': get_bucket(call)}))[0]['image']),
                              parse_mode='HTML', reply_markup=markup
                              )

    except IndexError:
        bot.send_message(call.message.chat.id, 'В кошику немає товарів :(')
        categories(call)

@bot.callback_query_handler(func=lambda call: call.data in ['next', 'prev'])
def change_bucket(call):
    index = int(get_user(call, 'index_buck'))
    if call.data == 'next':
        if index == len(Counter(get_user(call, 'tovar_id')).keys())-1:
             index = -1
        collection_user.update_one({'_id' : call.message.chat.id},
                                   {'$set': {'index_buck' : index+1}})

    else:
        if index == 0:
            index = len(Counter(get_user(call, 'tovar_id')).keys())
        collection_user.update_one({'_id': call.message.chat.id},
                                   {'$set': {'index_buck': index-1}})

    bucket_upd(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete'))
def delete(call):
    collection_user.update_one({'_id': call.message.chat.id},
                               {'$pull': {'tovar_id' : {'$in' : [call.data[6:]]}}})
    collection_user.update_one({'_id': call.message.chat.id},
                               {'$set': {'index_buck': 0}})


    bucket_upd(call)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm')
def confirm(call):

    markup = types.InlineKeyboardMarkup(row_width=2)

    but1 = types.InlineKeyboardButton('Самовивіз', callback_data='Самовивіз')
    but2 = types.InlineKeyboardButton('Нова Пошта', callback_data='Нова Пошта')
    but3 = types.InlineKeyboardButton('❌ Скасувати', callback_data='cancel')
    but4 = types.InlineKeyboardButton('🔙 Повернутись', callback_data='bucket')

    markup.add(but1, but2, but3, but4)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='Виберіть спосіб доставки', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['Самовивіз', 'Нова Пошта'])
def record_delivery(call):
    if call.data == 'Самовивіз':
        collection_user.update_one({'_id' : call.message.chat.id},
                               {'$set' : {'delivery' : '1'}})

        if get_user(call, 'name') == None:
            get_name(call.message)
        else:
            summary(call.message)

    elif call.data == 'Нова Пошта':
        collection_user.update_one({'_id': call.message.chat.id},
                                   {'$set': {'delivery': '2'}})

        get_pochta_name(call.message)

def get_pochta_name(message):

    bot.send_message(message.chat.id, 'Введіть ваше місто')

    bot.register_next_step_handler(message, record_pochta_name)

def record_pochta_name(message):
    collection_user.update_one({'_id': message.chat.id},
                               {'$set': {'pochta_city' : message.text}})

    get_pochta_num(message)


def get_pochta_num(message):

    bot.send_message(message.chat.id, 'Введіть номер відділення')

    bot.register_next_step_handler(message, record_pochta_num)

def record_pochta_num(message):

    collection_user.update_one({'_id': message.chat.id},
                               {'$set': {'pochta_num' : message.text}})

    if get_user(message, 'name') == None:
        get_name(message)
    else:
        summary(message)


def get_name(message):

    bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)

    bot.send_message(message.chat.id, 'Введіть ваш ПІБ:')

    bot.register_next_step_handler(message, record_name)

def record_name(message):
    collection_user.update_one({'_id': message.chat.id},
                               {'$set': {'name': message.text.replace(' ', '%20')}})

    if get_user(message, 'number') != 0:
        summary(message)
    else:
        get_number(message)


def get_number(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    but1 = types.KeyboardButton('Відправити контакт', request_contact=True)

    markup.add(but1)

    bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)

    bot.send_message(message.chat.id,
                     'Введіть ваш номер телефону в форматі 380XXYYYYYYY або надішліть контакт',
                     reply_markup=markup)

    bot.register_next_step_handler(message, record_number)

def record_number(message):
    if type(message.contact) == type(None):  # Protection vs non-contact input
        if re.match('^380\d{9}$', message.text):  # Cheking if input is a phone number
            collection_user.update_one({'_id': message.chat.id},
                                       {'$set': {'number': message.text}})
            summary(message)
        else:
            bot.send_message(chat_id=message.chat.id, text='Номер в неправильному форматі!')
            get_number(message)

    else:
        if message.contact.phone_number.startswith('+'):
            collection_user.update_one({'_id': message.chat.id},
                                   {'$set': {'number': message.contact.phone_number[1:]}})
        else:
            collection_user.update_one({'_id': message.chat.id},
                                       {'$set': {'number': message.contact.phone_number}})
        summary(message)

def summary(message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('Змінити спосіб доставки', callback_data='confirm')
    but2 = types.InlineKeyboardButton('Змінити ім\'я', callback_data='get_name')
    but3 = types.InlineKeyboardButton('Змінити номер телефону', callback_data='get_number')
    but4 = types.InlineKeyboardButton('Підтвердити замовлення', callback_data='final')

    markup.add(but1, but2, but3, but4)

    bot.send_message(chat_id=message.chat.id, reply_markup=markup,
                          text="Дані замовлення:\n"
                               "Сума: _{0}грн_\n"
                               "Ім'я: _{1}_\n"
                               "Телефон: _{2}_\n"
                               "Спосіб доставки: _{3}_".format(
                              sum([int(list(collection.find({'_id' : key}))[0]['price'][:-3])*value for key, value in Counter(get_user(message, 'tovar_id')).items()]),
                              get_user(message, 'name').replace('%20', ' '), get_user(message, 'number'), ('Нова Пошта' if get_user(message, 'delivery') == '2' else 'Самовивіз')


                          ), parse_mode='MarkdownV2')

@bot.callback_query_handler(func=lambda call: call.data in ['get_name', 'get_number'])
def change(call):
    if call.data == 'get_number':
        get_number(call.message)
    else:
        get_name(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'final')
def send_request(call):

    clientnamefirst = get_user(call, 'name')
    clientphone =  get_user(call, 'number')
    delivery = get_user(call, 'delivery')
    pochta = ''
    if delivery == '2':
        pochta_num = get_user(call, 'pochta_num')
        pochta_city = get_user(call, 'pochta_city')
        pochta = f'&customuser_NomerotdeleniyaNP={pochta_num},%20{pochta_city}'

    url = '{0}{1}?login={2}' \
                      '&password={3}' \
                      '&workflowid=11' \
                      '&clientnamefirst={4}' \
                      '&clientphone={5}' \
                      '&deliveryid={6}' \
                      '&groupid=5'\
                      '&typesex=woman'\
                      '{7}'.format(domen, method, login, password_box,
                                                clientnamefirst,
                                                clientphone, delivery, pochta)



    for i, item in enumerate(Counter(get_user(call, 'tovar_id')).most_common()):
        url += '&productArray[{0}][id]={2}&productArray[{1}][count]={3}'.format(
            i, i, item[0], item[1]
        )

    r_update = requests.get(url=url)

    data = r_update.json()
    if data['result'] == 'ok':
        bot.send_message(call.message.chat.id, 'Замовлення успішно створене!')
        collection_user.update_one({'_id': call.message.chat.id},
                                   {'$set': {'index': 0,
                                             'category': 0,
                                             'index_buck': 0,
                                             'tovar_id' : [],
                                             'delivery' : None
                                             }})
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'orders')
def get_ord_number(call):
    if get_user(call, 'number') == 0:
        markup = types.ReplyKeyboardMarkup()

        but1 = types.KeyboardButton('Відправити контакт', request_contact=True)

        markup.add(but1)

        bot.send_message(call.message.chat.id, 'Введіть ваш номер телефону в форматі (380) або відправте контакт',
                         reply_markup=markup)
        bot.register_next_step_handler(call.message, ord_record_number)

    else:
        orders(call.message)

def ord_record_number(message):
    if type(message.contact) == type(None):  # Protection vs non-contact input
        if re.match('^380\d{9}$', message.text):  # Cheking if input is a phone number
            collection_user.update_one({'_id': message.chat.id},
                                       {'$set': {'number': message.text}})
            orders(message)
        else:
            bot.send_message(chat_id=message.chat.id, text='Номер в неправильному форматі!')
            get_ord_number(message)

    else:
        collection_user.update_one({'_id': message.chat.id},
                                   {'$set': {'number': message.contact.phone_number[1:]}})
        orders(message)

def orders(message):
    number = get_user(message, 'number')

    url = 'https://crm.yumilashes.com.ua/api/orders/get/'\
        f'?login=yuriy&password=5cd1e067f9a747c45e6d5a0896aac817&clientphone={number}&workflowid=11'

    data = requests.get(url).json()
    print(data)

    for i in range(len(data['orders'])):
        text = ''
        text += 'Замовлення №' + data['orders'][i]['orderid'] + '\n'
        text += 'Дата замовлення: ' + data['orders'][i]['cdate'] + '\n'
        text += 'Спосіб доставки: ' + data['orders'][i]['deliveriID'].replace('1', 'Самовивіз').replace('2', 'Нова почта').replace('0', 'Відсутні') + '\n'
        text += 'Ваші товари:' + '\n'


        for x in range(len(data['orders'][i]['products'])):
            text += data['orders'][i]['products'][x]['name'] + ' \\- ' + data['orders'][i]['products'][x]['count'][:-4] + ' шт.'+ '\n'

        text += '\n' + 'Сума: '  + data['orders'][i]['sum'] + '\n'
        text += 'Статус: ' + translate_order_status(data['orders'][i]['statusid'])

        bot.send_message(message.chat.id, text)

    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('🛍 Товари', callback_data='tovars')
    but2 = types.InlineKeyboardButton('🛒 Кошик', callback_data='bucket')
    but3 = types.InlineKeyboardButton('📒 Історія замовленнь', callback_data='orders')

    markup.add(but1, but2, but3)

    bot.send_message(message.chat.id, 'Оберіть потрібну дію:', reply_markup=markup)

def translate_order_status(statusid):

    if statusid == '68':
        return 'Нове замовлення'

    if statusid == '77':
        return 'В роботі'

    if statusid == '74':
        return 'Відмінити'

    if statusid == '114':
        return 'Відмінено'

    if statusid == '72':
        return 'Доставлений'

    if statusid == '73':
        return 'Виконано'

    if statusid == '136':
        return 'Повернення'

    if statusid == '137':
        return 'Успішне повернення'


bot.polling(none_stop=True)
