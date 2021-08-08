import re

twitch_regexp = re.compile('twitch.tv\/(.+)')
youtube_regexp = re.compile('youtube.com\/channel\/(.+)')

def get_platform(link):
    
    if re.findall(twitch_regexp, link):
        return 'twitch', re.findall(twitch_regexp, link)[0]
    elif re.findall(youtube_regexp, link):
        return 'youtube', re.findall(youtube_regexp, link)[0]
    else:
        return None, None