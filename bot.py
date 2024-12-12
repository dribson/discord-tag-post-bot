import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import csv
import atexit
import sys
from random import randint

load_dotenv()
guildid = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

tag_dict = {}
post_dict = {}

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(guildid))
    print(f'We have logged in as {client.user}')
    
@client.event
async def on_message(message):
    print(message.type)
    get_post = ''
    msg_reply = ''
    command = False
    if message.author.id == client.user.id:
        return
    elif message.content.startswith('!tag'):
        if message.type == discord.MessageType.default:
            get_post = message.id
            print('Default')
        elif message.type == discord.MessageType.reply:
            get_post = message.reference.message_id
            print('Reply')
        else:
            print(f'Unknown Message Type: {message.type}, exiting...')
            return
        command = True
        tag_string = message.content[5:]
        tag_list = tag_string.split(",")
        tag_list = [x.strip() for x in tag_list]
        for tag in tag_list:
            TagPost(get_post, tag)
        msg_reply = await message.reply(f'Tagged post with tags: {tag_list}!')
    elif message.content.startswith('!untagall'):
        if message.type == discord.MessageType.reply:
            command = True
            get_post = message.reference.message_id
            UnTagPost(get_post, post_dict[str(get_post)])
            msg_reply = await message.reply('Removed all Tags from post!')
        else:
            print('UntagAll command detected in non-reply post, exiting...')
    elif message.content.startswith('!untag'):
        if message.type == discord.MessageType.reply:
            command = True
            get_post = message.reference.message_id
            tag_string = message.content[7:]
            tag_list = tag_string.split(",")
            UnTagPost(get_post, tag_list)
            msg_reply = await message.reply(f'Removed following Tags from post: {tag_list}!')
        else:
            print('Untag command detected in non-reply post, exiting...')
    else:
        print('Undefined command detected!')
    if command:
        print('Command detected!')
        await msg_reply.delete(delay = 2)

@tree.command(name="tag", description="Add a Tag to a post", guild=discord.Object(id=guildid))
async def command_tag(msg, tags_arg:str):
    # get the previous message in the channel 
    tag_channel = client.get_channel(msg.channel_id)
    tagpost = await discord.utils.get(tag_channel.history(), author__name=msg.user.name)
    print(tags_arg)
    print(tagpost.attachments)
    if len(tagpost.attachments) == 0:
        await msg.response.send_message(f'Message has no Attachments. Please only tag posts that have Attachments.')
    else:
        list_tags = tags_arg.split()
        for tag in list_tags:
            TagPost(tagpost.id, tag)
        await msg.response.send_message(f'Tagged post with: {list_tags}')
    
def TagPost(post_id, *args):
    # Add tags to a post
    print(post_id)
    post_id = str(post_id)
    if post_id in post_dict.keys():
        for arg in args:
            if arg not in post_dict[post_id]:
                post_dict[post_id].append(arg)
                print(f'Existing post: {post_id} tagged with: {arg}')
            else:
                print(f'Existing post: {post_id} already has tag: {arg}')
    else:
        new_tag_list = list(args)
        post_dict.update({post_id:new_tag_list})
        print(f'New post: {post_id} tagged with: {new_tag_list}')
        
    # Add post IDs to a tag
    for arg in args:
        if arg in tag_dict.keys():
            if post_id not in tag_dict[arg]:
                tag_dict[arg].append(post_id)
                print(f'Existing tag: {arg} added to post: {post_id}')
            else:
                print(f'Existing tag: {arg} already applied to post: {post_id}')
        else:
            new_post_list = [post_id]
            tag_dict.update({arg:new_post_list})
            print(f'New tag: {arg} applied to post: {post_id}')
    
    UpdateFiles()
    pass
    
