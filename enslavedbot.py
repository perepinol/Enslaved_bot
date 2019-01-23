# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, ConversationHandler, MessageHandler, RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
import logging
import urllib2
import json
import datetime

WEATHER_KEY = ""
WEATHER_URL = 'http://api.openweathermap.org'
WEATHER, HOROSCOPE, ARTICLE, TIME, DONE = range(5)
global USER_DATA

def user_logger(update, message):
    user = update.message.from_user
    print(user.last_name + ", " + user.first_name + " (id:" + str(user.id) + ") " + message)



def get_weather(location_id):
    weather_json = json.loads(urllib2.urlopen(WEATHER_URL + "/data/2.5/forecast?id=" + str(location_id) + "&APPID=" + WEATHER_KEY + "&units=metric").read())
        
    # Filter today's data (result is a list of dictionaries
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    today_data = []
    for entry in weather_json['list']:
        if (entry['dt_txt'].split()[0] == today):
            today_data.append(entry)
        
    # Calculate minimum and maximum temperatures, wind, rain and snow
    temp_min = (today_data[0]['main']['temp'], today_data[0]['dt_txt'].split()[1])
    temp_max = (today_data[0]['main']['temp'], today_data[0]['dt_txt'].split()[1])
    wind_max = (today_data[0]['wind']['speed'], today_data[0]['dt_txt'].split()[1])
    rain = 0
    snow = 0
    for item in today_data:
        # Mins/Maxs
        if (temp_min[0] > item['main']['temp']):
            temp_min = (item['main']['temp'], item['dt_txt'].split()[1])
        if (temp_max[0] < item['main']['temp']):
            temp_max = (item['main']['temp'], item['dt_txt'].split()[1])
        if (wind_max[0] < item['wind']['speed']):
            wind_max = (item['wind']['speed'], item['dt_txt'].split()[1])
           
        # Rain and snow accumulation
        if ('rain' in item):
            if ('3h' in item['rain']):
                rain += item['rain']['3h']
            elif ('1h' in item['rain']):
                rain += item['rain']['1h']
            
        if ('snow' in item):
            if ('3h' in item['snow']):
                rain += item['snow']['3h']
            elif ('1h' in item['snow']):
                rain += item['snow']['1h']
                    
        return ("**Weather in " + weather_json['city']['name'] + ", " + weather_json['city']['country'] + ":**\n" + 
               "Near forecast: " + today_data[0]['weather'][0]['description'] + "\n" +
               "Min temperature: " + str(temp_min[0]) + " C at ".encode('utf-8') + ":".join(temp_min[1].split(":")[:-1]) + "\n" +
               "Max temperature: " + str(temp_max[0]) + " C at ".encode('utf-8') + ":".join(temp_max[1].split(":")[:-1]) + "\n" + 
               "Max wind speed: " + str(wind_max[0]) + " m/s at " + ":".join(wind_max[1].split(":")[:-1]) + "\n" +
               "Expected rain: " + str(rain) + " mm\n" + 
               "Expected snow: " + str(snow) + " mm\n")



def get_horoscope(sign):
    horoscope_json = json.loads(urllib2.urlopen("http://horoscope-api.herokuapp.com/horoscope/today/" + sign).read())
    return horoscope_json['sunsign'] + "\n" + horoscope_json['horoscope']



def get_article():
    url = urllib2.urlopen("https://en.wikipedia.org/wiki/Special:RandomInCategory/Featured_articles")
    return url.geturl()



# User-prompted commands
def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Here is what I can do for you, Master:\n" + 
                                                            "- /help: See this guide.\n" +
                                                            "- /search <query>: look for something in google.\n" +
                                                            "- /forecast: See the forecast for today (you need to set up a daily update).\n" +
                                                            "- /sign: See your horoscope for today (you need to set up a daily update).\n" +
                                                            "- /dailyinfostart: Set up a daily information regarding the forecast in your location and your horoscope.\n" +
                                                            "- /dailyinfostop: Stop the daily information service.\n")



def start(bot, update):
    user_logger(update, "has started me")
    bot.send_message(chat_id=update.message.chat_id, text="I am started now, Master. Do you need /help?")



def search(bot, update, args):
    user_logger(update, "inputs search")
    bot.send_message(chat_id=update.message.chat_id, text=("Master " + update.message.from_user.first_name + ", I don't know how to search yet"))



def forecast(bot, update):
    user_logger(update, "requests forecast info")
    if (str(update.message.from_user.id) not in USER_DATA or USER_DATA[str(update.message.from_user.id)]['weather'] is None):
        bot.send_message(chat_id=update.message.chat_id, text="I need info on weather on the daily update to do this, Master")
        return
    
    bot.send_message(chat_id=update.message.chat_id, text=get_weather(USER_DATA[str(update.message.from_user.id)]['weather']), parse_mode="Markdown")



