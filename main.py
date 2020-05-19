import telebot
from telebot import types
import json
import requests
import re
from config import Token, password
import pymongo
from collections import Counter

bot = telebot.TeleBot(Token)

cluster = pymongo.MongoClient(f'mongodb+srv://Kesha:{password}@shop-ocoyn.mongodb.net/test?retryWrites=true&w=majority')

db = cluster['Shop']
collection = db['Tovars']

collection_user = db['Users']


def get_user(call, key):
    return  list(collection_user.find({'_id' : call.message.chat.id}))[0][key]

def get_tovar(call, key, index='index'):

    tovar = list(collection.find({'category': get_user(call, 'category')}))[int(get_user(call, index))]

    return tovar[key]

def get_bucket(call):
    return sorted(Counter(get_user(call, 'tovar_id')).keys())[int(get_user(call, 'index_buck'))]

@bot.message_handler(commands=['start'])
def start(message):
    if not collection_user.find_one({'_id': message.chat.id}):
        collection_user.insert_one({'_id': message.chat.id,
                                    'name': message.from_user.first_name,
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
                                              'tovar_id' : [],}})

    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('Товари', callback_data='tovars')
    but2 = types.InlineKeyboardButton('Кошик', callback_data='bucket')
    but3 = types.InlineKeyboardButton('Замовлення', callback_data='orders')

    markup.add(but1, but2, but3)

    bot.send_message(message.chat.id, 'Вас вітає телеграм-магазин Yumi!\n'
                                      'Оберіть потрібну дію', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'tovars')
def categories(call):

    markup = types.InlineKeyboardMarkup(row_width=1)

    but1 = types.InlineKeyboardButton('Основні продукти', callback_data='14')
    but2 = types.InlineKeyboardButton('Аксесуари', callback_data='13')

    markup.add(but1, but2)

    bot.send_message(call.message.chat.id, 'Оберіть категорію товару', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['13', '14'])
def tovars(call):
    markup = types.InlineKeyboardMarkup()
    if  call.data in ['13', '14']:
        collection_user.update_one({'_id':call.message.chat.id}, {'$set': {'category': call.data}})

        markup.row(types.InlineKeyboardButton('{} грн'.format(get_tovar(call, 'price')[:-3]),
                                          callback_data='add{}'.format(get_tovar(call, '_id'))))


        but1 = types.InlineKeyboardButton('⬅', callback_data='minus')
        but2 = types.InlineKeyboardButton('{}/{}'.format(int(get_user(call, 'index'))+1,
                                                         len(list(collection.find({'category': get_tovar(call, 'category')})))),
                                          callback_data='Noooooooooo')
        but3 =  types.InlineKeyboardButton('➡', callback_data='plus')

        markup.row(but1, but2, but3)

        bot.send_message(call.message.chat.id,
                         '<a href="{1}">{0}</a>'.format(get_tovar(call, 'name'), get_tovar(call, 'image')), parse_mode='HTML', reply_markup=markup)

    else:
        if Counter(get_user(call, 'tovar_id')).get(get_tovar(call, '_id')):
            markup.row(types.InlineKeyboardButton('{} грн - {}шт'.format(get_tovar(call, 'price')[:-3],
                                                    Counter(get_user(call, 'tovar_id')).get(get_tovar(call, '_id'))),
                                                  callback_data='add{}'.format(get_tovar(call, '_id'))))

            markup.row(types.InlineKeyboardButton('Кошик', callback_data='bucket'))
        else:
            markup.row(types.InlineKeyboardButton('{} грн'.format(get_tovar(call, 'price')[:-3]),
                                                  callback_data='add{}'.format(get_tovar(call, '_id'))))

        but1 = types.InlineKeyboardButton('⬅', callback_data='minus')
        but2 = types.InlineKeyboardButton('{}/{}'.format(int(get_user(call, 'index')) + 1,
                                                         len(list(collection.find(
                                                             {'category': get_tovar(call, 'category')})))),
                                          callback_data='Noooooooooo')
        but3 = types.InlineKeyboardButton('➡', callback_data='plus')

        markup.row(but1, but2, but3)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='<a href="{1}">{0}</a>'.format(get_tovar(call, 'name'), get_tovar(call, 'image')), parse_mode='HTML'
                              )
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=markup)

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
        but8 = types.InlineKeyboardButton('✅ Ваш заказ на {}грн. Офромить?'.format(sum([int(list(collection.find({'_id' : key}))[0]['price'][:-3])*value
                                                                                        for key, value
                                                                                        in Counter(get_user(call, 'tovar_id')).items()])),
                                          callback_data='confirm')

        markup.row(but1, but2, but3, but4)
        markup.row(but5, but6, but7)
        markup.row(but8)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Ваш кошик:\n'
                                    '<a href="{1}">{0}</a>'.format(list(collection.find({'_id': get_bucket(call)}))[0]['name'],
                                                                   list(collection.find({'_id': get_bucket(call)}))[0]['image']),
                              parse_mode='HTML'
                              )
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=markup)
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



bot.polling(none_stop=True)
