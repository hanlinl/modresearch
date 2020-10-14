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
        #write opt out mod list to file 
        opt_out_mods = open("opt_out_mods.txt", "w")
        opt_out_mods.write(opt_out_mod_list)
        myFile.write('\nwrite opt out mods: ' + opt_out_mod_list)
        opt_out_mod_list = opt_out_mod_list.split()

        #get what subs the bot is moderating 
        subreddit_list = get_subs()
        myFile.write('\nthe bot is added to these subs: ' + str(subreddit_list))

        for sub in subreddit_list:
            while True: 
                try: 
                    results =[]
                    #get mod log 
                    for log in reddit.subreddit(sub).mod.log():
                        #make sure the mod is not in the opt out mod list 
                        if (log.mod not in opt_out_mod_list):
                            logitem=[log.subreddit, log.description, log.target_body, log.mod_id36,log.created_utc,
                                            log.target_title, log.target_permalink, log.details, log.action, log.target_fullname[0:5],
                                            log.id, log.mod]
                            results.append(logitem)
                            print("Mod: {}, Subreddit: {}".format(log.mod, log.subreddit, log.created_utc))
                    #save mod log 
                    try:
                        
                        existing_logs = pd.read_csv(sub+'.csv', index_col=None)
                        new_logs = pd.DataFrame(results, columns =['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
                                            'target_title', 'target_permalink', 'details', 'action', 'target_author',
                                            'id', '_mod']) 
                        print('existing logs', len(existing_logs)) 
                        existing_logs = existing_logs.append(new_logs)
                        existing_logs = existing_logs[['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
                                            'target_title', 'target_permalink', 'details', 'action', 'target_author',
                                            'id', '_mod']]
                        existing_logs = existing_logs.drop_duplicates(subset=['id'])  
                        print('final logs', len(existing_logs))
                        existing_logs.to_csv(sub+'.csv', index= False)   
                    except:
                        
                        existing_logs = pd.DataFrame(results, columns =['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
                                            'target_title', 'target_permalink', 'details', 'action', 'target_author',
                                            'id', '_mod'])
                        existing_logs.to_csv(sub+'.csv', index= False)   
                    
                    
                    myFile.write('\nwrite: ' + sub)
                    break 
                except:
                    myFile.write('\nwait')
                    time.sleep(2)
            
            time.sleep(2)
        yag.send([RESEARCH_EMAIL],' success'])
        break
    except Exception as e: 
        yag.send([RESEARCH_EMAIL], 'fail', [ e, str(datetime.now())])