def horoscope(bot, update):
    user_logger(update, "requests horoscope info")
    if (str(update.message.from_user.id) not in USER_DATA or USER_DATA[str(update.message.from_user.id)]['horoscope'] is None):
        bot.send_message(chat_id=update.message.chat_id, text="I need your sign on the daily update to do this, Master")
        return
    
    bot.send_message(chat_id=update.message.chat_id, text=get_horoscope(USER_DATA[str(update.message.from_user.id)]['horoscope']))



def article(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=get_article())



def stop_daily_info(bot, update, job_queue):
    global USER_DATA
    user_logger(update, "has stopped daily info")
    jobs = job_queue.jobs()
    for job in jobs:
        if (job.name == str(update.message.from_user.id)):
            job.schedule_removal()
            USER_DATA.pop(str(update.message.from_user.id))
            bot.send_message(chat_id=update.message.chat_id, text="I will stop sending daily updates, Master " + update.message.from_user.first_name)
            return



def error(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I did not understand, Master. Do you need /help?")

# Conversation
def start_daily_info(bot, update, user_data):
    user_logger(update, "has started daily info")
    bot.send_message(chat_id=update.message.chat_id, text="I humbly request to know what I will have to say, Master " + update.message.from_user.first_name + 
                                                            ". If you want to stop at any moment, you can /cancel")
    bot.send_message(chat_id=update.message.chat_id, text="In which city do you live? (I need the full name). If you do not want me to tell you the weather, please tell me to /skip")
    return WEATHER



def skip_weather(bot, update, user_data):
    user_data['weather'] = (None, None, None)
    bot.send_message(chat_id=update.message.chat_id, text="Of course. Let's move on, Master " + update.message.from_user.first_name + "...")
    bot.send_message(chat_id=update.message.chat_id, text="Now, could you please give me your birthsign? Or tell me to /skip")
    return HOROSCOPE



def weather_handler(bot, update, user_data):
    city = update.message.text.split(",")[0]
    country = None
    code = None
    
    with open("city.list.json", "r") as fh:
        cities = json.load(fh)
    for city_json in cities:
        if (city_json['name'].lower() == city.lower()):
            city = city_json['name']
            country = city_json['country']
            code = city_json['id']
            break
    
    if (country is not None):
        bot.send_message(chat_id=update.message.chat_id, text="Your city is " + city + ", " + country + ", Master " + update.message.from_user.first_name)
        user_data['weather'] = (city, country, code)
        bot.send_message(chat_id=update.message.chat_id, text="Now, could you give me your birthsign? Or tell me to /skip")
        return HOROSCOPE
    bot.send_message(chat_id=update.message.chat_id, text="I cannot find this city, Master " + update.message.from_user.first_name + ". Are you sure it is correctly written?")
    return



def skip_horoscope(bot, update, user_data):
    user_data['horoscope'] = None
    bot.send_message(chat_id=update.message.chat_id, text="Of course. Let's move on, Master " + update.message.from_user.first_name + "...")
    bot.send_message(chat_id=update.message.chat_id, text="Do you want me to send you random Wikipedia articles, Master? Say yes or no")
    return ARTICLE



def horoscope_handler(bot, update, user_data):
    sign = None
    sunsigns = []
    with open("sunsigns.txt", "r") as fh:
        sunsigns = [line.strip() for line in fh]
    
    for line in sunsigns:
        if (update.message.text.lower() == line.lower()):
            sign = line
            break
    
    if (sign is not None):
        bot.send_message(chat_id=update.message.chat_id, text="So you are " + sign + ", Master " + update.message.from_user.first_name)
        user_data['horoscope'] = sign
        bot.send_message(chat_id=update.message.chat_id, text="Do you want me to send you random Wikipedia articles, Master? Say yes or no")
        return ARTICLE
    
    message = "I don't know this sign, Master " + update.message.from_user.first_name + ". These are the ones I know:\n"
    for sign in sunsigns:
        message += "- " + sign + "\n"
    bot.send_message(chat_id=update.message.chat_id, text=message)
    return



def article_handler(bot, update, user_data):
    user_data['article'] = (update.message.text.lower() == "yes")
    bot.send_message(chat_id=update.message.chat_id, text="Now, could you give me your the time to tell you this info, Master?")
    return TIME



def schedule_handler(bot, update, user_data):
    time_arr = update.message.text.split(":")
    time_arr = map(int, time_arr)
    if (len(time_arr) == 1):
        time_arr.append(0)
    if (time_arr[0] < 0 or time_arr[0] > 23 or time_arr[1] < 0 or time_arr[1] > 59):
        bot.send_message(chat_id=update.message.chat_id, text="This is not a valid time, Master " + update.message.from_user.first_name + ". Please try again")
        return
    user_data['time'] = (time_arr[0], time_arr[1])
    
    summary = "This is the result, Master " + update.message.from_user.first_name + ". If everything is as you want, tell me it is /done\n"
    
    if (user_data['weather'] != (None, None, None)):
        summary += "Weather for " + user_data['weather'][0] + "," + user_data['weather'][1] + "\n"
    
    if (user_data['horoscope'] is not None):
        summary += "Horoscope for " + user_data['horoscope'] + "\n"
    
    if (user_data['article']):
        summary += "With random Wikipedia article\n"
    
    summary += "Time of day to update: " + str(user_data['time'][0]).zfill(2) + ":" + str(user_data['time'][1]).zfill(2)
    
    bot.send_message(chat_id=update.message.chat_id, text=summary)
    return DONE



def set_daily_info(bot, update, user_data, job_queue):
    global USER_DATA
    print(user_data)
    time = datetime.time(user_data['time'][0], user_data['time'][1])
    job_queue.run_daily(daily_info, time, context={'uid': update.message.from_user.id, 'weather': user_data['weather'][2], 'horoscope': user_data['horoscope'], 'article': user_data['article']}, name=update.message.from_user.id)
    user_data['weather'] = user_data['weather'][2]
    USER_DATA[str(update.message.from_user.id)] = user_data
    bot.send_message(chat_id=update.message.chat_id, text="Master " + update.message.from_user.first_name + ", your daily update is set up")
    return ConversationHandler.END



def cancel_conversation(bot, update, user_data):
    bot.send_message(chat_id=update.message.chat_id, text="I'll stop, Master " + update.message.from_user.first_name)
    user_logger(update, "has cancelled daily info setup")
    return ConversationHandler.END



def error_conversation(bot, update):
    print("Error, reasking", update.message.text)
    bot.send_message(chat_id=update.message.chat_id, text="Master " + update.message.from_user.first_name + ", I didn't understand your message." + 
                                                                                                            " If you would repeat it again, or tell me to /cancel...")
    return
    

# Inline
def inline_search(bot, update):
    query = update.inline_query.query
    user = update.message.from_user
    print(user.last_name + ", " + user.first_name + " (id:" + str(user.id) + ") is querying inline: " + query)
    if not query:
        return
    
    # Search in google
    results = list()
    results.append(InlineQueryResultArticle(
        id=query,
        title=query.upper(),
        input_message_content=InputTextMessageContent(query.upper())
    ))
    bot.answer_inline_query(update.inline_query.id, results)
    
    
    
# Periodic
def daily_info(bot, job):
    bot.send_message(chat_id=job.context['uid'], text="Today is " + datetime.datetime.today().strftime("%d-%m-%Y"))
    # Weather
    if (job.context['weather'] is not None):
        bot.send_message(chat_id=job.context['uid'], text=get_weather(job.context['weather']), parse_mode="Markdown")
    
    # Horoscope
    if (job.context['horoscope'] is not None):
        bot.send_message(chat_id=job.context['uid'], text=get_horoscope(job.context['horoscope']))
    
    # Article
    if (job.context['article']):
        bot.send_message(chat_id=job.context['uid'], text=get_article())



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    get_article()
    with open("params.conf", "r") as fh:
        WEATHER_KEY = fh.readline().strip()
        updater = Updater(fh.readline().strip())
    dispatcher = updater.dispatcher
    jqueue = updater.job_queue
    
    global USER_DATA

    try:
        with open("user_data.txt", "r") as fh:
            USER_DATA = json.load(fh)
    except:
        USER_DATA = {}

    for entry in USER_DATA:
        time = datetime.time(USER_DATA[entry]['time'][0], USER_DATA[entry]['time'][1])
        jqueue.run_daily(daily_info, time, context={'uid': entry, 'weather': USER_DATA[entry]['weather'], 'horoscope': USER_DATA[entry]['horoscope']}, name=entry)
        print("Created daily update for " + str(entry))

    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('forecast', forecast))
    dispatcher.add_handler(CommandHandler('sign', horoscope))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('search', search, pass_args=True))
    dispatcher.add_handler(CommandHandler('article', article))
    dispatcher.add_handler(CommandHandler('dailyinfostop', stop_daily_info, pass_job_queue=True))
    dispatcher.add_handler(ConversationHandler(
                                                [CommandHandler('dailyinfostart', start_daily_info, pass_user_data=True)],
                                                {WEATHER: [CommandHandler('skip', skip_weather, pass_user_data=True), RegexHandler('^[\w\s]+$', weather_handler, pass_user_data=True)],
                                                 HOROSCOPE: [CommandHandler('skip', skip_horoscope, pass_user_data=True), RegexHandler('^\w+$', horoscope_handler, pass_user_data=True)],
                                                 ARTICLE: [RegexHandler('^[Yy]es$|^[Nn]o$', article_handler, pass_user_data=True)],
                                                 TIME: [RegexHandler('^\d{1,2}$|^\d{1,2}:\d{1,2}$', schedule_handler, pass_user_data=True)],
                                                 DONE: [CommandHandler('done', set_daily_info, pass_user_data=True, pass_job_queue=True)]
                                                },
                                                [CommandHandler('cancel', cancel_conversation, pass_user_data=True), RegexHandler('.*', error_conversation)]
                                              ))
    dispatcher.add_handler(InlineQueryHandler(inline_search))
    dispatcher.add_handler(RegexHandler('.*', error))

    updater.start_polling() 
    updater.idle()
    with open("user_data.txt", "w") as fh:
        json.dump(USER_DATA, fh)
