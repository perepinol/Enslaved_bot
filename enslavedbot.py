# -*- coding: utf-8 -*-
"""Needs: python-telegram-bot==11.1.0 (pip install python-telegram-bot)"""
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, ConversationHandler, MessageHandler, RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
import logging
import urllib2
import json
import datetime
import pytz

WEATHER_KEY = ""
WEATHER_URL = 'http://api.openweathermap.org'
ADMIN_ID = 0
WEATHER, CITY, TIMEZONE, HOROSCOPE, ARTICLE, TIME, DONE = range(7)
global USER_DATA


def log(message):
    m = logging.info(message)
    


def user_logger(update, message):
    """Log the given action and the user doing it (contained in the update)."""
    user = update.message.from_user
    line = ""
    if (user.last_name is not None):
        line += user.last_name + ", "
    if (user.first_name is not None):
        line += user.first_name + " "
    log(line + "(id:" + str(user.id) + ") " + message)



def send(bot, chat_id, text, parse_mode=None):
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except TelegramResponseException:
        bot.send_message(chat_id=ADMIN_ID, message="Error: " + e.strerror)



def get_weather(location_id):
    """Given a location id, get the weather info and parse it."""
    weather_json = json.loads(urllib2.urlopen(WEATHER_URL + "/data/2.5/forecast?id=" + str(location_id) + "&APPID=" + WEATHER_KEY + "&units=metric").read())
    
    # Filter today's data (result is a list of dictionaries)
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
        
    # Build finished message
    return ("**Weather in " + weather_json['city']['name'] + ", " + weather_json['city']['country'] + ":**\n" + 
           "Near forecast: " + today_data[0]['weather'][0]['description'] + "\n" +
           "Min temperature: " + str(temp_min[0]) + " C at ".encode('utf-8') + ":".join(temp_min[1].split(":")[:-1]) + "\n" +
           "Max temperature: " + str(temp_max[0]) + " C at ".encode('utf-8') + ":".join(temp_max[1].split(":")[:-1]) + "\n" + 
           "Max wind speed: " + str(wind_max[0]) + " m/s at " + ":".join(wind_max[1].split(":")[:-1]) + "\n" +
           "Expected rain: " + str(rain) + " mm\n" + 
           "Expected snow: " + str(snow) + " mm\n")



def get_horoscope(sign):
    """Given a sign name, get its horoscope for today and parse it."""
    horoscope_json = json.loads(urllib2.urlopen("http://horoscope-api.herokuapp.com/horoscope/today/" + sign).read())
    return horoscope_json['sunsign'] + "\n" + horoscope_json['horoscope']



def get_article():
    """Get a random featured article from Wikipedia."""
    url = urllib2.urlopen("https://en.wikipedia.org/wiki/Special:RandomInCategory/Featured_articles")
    return url.geturl()



def get_article_list(user):
    """Get the saved article list for a user"""
    # Check if user has any article
    if (user not in USER_DATA or 'user_articles' not in USER_DATA[user] or USER_DATA[user]['user_articles'] == []):
        return "You have no articles in the list, Master"
    
    # Get articles if user has them
    articles = USER_DATA[user]['user_articles']
    text = "This is your list of articles:"
    for i in range(len(articles)):
        text += "\n" + str(i) + ". " + articles[i]
    return text



# User-prompted commands
def thank_response(bot, update):
    """Answer to a 'thank you'."""
    send(bot, chat_id=update.message.chat_id, text="My pleasure, Master " + update.message.from_user.first_name)
    
    
    
def greeting(bot, update):
    """Answers to a greeting."""
    send(bot, chat_id=update.message.chat_id, text="Greetings, Master " + update.message.from_user.first_name + ".")



def farewell(bot, update):
    """Answers to a farewell."""
    send(bot, chat_id=update.message.chat_id, text="Farewell, Master " + update.message.from_user.first_name + ".")