# Update the local files with the current tag and post lists
def UpdateFiles():
    update_list = ''
    empty_list = []
    with open(os.getenv('TAGS_WITHPOSTS'), 'w') as file:
        for key in tag_dict:
            update_list = ''
            if len(tag_dict[key]) > 0:
                for value in tag_dict[key]:
                    update_list = update_list + f'{value},'
                update_list = update_list[:-1]
                file.write(f'{key}:{update_list}\n')
            else:
                print(f'No Posts found for tag: {key}')
                empty_list.append(key)
        for key in empty_list:
            tag_dict.pop(key)
            
    update_list = ''
    empty_list = []    
    with open(os.getenv('POSTS_WITHTAGS'), 'w') as file:
        for key in post_dict:
            update_list = ''
            if len(post_dict[key]) > 0:
                for value in post_dict[key]:
                    update_list = update_list + f'{value},'
                update_list = update_list[:-1]
                file.write(f'{key}:{update_list}\n')
            else:
                print(f'No Tags found for Post: {key}')
                empty_list.append(key)
        for key in empty_list:
            post_dict.pop(key)
    pass

@tree.command(name='fetch', description='Fetch a random post that has a specific tag', guild=discord.Object(id=guildid))
async def command_fetch(msg, tag_arg:str):
    try:
        print(tag_dict[tag_arg])
        fetched_post = RandomFromList(tag_dict[tag_arg])
        tag_channel = client.get_channel(msg.channel_id)
        fetched_msg = await tag_channel.fetch_message(fetched_post)
        fetched_attachment = fetched_msg.attachments[0]
        fetched_url = fetched_attachment.url
        await msg.response.send_message(f'Here is a Post that has the Tag: **{tag_arg}**:\n{fetched_url}')
    except:
        print(f'No Posts found for provided Tag: {tag_arg}')
        await msg.response.send_message(f'No Post found with Tag: **{tag_arg}**. This command only accepts 1 Tag argument. Check Tag spelling, or use **/tags** to find a Tag!')
    pass
   
@tree.command(name='fetch_match', description='Fetch a post that matches all provided tags', guild=discord.Object(id=guildid)) 
async def command_fetchmatch(msg, tag_arg:str):
    tag_channel = client.get_channel(msg.channel_id)
    tag_list = list(tag_arg.split(", "))
    is_in_all = False
    final_post_list = []
    if tag_list[0] not in tag_dict:
        await msg.response.send_message(f'Could not find Post that has all of the Tags: **{tag_list}**\nCheck Tag spelling, or use **/tags** to find a Tag!')
        return
    first_tag_posts = tag_dict[tag_list[0]]
    print(first_tag_posts)
    for post in first_tag_posts:
        print(post)
        for tag in tag_list:
            is_in_all = tag in post_dict[post]
            if is_in_all is False:
                break
        if is_in_all:
            final_post_list.append(post)
        print('~~~~~~~')
    print(final_post_list)
    if len(final_post_list) == 0:
        await msg.response.send_message(f'Could not find Post that has all of the Tags: **{tag_list}**\nCheck Tag spelling, or use **/tags** to find a Tag!')
        return
    fetched_post = RandomFromList(final_post_list)
    fetched_msg = await tag_channel.fetch_message(fetched_post)
    fetched_attachment = fetched_msg.attachments[0]
    fetched_url = fetched_attachment.url
    await msg.response.send_message(f'Here is a Post that has all of the Tags: **{tag_list}**:\n{fetched_url}')
    pass

@tree.command(name='fetch_any', description='Fetch a post that matches any provided tag', guild=discord.Object(id=guildid)) 
async def command_fetchany(msg, tag_arg:str):
    tag_channel = client.get_channel(msg.channel_id)
    tag_list = list(tag_arg.split(", "))
    final_post_list = []
    bad_tag_list = []
    for tag in tag_list:
        print(tag)
        if tag not in tag_dict:
            bad_tag_list.append(tag)
            continue
        for post_id in tag_dict[tag]:
            if post_id not in final_post_list:
                final_post_list.append(post_id)
    print(final_post_list)
    if len(final_post_list) == 0:
        await msg.response.send_message(f'Could not find Post that has any of the Tags: **{tag_list}**')
        return
    fetched_post = RandomFromList(final_post_list)
    fetched_msg = await tag_channel.fetch_message(fetched_post)
    fetched_attachment = fetched_msg.attachments[0]
    fetched_url = fetched_attachment.url
    if len(bad_tag_list) > 0:
        await msg.response.send_message(f'Here is a Post that has one of the Tags: **{tag_list}**:\n{fetched_url}\n The following Tags were not found: **{bad_tag_list}**. Check Tag spelling, or use **/tags** to find a Tag!')
    else:
        await msg.response.send_message(f'Here is a Post that has one of the Tags: **{tag_list}**:\n{fetched_url}')
    pass
    
