#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import pickle
import datetime

# TODO:
#  + timestamp for expenses
#  + categories
#  + stats per category, month user (sql-like syntax?)
#  + allow for multiple users as payers
#  ? check for user expenses < 0

class Expense:
	def __init__(self, user_id, amount):
		self.amount = amount
		self.datetime = datetime.datetime.now()
		self.user_id = user_id

	def __repr__(self):
		return '<Expense: {}: {} ({})>'.format(self.user_id, self.amount, self.datetime)

def update_expenses(bot, update, args):
	global expenses, users
	logger.info('Update expenses command, args={}'.format(args))
	chat_id = update.message.chat_id
	user = update.message.from_user

	if len(args) < 1:
		bot.sendMessage(chat_id=chat_id, text='/spent <amount> [<amount2>] [...]')
		return

	try:
		amount = sum([float(a) for a in args])
	except ValueError:
		error_handler(bot, update, 'ValueError')
		return

	if user.id not in users:
		bot.sendMessage(chat_id=chat_id, text='Hello {}, initialized your expenses with 0.'.format(user.first_name))
		users[user.id] = user
		expenses[user.id] = []

	expenses[user.id].append(Expense(user.id, amount))

	if amount > 0:
		text = 'Added {:.2f} to your expenses.'
	else:
		text = 'Subtracted {:.2f} from your expenses.'
	bot.sendMessage(chat_id=chat_id, text=text.format(amount))

def stats(bot, update):
	global expenses, users
	logger.info('Stats command')

	message = ''
	overall_sum = 0
	for user_id, user_expenses in expenses.items():
		user_sum = sum([e.amount for e in user_expenses])
		overall_sum += user_sum
		message += '{}: {:.2f}\n'.format(users[user_id].first_name, user_sum)

	message = 'Summed expenses: {:.2f}\n'.format(overall_sum) + message
	bot.sendMessage(chat_id=update.message.chat_id, text=message)

def error_handler(bot, update, error):
	bot.sendMessage('Syntax error or sth')
	logger.warn('Update "{}" caused error "{}"'.format(update, error))

def dump_to_file(expenses, users):
	pickle.dump(expenses, open('expenses.p', 'wb'))
	pickle.dump(users, open('users.p', 'wb'))
	logger.info('Dumped expenses and users to file.')

def main():
	global expenses, users
	try:
		expenses = pickle.load(open('expenses.p', 'rb')) # user_id:expenses
	except FileNotFoundError:
		logger.warn('Expenses file not found! Starting with empty one.')
		expenses = {}

	try:
		users = pickle.load(open('users.p', 'rb')) # user_id:user
	except FileNotFoundError:
		logger.warn('Users file not found! Starting with empty one.')
		users = {}

	updater = Updater(token=open('token').read())

	dp = updater.dispatcher
	dp.add_handler(CommandHandler('spent', update_expenses, pass_args=True))
	dp.add_handler(CommandHandler('stats', stats))
	dp.add_error_handler(error_handler)

	updater.start_polling()
	logger.info('Updater started polling...')
	updater.idle()

	dump_to_file(expenses, users)

if __name__ == '__main__':
	main()