def help(bot, update):
    """Display a help message."""
    send(bot, chat_id=update.message.chat_id, text="Here is what I can do for you, Master:\n" + 
                                                            "- /help: See this guide.\n" +
                                                            "- /search <query>: look for something in google.\n" +
                                                            "- /forecast: See the forecast for today (you need to set up a daily update).\n" +
                                                            "- /sign: See your horoscope for today (you need to set up a daily update).\n" +
                                                            "- /article: Get a random featured Wikipedia article.\n" +
                                                            "- /myarticles: See Wikipedia articles you have saved for later.\n" +
                                                            "- /addarticle: Add a Wikipedia article to the 'read later' list.\n" +
                                                            "- /removearticle: Remove an article from the 'read later' list.\n" +
                                                            "- /dailyinfostart: Set up a daily information regarding the forecast in your location and your horoscope.\n" +
                                                            "- /dailyinfostop: Stop the daily information service and erase your data.\n")



def start(bot, update):
    """Start the bot."""
    user_logger(update, "has started me")
    send(bot, chat_id=update.message.chat_id, text="I am started now, Master. If you need /help, you can ask me?")



def search(bot, update, args):
    """Search for a query in google."""
    user_logger(update, "inputs search")
    send(bot, chat_id=update.message.chat_id, text=("Master " + update.message.from_user.first_name + ", I don't know how to search yet"))



def forecast(bot, update):
    """
    Send forecast information for the user.
    To do this, user has to have used /dailyinfostart and set up their location.
    """
    user_logger(update, "requests forecast info")
    if (str(update.message.from_user.id) not in USER_DATA or USER_DATA[str(update.message.from_user.id)]['weather'] is None):
        send(bot, chat_id=update.message.chat_id, text="I need info on weather on the daily update to do this, Master")
        return
    
    send(bot, chat_id=update.message.chat_id, text=get_weather(USER_DATA[str(update.message.from_user.id)]['weather']), parse_mode="Markdown")



def horoscope(bot, update):
    """
    Send horoscope for the user.
    To do this, user has to have used /dailyinfostart and set up their sign.
    """
    user_logger(update, "requests horoscope info")
    if (str(update.message.from_user.id) not in USER_DATA or USER_DATA[str(update.message.from_user.id)]['horoscope'] is None):
        send(bot, chat_id=update.message.chat_id, text="I need your sign on the daily update to do this, Master")
        return
    
    send(bot, chat_id=update.message.chat_id, text=get_horoscope(USER_DATA[str(update.message.from_user.id)]['horoscope']))



def article(bot, update):
    """Send a random featured Wikipedia article."""
    user_logger(update, "requests random article")
    send(bot, chat_id=update.message.chat_id, text=get_article())



def stop_daily_info(bot, update, job_queue):
    """Stop sending daily info to the user and delete their data."""
    global USER_DATA
    user_logger(update, "has stopped daily info")
    send(bot, chat_id=update.message.chat_id, text="I will stop sending daily updates, Master " + update.message.from_user.first_name)
    jobs = job_queue.jobs()
    for job in jobs:
        if (job.name == str(update.message.from_user.id)):
            job.schedule_removal()
            if (str(update.message.from_user.id) in USER_DATA and 'user_articles' in USER_DATA[str(update.message.from_user.id)]):
                USER_DATA[str(update.message.from_user.id)] = {'user_articles': USER_DATA[str(update.message.from_user.id)]['user_articles']}
            else:
                USER_DATA.pop(str(update.message.from_user.id))
            return



def user_articles(bot, update):
    """Send the list of saved articles for this user."""
    user_logger(update, "requests list of articles")
    text = get_article_list(str(update.message.from_user.id))
    send(bot, chat_id=update.message.chat_id, text=text)



def error(bot, update):
    """Capture all non-command messages."""
    send(bot, chat_id=update.message.chat_id, text="I did not understand, Master. Do you need /help?")



# Conversation
def start_daily_info(bot, update, user_data):
    """Start the daily_info setup."""
    user_logger(update, "has started daily info")
    send(bot, chat_id=update.message.chat_id, text="I humbly request to know what I will have to say, Master " + update.message.from_user.first_name + 
                                                            ". If you want to stop at any moment, you can /cancel")
    send(bot, chat_id=update.message.chat_id, text="In which city do you live? (I need the full name). If you do not want me to tell you the weather, please tell me to /skip")
    return WEATHER



