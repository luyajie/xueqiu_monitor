#! /usr/bin/env python
#coding: utf-8

__author__ = 'Administrator'
#AIP: automatic investment plan, 基金定投

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import datetime
import urllib2
import mail
import os
import logging

class AIP():
    def __load_config_file(self, filename):
        with open(filename, 'r') as f:
            return json.loads(f.read())

    def __init__(self):
        config = self.__load_config_file("./conf/AIP_config.json")

        self.__mail = config["mail_config"]
        self.__month_money = config["month_money"]
        self.__cube_fixed = config["cube_fixed"]
        self.__cube_value = config["cube_value"]
        self.__last = ""
        tmp = config["trade_date"].encode('utf-8').split(',')
        self.__trade_date = [int(m) for m in tmp]
        self.__today = datetime.datetime.today()
        self.__deal_dir = config["deal_dir"]
        self.__log_dir = config["log_dir"]
        self.__record_dir = config["record_dir"]
        self.__dealer_config = config.get("dealer_config", {})
        self.__value_gap = config["value_gap"]
        self.__deal_rate = config["deal_rate"]
        self.__expect_rate = config["expect_rate"]
        self.__max_gap = config["max_gap"]
        self.__deal_list = []

        if not os.path.exists(self.__log_dir):
            os.mkdir(self.__log_dir)

        if not os.path.exists(self.__record_dir):
            os.mkdir(self.__record_dir)

        if not os.path.exists(self.__deal_dir):
            os.mkdir(self.__deal_dir)

        logging.basicConfig(level=logging.DEBUG, filename="%s.log.%s" % (os.path.join(self.__log_dir, 'AIP'), datetime.datetime.now().strftime("%Y%m%d")), filemode='a', format='%(asctime)s [%(levelname)s] [%(lineno)d] %(message)s')
        self.__logger = logging.getLogger(__name__)

    def __is_trade_time(self, stcok_id):
        time_obj = datetime.datetime.now()
        if not time_obj.day in self.__trade_date:
            self.__logger.info(stcok_id + " is not int trade days")
            return False

        if self.__last == "":
            # file_name = self.__record_dir + "/" + stcok_id + ".record"
            file_name = os.path.join(self.__record_dir, stcok_id + ".record")
            if os.path.exists(file_name):
                with open(file_name,'r') as f:
                    res = json.loads(f.readline())
                    self.__last = res["date"].encode("utf-8")
            else:
                self.__last = "2012-12"

        sep = self.__last.split('-')
        last_year = int(sep[0])
        last_month = int(sep[1])

        if self.__today.year == last_year and self.__today.month== last_month:
            self.__logger.info(stcok_id + " has been invested this month.")
            return False

        if time_obj.weekday() == 5 or time_obj.weekday() == 6:
            self.__logger.info(stcok_id + "Today is not work day.")
            return False

        return True

    def __get_net(self, stcok_id):
        url = "http://hq.sinajs.cn/list=" + stcok_id
        res = urllib2.urlopen(url)
        line = res.read()
        sep = line.split(',')
        return float(sep[3])

    def __store_deal(self, deal):
        file_name = deal["stock_id"] + "_" + str(deal["price"]) + "_" + str(deal["share"]) + "_" + str(deal["action"])
        # print file_name[:8]
        if file_name[:8] != "sh159915":
            with open("%s/%s" % (self.__deal_dir, file_name[2:]), "w") as f:
                f.write("\n")
        return

    def __store_record(self, deal):
        with open("%s/%s.record" % (self.__record_dir, deal["stock_id"]), "a") as f:
            f.write(json.dumps(deal))
            f.write("\n")
        return

    def __send_mail(self, deal_list):
        mail_detail = "<p>调仓时间啦</p>\n"
        mail_detail += "<table border=\"1\"><tbody>\n"
        mail_detail += u"<tr>\n"
        mail_detail += u"<td>股票id</td>\n"
        mail_detail += u"<td>股票名称</td>\n"
        mail_detail += u"<td>交易价格</td>\n"
        mail_detail += u"<td>交易数量</td>\n"
        mail_detail += u"</tr>\n"

        for item in deal_list:
            stock_id = item["stock_id"]
            stock_name = item["stock_name"]
            price = item["price"]
            share = item["share"]

            mail_detail += u"<tr>\n"
            mail_detail += u"<td>" + str(stock_id) + "</td>\n"
            mail_detail += u"<td>" + str(stock_name) + "</td>\n"
            mail_detail += u"<td>" + str(price) + "</td>\n"
            mail_detail += u"<td>" + str(share) + "%</td>\n"
            mail_detail += u"</tr>\n"

        title = "调仓啦~~(潘文海)"

        mail_detail += "</tbody></table>\n"

        mail_detail += "<br/>\n"
        mail_detail += "<p>生成订单:</p>\n"
        mail_detail += "<table border=\"1\"><tbody>\n"
        mail_detail += u"<tr>\n"
        mail_detail += u"<td>动作</td>\n"
        mail_detail += u"<td>证券id</td>\n"
        mail_detail += u"<td>证券名字</td>\n"
        mail_detail += u"<td>交易价格</td>\n"
        mail_detail += u"<td>交易股数</td>\n"
        mail_detail += u"</tr>\n"

        for deal in deal_list:
            mail_detail += u"<tr>\n"
            mail_detail += u"<td>" + str(deal["action"]) + "</td>\n"
            mail_detail += u"<td>" + str(deal["stock_id"]) + "</td>\n"
            mail_detail += u"<td>" + str(deal["price"]) + "</td>\n"
            mail_detail += u"<td>" + str(deal["share"]) + "</td>\n"
            mail_detail += u"</tr>\n"

        mail_detail += "</tbody></table>\n"


        if "email" in self.__dealer_config:
            for mail_address in self.__dealer_config["email"]:
                # mail.sendhtmlmail([mail_address], title,mail_detail.encode("utf-8", "ignore"))
                mail.sendhtmlmail(['sunada2005@163.com'], title,mail_detail.encode("utf-8", "ignore"))
        return

    def make_deal(self,cube_id, amount):
        net = self.__get_net(cube_id)
        deal = {}
        deal["action"] = "buy" if amount >= 0 else "sell"
        amount = amount if amount >= 0 else amount * (-1)
        share = int(amount / net / 100) * 100
        deal["stock_id"] = cube_id
        deal["price"] = net
        deal["share"] = share
        deal["amount"] = net * share
        deal["date"] = datetime.datetime.strftime(self.__today, "%Y-%m-%d")
        return deal

    def read_value_aip_sum(self, stock_id):
        filename = os.path.join(self.__record_dir, stock_id + ".sum")
        if not os.path.exists(filename):
            return None
        with open(filename) as f:
            lines = f.readlines()
            return json.loads(lines[-1])

    def cal_val_api_amount(self, cube_id):
        filename = os.path.join(self.__record_dir,cube_id + ".sum")
        if not os.path.exists(filename):
            return

        with open(filename) as f:
            line = f.readlines()[-1]
            net = self.__get_net(cube_id)
            # print "cal_val_api_amount", line
            #第n期|日期|stock_id|名称|买入价格|当月投入|累计投入|定投当月份额|定投累计份额|
            record = json.loads(line)
            expect_amount = float(record["sum_amount"]) * (1 + self.__expect_rate) + self.__value_gap
            month_amount = expect_amount - int(record["sum_share"]) * net
            month_amount = month_amount if month_amount < self.__max_gap else self.__max_gap
            month_amount = month_amount if month_amount > self.__max_gap * (-1) else self.__max_gap * (-1)
            return month_amount

    def save_val_api_sum(self,deal):
        #第n期|日期|stock_id|名称|买入价格|当月投入|累计投入|定投当月份额|定投累计份额|
        record = {}
        record["stock_id"] = deal["stock_id"]
        record["name"] = deal["name"]
        record["date"] = deal["date"]
        record["price"] = float(deal["price"])
        record["month_share"] = int(deal["share"])
        record["month_amount"] = float(deal["amount"])
        record["sum_share"] = int(record["month_share"])
        record["sum_amount"] = float(record["month_amount"])
        record["id"] = 1
        last_record = self.read_value_aip_sum(deal["stock_id"])
        if last_record != None:
            record["sum_share"] = int(last_record["sum_share"]) + record["sum_share"] if deal["action"] == "buy" else int(last_record["sum_share"]) - record["sum_share"]
            record["sum_amount"] = float(last_record["sum_amount"]) + record["sum_amount"] if deal["action"] == "buy" else float(last_record["sum_amount"]) - record["sum_amount"]
            record["id"] = int(last_record["id"]) + 1

        with open(os.path.join(self.__record_dir, deal["stock_id"] + ".sum"), "a") as f:
            f.write(json.dumps(record))
            f.write("\n")
            f.close()

    def AIP_fixedMonthMoney(self):
        self.__logger.info("AIP_fixedMonthMoney start")
        deal_list = []
        for cube_id in self.__cube_fixed:
            if not self.__is_trade_time(cube_id):
                break
            deal = self.make_deal(cube_id, self.__month_money)
            deal["stock_name"] = self.__cube_fixed[cube_id]
            self.__store_deal(deal)
            self.__store_record(deal)
            self.__deal_list.append(deal)
        return self.__deal_list

    def AIP_valueAvergaging(self):
        self.__logger.info("AIP_valueAvergaging start")
        deal_list = []
        for cube_id in self.__cube_value:
            if not self.__is_trade_time(cube_id):
                break
            amount = self.cal_val_api_amount(cube_id)
            month_amount = self.__value_gap if amount == None else amount
            deal = self.make_deal(cube_id, month_amount)
            deal["name"] = self.__cube_value[cube_id]
            # self.__store_deal(deal)
            self.__store_record(deal)
            self.__deal_list.append(deal)
            self.save_val_api_sum(deal)
        return self.__deal_list

    def AIP(self):
        self.AIP_fixedMonthMoney()
        self.AIP_valueAvergaging()

        # self.__last = self.__today
        if not self.__deal_list != None:
            self.__send_mail(self.__deal_list)

if __name__ == "__main__":
    aip = AIP()
    aip.AIP()
