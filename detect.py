import os, re, requests, html5lib, json, pprint
from database import Database
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment
from difflib import get_close_matches

class Article:
    path_to_dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, args=None):
        # Database is not in use at the time...
        if not args == None:
            username = args['database']['user']
            password = args['database']['pass']
            database = args['database']['database_name']
            self.db = Database(user, password, database)
            self.db_is_usable = True
        else:
            print('Cannot make a database connection...')
            self.db_is_usable = False

    @classmethod
    def get_domain(cls, url):
        parsed_url = urlparse(url)
        return str(parsed_url.netloc)

    """
        Returns a stripped version of the actual page
    """
    @classmethod
    def get_page(cls, url):
        content = (requests.get(url)).text
        soup = BeautifulSoup(content, 'html5lib')

        # Remove comments
        comments = soup.findAll(text=lambda text:isinstance(text, Comment))
        [comment.extract() for comment in comments]

        # Remove whitespace
        html = str(soup.body)
        return "".join(re.sub(r"[\n\t]*", "", line) for line in html.split("\n"))

    @classmethod
    def get_rules(cls, file_name):
        return Article.get_file(file_name)

    """
        Strips the most useless tags from the page
        Eg. <header>, <footer>
    """
    @classmethod
    def strip_tags(cls, html, rules):
        response = []
        html = BeautifulSoup(html, 'html5lib')

        # Extract every tag that's unimportant
        for tag in rules:
            if tag[0] != '#':
                [s.extract() for s in html(tag)]

        return [str(tag) for tag in html]

    """
        Returns an array of lines with
        the content of the requested file.
    """
    @classmethod
    def get_file(cls, file_name):
        # Check if file is relative or
        # absolute and make it absolute
        if not re.search(r"%s" % (Article.path_to_dir,), file_name):
            file_name = "%s/%s" % (Article.path_to_dir, file_name,)

        # Check if file doesn't already exist..
        # If not, create the file..
        if not os.path.isfile(file_name):
            with open(file_name, 'w+') as fw:
                fw.write("")
        with open(file_name, 'r+') as fr:
            file_content = fr.readlines() # Returns an array of rules

        # Remove \n's
        return [re.sub(r"\n", "", line) for line in file_content]

    """
        Returns the main text retrieved
        from the requested url
    """
    def get_article(self, url):
        domain = Article.get_domain(url)

        #TODO: Create table learning
        if self.db_is_usable:
            query = "SELECT * FROM learning WHERE base_url = %s" % (domain,)
            response = self.db.fetch(query)

        file_name = 'rules.txt'
        rules = Article.get_rules(file_name)
        html = Article.get_page(url)

        print("Checking url:", url)
        return Article.strip_tags(html, rules)

# Tests!!
if __name__ == '__main__':
    article = Article()
    articles = [
        'https://webdrawings.nl',
        'https://webdrawings.nl/contact',
        'https://nl.wikipedia.org/wiki/Auto',
        'https://nl.wikipedia.org/wiki/Fiets',
        'https://nl.wikipedia.org/wiki/Trema'
    ]

    for url in articles:
        main = article.get_article(url)

        path = article.path_to_dir+'/'+url[8:]
        try: os.makedirs(path)
        except: pass

        with open(path+'/index.html', 'w+') as fw:
            print("".join(main))
            fw.write("".join(main))
            fw.close()