def skip_weather(bot, update, user_data):
    """Skip weather setup, go to horoscope."""
    user_data['weather'] = (None, None, None)
    send(bot, chat_id=update.message.chat_id, text="Of course, Master " + update.message.from_user.first_name + ". Then I need to have your time zone (from -12 to +14")
    
    return TIMEZONE



def weather_handler(bot, update, user_data):
    """
    Set up the weather.
    This is done by searching the given location in the weather database and, if found, keeping its name and id.
    """
    city = update.message.text.split(",")[0]
    country = None
    code = None
    
    # Get city and country code
    with open("city.list.json", "r") as fh:
        cities = json.load(fh)
        if (city.lower() not in cities):  # If city does not exist, repeat weather
            send(bot, chat_id=update.message.chat_id, text="I cannot find this city, Master " + update.message.from_user.first_name +
                                                            ". I may not have it available. Could you choose a different one?")
            return
        
        # Format city name to uniformize
        city = list(city.lower())
        city[0] = city[0].upper()
        city = "".join(city)
        
        city_list = cities[city.lower()]
        if (len(city_list) > 1):  # If some city has same name, allow choice
            send(bot, chat_id=update.message.chat_id, text="There are various cities with this name. Could you choose which one, Master?")
            user_data['weather'] = (city, city_list)
            message = "Choose the number of the city you want, or /cancel to exit:\n"
            for i in range(len(city_list)):
                message += "\t" + str(i) + ". " + city + ", " + city_list[i]['country'] + " (" + str(city_list[i]['coord']['lat']) + "N, " + str(city_list[i]['coord']['lon']) + "E)\n"
    
            send(bot, chat_id=update.message.chat_id, text=message)
            return CITY
        
        # If city exists, save
        country = city_list[0]['country']
        code = city_list[0]['id']
        
        send(bot, chat_id=update.message.chat_id, text="Your city is " + city + ", " + country + ", Master " + update.message.from_user.first_name)
        user_data['weather'] = (city, country, code)
        
        # Go to horoscope
        send(bot, chat_id=update.message.chat_id, text="Now, could you give me your birthsign? Or tell me to /skip")
        return HOROSCOPE



def city_handler(bot, update, user_data):
    """
    Choose a city from various same-named ones list.
    """
    city, city_list = user_data['weather']
    num = int(update.message.text)
    if (num >= len(city_list)):
        send(bot, chat_id=update.message.chat_id, text="That is not one of the numbers, Master. Could you write another one?")
        return
    
    country = city_list[num]['country']
    code = city_list[num]['id']
    
    send(bot, chat_id=update.message.chat_id, text="Your city is " + city + ", " + country + ", Master " + update.message.from_user.first_name)
    user_data['weather'] = (city, country, code)
    send(bot, chat_id=update.message.chat_id, text="Now, could you give me your birthsign? Or tell me to /skip")
    return HOROSCOPE



def timezone_handler(bot, update, user_data):
    """Choose a timezone if a location has not been chosen."""
    offset = int(update.message.text)
    if (offset < -12 or offset > 14):
        send(bot, chat_id=update.message.chat_id, text="Master, this is not an existing timezone. Could you write it again?")
        return TIMEZONE
    
    user_data['timezone'] = offset
    send(bot, chat_id=update.message.chat_id, text="Now, could you please give me your birthsign? Or tell me to /skip")
    return HOROSCOPE



def skip_horoscope(bot, update, user_data):
    """Skip horoscope setup, go to random article setup."""
    user_data['horoscope'] = None
    send(bot, chat_id=update.message.chat_id, text="Of course. Let's move on, Master " + update.message.from_user.first_name + "...")
    send(bot, chat_id=update.message.chat_id, text="Do you want me to send you random Wikipedia articles, Master? Say yes or no")
    return ARTICLE



