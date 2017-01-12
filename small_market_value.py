import pandas as pd
import tushare as ts
import re
import os
import datetime
import logging
import json
import util

stRegex = re.compile(r"^[^\*ST.*]")

class Small_Market:
    def __init__(self):
        with open('./conf/small_market_config.json', 'r') as f:
            config = json.loads(f.read())

        self.__amount = config['dealer_config']['amount']
        self.__cnt = config['dealer_config']['stock_cnt']
        self.__amount_per_stock = self.__amount / self.__cnt
        self.__stock_amount = config['dealer_config']['stock_amount']
        self.__target = None
        self.__deal_dir = config["deal_dir"]
        self.__log_dir = config["log_dir"]
        self.__record_dir = config["record_dir"]
        self.__deal_list = []
        self.__record_filename = config["record_filename"]
        self.__period = config["period"]

        if not os.path.exists(self.__log_dir):
            os.mkdir(self.__log_dir)

        if not os.path.exists(self.__record_dir):
            os.mkdir(self.__record_dir)

        if not os.path.exists(self.__deal_dir):
            os.mkdir(self.__deal_dir)

        logging.basicConfig(level=logging.DEBUG, filename="%s.log.%s" % (os.path.join(self.__log_dir, 'small_market_value'), datetime.datetime.now().strftime("%Y%m%d")), filemode='a', format='%(asctime)s [%(levelname)s] [%(lineno)d] %(message)s')
        self.__logger = logging.getLogger(__name__)

    def target(self):
        # lc = ts.get_today_all()
        # lc.to_csv('a.txt',encoding="utf-8")
        lc = pd.read_csv('a.txt',encoding='utf-8')
        lc_amount = lc.query('amount>10000000')
        lc_amount_except_ST = lc_amount[(lc_amount['name'].str.contains(stRegex, regex=True))]
        res = lc_amount_except_ST.sort_values(by="mktcap").head(self.__cnt)
        # print(res)
        # res = res[['code','name','trade','amount']]
        self.__target = res[['code','name','trade']]
        self.__target['share'] = 0

    def deal_target(self):
        for i in range(self.__cnt):
            s = self.__target.iloc[i]
            trade = s['trade']
            share = int((self.__amount_per_stock / 100) / trade) * 100
            self.__target.iloc[i, 3] = share
        print(self.__target)

    def next_date(self):
        with open(os.path.join(self.__record_dir,self.__record_filename), 'r') as f:
            lines = f.readlines()
            line = lines[-1]
            deal = json.loads(line)
            date = datetime.datetime.strptime(deal["date"], "%Y-%m-%d")
            next_date = date
            for i in range(self.__period):
                next_date += datetime.timedelta(days=1)
                while not util.is_trade_date(next_date):
                    next_date += datetime.timedelta(days=1)
            return next_date


if __name__ == "__main__":
    sm = Small_Market()
    target = sm.target()
    sm.deal_target()
    print(sm.next_date())



