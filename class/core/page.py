# coding: utf-8

import math
import string
import slemp


class Page():
    #--------------------------
    # Paging class - JS callback version
    #--------------------------
    __PREV = 'Prev'
    __NEXT = 'Next'
    __START = 'First'
    __END = 'Last'
    __COUNT_START = 'From'
    __COUNT_END = 'Data'
    __FO = 'from'
    __LINE = 'line'
    __LIST_NUM = 4
    SHIFT = None  # Offset
    ROW = None  # Lines per page
    __C_PAGE = None  # current page
    __COUNT_PAGE = None  # total pages
    __COUNT_ROW = None  # total number of rows
    __URI = None  # URI
    __RTURN_JS = False  # Whether to return JS callback
    __START_NUM = None  # start line
    __END_NUM = None  # end line

    def __init__(self):
        # tmp = slemp.getMsg('PAGE')
        if False:
            self.__PREV = tmp['PREV']
            self.__NEXT = tmp['NEXT']
            self.__START = tmp['START']
            self.__END = tmp['END']
            self.__COUNT_START = tmp['COUNT_START']
            self.__COUNT_END = tmp['COUNT_END']
            self.__FO = tmp['FO']
            self.__LINE = tmp['LINE']

    def GetPage(self, pageInfo, limit='1,2,3,4,5,6,7,8'):
        # Get paging information
        # @param pageInfo Pass in a dictionary of pagination parameters
        # @param limit Back to series
        self.__RTURN_JS = pageInfo['return_js']
        self.__COUNT_ROW = pageInfo['count']
        self.ROW = pageInfo['row']
        self.__C_PAGE = self.__GetCpage(pageInfo['p'])
        self.__START_NUM = self.__StartRow()
        self.__END_NUM = self.__EndRow()
        self.__COUNT_PAGE = self.__GetCountPage()
        self.__URI = self.__SetUri(pageInfo['uri'])
        self.SHIFT = self.__START_NUM - 1

        keys = limit.split(',')

        pages = {}
        # start page
        pages['1'] = self.__GetStart()
        # previous page
        pages['2'] = self.__GetPrev()
        # pagination
        pages['3'] = self.__GetPages()
        # next page
        pages['4'] = self.__GetNext()
        # Tail
        pages['5'] = self.__GetEnd()

        # The currently displayed page and the total number of pages
        pages['6'] = "<span class='Pnumber'>" + \
            bytes(self.__C_PAGE) + "/" + bytes(self.__COUNT_PAGE) + "</span>"
        # This page shows start and end lines
        pages['7'] = "<span class='Pline'>" + self.__FO + \
            bytes(self.__START_NUM) + "-" + \
            bytes(self.__END_NUM) + self.__LINE + "</span>"
        # Number of lines
        pages['8'] = "<span class='Pcount'>" + self.__COUNT_START + \
            bytes(self.__COUNT_ROW) + self.__COUNT_END + "</span>"

        # Construct return data
        retuls = '<div>'
        for value in keys:
            retuls += pages[value]
        retuls += '</div>'

        # return paginated data
        return retuls

    def __GetEnd(self):
        # Construct last page
        endStr = ""
        if self.__C_PAGE >= self.__COUNT_PAGE:
            endStr = ''
        else:
            if self.__RTURN_JS == "":
                endStr = "<a class='Pend' href='" + self.__URI + "p=" + \
                    bytes(self.__COUNT_PAGE) + "'>" + self.__END + "</a>"
            else:
                endStr = "<a class='Pend' onclick='" + self.__RTURN_JS + \
                    "(" + bytes(self.__COUNT_PAGE) + ")'>" + self.__END + "</a>"
        return endStr

    def __GetNext(self):
        # Construct the next page
        nextStr = ""
        if self.__C_PAGE >= self.__COUNT_PAGE:
            nextStr = ''
        else:
            if self.__RTURN_JS == "":
                nextStr = "<a class='Pnext' href='" + self.__URI + "p=" + \
                    bytes(self.__C_PAGE + 1) + "'>" + self.__NEXT + "</a>"
            else:
                nextStr = "<a class='Pnext' onclick='" + self.__RTURN_JS + \
                    "(" + bytes(self.__C_PAGE + 1) + ")'>" + self.__NEXT + "</a>"

        return nextStr

    def __GetPages(self):
        # Construct pagination
        pages = ''
        num = 0
        # before the current page
        if (self.__COUNT_PAGE - self.__C_PAGE) < self.__LIST_NUM:
            num = self.__LIST_NUM + \
                (self.__LIST_NUM - (self.__COUNT_PAGE - self.__C_PAGE))
        else:
            num = self.__LIST_NUM
        n = 0
        for i in range(num):
            n = num - i
            page = self.__C_PAGE - n
            if page > 0:
                if self.__RTURN_JS == "":
                    pages += "<a class='Pnum' href='" + self.__URI + \
                        "p=" + bytes(page) + "'>" + bytes(page) + "</a>"
                else:
                    pages += "<a class='Pnum' onclick='" + self.__RTURN_JS + \
                        "(" + bytes(page) + ")'>" + bytes(page) + "</a>"

        # current page
        if self.__C_PAGE > 0:
            pages += "<span class='Pcurrent'>" + \
                bytes(self.__C_PAGE) + "</span>"

        # after the current page
        if self.__C_PAGE <= self.__LIST_NUM:
            num = self.__LIST_NUM + (self.__LIST_NUM - self.__C_PAGE) + 1
        else:
            num = self.__LIST_NUM
        for i in range(num):
            if i == 0:
                continue
            page = self.__C_PAGE + i
            if page > self.__COUNT_PAGE:
                break
            if self.__RTURN_JS == "":
                pages += "<a class='Pnum' href='" + self.__URI + \
                    "p=" + bytes(page) + "'>" + bytes(page) + "</a>"
            else:
                pages += "<a class='Pnum' onclick='" + self.__RTURN_JS + \
                    "(" + bytes(page) + ")'>" + bytes(page) + "</a>"

        return pages

    def __GetPrev(self):
        # Construct the previous page
        startStr = ''
        if self.__C_PAGE == 1:
            startStr = ''
        else:
            if self.__RTURN_JS == "":
                startStr = "<a class='Ppren' href='" + self.__URI + "p=" + \
                    bytes(self.__C_PAGE - 1) + "'>" + self.__PREV + "</a>"
            else:
                startStr = "<a class='Ppren' onclick='" + self.__RTURN_JS + \
                    "(" + bytes(self.__C_PAGE - 1) + ")'>" + self.__PREV + "</a>"
        return startStr

    def __GetStart(self):
        # Construct start page
        startStr = ''
        if self.__C_PAGE == 1:
            startStr = ''
        else:
            if self.__RTURN_JS == "":
                startStr = "<a class='Pstart' href='" + \
                    self.__URI + "p=1'>" + self.__START + "</a>"
            else:
                startStr = "<a class='Pstart' onclick='" + \
                    self.__RTURN_JS + "(1)'>" + self.__START + "</a>"
        return startStr

    def __GetCpage(self, p):
        # get current page
        if p:
            return p
        return 1

    def __StartRow(self):
        # how many lines to start with
        return (self.__C_PAGE - 1) * self.ROW + 1

    def __EndRow(self):
        # how many lines to end with
        if self.ROW > self.__COUNT_ROW:
            return self.__COUNT_ROW
        return self.__C_PAGE * self.ROW

    def __GetCountPage(self):
        # Get the total number of pages
        return int(math.ceil(self.__COUNT_ROW / float(self.ROW)))

    def __SetUri(self, input):
        # Structure URI
        uri = '?'
        for key in input:
            if key == 'p':
                continue
            uri += key + '=' + input[key] + '&'
        return str(uri)