def horoscope_handler(bot, update, user_data):
    """
    Set up the horoscope.
    Save the sunsign if it is a valid one, and display all signs if it is not.
    """
    sign = None
    sunsigns = []
    
    # Check the sunsign given
    with open("sunsigns.txt", "r") as fh:
        sunsigns = [line.strip() for line in fh]
    
    for line in sunsigns:
        if (update.message.text.lower() == line.lower()):
            sign = line
            break
    
    # If the sunsign is valid, save information and go to Wikipedia article
    if (sign is not None):
        send(bot, chat_id=update.message.chat_id, text="So you are " + sign + ", Master " + update.message.from_user.first_name)
        user_data['horoscope'] = sign
        send(bot, chat_id=update.message.chat_id, text="Do you want me to send you random Wikipedia articles, Master? Say yes or no")
        return ARTICLE
    
    # If the sign is not valid, display signs and repeat horoscope
    message = "I don't know this sign, Master " + update.message.from_user.first_name + ". These are the ones I know:\n"
    for sign in sunsigns:
        message += "- " + sign + "\n"
    send(bot, chat_id=update.message.chat_id, text=message)
    return



def article_handler(bot, update, user_data):
    """Save if the user wants a random Wikipedia article or not."""
    user_data['article'] = (update.message.text.lower() == "yes")
    send(bot, chat_id=update.message.chat_id, text="Now, could you give me the time to tell you this info, Master?")
    return TIME



def schedule_handler(bot, update, user_data):
    """Set the time of day at which the user wants to be updated."""
    # Get time as int array from a [hh:mm, h:mm, hh:m, h:m, h] format
    time_arr = update.message.text.split(":")
    time_arr = map(int, time_arr)
    if (len(time_arr) == 1): # If format is 'h', add minute value to the array
        time_arr.append(0)
    
    # If time is not valid, repeat scheduler
    if (time_arr[0] < 0 or time_arr[0] > 23 or time_arr[1] < 0 or time_arr[1] > 59):
        send(bot, chat_id=update.message.chat_id, text="This is not a valid time, Master " + update.message.from_user.first_name + ". Please try again")
        return
    
    # Get time offset
    if ('timezone' in user_data):
        offset = -timezone
    else:
        timezone = pytz.timezone(pytz.country_timezones(user_data['weather'][1])[0])
        utc_time = pytz.utc.localize(datetime.datetime.utcnow())
        rel_time = utc_time.astimezone(timezone).replace(tzinfo=None)
        
        offset = int((utc_time.replace(tzinfo=None) - rel_time).total_seconds()) / 3600
    
    # Save time if correct (in UTC)
    hour = (time_arr[0] + offset) % 24
    user_data['time'] = (hour, time_arr[1])
    
    # Display summary of configuration
    summary = "This is the result, Master " + update.message.from_user.first_name + ". If everything is as you want, tell me it is /done\n"
    
    if (user_data['weather'][0] is not None):
        summary += "Weather for " + user_data['weather'][0] + "," + user_data['weather'][1] + "\n"
    
    if (user_data['horoscope'] is not None):
        summary += "Horoscope for " + user_data['horoscope'] + "\n"
    
    if (user_data['article']):
        summary += "With random Wikipedia article\n"
    
    summary += "Time of day to update: %s:%s (%s:%s UTC)" % (str(time_arr[0]).zfill(2), str(time_arr[1]).zfill(2), str(user_data['time'][0]).zfill(2), str(user_data['time'][1]).zfill(2))
    
    send(bot, chat_id=update.message.chat_id, text=summary)
    return DONE



def set_daily_info(bot, update, user_data, job_queue):
    """Save the conversation result and set the job up."""
    global USER_DATA
    log(user_data)
    
    # Get the time in datetime format for job queue
    time = datetime.time(user_data['time'][0], user_data['time'][1])
    
    # Add job
    job_queue.run_daily(daily_info, time, context={'uid': update.message.from_user.id, 'weather': user_data['weather'][2], 'horoscope': user_data['horoscope'],
                                                   'article': user_data['article']}, name=update.message.from_user.id)
    
    # Save information into USER_DATA
    user_data['weather'] = user_data['weather'][2]  # Only the city ID is needed
    
    # Ensure the user's article list is not destroyed if it exists
    if (str(update.message.from_user.id) in USER_DATA and 'user_articles' in USER_DATA[str(update.message.from_user.id)]):
        user_data['user_articles'] = USER_DATA[str(update.message.from_user.id)]['user_articles']
    
    USER_DATA[str(update.message.from_user.id)] = user_data  # Save
    
    send(bot, chat_id=update.message.chat_id, text="Master " + update.message.from_user.first_name + ", your daily update is set up")
    return ConversationHandler.END