@tree.command(name="untag", description="Remove a list of Tags from the previous post", guild=discord.Object(id=guildid))
async def command_untag(msg, tags_arg:str):
    tag_channel = client.get_channel(msg.channel_id)
    tagpost = await discord.utils.get(tag_channel.history(), author__name=msg.user.name)
    list_tags = tags_arg.split()
    ret_msg = UnTagPost(tagpost.id, list_tags)
    await msg.response.send_message(ret_msg)
    pass
    
@tree.command(name="untagall", description="Remove all Tags from the previous post", guild=discord.Object(id=guildid))
async def command_untagall(msg):
    tag_channel = client.get_channel(msg.channel_id)
    tagpost = await discord.utils.get(tag_channel.history(), author__name=msg.user.name)
    ret_msg = UnTagPost(tagpost.id, post_dict[str(tagpost.id)])
    await msg.response.send_message(ret_msg)
    pass
    
def UnTagPost(post_id, *args):
    post_id = str(post_id)
    args = list(set(args[0]))
    BadTags = []
    GoodTags = []
    for tag in args:
        tag = tag.strip()
        print(tag)
        if tag in post_dict[post_id]:
            GoodTags.append(tag)
            print('Has Tag')
            tag_dict[tag].remove(post_id)
            post_dict[post_id].remove(tag)
        else: 
            print('No Tag Found')
            BadTags.append(tag)
    ret_msg = ''
    if len(BadTags) == len(args):
        ret_msg = f'Post did not contain any of the following Tags: {BadTags}. Use /tags to find the name of Tags.'
    elif len(BadTags) > 0:
        ret_msg = ret_msg + f'Tags remove from Post: {GoodTags}\n'
        ret_msg = ret_msg + f'Post did not have the following Tags: {BadTags}, Tags not removed from Post. Use /tags to find the name of Tags.'
    else:
        ret_msg = ret_msg + f'Tags remove from Post: {GoodTags}\n'
        
    UpdateFiles()
    return ret_msg
    
# Sync Tag and Post lists, then update files
@tree.command(name="sync", description="Refresh all Tags and Post lists", guild=discord.Object(id=guildid))
async def command_sync(msg):
    SyncLists()
    UpdateFiles()
    pass 
    
@tree.command(name="tags", description="Get all Tags", guild=discord.Object(id=guildid))
async def command_gettags(msg):
    list_tags = ''
    for tag in tag_dict:
        list_tags = list_tags + f'{tag} | '
    list_tags = list_tags[0:-2]
    await msg.response.send_message(f'List of tags:\n{list_tags}')

def SyncLists():
    print('syncing')
    pass
    
def RandomFromList(list):
    random_id = list[randint(0, len(list) - 1)]
    return random_id
    

@atexit.register
def Cleanup():
    print('cleanup')
    #SyncLists()
    #UpdateFiles()

with open(os.getenv('POSTS_WITHTAGS'), newline='') as file:
    for line in file:
        key, value = line.strip().split(':')
        key = key.replace("'", "")
        values = value.split(',')
        for v in values:
            v = v.replace('[', '')
            v = v.replace(']', '')
        post_dict[key] = values
    #print(post_dict)
with open(os.getenv('TAGS_WITHPOSTS'), newline='') as file:
    for line in file:
        key, value = line.strip().split(':')
        key = key.replace("'", "")
        values = value.split(',')
        for v in values:
            v = v.replace('[', '')
            v = v.replace(']', '')
        tag_dict[key] = values
    #print(tag_dict)
        
client.run(os.getenv('DISCORD_TOKEN'))