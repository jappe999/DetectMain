import os, re, requests, html5lib, json, pprint
from database import Database
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment
from difflib import get_close_matches

class Article:
    path_to_dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, args=None):
        Article.init_data()
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
    def init_data(cls):
        try: os.mkdir(Article.path_to_dir+'/Data')
        except: pass

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

        # Extract every tag that's unimportant
        [s.extract() for s in soup('script')]
        [s.extract() for s in soup('noscript')]
        [s.extract() for s in soup('img')]
        [s.extract() for s in soup('video')]
        [s.extract() for s in soup('audio')]

        # Remove comments
        comments = soup.findAll(text=lambda text:isinstance(text, Comment))
        [comment.extract() for comment in comments]

        # Remove whitespace
        html = str(soup.body)
        return "".join(re.sub(r"[\n\t]*", "", line) for line in html.split("\n"))

    @classmethod
    def save_rule(cls, file_name, rule):
        with open(file_name, 'a') as fw:
            fw.write(rule)

    @classmethod
    def get_rules(cls, file_name):
        file_content = "".join(Article.get_file(file_name))
        if file_content == "":
            return []

        response = [str(line) for line in BeautifulSoup(file_content, "html5lib").findAll()] # Array of rules
        for x in response:
            for y in response:
                if x.find(y) > -1:
                    response.remove(y)

        return response

    @classmethod
    def get_selector(cls, element):
        elem_id = ''
        elem_class = ''
        elem_selector = element.name
        try: elem_id = '#' + element.attrs['id']
        except: pass
        try:
            elem_class = ['.'+class_name for class_name in element.attrs['class']][0]
        except: pass
        if not elem_id == '':
            elem_selector += elem_id
            if not elem_class == '':
                elem_selector += elem_class
        elif not elem_class == '':
            elem_selector += elem_class

        return elem_selector

    @classmethod
    def check_lines(cls, html, rules):
        response = []
        html = BeautifulSoup(html, 'html5lib').findAll()

        selectors = []
        for element in html:
            element_selector = Article.get_selector(element)
            children = element.children
            for child in children:
                found_selector = False
                for line in selectors:
                    selector = line[0]
                    latest_element = line[1]
                    if element_selector == latest_element:
                        #print(element_selector, latest_element, Article.get_selector(child))
                        line[0] += str(' > ' + Article.get_selector(child))
                        line[1] = element_selector
                        print(selectors)
                        found_selector = True
                        break

                if not found_selector:
                    # markup: ['selector', 'latest element']
                    selectors.append([element_selector, element_selector])

        print(selectors)

        for tag in html:
            if tag.text == '':
                # If the tag contains no text
                # it's useless and is deleted
                del tag
            else:
                # If tag is like one of the rules
                if not get_close_matches(str(tag), rules, cutoff=0.6) == []:
                    #print('Matched:', str(tag))
                    del tag
                # If tag isn't like one of the rules
                else:
                    #print('Added:', str(tag))
                    response.append(str(tag))

        for x in response:
            for y in response:
                if x.find(y) > -1:
                    response.remove(y)

        return response

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

        file_name = 'Data/'+domain+'.txt'
        rules = Article.get_rules(file_name)
        html = Article.get_page(url)

        print("Checking url:", url)
        if not rules == []:
            return Article.check_lines(html, rules)
        else:
            # No rules yet...
            Article.save_rule(file_name, str(html))
            return Article.check_lines(html, rules)

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