def cancel_conversation(bot, update):
    """Cancel an ongoing conversation."""
    send(bot, chat_id=update.message.chat_id, text="I'll stop, Master " + update.message.from_user.first_name)
    user_logger(update, "has cancelled the conversation")
    return ConversationHandler.END



def error_conversation(bot, update):
    """Send an error message and repeat the current step."""
    log("Error, reasking", update.message.text)
    send(bot, chat_id=update.message.chat_id, text="Master " + update.message.from_user.first_name + ", I didn't understand your message." + 
                                                   " If you would repeat it again, or tell me to /cancel...")
    return
    

def start_add_article(bot, update):
    """Start the add article conversation."""
    user_logger(update, "starts add article")
    send(bot, chat_id=update.message.chat_id, text="Which is the title of the article you wish to add? Or /cancel if you want") 
    return ARTICLE



def add_article(bot, update):
    """Add an article to the user's list."""
    # If the url exists, get it. If not, repeat step
    try:
        url = urllib2.urlopen("https://en.wikipedia.org/wiki/" + update.message.text)
    except:
        send(bot, chat_id=update.message.chat_id, text="This article does not exist, Master. Could you write it again, or /cancel?")
        return
    
    global USER_DATA
    
    # Add url into article list
    if (str(update.message.from_user.id) in USER_DATA):  # If the user has data already, it has to be updated
        user_data = USER_DATA[str(update.message.from_user.id)]
        if ('user_articles' in user_data):
            articles = user_data['user_articles']
        else:
            articles = []
        articles.append(url.geturl())
        user_data['user_articles'] = articles
    
    else:  # If the user has no data, it can be created from scratch
        user_data = {'user_articles': [url.geturl()]}
    
    USER_DATA[str(update.message.from_user.id)] = user_data  # Save data
    
    send(bot, chat_id=update.message.chat_id, text="The article has been added, Master")
    return ConversationHandler.END



def start_remove_article(bot, update):
    """Start remove article conversation."""
    user_logger(update, "starts remove article")
    
    # Display article list
    article_list = get_article_list(str(update.message.from_user.id))
    send(bot, chat_id=update.message.chat_id, text=article_list)
    
    # If the user has no articles, end conversation
    if (article_list == "You have no articles in the list, Master"):
        return ConversationHandler.END
    
    send(bot, chat_id=update.message.chat_id, text="Which is the number of the article you wish to remove? You can /cancel if you want") 
    return ARTICLE



def remove_article(bot, update):
    """Remove an article from the user's list."""
    articles = USER_DATA[str(update.message.from_user.id)]['user_articles']
    num = int(update.message.text)
    
    # If the number is not valid, repeat step
    if (num >= len(articles) or num < 0):
        send(bot, chat_id=update.message.chat_id, text="This number is not valid, try again or /cancel")
        return
    
    # Remove article
    del articles[num]
    
    send(bot, chat_id=update.message.chat_id, text="Article number " + update.message.text + " has been removed, Master")
    return ConversationHandler.END


    
# Inline
def inline_search(bot, update):
    """Search google via inline input."""
    # Get query
    query = update.inline_query.query
    user = update.message.from_user
    user_logger(update, "is querying inline: " + query)
    if not query:
        return
    
    # Search in google
    results = list()
    results.append(InlineQueryResultArticle(
        id=query,
        title=query.upper(),
        input_message_content=InputTextMessageContent(query.upper())
    ))
    
    # Update inline response
    bot.answer_inline_query(update.inline_query.id, results)
    
    
    
