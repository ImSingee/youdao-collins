from bs4 import BeautifulSoup
import requests
import re

headers =  {
        'Accept': r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': r'gzip, deflate, br',
        'Accept-Language': r'zh-CN,zh;q=0.8,zh-TW;q=0.6,en-US;q=0.4,en;q=0.2',
        'Upgrade-Insecure-Requests': r'1',
        'Host': r'www.youdao.com',
        'User-Agent': r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
}


class Collins:
    word = ''
    spell = ''
    star = 0
    rank = []
    additional = []
    explains = []

    ERROR = '[ERROR]'

    def __init__(self, word, method='online'):
        self.word = word
        if method == 'online':
            self.init_online()
        else:
            self.word = self.ERROR

    def init_online(self):
        url = 'http://dict.youdao.com/w/eng/{}'.format(self.word)
        text = requests.get(url, headers=headers).text
        collins = BeautifulSoup(text, 'html.parser').find('div', id="collinsResult")
        if not collins:
            self.word = self.ERROR
            return
        # 音标
        self.spell = collins.find('em', class_="additional spell phonetic").text
        # 星级
        self.star = int(collins.find('span', class_="star")['class'][1][-1])
        # 来源
        self.rank = collins.find('span', class_="via rank").text.split()
        # 派生词
        self.additional = re.findall(re.compile('[A-Za-z]+', re.S), collins.find('span', class_='additional pattern').text)
        # 解释
        li = collins.find('ul').find_all('li')
        self.explains = [Explain(x.find('div', class_='collinsMajorTrans').p, x.find_all('div', class_='examples')) for x in li]

    def raw_output(self):
        return {
            'word': self.word,
            'spell': self.spell,
            'star': self.star,
            'rank': self.rank,
            'additional': self.additional,
            'explains': [x.raw_output() for x in self.explains]
        }


class Explain:
    raw_explain = ''  # .collinsMajorTrans p
    raw_examples = []  # .examples
    explain = {}  # type, raw, e-c/alias; english,chinese
    examples = []

    ALIAS = 'ALIAS'

    def __init__(self, explain, examples):
        # explain must be type of bs4.element.Tag
        # examples should be type of bs4.element.ResultSet
        self.raw_explain = explain
        self.raw_examples = examples
        self.explain = {}
        self.examples = []

        type_t = explain.find('span', class_='additional')
        if type_t is None:
            self.explain['type'] = self.ALIAS
            self.explain['raw'] = ' '.join(explain.text.strip().replace('\t','').replace('\n','').split())
            self.explain['alias'] = explain.a.text
            self.explain['raw_b'] = self.explain['raw'].replace(self.explain['alias'], '**'+self.explain['alias']+'**')

        else:
            self.explain['type'] = type_t.text
            explain.span.extract()
            usu_t = explain.find('span', class_='additional')
            if usu_t:
                self.explain['usu'] = usu_t.text
                self.explain['raw'] = ' '.join(explain.text.strip().split())
                usu_t.extract()
                self.explain['e-c'] = explain.text.strip()
            else:
                self.explain['raw'] = explain.text.strip()
                self.explain['e-c'] = self.explain['raw']
            self.explain['english'] = re.findall(r'^.[A-Za-z…\- ,.;:_]*[A-Za-z….]', self.explain['e-c'])[0]  # Todo
            self.explain['chinese'] = self.explain['e-c'].replace(self.explain['english'], '').strip()  # Todo

        # Todo:examples
        if examples:
            self.examples = [{
                'english': x.find_all('p')[0].text.strip(),
                'chinese': x.find_all('p')[1].text.strip()
            } for x in examples]


    def raw_output(self):
        return {
            'explain': self.explain,
            'examples': self.examples
        }

if __name__ == '__main__':
    test = Collins('test')
    print(test.raw_output())
    # print(test.__dict__)
