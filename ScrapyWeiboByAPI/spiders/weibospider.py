#-*- coding=utf-8 -*-
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from ScrapyWeiboByAPI import UserItem,WeiboItem
import time
import json
import base62

class WeiboSpider(CrawlSpider):
	name = 'weibospider'
	allowed_domains = ['weibo.cn']

	
	def __init__(self):
		super(WeiboSpider,self).__init__()


		#start time or end time of an event
		self.start_time = time.mktime(time.strptime("2012-11-20","%Y-%m-%d"))
		self.end_time = time.mktime(time.strptime("2012-12-20","%Y-%m-%d"))
		self.base_url = "https://api.weibo.com/2/comments/show.json?"

	def start_requests(self):
		fp = open("weibo_id_of_leader_not_clean",'r')

		line = fp.readline()

		while "" != line:
			if not line.startswith("#"):
				req_url = mk_request(base62.url_to_mid(line.striip()),0)
				yield Request(url=req_url,callback=self.parse_weibo)
			line = fp.readline()
		fp.close()

	def mk_request(self,mid,max_id):
		req_url = self.base_url + "access_token=" + self.access_token + "&"
		req_url += "id=" + mid + "&count=200&"
		req_url += "max_id=" + max_id
		self.log(req_url)
		return req_url 

    #parse status of the original weibo
    #decide whether we need to further parse it comment

	def parse_status(self,status):
		try:
			#Sun May 13 00:56:44 +0800 2012
			u_time = time.mktime(time.strptime(status["created_at"],"%a %b %d %H:%M:%S +0800 %Y"))
			#if the users is created later than the event start later
			if u_time < self.start_time or u_time > self.end_time:
				return False
		except:
			return False
			self.log(status["created_at"])

		try:
			if status.has_key("deleted"):
				return False
			#get an new item
			wItem = WeiboItem()

			wItem["mid"] = status['mid']
			result +=  status["text"]

			if status.has_key("retweeted_status"):
				retweet_status = status["retweeted_status"]
				if not retweet_status.has_key("deleted"):
					result += "//@" + retweet_status["user"]["screen_name"] + ": " + retweet_status["text"]

			wItem["content"] = result
			wItem["uid"] = status['user']['id']
			wItem["pos"] = status['user']['location']
			wItem["time"] = status['created_at']
			yield wItem
			return True
		except:
			return False

	def parse_comment(self,comment):
		cItem = WeiboItem()
		cItem["mid"] =  comment["status"]["mid"]
		cItem["content"] = comment["text"]
		cItem["uid"] = comment["user"]["id"]
		cItem["pos"] = comment["user"]["location"]
		cItem["time"] = comment["created_at"]		
		return cItem

		
	def parse_user(self,user):

		userItem = UserItem()

		userItem["uid"] = user["id"]
		userItem["sname"] = user["screen_name"] 
		userItem["location"] = user["location"] 
		userItem["created_at"] = user["created_at"]  
		userItem["verified"] = user["verified"]  
		userItem["followers_count"] = user["followers_count"]
		userItem["friends_count"] = user["friends_count"]
		return userItem
		
	def parse_weibo(self,response):
		json_data = json.loads(response.body)

		b_continue = False
		#if it is the first request
		if json_data["previous_cursor"] == 0:
			b_continue = self.parse_status(json_data["comments"][0]["status"])

		if b_continue == True:

			for comment in json_data["comments"]:
				self.parse_user(comment["user"])
				self.parse_comment(comment)

				if json_data["next_cursor"] != 0:
					next_req_url= self.mk_request(json_data["comments"][0]["status"]["mid"],\
						json_data["next_cursor"])
					yield Request(url=next_req_url,callback=self.parse_weibo)