# Periodic
def daily_info(bot, job):
    """Send daily update to the user."""
    send(bot, chat_id=job.context['uid'], text="Today is " + datetime.datetime.today().strftime("%d-%m-%Y"))
    # Weather
    if (job.context['weather'] is not None):
        send(bot, chat_id=job.context['uid'], text=get_weather(job.context['weather']), parse_mode="Markdown")
    
    # Horoscope
    if (job.context['horoscope'] is not None):
        send(bot, chat_id=job.context['uid'], text=get_horoscope(job.context['horoscope']))
    
    # Article
    if (job.context['article']):
        send(bot, chat_id=job.context['uid'], text=get_article())



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)
    
    # Get config parameters
    with open("params.conf", "r") as fh:
        WEATHER_KEY = fh.readline().strip()
        updater = Updater(fh.readline().strip())
        ADMIN_ID = int(fh.readline().strip())
    dispatcher = updater.dispatcher
    jqueue = updater.job_queue
    
    global USER_DATA
    
    # Get user data
    try:
        with open("user_data.txt", "r") as fh:
            USER_DATA = json.load(fh)
    except:
        USER_DATA = {}
    
    # Set up existing daily updates
    for entry in USER_DATA:
        if ('time' in USER_DATA[entry]):
            time = datetime.time(USER_DATA[entry]['time'][0], USER_DATA[entry]['time'][1])
            jqueue.run_daily(daily_info, time, context={'uid': entry, 'weather': USER_DATA[entry]['weather'], 'horoscope': USER_DATA[entry]['horoscope']}, name=entry)
            log("Created daily update for " + str(entry))
    
    # Add handlers
    dispatcher.add_handler(RegexHandler('^[\w\s]+\shelp\s[\w\s]+$', help))
    dispatcher.add_handler(RegexHandler('^[Tt]hank you$', thank_response))
    dispatcher.add_handler(RegexHandler('[Hh]i|[Hh]ello', greeting))
    dispatcher.add_handler(RegexHandler('[Gg]oodbye|[Bb]ye', farewell))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('forecast', forecast))
    dispatcher.add_handler(CommandHandler('sign', horoscope))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('search', search, pass_args=True))
    dispatcher.add_handler(CommandHandler('article', article))
    dispatcher.add_handler(CommandHandler('myarticles', user_articles))
    dispatcher.add_handler(CommandHandler('dailyinfostop', stop_daily_info, pass_job_queue=True))
    dispatcher.add_handler(ConversationHandler(
                                                [CommandHandler('addarticle', start_add_article)],
                                                {ARTICLE: [RegexHandler('.*', add_article)]},
                                                []
                                              ))
    dispatcher.add_handler(ConversationHandler(
                                                [CommandHandler('removearticle', start_remove_article)],
                                                {ARTICLE: [RegexHandler('^\d+$', remove_article)]},
                                                [CommandHandler('cancel', cancel_conversation), RegexHandler('.*', error_conversation)]
                                              ))
    dispatcher.add_handler(ConversationHandler(
                                                [CommandHandler('dailyinfostart', start_daily_info, pass_user_data=True)],
                                                {WEATHER: [CommandHandler('skip', skip_weather, pass_user_data=True), RegexHandler('^[\w\s]+$', weather_handler, pass_user_data=True)],
                                                 CITY: [RegexHandler('^\d$', city_handler, pass_user_data=True)],
                                                 TIMEZONE: [RegexHandler('^\d{1,2}$', timezone_handler)],
                                                 HOROSCOPE: [CommandHandler('skip', skip_horoscope, pass_user_data=True), RegexHandler('^\w+$', horoscope_handler, pass_user_data=True)],
                                                 ARTICLE: [RegexHandler('^[Yy]es$|^[Nn]o$', article_handler, pass_user_data=True)],
                                                 TIME: [RegexHandler('^\d{1,2}$|^\d{1,2}:\d{1,2}$', schedule_handler, pass_user_data=True)],
                                                 DONE: [CommandHandler('done', set_daily_info, pass_user_data=True, pass_job_queue=True)]
                                                },
                                                [CommandHandler('cancel', cancel_conversation), RegexHandler('.*', error_conversation)]
                                              ))
    dispatcher.add_handler(InlineQueryHandler(inline_search))
    dispatcher.add_handler(RegexHandler('.*', error))

    log("Started")
    
    # Poll
    updater.start_polling()
    updater.idle()
    
    # If terminated, save user data
    with open("user_data.txt", "w") as fh:
        json.dump(USER_DATA, fh)
    
    log("Terminated")
