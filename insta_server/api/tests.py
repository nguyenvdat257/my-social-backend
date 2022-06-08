from django.test import TestCase

# Create your tests here.
import re
def get_hashtag(body):
    hashtags = set(re.findall(r"#(\w+)", body))
    return hashtags

a = '3982 #la感じkfふぇe #lkfe ewe'
print(get_hashtag(a))