#!/usr/bin/python3
import mysql.connector
from mysql.connector import errorcode
import sys
import datetime
import json
import mysqlConnector as sql
import analytics
import logging
import os

logging.basicConfig(
        filename='railApplication.log',
        format='%(asctime)s.%(msecs)-3d:%(filename)s:%(funcName)s:%(levelname)s:%(lineno)d:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )

PATH = "/home/tarun/github/rail/pythonFiles/"

class main:
	'''
	1)GET A BETTER NAME FOR THE CLASS
	2)WRITE BETTER DOCUMENTATION AS YOU GO
	4)PLEASE MAKE SURE YOU PASS 'null' AND NOT AN EMPTY LIST OR A DICTIONARY
	'''
	def __init__(self,jsonData,levelNumber):		#Constructor which decodes the incoming json data
		logging.info("Constructor of class __name__:{} __class__:{} was called in levelNumber:{}".format(__name__,__class__,levelNumber))
		#The following piece of code is used to convert the data to dict format if it inst already in that format
		try:	#Checking if the input data is of string type
			logging.debug("Input data is of string type, converting into dict format")
			self.jsonString = json.loads(str(jsonData))
		except:	#Checking of the input data is of dict type, this happens only when the class create an instance of itself!
			logging.debug("Input data is of dict type, no changes made")
			self.jsonString = jsonData
		logging.debug("Input data is:"+str(json.dumps(self.jsonString)))

		self.levelNumber = levelNumber

		self.header = self.jsonString["HEADER"]			#Gets the header
		self.database = self.header["DATABASE"]			#database name within header
		self.table = self.header["TABLE_NAME"]			#table name name within header
		self.requestType = self.header["REQUEST_TYPE"]	#request type name within header

		self.data = self.jsonString["DATA"]				#Gets the data
		self.fields = self.data["FIELDS"]				#fields name within header
		self.setClause = self.data["SET"]				#setClause name within header
		self.whereClause = self.data["WHERE"]			#whereClause name within header

		self.footer = self.jsonString["FOOTER"]			#Gets the footer
		self.updateList = self.footer["UPDATE"]			#update name within header
		self.conditionList = self.footer["DEP"]			#dep name within header
		try:
			self.runCondition = self.footer["CONDITION"]	#Run analytics
			self.analyticsArguments = self.data["FIELDS"]
		except:
			logging.warning("Change 'DATA ABOUT THE REQUEST' to 'CONDITION'")
		'''
		WRITE THE CODE HERE TO GET THE COMMENT FROM THE FOOTER SECTION
		'''


	def getDatabase(self):
		"""
		Returns the current database name.
		"""
		return self.database

	def getTable(self):
		"""
		Returns the current table name.
		"""
		return self.table

	def setConnection(self,connection=None):	#Establishes a connection between the script and the mysql database
		"""
		Sets the connection the database
		"""
		if(connection == None):
			logging.info("Creating a new connection to the database")
			self.mysqlConnection = sql.mysqlConnector(option_files=(PATH+".config/mysql.cnf"),database=self.database)
			logging.info("Connection successful")
		else:
			logging.info("This connection in inherited from the calling function/script.")
			self.mysqlConnection = connection

	def processRequest(self):
		"""
		Process the request sent by the front end/calling script.
		"""
		logging.info("Processing request")
		self.conditionFlag  = False
		if(self.conditionList != None): #cannot test for len(self.conditionList) == 0 i.e when there is a empty list passed, raises TypeError
			for element in self.conditionList:
				logging.info("LevelNumber: {} - Creating a new sub process for conditionList with:".format(self.levelNumber)+str(element))
				subProcess = main(element,self.levelNumber + 1)
				subProcess.setConnection(self.mysqlConnection)
				if subProcess.processRequest():       #Ok, I have forgotten what this statement is supposed to mean
					logging.info("The condition flag is being set to True")
					self.conditionFlag = True
				else:
					logging.info("The condition flag is being set to False")
					self.conditionFlag = False
					break
		else:
			logging.info("conditionList is null")
		if(self.conditionList == None or self.conditionFlag == True): #cannot test for len(self.conditionList) == 0 i.e when there is a empty list passed, raises TypeError
			'''
			KIMS THAT WHEN A SELECT IS USED IT RETURNS DATA AND CANNOT BE USED TO UPDATE ANOTHER TABLE.
			I NEED TO RESTRUCTURE IT TO BE ABLE TO RETURN AS WELL AS RUN AN UPDATE.
			'''
			if(self.requestType == "insert"):
				self.mysqlConnection.insert(self.getTable(),self.fields)
			elif(self.requestType == "delete"):
				self.mysqlConnection.delete(self.getTable(),self.fields,self.whereClause)
			elif(self.requestType == "update"):
				self.mysqlConnection.update(self.getTable(),self.setClause,self.whereClause)
			elif(self.requestType == "select"):
				return self.mysqlConnection.select([self.getTable()],self.fields,self.whereClause)
			elif(self.requestType == "alter"):
				logging.warning("ALTER IS NOT SUPPORTED YET, WILL BE ADDED IN A NEWER VERSION!")
			if(self.updateList):
				try:
					for anObject in self.updateList:
						logging.info("LevelNumber: {} - Creating a new sub process for updateList with:".format(self.levelNumber)+str(anObject))
						subProcess = main(anObject,self.levelNumber + 1)
						subProcess.setConnection(self.mysqlConnection)
						subProcess.processRequest()
				except TypeError:
					logging.critical("TypeError was raised when processing a condition expected a dict type got {}".format(type(anObject)))
					exit(0)
				except BaseException as e:
					logging.info("Exception Raised:"+str(e))
					exit(0)
			if(self.levelNumber == 0):
				self.mysqlConnection.commitChanges()


	def generateAnalytics(self):		#Write # logger function for this
		"""
		This is still incomplete
		"""
		if(self.conditionFlag == False):
			return
		else:
			genAnalytics = analytics.analytics(self.mysqlConnection,**self.analyticsArguments)
			genAnalytics.generateAnalytics(self.runCondition)
		return



if __name__ == '__main__':
	logging.info("Start of database.py")
	if(len(sys.argv) == 2):
		process = main(sys.argv[1],0)
		process.setConnection()
		process.processRequest()
		process.generateAnalytics()
	else:
		logging.critical("Invalid number of arguments was passed the script.")
	logging.info("End of database.py")
else:
	print("This code does not support being imported as a module")
	exit(0)