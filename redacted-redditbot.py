import praw
import time
import pandas as pd
from datetime import datetime
import yagmail

yag = yagmail.SMTP([RESEARCH_EMAIL], [RESEARCH_EMAIL_PWD])
def get_subs():
            sub_list=[]
            path = "/user/{user}/moderated_subreddits".format(user=[BOT_NAME])
            response = reddit.get(path)
            for sub in response["data"]:
                sub_list.append(sub["sr"])
            return sub_list

def handle_msgs():
            while True: 
                        try: 
                            inbox = reddit.inbox.unread()
                            for message in inbox:
                                #if a msg's subject is withdraw, add the sender to opt out mod list 
                                if (message.subject).lower() =='withdraw':
                                    opt_out_mod_list = opt_out_mod_list + message.author.name + ' '
                                    message.reply('Thank you for the message! I will not collect your moderation actions for our study.')
                                    message.mark_read()
                                #if a msg is an invitation, accept it
                                if message.body.startswith('gadzooks!'):
                                    print(message.subreddit.display_name)
                                    print(message.body)
                                    sr = reddit.subreddit(message.subreddit.display_name)
                                    try:
                                        sr.mod.accept_invite()
                                        message.reply('Thank you for adding me! I am a bot developed by a research team at Northwestern University to study moderator labor practices(see u/mod_research for details). I will be collecting your community’s mod logs for a maximum of two months. Your mod logs will never be shared with anyone outside of the research team. If anyone on your moderator team does not want me to collect their moderation actions, just send me a direct message with the subject line being “WITHDRAW”. Then the corresponding subset of mod logs will be deleted within 24 hours. ')
                                        message.mark_read()
                                        print('accept ' + message.subreddit.fullname)
                                    except:
                                        myFile.write('invalid invite')
                                        message.mark_read()
                            break        
                        except:
                            myFile.write('\nwait unread msgs ')
                            time.sleep(2)

#def collect_logs():

#def get_opt_out_mod():
            
def collect_modlogs(sub, opt_out_mod_list, last_action=None):
    results =[]
    if last_action: 
        for log in reddit.subreddit(sub).mod.log(limit=500, params={'after':last_action}):
            logitem=[log.subreddit, log.description, log.target_body, log.mod_id36,log.created_utc,
                    log.target_title, log.target_permalink, log.details, log.action, str(log.target_fullname)[0:6],
                    log.id, log.mod]
            results.append(logitem)
    else:
        for log in reddit.subreddit(sub).mod.log(limit=500):
            logitem=[log.subreddit, log.description, log.target_body, log.mod_id36,log.created_utc,
                    log.target_title, log.target_permalink, log.details, log.action, str(log.target_fullname)[0:6],
                    log.id, log.mod]
            results.append(logitem)
            
    existing_logs = pd.DataFrame(results, columns =['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
                'target_title', 'target_permalink', 'details', 'action', 'target_author','id', '_mod'])
    
    last_action = existing_logs.loc[len(existing_logs)-1, 'id']
    time.sleep(2)

    print(sub)
    key=1
    threshold = len(existing_logs)
    
    while (threshold>=500): 
        if 'modlog_research_bot' is in existing_logs['_mod']: 
            break
        else: 
            results =[]
            for log in reddit.subreddit(sub).mod.log(limit=500, params={'after':last_action}):
                logitem=[log.subreddit, log.description, log.target_body, log.mod_id36,log.created_utc,
                        log.target_title, log.target_permalink, log.details, log.action, str(log.target_fullname)[0:6],
                        log.id, log.mod]
                results.append(logitem)
            new_logs = pd.DataFrame(results, columns =['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
                        'target_title', 'target_permalink', 'details', 'action', 'target_author','id', '_mod'])

            #new_logs = new_logs.sort_values('created_utc', ascending = True)
            existing_logs = existing_logs.append(new_logs)
            #print(len(new_logs), new_logs.loc[0,'created_utc'], new_logs.loc[499,'created_utc'])  
            threshold = len(new_logs)
            if threshold <500:
                print('end')
                break
            else:
                last_action = new_logs.loc[499,'id']
                print(key)
                key = key+1
                time.sleep(2)
        
            
    existing_logs = existing_logs[['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
                                                    'target_title', 'target_permalink', 'details', 'action', 'target_author',
                                                    'id', '_mod']]
    existing_logs.drop_duplicates(subset=['id'], inplace=True)
    opt_out_mod_list = existing_logs[~existing_logs['_mod'].isin(opt_out_mod_list)]
    existing_logs.to_csv('historical/Nov11/'+sub+'.csv', index= False)


while True: 
    try: 
        myFile = open('log.txt', 'a') 
        myFile.write('\nStarted on ' + str(datetime.now()))
        myFile.write('\nconnecting to praw')
        while True: 
            try:
                reddit = praw.Reddit(client_id=[CLIENT_ID], client_secret=[CLIENT_SECRET], user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
                                    username=[BOT_NAME], password=[BOT_PWD])
                break
            except:
                myFile.write('\nwait')
                time.sleep(2)
        #get usernames of mods who have opted out 
        myFile.write('\ngetting opt out mods')
        opt_out_mods = open("opt_out_mods.txt", "r")
        opt_out_mod_list=opt_out_mods.read()
        opt_out_mods.close() 
        myFile.write('\nget opt out mods: ' + opt_out_mod_list)
        
        #read unread messages 
        handle_msgs()

        #write opt out mod list to file 
        opt_out_mods = open("opt_out_mods.txt", "w")
        opt_out_mods.write(opt_out_mod_list)
        myFile.write('\nwrite opt out mods: ' + opt_out_mod_list)
        opt_out_mod_list = opt_out_mod_list.split()

        #get what subs the bot is moderating 
        subreddit_list = get_subs()
        myFile.write('\nthe bot is added to these subs: ' + str(subreddit_list))

        for sub in subreddit_list:
        
            try:
                mod_df = pd.read_csv('historical/Nov10/'+ sub + '.csv')
                
                mod_df = mod_df.sort_values('created_utc')
                last_action = mod_df.loc[len(mod_df)-1, 'id']
                collect_modlogs(sub, opt_out_mod_list, last_action)
                
            except:
                collect_modlogs(sub, opt_out_mod_list)
            
            time.sleep(2)
        yag.send([RESEARCH_EMAIL],' success'])
        break
    except Exception as e: 
        yag.send([RESEARCH_EMAIL], 'fail', [ e, str(datetime.now())])

